# RFID Inventory Kivy App

This Kivy app provides a tabbed UI for:

- Login authentication via an API
- Importing RFID tags in bulk
- Registering inventory items with RFID tags and optional images
- Defining RFID-based locations
- Inspecting items by location and logging inspections

## Setup

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Run the application:

```bash
python main.py
```

## API Configuration

The app uses `http://localhost:8000` by default. If your Django API uses different endpoints, update `API_BASE_URL` and endpoint paths in `main.py`.

### Expected API endpoints

- `POST /api/token/` or `/api/login/` for authentication
- `GET/POST /api/rfid-tags/` for RFID tags
- `GET/POST /api/inventory/` for inventory records
- `GET/POST /api/locations/` for location records
- `GET/POST /api/inspections/` for inspections

If your Django REST API uses different paths, adjust the client methods in `main.py`.
