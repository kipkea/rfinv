<!-- Copied/created by AI assistant: concise, actionable guidance for agent contributions -->
# Copilot instructions for the rfinv repository

This file contains brief, concrete notes to help an AI coding agent be productive immediately in this codebase.

## Project overview
- **Type**: Django REST API + Raspberry Pi edge devices + Kivy touch UI
- **Scope**: RFID inventory & location tracking system with asset inspections
- **Architecture**: Django 5.x monolith (`rfinv/` project) + single API app (`rvapi/`) + Raspberry Pi clients (`r3/`) + Windows development UI (`r3/kv_win/`)
- **Database**: sqlite3 (`db.sqlite3`) locally; production uses same engine
- **Localization**: Thai language (LANGUAGE_CODE='th-TH', TIME_ZONE='Asia/Bangkok')

## Core domain model (rvapi/models.py)
**Data relationships** follow asset tracking workflow:
- `RFIDTag`: Unique RFID identifiers (raw tag data, ~100 char max). Can be locations (`is_location=True`) or inventory items.
- `Location`: Place where items are stored—references an `RFIDTag` (one-to-one). Has name and audit trail (recorded_by, recorded_at).
- `Inventory`: Physical asset/item with unique `RFIDTag`. Last-location tracking: `Inv_Last_Loc` (FK to Location) + `Inv_Last_Check_Time` (timestamp). Updated **externally in views** during inspections (not auto on save).
- `Inspection`: Captures asset audit event at a specific location. Has `location` (FK, PROTECT), `inspected_inventories` (M2M), `inspected_by` (user), `inspected_at` (datetime, default=now, not auto). **Critical**: View code responsible for updating Inventory.Inv_Last_Loc/Inv_Last_Check_Time after Inspection.save().
- `InventoryImage`: Photos tied to Inventory + optional Location. Stores GPS coordinates, photographer, timestamp.

**Note**: Thai comments in code explain intent; preserve them on modifications to audit trail fields.

## Key concepts and files
- **API app: `rvapi/`**
  - Models: `rvapi/models.py` — domain objects as above
  - Serializers: `rvapi/serializers.py` — nested serializers (e.g., `Inventory_SL` nests `RFIDTag_SL`). **Convention**: `_SL` suffix = serializer class.
  - Views: `rvapi/views.py` — mix of `APIView` (custom logic) and `ModelViewSet` (CRUD). 
    - Permissions: `permission_classes = [HasAPIKey | IsAuthenticatedOrReadOnly]` (both auth forms supported).
    - Custom action example: `@action(detail=False, methods=['get']) def missing_items(...)` on `InspectionViewSet` queries Inventory items not inspected in 30 days.
  - URLs: `rvapi/urls.py` — router auto-exposes `rfidtags`, `locations`, `inventorys` (note misspelling), `inspections`. Custom paths: `/api/basic/` (RFIDTagViewAll), `/api/inv/<tagNo>/` (INV_Info).

- **Project settings: `rfinv/settings.py`**
  - Localization: `LANGUAGE_CODE='th-TH'`, `TIME_ZONE='Asia/Bangkok'` (used in date serialization).
  - CORS: `CORS_ALLOW_ALL_ORIGINS=True` (dev mode; change for production).
  - Static files: `STATIC_ROOT='root_static/'`, `STATICFILES_DIRS=['assets/']` for custom static.
  - API authentication: `API_KEY_CUSTOM_HEADER="HTTP_X_API_KEY"`. Clients send header `x-api-key: <key>` (djangorestframework-api-key).
  - REST framework defaults: `DEFAULT_PERMISSION_CLASSES=[IsAuthenticated, HasAPIKey]`. Swagger docs: `/api-docs/` and `/swagger-docs/`.

- **Hardware / edge scripts: `r3/`**
  - `r3/scan.py` — Raspberry Pi RFID serial reader + API client. Hard-coded variables: `APISERVER` (IP:port), `key` (API key). Uses `requests` with `headers={'x-api-key': key}`. Calls `/api/inventorys/` endpoints. GPIO pins defined: `RFID_EN_PIN=4`, serial port `/dev/ttyAMA0` at 38400 baud. Treat as external API consumer; changes to endpoints must consider this client.
  - `r3/kv/kivy_kiosk_app.py` — Kivy touch UI for Raspberry Pi (fullscreen, no escape). Multi-tab interface with camera integration (e.g., Tab 1 for image display, Tab 2 for settings). Thai font support: imports `THSarabunNew.ttf`.
  - `r3/kv_win/k*.py` — Windows dev versions of Kivy UI (not deployed on hardware).
  - Multiple `rpicam*` variants: experimental camera pipelines (opencv, local processing, etc.).

- **Deployment: `aws/server config.txt`** — worked example for gunicorn + nginx on Ubuntu (systemd units, nginx config). Reference for production setup.

## Developer workflows
**Setup** (Windows PowerShell from repo root):
```powershell
# Activate virtualenv
.\env\Scripts\Activate.ps1

# Install dependencies
pip install -r req.txt

# First-time DB setup
python manage.py migrate
python manage.py createsuperuser

# Collect static files (dev only if needed)
python manage.py collectstatic --noinput
```

**Local development**:
```powershell
# Run dev server on all interfaces (for testing from other machines)
python manage.py runserver 0.0.0.0:8000

# Make schema changes
python manage.py makemigrations rvapi
python manage.py migrate

# Reset DB (destructive—use for dev only)
rm db.sqlite3
python manage.py migrate
```

**Testing**: `rvapi/tests.py` is minimal. Add test cases for new views/serializers following Django TestCase patterns. Run via `python manage.py test rvapi`.

**Docker/Raspberry Pi**: No Dockerfile in repo; deployment is manual (see `aws/server config.txt` for gunicorn + systemd reference).

## Project-specific conventions and patterns
**Naming gotchas**:
- Endpoint plurals: `inventorys` (not `inventories`)—always confirm in `rvapi/urls.py`.
- Serializer suffix: Classes end with `_SL` (e.g., `RFIDTag_SL`, `Inventory_SL`).
- Model field audit trail: `recorded_by` (User FK), `recorded_at` (auto_now_add). Preserve Thai comments explaining these.
- Inspection behavior: `inspected_at` uses `default=timezone.now` (not `auto_now_add`), allowing historical corrections. View code **must** update `Inventory.Inv_Last_Loc` and `Inv_Last_Check_Time` after creating/updating Inspection (see comment in `models.py`).

**API authentication**:
- Two forms coexist: API key (`x-api-key: <key>` header) or user auth (`Authorization: Api-Key`).
- All views use permission: `[HasAPIKey | IsAuthenticatedOrReadOnly]` to support both.
- `r3/scan.py` uses `headers={'x-api-key': key}` pattern—maintain compatibility.
- API key defined in `settings.API_KEY_CUSTOM_HEADER = "HTTP_X_API_KEY"`.

**Serializers**:
- Nested pattern: `Inventory_SL` embeds `rfid_tag = RFIDTag_SL()`, `Location_SL` embeds `rfid_tag = RFIDTag_SL()`.
- Use `fields = '__all__'` for simplicity (no selective exposure yet).
- Custom serializers (if added) should follow `_SL` suffix and same nesting pattern.

**Permissions & CORS**:
- `CORS_ALLOW_ALL_ORIGINS=True` in dev (production: restrict).
- Thai localization active: dates/times serialize in Bangkok timezone.

**Kivy UI conventions** (`r3/kv/`):
- Config set before imports: `Config.set('graphics', 'fullscreen', 'auto')`, `Config.set('kivy', 'exit_on_escape', '0')`.
- Thai font: `THSarabunNew.ttf` in working directory or imported directly.
- Multi-tab `TabbedPanel` structure: each tab is a `TabbedPanelItem` with layout hierarchy.

## Integration points & data flows
- **API-to-Hardware**: `r3/scan.py` is the primary consumer. It:
  - Reads RFID tags via serial port (`/dev/ttyAMA0`, 38400 baud).
  - Calls API endpoints (e.g., POST `/api/inventorys/`, GET `/api/inv/<tagNo>/`) using `requests` + `x-api-key` header.
  - Hard-coded: `APISERVER`, `key`, GPIO pin `RFID_EN_PIN=4`.
  - **Any API contract changes must account for this client.**
- **Kivy UI-to-API**: Kivy apps (`r3/kv/kivy_kiosk_app.py`, `r3/kv_win/k*.py`) are separate consumers. May also use API client patterns; check if HTTP calls present before modifying API.
- **Deployment**: `aws/` contains server deployment keys/config. Use environment variables (via `django-environ`) to avoid hardcoding secrets in code.
- **Static files**: Custom static served from `assets/` (collected to `root_static/` on production); media uploads go to `root_media/`.

## Where to look for examples
- **View patterns**: `rvapi/views.py` — APIView + ViewSet examples, custom @action decorator usage (`missing_items` on InspectionViewSet).
- **Serializer nesting**: `rvapi/serializers.py` — how `RFIDTag_SL` embeds in other serializers.
- **API consumer**: `r3/scan.py` — header usage, error handling, hard-coded config variables.
- **Kivy structure**: `r3/kv/kivy_kiosk_app.py` — TabbedPanel layout, Thai font integration, fullscreen config.
- **Database schema**: Run `python manage.py migrate --dry-run` to preview schema; inspect `rvapi/migrations/` for historical changes.

## When modifying this codebase
1. **Adding API endpoints**: Register in `rvapi/urls.py` router or URLpatterns; ensure `_SL` serializer exists and uses nested `RFIDTag_SL` if referencing RFID tags.
2. **Updating Inspection model**: Remember that Inventory audit fields (`Inv_Last_Loc`, `Inv_Last_Check_Time`) are updated **in view code**, not model save(). Preserve Thai comments explaining this.
3. **Changing authentication**: Both `HasAPIKey` and user auth must remain compatible. Test with `x-api-key: <key>` header (as `r3/scan.py` uses it).
4. **Modifying settings**: Use `environ.Env()` for production overrides (project already calls `environ.Env.read_env()`); avoid hardcoding secrets.
5. **Adding tests**: Follow Django TestCase pattern in `rvapi/tests.py`; run with `python manage.py test rvapi`.
6. **Kivy UI changes**: Thai font must be available (`THSarabunNew.ttf`); test fullscreen + no-escape config on actual Pi before merging.

## Architecture decisions (the "why")
- **Inspection.inspected_at uses default=timezone.now** (not auto_now_add): Allows backdating inspections for historical audit records.
- **Location.on_delete=PROTECT** on Inspection FK: Prevents accidental data loss if a location is deleted while inspections reference it.
- **Nested serializers with RFIDTag**: Avoids separate calls to fetch tag data; API responses include both tag and entity info.
- **Thai localization in settings**: All timestamps serialize in Asia/Bangkok timezone for consistency across devices.

## Known technical debt & gotchas
- `rvapi/tests.py` is minimal—add tests for new endpoints before merging.
- Some Kivy scripts are numbered iterations (`kv01.py` through `kv17.py`, `rpicam` through `rpicam4`). Check timestamps/git history to identify the active one before editing.
- `aws/` contains RSA keys—do NOT commit secrets; use environment variables.
- CORS is wide open (`CORS_ALLOW_ALL_ORIGINS=True`) for dev; must be restricted for production.

If anything above is unclear, or to add more detail on specific sections, please provide feedback and this document will be updated.
