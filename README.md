# Jinja2 & FastAPI Monolithic Banking Management System

A premium digital banking management monolith built in pure Python using **FastAPI**, **Jinja2 Templates**, **Bootstrap 5**, **SQLAlchemy**, **PostgreSQL**, and **Azure Blob Storage (GRS)**. Designed to be deployed as a single code deployment directory directly on **Azure App Service**.

## Project Objectives

* **Pure Monolithic Architecture**: Simplifies deployment and maintenance. The entire system (both frontend pages and backend APIs) is served by a single FastAPI application.
* **Modern Jinja2 Templating**: High-performance server-side rendering with no node, NPM, or complex JS framework dependencies.
* **Premium Bootstrap 5 Custom UI**: Built with custom fonts, glassmorphism, linear gradients, sidebar interfaces, active states, and mobile responsive layout tables.
* **PostgreSQL Native**: Runs on Azure Database for PostgreSQL.
* **Azure Blob Storage Integration**: Secure uploads for KYC identity documents, supporting loan documentation, and generated bank statements.
* **Local Development Fallback**: Fallbacks to local SQLite database and local uploads folders to ensure the project is immediately runnable and testable locally out-of-the-box.

---

## Folder Structure

```text
/ (Workspace Root)
├── app/
│   ├── auth/              # Router, dependencies for JWT cookie validation
│   ├── users/             # User service, repository, profile routers
│   ├── kyc/               # KYC router, document upload, status review workflows
│   ├── accounts/          # Savings and Current accounts, activation status
│   ├── transactions/      # Deposits, withdrawals, transfers, statement compilation
│   ├── loans/             # Loan application, active EMI schedules, repayment logs
│   ├── core/              # Config (Pydantic settings), security (JWT, hashing)
│   ├── database/          # Connection manager and SQLAlchemy session factories
│   ├── models/            # SQLAlchemy models (User, KYC, Account, Loan, Transaction)
│   ├── schemas/           # Pydantic validation schemas
│   ├── services/          # Pure Python business services & DB repositories
│   └── main.py            # Entrypoint, startup seeding, error redirect handlers
├── templates/             # Jinja2 HTML Templates
│   ├── layouts/           # Base HTML layouts (Navbar, sidebar, modals)
│   ├── auth/              # Login, register, forgot-password forms
│   ├── customer/          # Portals for accounts, transactions, statements, loans
│   └── admin/             # Portals for KYC reviews, loan approvals, users toggles
├── static/                # Static assets
│   ├── css/
│   │   └── custom.css     # Premium styling additions (gradients, cards, animation transitions)
│   ├── js/
│   │   └── main.js        # Universal forms validations and dynamic search filters
│   └── uploads/           # Mock directory for local file uploads (fallback)
├── requirements.txt       # Python package dependencies
├── .env.example           # Example application configurations
├── test_app.py            # Full end-to-end integration test suite
└── README.md              # Project documentation (this file)
```

---

## Features

### 👤 Identity & Roles
* **Customer**: Registration, secure authentication, profile management, and password recovery.
* **Admin**: Centralized dashboard showing total deposits, outstanding loan portfolio, pending KYC requests, user active toggling, KYC reviews, and loan approvals.

### 🛡️ Authentication & Verification
* Cookie-based **JWT Token validation** for server-side HTML template rendering and direct REST API request authentication.
* Fully interactive **KYC flow** supporting document uploads (Aadhaar, PAN, Passport, Driving License) and admin approval/rejection workflows.

### 💰 Accounts & Transactions
* Instant opening of **Savings** and **Current** accounts upon KYC approval.
* Real-time **Deposits** and **Withdrawals**.
* Direct account-to-account **Transfers** with destination account validation.
* Instant generation and download of formatted bank statement files.

### 🏦 Loan & EMI Amortization
* Interactive loan application calculator supporting Personal, Home, Vehicle, and Education loan types.
* Automatic generation of full monthly **Amortization Schedules** (detailing installment principal/interest components) upon admin loan approval.
* Full-history repayments that update outstanding principal balances and mark respective installments as `PAID`.

---

## Local Development & Testing

### 1. Set Up Virtual Environment
Ensure you have Python 3.10+ installed. In your terminal:
```powershell
# Create virtual environment
python -m venv venv

# Activate on Windows
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install httpx
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```

### 3. Run Automated Integration Tests
You can run the full end-to-end validation test suite locally:
```powershell
python test_app.py
```
*The script will automatically detect that PostgreSQL is not running locally, fall back to a clean SQLite database (`banking_db.db`), run all lifecycles successfully, and print status messages.*

### 4. Start the Application Server
Run the local uvicorn server:
```powershell
python -m uvicorn app.main:app --port 8000 --reload
```
Open your browser at `http://127.0.0.1:8000` to interact with the application.

* **Default Admin Credentials**:
  * **Email**: `admin@bank.com`
  * **Password**: `adminpassword`

---

## Azure Deployment Guide

This repository is optimized for direct Git deployment to **Azure App Service (Linux)**.

### 1. Azure Resources Configuration
Create the following resources in your Azure subscription:
1. **Azure App Service** (Python 3.10+ or Python 3.12+ Runtime stack, Linux OS).
2. **Azure Database for PostgreSQL Flexible Server**.
3. **Azure Storage Account** (GRS configured container).

### 2. Configure App Service Settings
Under the **Settings > Configuration** blade of your Azure App Service, add the following Application Settings:
* `DATABASE_URL`: Set to your Azure PostgreSQL connection string:
  `postgresql://<username>:<password>@<server-name>.postgres.database.azure.com:5432/<database-name>?sslmode=require`
* `SECRET_KEY`: A secure random cryptographic string for JWT signatures.
* `REFRESH_SECRET_KEY`: A secure random cryptographic string for JWT refresh tokens.
* `AZURE_STORAGE_CONNECTION_STRING`: Set to your Azure Storage connection string.
* `AZURE_CONTAINER_NAME`: The name of the target storage container (e.g., `banking-documents`).

### 3. Set Startup Command
Under **Settings > Configuration > General Settings > Startup Command** of your Azure App Service, enter:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 4. Deploy code via GitHub Actions / Local Git
1. Configure your deployment center to pull from your repository branch.
2. Azure will build your project using Oryx, automatically install the packages inside `requirements.txt`, start your app service, run `Base.metadata.create_all` to initialize PostgreSQL tables, and seed the default admin account.
