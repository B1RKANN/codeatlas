# CodeAtlas Auth API

FastAPI, PostgreSQL, SQLAlchemy ve Alembic kullanan temel auth servisi.

## Kurulum

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env` içindeki `DATABASE_URL` değerini yerel PostgreSQL kurulumuna göre güncelle.

## Veritabanı

Önce PostgreSQL içinde `codeatlas` veritabanını oluştur:

```sql
CREATE DATABASE codeatlas;
```

Sonra migration çalıştır:

```powershell
.venv\Scripts\Activate.ps1
alembic upgrade head
```

## Uygulamayı Çalıştırma

```powershell
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## Endpointler

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /health`
