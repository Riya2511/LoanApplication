import sqlite3
import os

class DatabaseManager:
    @staticmethod
    def init_database():
        """Initialize the database and create tables if they don't exist."""
        try:
            conn = sqlite3.connect("loanApp.db")
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Customers (
                    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR NOT NULL,
                    phone VARCHAR UNIQUE,
                    address TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Loans (
                    loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    loan_account_number TEXT UNIQUE NOT NULL,
                    loan_amount DECIMAL(10, 2) NOT NULL,
                    loan_amount_paid DECIMAL(10, 2) DEFAULT 0.00,
                    loan_status TEXT DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Assets (
                    asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loan_id INTEGER NOT NULL,
                    reference_id TEXT UNIQUE,
                    description TEXT NOT NULL,
                    weight DECIMAL(10, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (loan_id) REFERENCES Loans(loan_id)
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS LoanPayments (
                    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loan_id INTEGER NOT NULL,
                    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    payment_amount DECIMAL(10, 2) NOT NULL,
                    interest_amount DECIMAL(10, 2) NOT NULL,
                    amount_left DECIMAL(10, 2) NOT NULL,
                    asset_description TEXT NULL,
                    FOREIGN KEY (loan_id) REFERENCES Loans(loan_id)
                );
            ''')

            cursor.execute('''
                CREATE VIEW IF NOT EXISTS LoanView AS
                SELECT
                    l.created_at AS loan_date,
                    GROUP_CONCAT(a.description, '; ') AS asset_descriptions,
                    SUM(a.weight) AS total_asset_weight,
                    l.loan_amount AS loan_amount,
                    (l.loan_amount - l.loan_amount_paid) AS loan_amount_due,
                    COALESCE(SUM(p.interest_amount), 0) AS total_interest_amount,
                    l.loan_account_number AS loan_account_number,
                    l.loan_id AS loan_id,
                    l.customer_id AS customer_id
                FROM Loans l
                LEFT JOIN Assets a ON l.loan_id = a.loan_id
                LEFT JOIN LoanPayments p ON l.loan_id = p.loan_id
                GROUP BY l.loan_id;
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS SystemUsers (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    password_hash TEXT NOT NULL
                );
            ''')

            cursor.execute("SELECT COUNT(*) FROM SystemUsers")
            if cursor.fetchone()[0] == 0:
                # Insert a default password (hash for "admin")
                import hashlib
                default_password = hashlib.sha256("admin".encode()).hexdigest()
                cursor.execute("INSERT INTO SystemUsers (password_hash) VALUES (?)", (default_password,))

            conn.commit()
        except sqlite3.Error as e:
            print(f"Database initialization error: {e}")
        finally:
            if conn:
                conn.close()

    @staticmethod
    def create_connection():
        conn = sqlite3.connect("loanApp.db")
        return conn

    @staticmethod
    def execute_query(query, params=None):
        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            conn.commit()
            return cursor
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            if conn:
                conn.close()

    @staticmethod
    def fetch_data(query, params=None):
        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            data = cursor.fetchall()
            return data
        except sqlite3.Error as e:
            print(f"Database error: {e} {query}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def verify_password(input_password):
        """Verify the provided password."""
        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM SystemUsers LIMIT 1")
            stored_hash = cursor.fetchone()[0]

            # Compare hash of input password with stored hash
            import hashlib
            input_hash = hashlib.sha256(input_password.encode()).hexdigest()
            return input_hash == stored_hash
        except sqlite3.Error as e:
            print(f"Database error while verifying password: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_password(new_password):
        """Update the system password."""
        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()

            # Hash the new password
            import hashlib
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute("UPDATE SystemUsers SET password_hash = ? WHERE user_id = 1", (new_hash,))

            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error while updating password: {e}")
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_all_customers():
        """Fetch all customers for dropdown"""
        query = "SELECT customer_id, name, phone FROM Customers ORDER BY name"
        return DatabaseManager.fetch_data(query)

    @staticmethod
    def get_customer_by_id(customer_id):
        """Fetch full customer details by ID"""
        query = """
        SELECT customer_id, name, phone, address
        FROM Customers 
        WHERE customer_id = ?
        """
        customer = DatabaseManager.fetch_data(query, (customer_id,))
        if customer:
            columns = ['customer_id', 'name', 'phone', 'address']
            return dict(zip(columns, customer[0]))  # Return first record as dict
        return None

    @staticmethod
    def insert_loan(customer_id, loan_amount, loan_date, loan_account_number):
        """Insert a new loan and return the loan_id"""
        query = """
        INSERT INTO Loans 
        (customer_id, loan_amount, created_at, loan_account_number) 
        VALUES (?, ?, ?, ?)
        """
        conn = DatabaseManager.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (customer_id, loan_amount, loan_date, loan_account_number))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def insert_asset(loan_id, reference_id, description, weight):
        """Insert a new asset associated with a loan"""
        query = """
        INSERT INTO Assets 
        (loan_id, reference_id, description, weight) 
        VALUES (?, ?, ?, ?)
        """
        conn = DatabaseManager.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (loan_id, reference_id, description, weight))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def insert_loan_payment(loan_id, payment_amount, interest_amount, amount_left, asset_description, payment_date):
        """Insert a new loan payment with asset details."""
        query = """
        INSERT INTO LoanPayments (
            loan_id, payment_amount, interest_amount, 
            amount_left, asset_description, payment_date
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        DatabaseManager.execute_query(
            query, 
            (loan_id, payment_amount, interest_amount, amount_left, asset_description, payment_date)
        )

    @staticmethod
    def update_loan_payment(loan_id, amount_paid):
        """Update loan payment and mark as completed if fully paid."""
        query_fetch = """
        SELECT loan_amount, loan_amount_paid
        FROM Loans
        WHERE loan_id = ?
        """
        query_update = """
        UPDATE Loans
        SET loan_amount_paid = ?, loan_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE loan_id = ?
        """
        conn = DatabaseManager.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query_fetch, (loan_id,))
            loan = cursor.fetchone()

            if not loan:
                raise ValueError("Loan not found.")

            loan_amount, loan_amount_paid = loan
            total_due = loan_amount  # Assuming no interest is considered in this case
            new_paid_amount = loan_amount_paid + amount_paid

            if new_paid_amount > total_due:
                raise ValueError("Payment exceeds total due amount.")
            loan_status = "Completed" if new_paid_amount == total_due else "Pending"
            cursor.execute(query_update, (new_paid_amount, loan_status, loan_id))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def delete_loan(loan_id):
        """Delete a loan and its associated assets."""
        query_delete_assets = """
        DELETE FROM Assets
        WHERE loan_id = ?
        """
        query_delete_loan = """
        DELETE FROM Loans
        WHERE loan_id = ?
        """
        conn = DatabaseManager.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query_delete_assets, (loan_id,))
            cursor.execute(query_delete_loan, (loan_id,))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    @staticmethod
    def fetch_loans_for_customer(customer_id):
        """
        Fetch all loans for a specific customer, including loan date,
        asset description, asset weight, total loan amount, and due amount.
        """
        query = """
            SELECT * FROM LoanView WHERE customer_id = ?;
        """
        try:
            return DatabaseManager.fetch_data(query, (customer_id,))
        except sqlite3.Error as e:
            print(f"Database error while fetching loans for customer {customer_id}: {e}")
            return []

    @staticmethod
    def fetch_loan_details(loan_id):
        """
        Fetch detailed information about a specific loan, including:
        - Asset Description
        - Asset Weight
        - Loan Amount Left to Be Paid
        """
        query = """
        SELECT
            Assets.description AS asset_description,
            Assets.weight AS asset_weight,
            Loans.loan_amount AS loan_amount_left
        FROM Loans
        LEFT JOIN Assets ON Loans.loan_id = Assets.loan_id
        WHERE Loans.loan_id = ? 
        """
        try:
            result = DatabaseManager.fetch_data(query, (loan_id,))
            if result:
                columns = ["asset_description", "asset_weight", "loan_amount_left"]
                return dict(zip(columns, result[0]))
            return None
        except sqlite3.Error as e:
            print(f"Database error while fetching loan details for loan_id {loan_id}: {e}")
            return None

    @staticmethod
    def fetch_loan_assets(loan_id):
        """Fetch assets attached to a given loan."""
        query = """
        SELECT reference_id, description, weight
        FROM Assets
        WHERE loan_id = ?
        """
        return DatabaseManager.fetch_data(query, (loan_id,))

    @staticmethod
    def fetch_loan_payments(loan_id):
        """Fetch all payments made for a given loan."""
        query = """
        SELECT payment_date, payment_amount, amount_left, interest_amount, asset_description
        FROM LoanPayments
        WHERE loan_id = ?
        ORDER BY payment_date ASC
        """
        results = DatabaseManager.fetch_data(query, (loan_id,))
        return [
            {"payment_date": result[0], "payment_amount": result[1], "amount_left": result[2], "interest_amount": result[3], "asset_description": result[4]}
            for result in results
        ]

    @staticmethod
    def get_total_loan_payments(loan_id):
        """Get total amount paid for a loan."""
        query = "SELECT SUM(payment_amount) FROM LoanPayments WHERE loan_id = ?"
        result = DatabaseManager.fetch_data(query, (loan_id,))[0][0]
        return float(result or 0)

    @staticmethod
    def get_loan_amount(loan_id):
        """Get total loan amount."""
        query = "SELECT loan_amount FROM Loans WHERE loan_id = ?"
        result = DatabaseManager.fetch_data(query, (loan_id,))[0][0]
        return float(result)
    
    @staticmethod
    def get_repaid_assets(loan_id):
        """
        Get a list of asset descriptions that have been fully repaid for a given loan.
        """
        query = """
        WITH AssetPayments AS (
            SELECT 
                asset_description,
                SUM(payment_amount) as total_paid
            FROM LoanPayments
            WHERE loan_id = ? AND asset_description IS NOT NULL
            GROUP BY asset_description
        ),
        AssetValues AS (
            SELECT 
                description,
                weight
            FROM Assets
            WHERE loan_id = ?
        )
        SELECT DISTINCT asset_description
        FROM AssetPayments ap
        JOIN AssetValues av ON ap.asset_description = av.description
        """
        
        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()
            cursor.execute(query, (loan_id, loan_id))
            results = cursor.fetchall()
            
            # Return list of repaid asset descriptions
            return [result[0] for result in results] if results else []
        except sqlite3.Error as e:
            print(f"Database error while fetching repaid assets for loan_id {loan_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def insert_loan_with_assets(customer_id, loan_amount, loan_date, loan_account_number, assets_data):
        conn = None
        try:
            conn = DatabaseManager.create_connection()
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.cursor()
            
            # Insert loan
            cursor.execute("""
                INSERT INTO Loans 
                (customer_id, loan_amount, created_at, loan_account_number) 
                VALUES (?, ?, ?, ?)
            """, (customer_id, loan_amount, loan_date, loan_account_number))
            
            loan_id = cursor.lastrowid
            
            # Insert assets
            for asset in assets_data:
                cursor.execute("""
                    INSERT INTO Assets 
                    (loan_id, reference_id, description, weight) 
                    VALUES (?, ?, ?, ?)
                """, (loan_id, asset['reference_id'], asset['description'], asset['weight']))
            
            conn.commit()
            return True, "Loan registered successfully"
            
        except sqlite3.IntegrityError as e:
            if conn:
                conn.rollback()
            if "loan_account_number" in str(e):
                return False, "Loan account number already exists"
            elif "reference_id" in str(e):
                return False, "Asset reference ID already exists"
            return False, f"Data integrity error: {str(e)}"
            
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            return False, f"Database error: {str(e)}"
            
        except Exception as e:
            if conn:
                conn.rollback()
            return False, f"Unexpected error: {str(e)}"
            
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def get_summary_stats():
        """Fetch total customers and total loan amount due."""
        query_customers = "SELECT COUNT(*) FROM Customers"
        query_loan_due = "SELECT SUM(loan_amount_due) FROM LoanView"

        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()

            cursor.execute(query_customers)
            total_customers = cursor.fetchone()[0]

            cursor.execute(query_loan_due)
            total_loan_due = cursor.fetchone()[0] or 0  # Handle NULL with 0

            return total_customers, total_loan_due
        except sqlite3.Error as e:
            print(f"Database error while fetching summary stats: {e}")
            return 0, 0
        finally:
            if conn:
                conn.close()