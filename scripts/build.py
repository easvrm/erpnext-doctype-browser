#!/usr/bin/env python3
"""Injecte data.json dans src/template.html -> dist/index.html."""
import pathlib, sys
root = pathlib.Path(__file__).resolve().parent.parent
data = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'data.json').read_text(encoding='utf8')
html = (root / 'src' / 'template.html').read_text(encoding='utf8').replace('__DATA__', data)
(root / 'dist' / 'index.html').write_text(html, encoding='utf8')
print('dist/index.html', len(html), 'octets')
