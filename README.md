# erpnext-doctype-browser

Carte interactive des relations entre DocTypes ERPNext, un diagramme par module.

```bash
python3 scripts/extract.py dump.sql.gz data.json   # extrait les relations du dump
python3 scripts/build.py data.json                 # génère dist/index.html
```

`dist/index.html` est autonome (d3 chargé depuis cdnjs). Le dump et `data.json` ne sont pas versionnés.
