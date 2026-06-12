import sys
import os
from decimal import Decimal
from fastapi.testclient import TestClient

# Ensure the application module is in the import path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app
from app.database.connection import SessionLocal, engine, Base
from app.models.user import User, KYCStatus, UserRole
from app.models.account import Account, AccountStatus, AccountType
from app.models.loan import Loan, LoanStatus, EMIStatus
from app.models.transaction import Transaction

client = TestClient(app)

from app.core.security import get_password_hash

def setup_test_db():
    # We will reset the database tables for clean testing
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Seed default admin directly
    db = SessionLocal()
    try:
        admin_email = "admin@bank.com"
        hashed_pw = get_password_hash("adminpassword")
        default_admin = User(
            full_name="System Administrator",
            email=admin_email,
            hashed_password=hashed_pw,
            role=UserRole.ADMIN,
            kyc_status=KYCStatus.APPROVED,
            is_active=True
        )
        db.add(default_admin)
        db.commit()
        print("Test database initialized and admin seeded.")
    finally:
        db.close()

def test_banking_flows():
    print("\n=== STARTING INTEGRATION TESTS ===")
    
    # 1. Test Landing Page
    response = client.get("/")
    assert response.status_code == 200
    assert "Antigravity Bank" in response.text
    print("[OK] Landing Page loaded successfully.")

    # 2. Seed default admin (FastAPI startup event does this, but let's verify or seed if missing)
    # The TestClient's startup events will run, seeding admin@bank.com.
    # Let's verify admin account login
    response = client.post(
        "/login",
        data={"email": "admin@bank.com", "password": "adminpassword"},
        follow_redirects=False
    )
    print("Admin login response status:", response.status_code)
    print("Admin login response headers:", dict(response.headers))
    print("Admin login response text:", response.text)
    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard"
    admin_cookie = response.headers.get("set-cookie")
    assert "access_token=" in admin_cookie
    print("[OK] Admin Login and cookie generation verified.")

    # 3. Register Customer A
    response = client.post(
        "/register",
        data={
            "full_name": "Alice Smith",
            "email": "alice@example.com",
            "mobile_number": "1234567890",
            "password": "password123",
            "address": "123 Main St, New York"
        },
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "success=" in response.headers["location"]
    print("[OK] Customer A registration successful.")

    # 4. Login Customer A
    response = client.post(
        "/login",
        data={"email": "alice@example.com", "password": "password123"},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    alice_cookie = response.headers.get("set-cookie")
    assert "access_token=" in alice_cookie
    
    # Extract access_token value
    alice_token = None
    for cookie in alice_cookie.split(";"):
        if cookie.strip().startswith("access_token="):
            alice_token = cookie.split("=")[1]
            break
            
    # Set headers/cookies for Alice's test requests
    alice_headers = {"Cookie": f"access_token={alice_token}"}
    print("[OK] Customer A Login verified.")

    # 5. Customer A Dashboard
    response = client.get("/dashboard", headers=alice_headers)
    assert response.status_code == 200
    assert "Alice Smith" in response.text
    assert "DRAFT" in response.text  # KYC Status starts as DRAFT
    print("[OK] Customer A Dashboard loaded.")

    # 6. Try to create account before KYC approval (should fail)
    response = client.post(
        "/accounts/create",
        data={"account_type": "SAVINGS"},
        headers=alice_headers,
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "error=" in response.headers["location"]
    print("[OK] Attempting account creation before KYC approval correctly failed.")

    # 7. Upload KYC Document & Submit
    # We simulate file upload using multipart/form-data
    dummy_file = b"Dummy document contents representing Aadhaar Card"
    response = client.post(
        "/kyc/upload",
        data={"document_type": "AADHAAR"},
        files={"file": ("aadhaar.pdf", dummy_file, "application/pdf")},
        headers=alice_headers,
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "success=" in response.headers["location"]
    print("[OK] KYC Document uploaded successfully.")

    response = client.post(
        "/kyc/submit",
        headers=alice_headers,
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "success=" in response.headers["location"]
    print("[OK] KYC Final submission triggered.")

    # Verify User KYC status is now SUBMITTED in DB
    db = SessionLocal()
    alice_db = db.query(User).filter(User.email == "alice@example.com").first()
    assert alice_db.kyc_status == KYCStatus.SUBMITTED
    alice_id = alice_db.id
    db.close()
    print("[OK] KYC Database status set to SUBMITTED.")

    # 8. Admin reviews and approves KYC for Customer A
    admin_token = None
    for cookie in admin_cookie.split(";"):
        if cookie.strip().startswith("access_token="):
            admin_token = cookie.split("=")[1]
            break
    admin_headers = {"Cookie": f"access_token={admin_token}"}

    response = client.post(
        f"/admin/kyc-reviews/{alice_id}/review",
        data={"review_status": "APPROVED", "comments": "All documents verified."},
        headers=admin_headers,
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "success=" in response.headers["location"]
    
    db = SessionLocal()
    alice_db = db.query(User).filter(User.id == alice_id).first()
    assert alice_db.kyc_status == KYCStatus.APPROVED
    db.close()
    print("[OK] Admin KYC approval verified in database.")

    # 9. Create Savings Account for Customer A (now should succeed)
    response = client.post(
        "/accounts/create",
        data={"account_type": "SAVINGS"},
        headers=alice_headers,
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "success=" in response.headers["location"]
    
    db = SessionLocal()
    alice_accounts = db.query(Account).filter(Account.user_id == alice_id).all()
    assert len(alice_accounts) == 1
    alice_account = alice_accounts[0]
    assert alice_account.account_type == AccountType.SAVINGS
    assert alice_account.balance == Decimal("0.00")
    alice_account_id = alice_account.id
    alice_account_number = alice_account.account_number
    db.close()
    print(f"[OK] Savings account created successfully: {alice_account_number}")

    # 10. Deposit money into Savings Account
    response = client.post(
        "/transactions/deposit",
        data={"account_id": alice_account_id, "amount": "1000.00", "description": "Birthday gift"},
        headers=alice_headers,
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "success=" in response.headers["location"]
    
    db = SessionLocal()
    alice_account = db.query(Account).filter(Account.id == alice_account_id).first()
    assert alice_account.balance == Decimal("1000.00")
    db.close()
    print("[OK] Deposit of $1,000.00 successful. Balance updated.")

    # 11. Withdraw money from Savings Account
    response = client.post(
        "/transactions/withdraw",
        data={"account_id": alice_account_id, "amount": "200.00", "description": "Cash withdrawal"},
        headers=alice_headers,
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "success=" in response.headers["location"]
    
    db = SessionLocal()
    alice_account = db.query(Account).filter(Account.id == alice_account_id).first()
    assert alice_account.balance == Decimal("800.00")
    db.close()
    print("[OK] Withdrawal of $200.00 successful. Balance updated to $800.00.")

    # 12. Register Customer B & Open Account (to test transfer)
    client.post(
        "/register",
        data={
            "full_name": "Bob Jones",
            "email": "bob@example.com",
            "mobile_number": "0987654321",
            "password": "password123",
            "address": "456 Oak St, Boston"
        },
        follow_redirects=False
    )
    
    db = SessionLocal()
    bob_db = db.query(User).filter(User.email == "bob@example.com").first()
    bob_id = bob_db.id
    db.close()

    # Approve Bob's KYC
    client.post(
        f"/admin/kyc-reviews/{bob_id}/review",
        data={"review_status": "APPROVED", "comments": "Auto-approved."},
        headers=admin_headers,
        follow_redirects=False
    )

    # Bob logs in and creates account
    bob_login_resp = client.post(
        "/login",
        data={"email": "bob@example.com", "password": "password123"},
        follow_redirects=False
    )
    bob_cookie = bob_login_resp.headers.get("set-cookie")
    bob_token = None
    for cookie in bob_cookie.split(";"):
        if cookie.strip().startswith("access_token="):
            bob_token = cookie.split("=")[1]
            break
    bob_headers = {"Cookie": f"access_token={bob_token}"}

    client.post(
        "/accounts/create",
        data={"account_type": "SAVINGS"},
        headers=bob_headers,
        follow_redirects=False
    )

    db = SessionLocal()
    bob_account = db.query(Account).filter(Account.user_id == bob_id).first()
    bob_account_number = bob_account.account_number
    bob_account_id = bob_account.id
    db.close()
    print(f"[OK] Customer B account created successfully: {bob_account_number}")

    # 13. Transfer from Customer A (Alice) to Customer B (Bob)
    response = client.post(
        "/transactions/transfer",
        data={
            "source_account_id": alice_account_id,
            "destination_account_number": bob_account_number,
            "amount": "300.00",
            "description": "Payment for dinner"
        },
        headers=alice_headers,
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "success=" in response.headers["location"]

    db = SessionLocal()
    alice_acc = db.query(Account).filter(Account.id == alice_account_id).first()
    bob_acc = db.query(Account).filter(Account.id == bob_account_id).first()
    assert alice_acc.balance == Decimal("500.00")
    assert bob_acc.balance == Decimal("300.00")
    
    # Check that a transfer transaction was logged
    transfer_tx = db.query(Transaction).filter(
        Transaction.source_account_id == alice_account_id,
        Transaction.destination_account_id == bob_account_id
    ).first()
    assert transfer_tx is not None
    assert transfer_tx.amount == Decimal("300.00")
    db.close()
    print("[OK] Transfer of $300.00 from Customer A to Customer B successful.")

    # 14. Apply for a Loan (Customer A)
    response = client.post(
        "/loans/apply",
        data={
            "loan_type": "PERSONAL",
            "principal_amount": "5000.00",
            "tenure_months": "12"
        },
        headers=alice_headers,
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "success=" in response.headers["location"]

    db = SessionLocal()
    alice_loans = db.query(Loan).filter(Loan.user_id == alice_id).all()
    assert len(alice_loans) == 1
    alice_loan = alice_loans[0]
    assert alice_loan.status == LoanStatus.PENDING
    assert alice_loan.principal_amount == Decimal("5000.00")
    alice_loan_id = alice_loan.id
    db.close()
    print("[OK] Personal Loan application of $5,000.00 submitted.")

    # 15. Admin reviews and approves Loan
    response = client.post(
        f"/admin/loans/{alice_loan_id}/review",
        data={"status": "APPROVED", "comments": "Good credit history."},
        headers=admin_headers,
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "success=" in response.headers["location"]

    db = SessionLocal()
    alice_loan = db.query(Loan).filter(Loan.id == alice_loan_id).first()
    assert alice_loan.status == LoanStatus.ACTIVE
    assert len(alice_loan.emi_schedule) == 12
    # Verify first installment values
    first_emi = sorted(alice_loan.emi_schedule, key=lambda x: x.installment_number)[0]
    assert first_emi.status == EMIStatus.UNPAID
    print(f"[OK] Loan approved. Active status and 12-month amortization schedule generated.")
    print(f"  Monthly EMI Amount: ${alice_loan.emi_amount:,.2f}")
    db.close()

    # 16. Customer A repays first EMI installment
    db = SessionLocal()
    alice_loan = db.query(Loan).filter(Loan.id == alice_loan_id).first()
    repay_amount = alice_loan.emi_amount
    db.close()

    response = client.post(
        f"/loans/{alice_loan_id}/repay",
        data={"amount": str(repay_amount)},
        headers=alice_headers,
        follow_redirects=False
    )
    assert response.status_code == 303
    assert "success=" in response.headers["location"]

    db = SessionLocal()
    alice_loan = db.query(Loan).filter(Loan.id == alice_loan_id).first()
    first_emi = sorted(alice_loan.emi_schedule, key=lambda x: x.installment_number)[0]
    assert first_emi.status == EMIStatus.PAID
    assert alice_loan.outstanding_balance == Decimal("5000.00") - repay_amount
    db.close()
    print(f"[OK] First EMI payment of ${repay_amount:,.2f} processed. Installment marked PAID.")

    # 17. Statement Download link verification
    response = client.post(
        f"/statements/{alice_account_id}/download",
        headers=alice_headers,
        follow_redirects=False
    )
    assert response.status_code == 303
    download_url = response.headers["location"]
    assert ".txt" in download_url
    print(f"[OK] Account statement generated successfully. Redirect URL: {download_url}")

    print("\n=== ALL INTEGRATION TESTS PASSED SUCCESSFULLY! ===")

import traceback

if __name__ == "__main__":
    setup_test_db()
    try:
        test_banking_flows()
    except AssertionError as e:
        print("\n[FAIL] Assertion failed! Integration tests failed.")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)
