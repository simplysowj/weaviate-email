# AI-Powered Email Marketing Automation System

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Django](https://img.shields.io/badge/django-4.2+-green.svg)
![React](https://img.shields.io/badge/react-18+-61dafb.svg)
![GPT-4](https://img.shields.io/badge/OpenAI-GPT4-purple.svg)
![AutoGen](https://img.shields.io/badge/Microsoft-AutoGen-blueviolet.svg)

**An intelligent email automation platform** combining AI content generation with secure bulk email delivery for e-commerce, HR, and healthcare applications.

➡️ [Live Demo](#) | 📹 [Demo Video](#) | 📧 [Request Enterprise Version](#)

## 🚀 Key Features

| Feature | Technology | Benefit |
|---------|------------|---------|
| **AI-Powered Email Generation** | GPT-4 + AutoGen | Creates hyper-personalized content at scale |
| **Smart Reply Handling** | AutoGen Agentic AI | Context-aware automated responses |
| **Bulk Email Campaigns** | Gmail API + OAuth 2.0 | Secure delivery with enterprise-grade auth |
| **Real-Time Tracking** | PostgreSQL | Monitor sent/delivered/replied status |
| **CSV Data Pipeline** | Django Backend | Process 10,000+ recipients in minutes |

## 🛠️ Tech Stack

**Backend**
- Python 3.10+
- Django 4.2 (REST API)
- Gmail API with OAuth 2.0
- OpenAI GPT-4 & AutoGen
- PostgreSQL

**Frontend**
- React 18 (Vite)
- Axios for API calls
- Material-UI Dashboard

**Infrastructure**
- Dockerized deployment
- Environment-based secrets
- Automated CI/CD pipeline

## 📦 Installation

```bash
# Backend
git clone https://github.com/yourrepo/ecom-marketing.git
cd backend
pip install -r requirements.txt
python manage.py migrate

# Frontend
cd ../frontend
npm install
npm run dev
