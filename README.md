# Django Project

## Chạy project (development)

```bash
# 1. Tạo virtual environment (chỉ lần đầu)
python -m venv venv

# 2. Active venv (Windows)
venv\Scripts\activate

# 3. Cài dependencies
pip install -r requirements.txt

# 4. Chạy migrations
python manage.py migrate

# 5. Run server
python manage.py runserver

# Vào http://localhost:8000/
```

## Chạy tests

```bash
python manage.py test tasks
```

## Docker

```bash
docker compose up --build
```
