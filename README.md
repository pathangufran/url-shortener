# 🔗 URL Shortener

A backend URL Shortener application built using **Python, Django, Django REST Framework, PostgreSQL, Redis, Docker, Nginx, and Gunicorn**.

The application allows users to create short URLs and redirect users to the original URLs using the generated short code.

---

## 🏗️ Architecture

```text
                    Client
                      │
                      ▼
                    Nginx
                Reverse Proxy
                      │
                      ▼
                  Gunicorn
                      │
                      ▼
              Django + DRF API
                 │          │
                 ▼          ▼
            PostgreSQL     Redis
             Database      Cache
```

### URL Redirect Flow

```text
Client
  │
  │ GET /<short_code>
  ▼
 Nginx
  │
  ▼
Gunicorn
  │
  ▼
Django API
  │
  ▼
Redis Cache
  │
  ├── Cache Hit ──────► Redirect to Original URL
  │
  └── Cache Miss
          │
          ▼
      PostgreSQL
          │
          ▼
      Store in Redis
          │
          ▼
      Redirect
```

---

## ✨ Features

* Create short URLs
* Redirect short URLs to original URLs
* User authentication
* User-specific URL management
* URL CRUD APIs
* Redis caching for faster redirects
* Rate limiting
* PostgreSQL database
* Database indexing and query optimization
* API documentation with Swagger/OpenAPI
* Dockerized application
* Nginx reverse proxy
* Gunicorn application server

---

## 📁 Project Structure

```text
url-shortener/
│
├── .github/
│
├── apps/
│   ├── accounts/
│   ├── analytics/
│   ├── common/
│   └── shortener/
│
├── config/
│
├── nginx/
│
├── venv/
│
├── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── pyproject.toml
├── README.md
└── requirements.txt
```

---

## 🚀 How to Run Locally

### 1. Clone the Repository

```bash
git clone <repository-url>
cd url-shortener
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Configure the required values in your `.env` file.

### 3. Run with Docker

```bash
docker compose up --build
```

### 4. Run Migrations

```bash
docker compose exec web python manage.py migrate
```

### 5. Create Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

### 6. Run Tests

```bash
docker compose exec web python manage.py test
```

Application:

```text
http://localhost:8080/
```

---

# 📚 API Documentation

Swagger/OpenAPI documentation can be exposed through:

```text
/api/docs/
```

Schema:

```text
/api/schema/
```

The exact URLs may vary depending on the API documentation package/configuration used.

---

# 🧪 Testing Strategy

The project includes tests for:

### Unit Tests

* Short-code generation
* URL validation
* Services
* Cache operations

### API Tests

* Create URL
* Retrieve URL
* Update URL
* Delete URL
* Authentication
* Permissions
* Redirects

### Integration Tests

* PostgreSQL integration
* Redis integration
* Complete redirect flow

### Edge Cases

* Invalid URL
* Duplicate short code
* Expired URL
* Deleted URL
* Unauthorized access
* Rate-limit exceeded
* Redis unavailable

---

## 🛠️ Tech Stack

* **Python**
* **Django**
* **Django REST Framework**
* **PostgreSQL**
* **Redis**
* **Celery**
* **Docker**
* **Nginx**
* **Gunicorn**

---

# 📄 License

This project is intended for learning, portfolio development, and backend/system-design practice.

---

## ⭐ Author

**Gufran Pathan**

Backend Developer — Python / Django / REST APIs

```text
Python • Django • DRF • PostgreSQL • Redis • Docker • Nginx • Gunicorn
```
