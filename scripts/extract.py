#!/usr/bin/env python3
"""Extract DocType relationships from an ERPNext/Frappe (MariaDB) SQL dump.

Usage: python3 scripts/extract.py dump.sql.gz [data.json]

Reads tabDocType, tabDocField, tabCustom Field and tabProperty Setter and
writes data.json (nodes + Link / Table / Table MultiSelect relations).
"""
import collections, gzip, json, re, sys

TABLES = ['tabDocType', 'tabDocField', 'tabCustom Field', 'tabProperty Setter']


def read_tables(path):
    """Keep only the CREATE/INSERT statements of the tables we need."""
    opener = gzip.open if path.endswith('.gz') else open
    keep, out = False, []
    pat = re.compile(r'^(?:DROP TABLE IF EXISTS|CREATE TABLE|LOCK TABLES|INSERT INTO) `([^`]+)`')
    with opener(path, 'rt', encoding='utf8', errors='replace') as f:
        for line in f:
            m = pat.match(line)
            if m and line.startswith('DROP TABLE'):
                keep = m.group(1) in TABLES
            if keep:
                out.append(line)
    return ''.join(out)


def cols_of(txt, table):
    m = re.search(r'CREATE TABLE `%s` \((.*?)\n\) ENGINE' % re.escape(table), txt, re.S)
    return [mm.group(1) for mm in (re.match(r'\s*`([^`]+)`', l) for l in m.group(1).split('\n')) if mm]


def parse_values(s):
    rows, i, n = [], 0, len(s)
    while i < n:
        if s[i] != '(':
            i += 1
            continue
        i += 1
        row = []
        while True:
            if s[i] == "'":
                i += 1
                buf = []
                while True:
                    c = s[i]
                    if c == '\\':
                        buf.append({'n': '\n', 'r': '\r', 't': '\t', '0': '\0', 'Z': '\x1a'}.get(s[i + 1], s[i + 1]))
                        i += 2
                    elif c == "'":
                        if i + 1 < n and s[i + 1] == "'":
                            buf.append("'")
                            i += 2
                        else:
                            i += 1
                            break
                    else:
                        buf.append(c)
                        i += 1
                row.append(''.join(buf))
            else:
                j = i
                while s[j] not in ',)':
                    j += 1
                tok = s[i:j]
                i = j
                row.append(None if tok == 'NULL' else tok)
            if s[i] == ',':
                i += 1
                continue
            i += 1
            break
        rows.append(row)
    return rows


def load(txt, table):
    cols = cols_of(txt, table)
    pat = r'^INSERT INTO `%s`(?: \([^)]*\))? VALUES (.*);$' % re.escape(table)
    return [dict(zip(cols, r)) for m in re.finditer(pat, txt, re.M) for r in parse_values(m.group(1))]


def build(raw):
    dts = {d['name']: d for d in raw['tabDocType']}
    flag = lambda x: str(x) == '1'
    nodes = {n: dict(id=n, module=d['module'], flags=(1 if flag(d['custom']) else 0) | (2 if flag(d['istable']) else 0)
                     | (4 if flag(d['issingle']) else 0) | (8 if flag(d['is_submittable']) else 0)
                     | (16 if flag(d.get('is_virtual')) else 0), fields=0, custom=0) for n, d in dts.items()}
    fields = [dict(p=f['parent'], fn=f['fieldname'], t=f['fieldtype'], o=f['options'], c=False,
                   r=1 if f.get('reqd') == '1' else 0, i=int(f.get('idx') or 0))
              for f in raw['tabDocField'] if f['parent'] in dts and f['parenttype'] == 'DocType']
    fields += [dict(p=f['dt'], fn=f['fieldname'], t=f['fieldtype'], o=f['options'], c=True,
                    r=1 if f.get('reqd') == '1' else 0, i=10**6 + int(f.get('idx') or 0))
               for f in raw['tabCustom Field'] if f['dt'] in dts]
    LAYOUT = {'Section Break', 'Column Break', 'Tab Break', 'HTML', 'Fold', 'Heading'}
    flist = collections.defaultdict(list)
    ps = {(p['doc_type'], p['field_name']): p['value'] for p in raw['tabProperty Setter']
          if p['property'] == 'options' and p['doctype_or_field'] == 'DocField'}
    edges, dyn, missing = collections.OrderedDict(), 0, collections.Counter()
    for f in fields:
        f['o'] = ps.get((f['p'], f['fn']), f['o'])
        nodes[f['p']]['custom' if f['c'] else 'fields'] += 1
        if f['t'] not in LAYOUT and f['fn']:
            flist[f['p']].append((f['i'], [f['fn'], f['t'], f['r'], 1 if f['c'] else 0]))
        if f['t'] in ('Link', 'Table', 'Table MultiSelect') and f['o']:
            o = f['o'].strip()
            if o not in dts:
                missing[o] += 1
                continue
            k = 0 if f['t'] == 'Link' else 1
            e = edges.setdefault((f['p'], o, k), dict(s=f['p'], t=o, k=k, c=False, f=[]))
            e['f'].append(f['fn'])
            e['c'] = e['c'] or f['c']
        elif f['t'] == 'Dynamic Link':
            dyn += 1
    idx = {n: i for i, n in enumerate(nodes)}
    N = [[n['id'], n['module'], n['flags'], n['fields'], n['custom'], [x for _, x in sorted(flist[n['id']], key=lambda y: y[0])]]
         for n in nodes.values()]
    E = [[idx[e['s']], idx[e['t']], e['k'], 1 if e['c'] else 0, e['f']] for e in edges.values()]
    return {'n': N, 'e': E, 'd': dyn}, missing


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    txt = read_tables(sys.argv[1])
    raw = {t: load(txt, t) for t in TABLES}
    data, missing = build(raw)
    out = sys.argv[2] if len(sys.argv) > 2 else 'data.json'
    json.dump(data, open(out, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print(f"{len(data['n'])} DocTypes, {len(data['e'])} relations, {data['d']} Dynamic Links skipped -> {out}")
    if missing:
        print('Link targets missing from the database:', dict(missing))
