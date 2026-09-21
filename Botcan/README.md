# Scraper Demo Site

A local HTML playground for testing all actions in the Scraper module.

## Quick Start

```bash
# 1. Create output directory (screenshots & JSON results go here)
mkdir -p output

# 2. Run the scraper with the demo recipe
python main.py
```

**Note:** Update `main.py` to load `demo_recipe.yaml` instead of `scrape.yaml`, or run:

```bash
python -c "
from scraper import Scraper
from pathlib import Path
bot = Scraper()
bot.start(False)
bot.read_recipe(bot.load_recipe(Path('demo_recipe.yaml')))
"
```

## What Each Action Tests

| Action | What it does | Where in demo site |
|---|---|---|
| `open` | Load the HTML file | — |
| `click` | Click tab links by text | Products, About, Contact, Blog, Lab |
| `extract` (single) | Grab single element text | Home, Contact, Lab |
| `extract` (all) | Grab lists of matching elements | Home, Products, About, Blog, Lab |
| `extract` (first) | Grab first matching element only | Home |
| `fill` | Type into form fields | Contact (name, email, message) |
| `select` | Choose dropdown option | Contact (subject), Lab (standalone) |
| `hover` | Hover to reveal hidden content | Lab (hover-card) |
| `scroll` | Scroll to a specific element | Lab (scroll-target) |
| `screenshot` | Capture a page screenshot | — |
| `save` | Write extracted data to JSON | — |
| `close` | Close the browser | — |

## Page Structure

| Tab | Elements |
|---|---|
| **Home** | Heading, feature list (5 items), testimonials (3) |
| **Products** | 6 product cards with name, price, description |
| **About** | Team member list (5 items) |
| **Contact** | Name/email inputs, subject dropdown, message textarea |
| **Blog** | 2 blog article cards |
| **Lab** | Hover card, dropdown, load-more button, secret data element, scroll container |

## Output

```
output/
├── demo_screenshot.png    # Full-page screenshot
└── demo_results.json      # All extracted data in JSON format
```

## MCP server (for Naoki)

`mcp_server.py` exposes Botcan over the MCP stdio protocol so Naoki can
call it as tools (`botcan_scrape`, `botcan_run_recipe`,
`botcan_screenshot`). No daemon needed -- clients spawn it per call:

```bash
../ml_shit/bin/python mcp_server.py
```

Needs this venv's `playwright` + `mcp` packages and a headless Firefox
(`../ml_shit/bin/python -m playwright install firefox`). First run
downloads the browser; the server itself is stateless (fresh browser
per tool call, always closed).

## Supported Actions Reference

```yaml
# --- Navigation ---
open: <url>
close:

# --- Interacting ---
click:
  selector: <css-selector>
  text: <optional-text-filter>

fill:
  selector: <css-selector>
  value: <text-to-type>

select:
  selector: <css-selector>
  value: <option-value>
  # label: <option-label>
  # index: <number>

hover:
  selector: <css-selector>

scroll:
  selector: <css-selector>
  # amount: <pixels>

# --- Extracting ---
extract:
  selector: <css-selector>
  # all: true
  # first: true

# --- Output ---
screenshot:
  path: <filepath>
  full_page: true

save:
  path: <filepath>
  format: json
  # format: csv
```
