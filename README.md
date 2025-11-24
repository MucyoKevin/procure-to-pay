# Django Procure-to-Pay System

A comprehensive Django-based procurement management system with **multi-level approval workflow**, **AI-powered document extraction**, and **automated receipt validation**.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.2-green.svg)
![DRF](https://img.shields.io/badge/DRF-3.16-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [API Endpoints](#-api-endpoints)
- [User Roles](#-user-roles)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Security Features](#-security-features)
- [Contributing](#-contributing)
- [License](#-license)

---

## Features

### Core Functionality
- 🔐 **Role-Based Access Control** - Four distinct user roles (Staff, L1/L2 Approvers, Finance)
- 📝 **Multi-Level Approval Workflow** - Sequential two-level approval process
- 🤖 **AI-Powered Document Extraction** - Automatic metadata extraction from proforma invoices
- 📄 **Automated PO Generation** - PDF purchase orders created upon final approval
- ✅ **Receipt Validation** - AI-based comparison of receipts against purchase orders
- 🔒 **Transaction Safety** - ACID-compliant operations with row-level locking

### Technical Features
- RESTful API with Django REST Framework
- JWT Authentication
- Swagger/OpenAPI documentation
- PostgreSQL database with optimized indexes
- Redis caching and Celery for background tasks
- Docker containerization
- OCR support for PDF and image files
- File upload handling with validation

---

## System Architecture

```
┌─────────────┐
│   Staff     │ Creates Purchase Request → Upload Proforma
└─────┬───────┘
      │
      ↓
┌─────────────┐
│  L1 Approver│ Reviews & Approves/Rejects
└─────┬───────┘
      │
      ↓
┌─────────────┐
│  L2 Approver│ Final Approval → PO Generated
└─────┬───────┘
      │
      ↓
┌─────────────┐
│   Staff     │ Upload Receipt → AI Validation
└─────────────┘
      │
      ↓
┌─────────────┐
│   Finance   │ View Approved Requests & Reports
└─────────────┘
```

---

## Technology Stack

### Backend
- **Framework:** Django 5.2.8
- **API:** Django REST Framework 3.16
- **Authentication:** JWT (Simple JWT)
- **Database:** PostgreSQL 15+ / SQLite (dev)
- **Cache/Queue:** Redis 7+
- **Task Queue:** Celery 5.5

### AI & Document Processing
- **OCR:** Tesseract, PDFPlumber
- **AI:** OpenAI GPT-4o-mini
- **PDF Generation:** ReportLab
- **Image Processing:** Pillow

### DevOps
- **Containerization:** Docker, Docker Compose
- **WSGI Server:** Gunicorn
- **API Docs:** drf-yasg (Swagger/OpenAPI)

---

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+ (optional, SQLite works for dev)
- Redis 7+ (optional for dev)
- Tesseract OCR
- OpenAI API Key

### Installation

#### Docker (Recommended)

1. **Clone and configure:**
```bash
git clone <repository-url>
cd procure-to-pay
cp env.example.txt .env
# Edit .env with your configuration
```

2. **Start services:**
```bash
docker-compose up --build
```

3. **Initialize database:**
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py create_test_users
docker-compose exec web python manage.py create_test_data
```

4. **Access the application:**
- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/
- API Docs: http://localhost:8000/api/docs/

---


## User Roles

### 1. **Staff** 👨‍💼
- Create purchase requests
- Upload proforma invoices
- Submit receipts for approved requests
- View own requests

### 2. **Approver Level 1** ✅
- Review and approve/reject purchase requests
- View pending requests at Level 1
- Add approval comments

### 3. **Approver Level 2** ✅✅
- Final approval/rejection (after L1 approval)
- View requests approved by L1
- Trigger PO generation on approval

### 4. **Finance** 💰
- View all approved purchase requests
- Access financial reports
- Review receipt validations

---


---

## Testing

### Run Test Suite
```bash
python manage.py test
```

### Create Test Data
```bash
python manage.py create_test_data
```

### Manual Testing Checklist
- [ ] User authentication (all roles)
- [ ] Request creation with file upload
- [ ] Document metadata extraction
- [ ] L1 approval workflow
- [ ] L2 approval workflow
- [ ] Rejection workflow
- [ ] PO generation
- [ ] Receipt upload
- [ ] Receipt validation
- [ ] Role-based access control

---

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions covering:
- Local development setup
- Docker deployment (dev & prod)
- AWS EC2 deployment
- Render.com deployment
- Environment configuration
- Security best practices




## Security Features

- ✅ JWT-based authentication
- ✅ Role-based access control (RBAC)
- ✅ Row-level permissions
- ✅ CSRF protection
- ✅ SQL injection prevention (ORM)
- ✅ File upload validation
- ✅ Environment variable configuration
- ✅ CORS configuration
- ✅ Transaction-safe operations

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.






