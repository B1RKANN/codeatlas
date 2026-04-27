# CodeAtlas API

FastAPI, PostgreSQL, SQLAlchemy ve Alembic kullanan auth servisi. Ayrıca proje zip dosyalarını Tree-sitter ile analiz edip Gemini destekli Mermaid mimari çıktısı üreten analiz endpointi içerir.

## Kurulum

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env` içindeki `DATABASE_URL` değerini yerel PostgreSQL kurulumuna göre güncelle.
Gemini destekli mimari özet için `.env` içindeki `GEMINI_API_KEY` değerini doldur. Bu değer boşsa analiz endpointi yalnızca yerel Tree-sitter çıktısından fallback özet ve Mermaid diyagramı döner.
Gemini tarafında `429`, `500`, `502`, `503` veya `504` gibi geçici hatalar olursa istek varsayılan olarak 2 kez tekrar denenir. `GEMINI_MAX_RETRIES` ve `GEMINI_RETRY_BACKOFF_SECONDS` ile bu davranışı değiştirebilirsin. `429` rate-limit hatası tüketilirse servis `GEMINI_RATE_LIMIT_COOLDOWN_SECONDS` süresince Gemini'yi tekrar çağırmadan yerel analize düşer.
Analiz servisi büyük projelerde Gemini prompt'una girecek dosyaları lokal `BAAI/bge-m3` embedding modeliyle semantik olarak sıralar. `SEMANTIC_ANALYSIS_ENABLED`, `SEMANTIC_EMBEDDING_MODEL` ve `SEMANTIC_MAX_PROMPT_FILES` ile bu davranışı değiştirebilirsin. Dosya sayısı limitin altındaysa model yüklenmez.

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

Migration varsayılan olarak uygulama başlangıcında otomatik çalışmaz. Otomatik çalışmasını istersen `.env` içine `RUN_MIGRATIONS_ON_STARTUP=true` ekleyebilirsin.

## Uygulamayı Çalıştırma

```powershell
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

## Endpointler

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /analysis/upload`
- `GET /health`

## Proje Analizi

`POST /analysis/upload` endpointi token gerektirmez ve `multipart/form-data` içinde `file` alanı ile `.zip` bekler.

İlk etapta desteklenen dosya türleri:

- Python: `.py`
- JavaScript: `.js`, `.jsx`
- TypeScript: `.ts`, `.tsx`

Güvenlik limitleri `.env` üzerinden değiştirilebilir:

- `ANALYSIS_MAX_ZIP_BYTES`
- `ANALYSIS_MAX_UNCOMPRESSED_BYTES`
- `ANALYSIS_MAX_SOURCE_FILE_BYTES`
- `ANALYSIS_MAX_FILES`

Varsayılan limitler: 100 MB zip, 300 MB açılmış toplam boyut, dosya başına 512 KB kaynak kod ve ignore sonrası 5000 analiz edilebilir dosya.
