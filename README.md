# erpnext-doctype-browser

Interactive map of ERPNext DocType relationships, one diagram per module.

```bash
python3 scripts/extract.py dump.sql.gz data.json   # extract relationships from a database dump
python3 scripts/build.py data.json                 # generate docs/index.html
```

`docs/index.html` is self-contained (d3 is loaded from cdnjs) and is served by GitHub Pages.
The dump and `data.json` are not versioned.
