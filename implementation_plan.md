# Implementation Plan - Banking Management System

This plan outlines the architecture, database schema, module designs, and implementation steps for building the Banking Management System as a single monolithic full-stack application.

## Core Architectural Alignment

> [!IMPORTANT]
> - **Single Folder Monolith**: The React frontend and FastAPI backend are in the same workspace root. The React app is in `/frontend` and builds to `/frontend/dist`. The FastAPI app sits at the root/`/app` and serves `/frontend/dist` static assets and handles SPA routing fallback to `/frontend/dist/index.html`.
> - **Strict PostgreSQL**: We will use PostgreSQL exclusively (no SQLite fallback) configured via database environment variables.
> - **Azure Blob Storage (GRS)**: All document uploads (KYC cards, loan documents, and statements) are uploaded directly to Azure Blob Storage using `azure-storage-blob` client SDK.

## Folder Structure

The monolithic codebase will be organized as follows:

```text
/ (Workspace Root)
├── app/
│   ├── core/
│   │   ├── config.py        # Settings using Pydantic Settings & environment variables
│   │   ├── security.py      # JWT (Access & Refresh tokens) and Passlib hashing (bcrypt)
│   │   └── database.py      # SQLAlchemy PostgreSQL engine and sessionmaker
│   ├── modules/
│   │   ├── users/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── kyc/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── accounts/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── transactions/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   ├── loans/
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── repository.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   └── storage/
│   │       ├── service.py
│   │       └── router.py
│   └── main.py              # Main FastAPI application mounting static files & API routes
├── frontend/
│   ├── src/
│   │   ├── components/      # Common UI elements (Navbar, Sidebar, Cards, etc.)
│   │   ├── context/         # AuthContext for login/session state
│   │   ├── pages/           # Customer & Admin pages
│   │   ├── services/        # Axios API configurations
│   │   ├── App.jsx          # React routes (Protected & Role-based)
│   │   ├── index.css        # Tailwind CSS styling
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── requirements.txt
├── alembic.ini
└── README.md
```

## Database Schema (PostgreSQL)

1. **User**: `id` (PK), `full_name`, `email` (unique), `mobile_number`, `hashed_password`, `address`, `role` (CUSTOMER, ADMIN), `kyc_status` (DRAFT, SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, RESUBMITTED), `is_active`, `created_at`, `updated_at`.
2. **KYCDocument**: `id` (PK), `user_id` (FK), `document_type` (AADHAAR, PAN, PASSPORT, DRIVING_LICENSE), `document_url` (Azure blob URL), `blob_name`, `status`, `comments`, `created_at`.
3. **Account**: `id` (PK), `user_id` (FK), `account_number` (unique), `account_type` (SAVINGS, CURRENT), `balance`, `status` (ACTIVE, FROZEN, CLOSED), `created_at`, `updated_at`.
4. **Transaction**: `id` (PK), `source_account_id` (FK, nullable), `destination_account_id` (FK, nullable), `transaction_type` (DEPOSIT, WITHDRAW, TRANSFER), `amount`, `description`, `created_at`.
5. **Loan**: `id` (PK), `user_id` (FK), `loan_type` (PERSONAL, HOME, VEHICLE, EDUCATION), `principal_amount`, `interest_rate`, `tenure_months`, `emi_amount`, `status` (PENDING, APPROVED, REJECTED, ACTIVE, COMPLETED, DEFAULTED), `outstanding_balance`, `comments`, `created_at`, `updated_at`.
6. **LoanEMISchedule**: `id` (PK), `loan_id` (FK), `installment_number`, `due_date`, `emi_amount`, `principal_component`, `interest_component`, `outstanding_principal`, `status` (UNPAID, PAID, OVERDUE), `paid_date`.
7. **LoanRepaymentHistory**: `id` (PK), `loan_id` (FK), `amount_paid`, `payment_date`, `payment_method`.

## Verification Plan

### Automated & Manual Checks
- Build the React application into `/frontend/dist`.
- Verify database migrations and tables inside PostgreSQL.
- Run the FastAPI application locally using PostgreSQL.
- Verify API endpoints via `/docs` (Swagger UI).
- Test all major workflows (Auth, KYC uploads, Account management, transactions, and loans).
