# Mahad Group Accounting Suite

Short dev notes and how to view API documentation

## Quick start (development)

1. Create and activate a virtualenv, then install requirements:

```bash
# from repo root
python -m venv venv
source venv/bin/activate
pip install -r config/requirements.txt
```

2. Run Django checks and start the server:

```bash
python3 config/manage.py check
python3 config/manage.py migrate
python3 config/manage.py runserver
```

3. Open the API docs in your browser:

- Swagger UI (interactive): http://127.0.0.1:8000/api/docs/
- ReDoc UI: http://127.0.0.1:8000/api/redoc/
- Raw OpenAPI schema: http://127.0.0.1:8000/api/schema/

Notes:
- `drf-spectacular` is used for OpenAPI 3 schema generation.
- If you add custom view/serializer docs, refer to drf-spectacular docs: https://drf-spectacular.readthedocs.io/
- In production, consider restricting access to docs or turning off DEBUG.

If you'd like, I can also add a brief `docs/` page or generate a static OpenAPI JSON file checked into the repo.
