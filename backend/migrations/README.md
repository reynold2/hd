# Backend Migrations

Alembic manages production schema changes.

Common commands from `D:\3d\fh\backend`:

```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "describe change"
```

Set `DATABASE_URL` before running migrations against MySQL:

```powershell
$env:DATABASE_URL = "mysql+pymysql://queue:secret@127.0.0.1:3306/queue_calling?charset=utf8mb4"
..\.venv\Scripts\python.exe -m alembic upgrade head
```
