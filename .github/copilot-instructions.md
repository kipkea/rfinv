<!-- Copied/created by AI assistant: concise, actionable guidance for agent contributions -->
# Copilot instructions for the rfinv repository

This file contains brief, concrete notes to help an AI coding agent be productive immediately in this codebase.

- Project type: Django web app (project root `rfinv/`) with a single API app `rvapi` and several helper scripts under `r3/` (hardware scanning/Kivy UI).
- Django version in requirements: see `req.txt` (Django 5.x). Database: sqlite3 (`db.sqlite3`) by default.

Key concepts and files
- API app: `rvapi/`
  - Models: `rvapi/models.py` — main domain objects: `RFIDTag`, `Location`, `Inventory`, `Inspection`.
  - Serializers: `rvapi/serializers.py` — nested serializers (e.g. `Inventory_SL` includes `RFIDTag_SL`). Note the `_SL` suffix convention.
  - Views: `rvapi/views.py` — mix of `APIView` and `ModelViewSet`. Permissions commonly use API keys or normal auth: `permission_classes = [ HasAPIKey | IsAuthenticatedOrReadOnly ]`.
  - URLs: `rvapi/urls.py` — router exposes `rfidtags`, `locations`, `inventorys` (note: plural is `inventorys` in code), and `inspections`.

- Project settings: `rfinv/settings.py`
  - Static files: `STATIC_ROOT` -> `root_static/`, extra static dirs in `assets/`.
  - API key header: `API_KEY_CUSTOM_HEADER = "HTTP_X_API_KEY"`. The codebase uses both `x-api-key` and Authorization forms; follow existing usage in `r3/scan.py` and views.
  - REST framework defaults require authentication + API key class. Swagger/docs endpoints are mounted (see `rfinv/urls.py`).

- Hardware / edge scripts: `r3/scan.py` — Raspberry Pi serial reader and API client. It calls endpoints like `/api/inventorys/` and uses header `x-api-key` (see variables `APISERVER` and `key`). Treat `r3/` scripts as consumers of the API, not part of the Django runtime.

- Deployment notes: `aws/server config.txt` contains a worked example for gunicorn + nginx on Ubuntu (systemd unit files and Nginx config). Use it for production guidance.

Developer workflows (concrete commands)
- Create/activate virtualenv (Windows PowerShell):
  - .\env\Scripts\Activate.ps1  (or run .\env\Scripts\activate)
- Install dependencies:
  - pip install -r req.txt
- Common Django commands (run from repository root where `manage.py` lives):
  - python manage.py makemigrations
  - python manage.py migrate
  - python manage.py createsuperuser
  - python manage.py runserver 0.0.0.0:8000
  - python manage.py collectstatic

Project-specific conventions and gotchas
- API key handling: codebase uses djangorestframework-api-key and also custom header `x-api-key`. Many client scripts set `headers = {'x-api-key': key}` while some curl examples use `Authorization: Api-Key <key>` — prefer `x-api-key` when replicating existing client behavior (see `r3/scan.py`).
- Plural naming: endpoint names may be misspelled (e.g., `inventorys` not `inventories`). Always read `rvapi/urls.py` to confirm endpoint paths.
- Serializer naming: serializer classes end with `_SL` and often embed `RFIDTag_SL` inside `Inventory_SL`/`Location_SL`. When creating new serializers, follow that nested pattern.
- Permissions: views frequently allow either an API key OR authenticated user. Use `HasAPIKey | IsAuthenticatedOrReadOnly` to match existing intent.

Integration points
- `r3/scan.py` and other `r3/` scripts call the REST API (APISERVER + x-api-key). Changes to API contracts must consider these clients.
- `aws/` folder contains deployment keys and server instructions — do not hard-code new secrets; prefer environment variables (project already uses `django-environ`).

Where to look for examples
- Read `rvapi/views.py` for concrete view patterns (APIView + ViewSet + custom @action `missing_items`).
- Read `rvapi/serializers.py` for nested serializer examples and field choices.
- Read `r3/scan.py` for an example API consumer and header usage, plus hardware assumptions (serial port, GPIO pins).

If you need to change behavior
- Update or add unit tests in `rvapi/tests.py` where possible. If adding endpoints, register with router in `rvapi/urls.py`.
- When touching settings, prefer using environment variables via `django-environ` (the project already calls `environ.Env.read_env()`).

Notes for the next iteration
- Ask the repo owner where secrets/keys should be stored (current repo contains `aws/rfINV.pem` and local `env/` virtualenv). Avoid committing secrets.

If anything above is unclear or you want more detail (example requests/responses, missing endpoints, or tests), tell me which area to expand and I'll update this doc.
