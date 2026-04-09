# Pulse Backend

A production-ready Django REST API with async WebSocket support, JWT authentication, task queuing, and full Docker orchestration.

**Stack:** Django 5 · DRF · PostgreSQL · Redis · Celery · Daphne · Django Channels · Djoser + SimpleJWT · drf-spectacular

---

## Project Structure

```
project/
├── config/
│   ├── settings/
│   │   ├── base.py           # Shared settings
│   │   ├── development.py    # Dev overrides
│   │   └── production.py     # Prod hardening + whitenoise + S3
│   ├── urls.py
│   └── asgi.py               # HTTP + WebSocket routing
├── core/                     # Abstract models, exceptions, permissions, pagination
├── apps/
│   ├── users/                # Custom email-based user model, JWT auth, RBAC
│   └── notifications/        # WebSocket consumers, JWT WS auth
├── celery_app/               # Celery factory + tasks + beat schedule
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── docker/
│   └── entrypoint.sh
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/pulse-macabalan-mcquinley-branch/pulse-backend.git
cd pulse-backend
cp .env.example .env
```

Open `.env` and set at minimum:

```ini
SECRET_KEY=your-50+-char-random-secret-key
DB_PASSWORD=your-db-password
```

### 2. Start all services

```bash
docker compose up --build
```

On first run, the `migrate` service automatically:

- Runs `makemigrations` for all apps
- Applies all migrations
- Exits cleanly before `web`, `worker`, and `beat` start

| Service      | URL                                                |
| ------------ | -------------------------------------------------- |
| Django API   | http://localhost:8000/api/v1/                      |
| Swagger UI   | http://localhost:8000/api/v1/docs/                 |
| ReDoc        | http://localhost:8000/api/v1/redoc/                |
| Django Admin | http://localhost:8000/admin/                       |
| pgAdmin      | http://localhost:5050 (run with `--profile tools`) |

### 3. Create a superuser

```bash
docker compose exec web python manage.py createsuperuser
```

---

## API Reference

### Authentication

**Register**

```bash
curl -X POST http://localhost:8000/api/v1/auth/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "password": "StrongPass@1",
    "re_password": "StrongPass@1"
  }'
```

**Login — get access + refresh tokens**

```bash
curl -X POST http://localhost:8000/api/v1/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "StrongPass@1"}'

# Response:
# {"access": "<access_token>", "refresh": "<refresh_token>"}
```

**Refresh access token**

```bash
curl -X POST http://localhost:8000/api/v1/auth/jwt/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh_token>"}'
```

**Logout — blacklist refresh token**

```bash
curl -X POST http://localhost:8000/api/v1/auth/token/logout/ \
  -H "Authorization: Bearer <access_token>"
```

### Users

**Get own profile**

```bash
curl http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer <access_token>"
```

**Update own profile**

```bash
curl -X PATCH http://localhost:8000/api/v1/users/me/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Updated"}'
```

**Change password**

```bash
curl -X POST http://localhost:8000/api/v1/users/me/change-password/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "StrongPass@1",
    "new_password": "NewPass@5678",
    "confirm_password": "NewPass@5678"
  }'
```

**List all users (admin only)**

```bash
curl http://localhost:8000/api/v1/users/?role=admin&search=jane \
  -H "Authorization: Bearer <admin_access_token>"
```

---

## WebSocket

Connect with a valid JWT access token as a query parameter:

```javascript
const ws = new WebSocket(
  "ws://localhost:8000/ws/notifications/?token=<access_token>",
);

// Receive real-time notifications
ws.onmessage = (e) => console.log(JSON.parse(e.data));

// Mark a notification as read
ws.send(JSON.stringify({ type: "mark_read", id: "<notification_uuid>" }));
```

On connect, the server sends:

```json
{ "type": "init", "unread_count": 3 }
```

Incoming notification shape:

```json
{
  "type": "notification",
  "payload": {
    "id": "<uuid>",
    "title": "...",
    "body": "...",
    "is_read": false,
    "created_at": "..."
  }
}
```

---

## Adding a New App

```bash
# 1. Create the app
docker compose run --rm web python manage.py startapp myapp apps/myapp

# 2. Add AppConfig to apps/myapp/apps.py
# 3. Add "apps.myapp.apps.MyappConfig" to LOCAL_APPS in config/settings/base.py
# 4. Add models, then restart — migrations run automatically
docker compose down && docker compose up
```

---

## Development Workflow

**Access a running container**

```bash
docker compose exec web bash
docker compose exec db psql -U django_user -d django_db
docker compose exec redis redis-cli
```

**Django shell**

```bash
docker compose exec web python manage.py shell
```

**Run tests**

```bash
docker compose exec web pytest --tb=short -v
docker compose exec web pytest --cov=apps --cov-report=term-missing
```

**Code quality**

```bash
docker compose exec web black .
docker compose exec web isort .
docker compose exec web flake8 .
```

---

## Celery

**Monitor tasks with Flower**

```bash
docker compose exec worker celery -A celery_app.celery flower --port=5555
# Open http://localhost:5555
```

**List registered tasks**

```bash
docker compose exec worker celery -A celery_app.celery inspect registered
```

**Trigger a task manually**

```bash
docker compose exec web python manage.py shell -c "
from celery_app.tasks import send_welcome_email
send_welcome_email.delay('<user_uuid>')
"
```

**Periodic tasks** are managed via the Django admin at `/admin/` under `django_celery_beat`.

---

## Environment Variables

| Variable                            | Description                   | Default                |
| ----------------------------------- | ----------------------------- | ---------------------- |
| `SECRET_KEY`                        | Django secret key             | — (required)           |
| `DEBUG`                             | Enable debug mode             | `False`                |
| `ALLOWED_HOSTS`                     | Comma-separated allowed hosts | `localhost,127.0.0.1`  |
| `DB_NAME`                           | PostgreSQL database name      | `django_db`            |
| `DB_USER`                           | PostgreSQL user               | `django_user`          |
| `DB_PASSWORD`                       | PostgreSQL password           | — (required)           |
| `DB_HOST`                           | PostgreSQL host               | `db`                   |
| `REDIS_URL`                         | Redis URL for cache/channels  | `redis://redis:6379/0` |
| `CELERY_BROKER_URL`                 | Celery broker URL             | `redis://redis:6379/1` |
| `CELERY_RESULT_BACKEND`             | Celery result backend URL     | `redis://redis:6379/2` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Access token TTL in minutes   | `60`                   |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS`   | Refresh token TTL in days     | `7`                    |
| `EMAIL_BACKEND`                     | Django email backend          | `console` (dev)        |
| `CORS_ALLOWED_ORIGINS`              | Comma-separated CORS origins  | —                      |
| `SENTRY_DSN`                        | Sentry error tracking DSN     | — (production)         |
| `AWS_STORAGE_BUCKET_NAME`           | S3 bucket for media files     | — (production)         |

---

## Service Ports

| Service             | Port |
| ------------------- | ---- |
| Django API (Daphne) | 8000 |
| PostgreSQL          | 5432 |
| Redis               | 6379 |
| pgAdmin             | 5050 |

---

## Production Checklist

- [ ] Set a strong `SECRET_KEY` (50+ random characters)
- [ ] Set `DEBUG=False`
- [ ] Set `ALLOWED_HOSTS` to your domain(s)
- [ ] Configure SMTP email (`EMAIL_HOST`, `EMAIL_HOST_PASSWORD`)
- [ ] Configure S3 for media storage (`AWS_*` variables)
- [ ] Set `SENTRY_DSN` for error tracking
- [ ] Set `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`
- [ ] Use the `runtime` Docker target instead of `builder`
- [ ] Set up a reverse proxy (nginx) in front of Daphne
- [ ] Commit all `migrations/` folders to version control

---

## License

MIT
