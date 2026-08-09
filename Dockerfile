FROM python:3.12-slim

# Prevent Python from creating .pyc files
# and ensure logs are immediately visible.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required by PostgreSQL
# and Python packages that may require compilation.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first so Docker can cache
# the dependency installation layer.
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code.
COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]