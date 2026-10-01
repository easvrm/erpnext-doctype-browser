#!/usr/bin/env python3
"""Inject data.json into src/template.html and write docs/index.html."""
import pathlib, sys
root = pathlib.Path(__file__).resolve().parent.parent
data = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'data.json').read_text(encoding='utf8')
body = (root / 'src' / 'template.html').read_text(encoding='utf8').replace('__DATA__', data)
html = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n' + body)
out = root / 'docs' / 'index.html'
out.parent.mkdir(exist_ok=True)
out.write_text(html, encoding='utf8')
print(out.relative_to(root), len(html), 'bytes')
