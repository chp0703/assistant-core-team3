# Lab 04 Baseline Test Log

This log records the baseline verification performed before integrating the remaining Lab 04 tasks.

## Environment

- Project: `public_materials/lab04/starter`
- Branch: `feat/lab04-phat-foundation`
- Date: 2026-10-31
- Python executable: `C:\msys64\ucrt64\bin\python.exe`

## Static validation

Command:

```powershell
python -c "import ast,pathlib; files=list(pathlib.Path('src').rglob('*.py')); [ast.parse(p.read_text(encoding='utf-8')) for p in files]; print(f'AST parse: PASS ({len(files)} files)')"
```

Result:

```text
AST parse: PASS (16 files)
```

## Pytest baseline

Command:

```powershell
python -m pytest -q
```

Result:

```text
FAIL - No module named pytest
```

The test suite could not start because the current environment does not have the Lab 04 dependencies installed.

## Uvicorn access history

Command:

```powershell
python -m uvicorn assistant_api.main:create_app --factory --host 127.0.0.1 --port 8765
```

Result:

```text
FAIL - No module named uvicorn
```

The server did not start, so `/health`, `/docs`, and `/openapi.json` could not be accessed during this baseline run.

## Reproduction after installing dependencies

```powershell
pip install -r requirements.txt
pip install -e .
python -m pytest -q
python -m uvicorn assistant_api.main:create_app --factory --host 127.0.0.1 --port 8765
```

With the server running, verify these URLs from another terminal:

```powershell
Invoke-WebRequest http://127.0.0.1:8765/health
Invoke-WebRequest http://127.0.0.1:8765/docs
Invoke-WebRequest http://127.0.0.1:8765/openapi.json
```

Expected baseline responses:

- `/health`: HTTP 200 with `{"status":"ok","version":"1.0.0"}`
- `/docs`: HTTP 200 Swagger UI page
- `/openapi.json`: HTTP 200 OpenAPI document
