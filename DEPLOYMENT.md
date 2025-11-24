# Deployment Guide - Procure-to-Pay System

This guide covers deployment options for the Django Procure-to-Pay system.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [AWS EC2 Deployment](#aws-ec2-deployment)
- [Render.com Deployment](#rendercom-deployment)
- [Environment Variables](#environment-variables)
- [Post-Deployment Setup](#post-deployment-setup)

---

## Prerequisites

### Required Software
- Python 3.11+
- PostgreSQL 15+ (or SQLite for local development)
- Redis 7+ (for caching and Celery)
- Tesseract OCR
- Docker & Docker Compose (for containerized deployment)

### Required API Keys
- OpenAI API Key (for document processing)

---

## Local Development

### 1. Clone Repository
```bash
git clone <repository-url>
cd procure-to-pay
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Add to PATH

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr libtesseract-dev
```

**Mac:**
```bash
brew install tesseract
```

### 5. Configure Environment Variables
Create a `.env` file in the project root:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-your-openai-key
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 6. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Test Users
```bash
python manage.py create_test_users
```

### 8. Create Test Data (Optional)
```bash
python manage.py create_test_data
```

### 9. Run Development Server
```bash
python manage.py runserver
```

### 10. Access Application
- **API:** http://localhost:8000/api/v1/
- **Admin:** http://localhost:8000/admin/
- **API Docs:** http://localhost:8000/api/docs/

---

## Docker Deployment

### Development Mode

1. **Start all services:**
```bash
docker-compose up --build
```

2. **Run migrations:**
```bash
docker-compose exec web python manage.py migrate
```

3. **Create superuser:**
```bash
docker-compose exec web python manage.py createsuperuser
```

4. **Create test users:**
```bash
docker-compose exec web python manage.py create_test_users
```

5. **Access application:**
- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/

### Production Mode

1. **Create production environment file (.env.prod):**
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
DB_NAME=procure_to_pay
DB_USER=postgres
DB_PASSWORD=your-secure-password
OPENAI_API_KEY=sk-your-openai-key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

2. **Start with production config:**
```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

3. **Run migrations:**
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

4. **Create superuser:**
```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## Render.com Deployment

### Option 1: Web Service + PostgreSQL

1. **Create New Web Service:**
   - Repository: Connect your Git repository
   - Environment: Docker
   - Build Command: `docker build -t procure .`
   - Start Command: `gunicorn procure.wsgi:application --bind 0.0.0.0:$PORT`

2. **Add PostgreSQL Database:**
   - Create new PostgreSQL database
   - Copy internal connection string

3. **Set Environment Variables:**
   ```
   DATABASE_URL=<from-render-postgres>
   SECRET_KEY=<generate-secure-key>
   OPENAI_API_KEY=<your-key>
   ALLOWED_HOSTS=.onrender.com
   DEBUG=False
   ```

4. **Deploy:**
   - Render will automatically deploy on push to main branch

### Option 2: Blueprint (render.yaml)

Create `render.yaml`:
```yaml
services:
  - type: web
    name: procure-to-pay
    env: docker
    dockerfilePath: ./Dockerfile
    plan: starter
    healthCheckPath: /api/schema/
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: procure-db
          property: connectionString
      - key: OPENAI_API_KEY
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: ALLOWED_HOSTS
        value: .onrender.com
      - key: DEBUG
        value: False

  - type: redis
    name: procure-redis
    plan: starter

databases:
  - name: procure-db
    databaseName: procure_to_pay
    plan: starter
```

---

## Environment Variables

### Required Variables
```env
SECRET_KEY=<django-secret-key>
DEBUG=<True|False>
ALLOWED_HOSTS=<comma-separated-hosts>
DATABASE_URL=<database-connection-string>
OPENAI_API_KEY=<openai-api-key>
```

### Optional Variables
```env
REDIS_URL=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=<comma-separated-origins>
MAX_UPLOAD_SIZE=10485760
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<email>
EMAIL_HOST_PASSWORD=<password>
```

---

## Post-Deployment Setup

### 1. Create Superuser
```bash
python manage.py createsuperuser
```

### 2. Create Test Users
```bash
python manage.py create_test_users
```

### 3. Access Admin Panel
Navigate to `/admin/` and login with superuser credentials.

### 4. Configure Users
- Create actual users with appropriate roles
- Assign departments
- Configure email notifications (if enabled)

### 5. Test the System
1. Login as Staff user
2. Create a purchase request
3. Upload a proforma invoice
4. Login as L1 Approver and approve
5. Login as L2 Approver and approve
6. Verify PO generation
7. Login as Staff and upload receipt
8. Verify receipt validation

---

## Monitoring & Maintenance

### View Logs
```bash
# Docker
docker-compose logs -f web

# Celery
docker-compose logs -f celery

# All services
docker-compose logs -f
```

### Database Backup
```bash
# Docker PostgreSQL
docker-compose exec db pg_dump -U postgres procure_to_pay > backup.sql

# Restore
docker-compose exec -T db psql -U postgres procure_to_pay < backup.sql
```

### Update Application
```bash
git pull origin main
docker-compose down
docker-compose up --build -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

---

## Troubleshooting

### Issue: Database connection error
**Solution:** Check DATABASE_URL and ensure PostgreSQL is running

### Issue: Static files not loading
**Solution:** Run `python manage.py collectstatic --noinput`

### Issue: Tesseract not found
**Solution:** Install Tesseract OCR and add to PATH

### Issue: OpenAI API errors
**Solution:** Verify OPENAI_API_KEY is set and valid

### Issue: File upload fails
**Solution:** Check MEDIA_ROOT permissions and MAX_UPLOAD_SIZE setting

---

## Security Checklist

- [ ] Change DEBUG to False in production
- [ ] Use strong SECRET_KEY
- [ ] Configure ALLOWED_HOSTS properly
- [ ] Use HTTPS (SSL certificate)
- [ ] Secure database credentials
- [ ] Enable CORS restrictions
- [ ] Regular security updates
- [ ] Database backups
- [ ] Monitor logs for suspicious activity
- [ ] Use environment variables for secrets

---

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review application logs
3. Check Django/Celery documentation
4. Open an issue on GitHub repository




