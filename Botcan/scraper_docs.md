# Botcan Recipe Reference

A recipe is a YAML mapping with up to three **top-level** keys:

```yaml
open: <url>          # where to start
steps:               # list of action steps
  - <action>: { ... }
close:               # shut the browser down
```

`open` and `close` are top-level keys, **not** steps. `steps` is a list.

## URL rules

`open:` accepts:

- Full URLs: `https://example.com`
- Absolute file URIs: `file:///home/nishant/Nishant_stuff/Botcan/test/demo_site.html`

Relative paths resolve against the **process working directory**, which is not
necessarily `Botcan/`. Always use a full URL or an absolute `file://` URI.

## Actions

| Action | Options | Notes |
|---|---|---|
| `click` | `selector`, `text` (filter) | |
| `check` | `selector` | |
| `uncheck` | `selector` | |
| `clear` | `selector` | |
| `press` | `key`, `selector` (optional) | `key` required |
| `copy_link` | `selector`, `attr` (default `href`), `key` | copies to clipboard |
| `download` | `selector`, `path`, `text` (filter) | `path` required |
| `extract` | `selector`, `all`, `first` | |
| `fill` | `selector`, `value` | |
| `screenshot` | `path`, `full_page` | |
| `save` | `path`, `format` (`json` / `csv`) | |
| `select` | `selector`, `label` / `value` / `index` | |
| `hover` | `selector` | |
| `wait` | `selector` + `state`, or `timeout`, or `load_state` | |
| `scroll` | `selector`, `amount` | |

## Minimal example

```yaml
open: file:///home/nishant/Nishant_stuff/Botcan/test/demo_site.html
steps:
  - click:
      selector: .tab-link
      text: "Models"
  - extract:
      selector: .product-card h3
      all: true
close:
```

## Full example

See `test/demo_recipe.yaml` — a working recipe covering every action.
