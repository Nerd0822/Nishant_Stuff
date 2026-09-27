# Raahi — a road-trip companion for India

Pick a route on the map, ask the assistant what is worth stopping for along
the way, and share your own experiences on the explore feed.

## Features

- **Map** — Leaflet map with routing, live-location search, and nearby
  places (restaurants, hotels, cafes, fuel) from OpenStreetMap
- **Assistant** — local LLM chat (Ollama) + Wikipedia-grounded itineraries,
  running as Celery background jobs
- **Accounts** — register, login, profiles, search history, saved locations
- **Explore** — user posts with images, likes, comments, and share links
  (X / Facebook / WhatsApp) with Open Graph previews
- **Travel APIs** — free-tier places/hotels lookup with Redis caching;
  flights and buses are stubbed service functions ready for API keys

## Project layout

```
Raahi/
├── Backend/               # Django project (manage.py, CORE/, home/, accounts/, explore/, travel/)
├── Frontend/              # templates/ + static/ (CSS, JS, vendor)
├── nginx/nginx.conf       # reverse proxy + load balancer (3 app instances)
├── Dockerfile             # gunicorn (uvicorn workers) + DEBUG=False
├── docker-compose.yml     # nginx, raahi1-3, celery, postgres, redis
├── requirements.txt
├── .env                   # all config, no hardcoded fallbacks in code
└── README.md
```

## Configuration

Every setting comes from `.env` — the code has no hardcoded fallbacks.
A missing variable fails fast with
`ImproperlyConfigured: Environment variable X is required but missing or empty.`

| Variable | Purpose |
|---|---|
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Django core |
| `POSTGRES_DB/USER/PASSWORD/HOST/PORT` | PostgreSQL (Docker service `db`, host port `5433`) |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Celery via Redis |
| `CACHE_URL` | Django cache via Redis |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | Local LLM |
| `FRONTEND_DIR` | Frontend path override (Docker only) |

## Local development

Prerequisites: Python 3.14 venv, Postgres + Redis in Docker, Ollama.

```bash
cd Backend
python manage.py migrate
python manage.py runserver
```

Start the infrastructure (postgres on :5433, redis internally):

```bash
docker compose up -d db redis
```

## Docker (3 instances + load balancer)

```bash
docker compose up -d --build
docker compose ps          # raahi1, raahi2, raahi3, celery, nginx, db, redis
```

Open http://localhost/ — nginx round-robins across the three gunicorn
instances. Each response carries an `X-Upstream` header naming the instance
that served it; hit refresh a few times to watch it rotate:

```bash
for i in 1 2 3 4; do curl -sI http://localhost/ | grep -i x-upstream; done
```

## Tests

Unit tests (mocked network, Postgres test database):

```bash
cd Backend
python manage.py test
```

Live Ollama pre-deploy gate — proves the model is up and replying.
Run this **before every deploy**; it fails if Ollama is unreachable:

```bash
RAAHI_LIVE_TESTS=1 python manage.py test home.test_ollama_live
```
