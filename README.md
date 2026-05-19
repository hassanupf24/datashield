# DATASHIELD

## Enterprise AI Data Governance Platform

> AI-powered data governance for banks, government institutions, and regulated industries.
> Real-time monitoring • AI Classification • Anomaly Detection • Compliance Automation

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DATASHIELD Platform                       │
├─────────────┬───────────────────────────┬───────────────────┤
│  Frontend   │      Backend API          │   AI Services     │
│  Next.js 14 │      FastAPI              │                   │
│  Tailwind   │  ┌─────────────────────┐  │  Classification   │
│  RTL/LTR    │  │ Auth & RBAC         │  │  Risk Scoring     │
│  Dark Mode  │  │ Access Tracking     │  │  Anomaly Detect.  │
│  Arabic UI  │  │ Policy Enforcement  │  │  Copilot (LLM)    │
│             │  │ Audit Logging       │  │                   │
│             │  │ Data Lineage        │  │                   │
│             │  │ Dashboard API       │  │                   │
│             │  └─────────────────────┘  │                   │
├─────────────┴───────────────────────────┴───────────────────┤
│                    Data Layer                                │
│  PostgreSQL (Metadata)  │  Redis (Cache/Events)             │
└─────────────────────────────────────────────────────────────┘
```

## Features

### Core Platform
- **Real-time Data Access Monitoring** — Track every data query across the enterprise
- **AI-Powered Data Classification** — Automatic sensitivity detection (Public → Regulated)
- **Anomaly Detection Engine** — Behavioral analysis with SHAP-style explainability
- **Policy Enforcement** — Real-time access decisions with automatic blocking
- **Immutable Audit Logs** — Cryptographically chained, tamper-evident audit trail
- **Data Lineage Tracking** — Source-to-consumption graph with blast radius analysis
- **Executive Dashboard** — Risk heatmaps, compliance scores, real-time alerts

### Security
- **Zero Trust Architecture** — Never trust, always verify
- **RBAC + ABAC** — Role hierarchy with attribute-based contextual decisions
- **JWT Authentication** — Argon2id password hashing, token-based access
- **Rate Limiting** — IP-based request throttling
- **Data Masking** — Dynamic PII masking based on user role
- **Input Sanitization** — Injection prevention on all inputs
- **Request Tracing** — End-to-end trace IDs on every request

### Arabic Language Support
- **Full RTL Layout** — CSS Logical Properties for instant mirroring
- **Bilingual UI** — Complete Arabic/English translation dictionary
- **Arabic NLP** — PII detection for Arabic names, national IDs, addresses
- **Arabic Copilot** — Governance assistant responds in Arabic
- **Arabic Font System** — IBM Plex Sans Arabic + Cairo

### Compliance
- **GDPR** — Data lineage for Right to be Forgotten, encryption at rest
- **ISO 27001** — Access controls, audit logging, monitoring
- **PCI-DSS** — Card data detection and masking

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, Tailwind CSS, Recharts |
| Backend | Python FastAPI, SQLAlchemy (async), Pydantic v2 |
| AI/ML | scikit-learn, regex NER, rule-based classification |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Auth | JWT (python-jose), Argon2id |
| Logging | structlog (JSON) |
| Deployment | Docker, Docker Compose |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Deploy

```bash
# Clone
git clone <repo-url>
cd DATASHIELD

# Deploy (Linux/macOS)
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Deploy (Windows)
scripts\deploy.bat
```

### Access

| Service | URL |
|---------|-----|
| Frontend Dashboard | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |

### Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Super Admin | `admin` | `DataShield@2026` |
| Data Steward | `steward` | `DataShield@2026` |
| Security Analyst | `analyst` | `DataShield@2026` |
| Auditor | `auditor` | `DataShield@2026` |
| Viewer | `viewer` | `DataShield@2026` |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login and get JWT tokens |
| POST | `/api/v1/auth/register` | Register user (Admin only) |
| GET | `/api/v1/auth/me` | Get current user profile |

### Data Assets
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/assets/` | Register data asset |
| GET | `/api/v1/assets/` | List assets (filtered) |
| GET | `/api/v1/assets/{id}` | Get specific asset |

### Access Tracking
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/tracking/events` | Ingest access event |
| GET | `/api/v1/tracking/events` | Query events |

### AI Classification
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/classification/analyze` | Classify data samples |
| POST | `/api/v1/classification/batch` | Batch classification |

### Risk Assessment
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/risk/evaluate` | Evaluate event risk |

### Policy Enforcement
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/policies/` | Create policy |
| GET | `/api/v1/policies/` | List policies |
| POST | `/api/v1/policies/check` | Real-time policy check |

### Audit Logs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/audit/logs` | Query audit logs |
| GET | `/api/v1/audit/verify-chain` | Verify chain integrity |

### Data Lineage
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/lineage/` | Create lineage edge |
| GET | `/api/v1/lineage/graph/{id}` | Get lineage graph |
| GET | `/api/v1/lineage/impact/{id}` | Blast radius analysis |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dashboard/stats` | Dashboard statistics |
| GET | `/api/v1/dashboard/compliance` | Compliance overview |
| GET | `/api/v1/dashboard/alerts` | Recent alerts |

## Project Structure

```
DATASHIELD/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py          # Pydantic settings
│   │   ├── database.py        # Async SQLAlchemy
│   │   ├── logging_config.py  # Structured logging
│   │   ├── models.py          # ORM models (11 tables)
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── security.py        # JWT, RBAC, masking
│   │   ├── ai/
│   │   │   ├── __init__.py    # Classification engine
│   │   │   └── risk_engine.py # Risk scoring
│   │   └── api/
│   │       ├── auth.py        # Authentication
│   │       ├── events.py      # Access tracking
│   │       ├── assets.py      # Data assets CRUD
│   │       ├── classification.py
│   │       ├── risk.py        # Risk assessment
│   │       ├── policies.py    # Policy enforcement
│   │       ├── audit.py       # Audit logs
│   │       ├── lineage.py     # Data lineage
│   │       └── dashboard.py   # Dashboard stats
│   ├── tests/
│   │   └── test_core.py       # 25+ test cases
│   ├── main.py                # FastAPI entrypoint
│   ├── seed.py                # Database seeder
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx     # Root layout
│   │   │   ├── page.tsx       # Main page
│   │   │   └── globals.css    # Design system
│   │   ├── components/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── SecurityMonitoring.tsx
│   │   │   └── CopilotChat.tsx
│   │   └── lib/
│   │       ├── api.ts         # API client
│   │       └── i18n.ts        # Translations (AR/EN)
│   ├── Dockerfile
│   └── package.json
├── scripts/
│   ├── deploy.sh
│   └── deploy.bat
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Security Model

### RBAC Role Hierarchy
```
SUPER_ADMIN (100) → Full system access
  └── ADMIN (80) → User management, policy creation
      ├── DATA_STEWARD (60) → Classification, lineage management
      ├── SECURITY_ANALYST (50) → Monitoring, alerts
      ├── AUDITOR (40) → Read-only audit access
      ├── DATA_ANALYST (30) → Data queries (masked)
      └── VIEWER (10) → Dashboard only
```

### Audit Chain Integrity
Every audit log entry is cryptographically chained:
```
Hash(N) = SHA256(Hash(N-1) + Event_Data)
```
The `/api/v1/audit/verify-chain` endpoint validates the entire chain for tamper evidence.

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

## License

Proprietary — DATASHIELD Corp © 2026
