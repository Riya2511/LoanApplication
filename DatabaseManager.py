import sqlite3
import os
class DatabaseManager:
    @staticmethod
    def init_database():
        """Initialize the database and create tables if they don't exist."""
        try:
            conn = sqlite3.connect("loanApp.db")
            # if os.name == 'nt':  # Check if the OS is Windows
            #     os.system(f"attrib +h {"loanApp.db"}")
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Customers (
                    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR NOT NULL,
                    account_number VARCHAR UNIQUE NOT NULL,
                    reference_id VARCHAR NULL,
                    phone VARCHAR UNIQUE,
                    address TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Loans (
                    loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
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
                    l.loan_id AS loan_id,
                    l.customer_id AS customer_id
                FROM Loans l
                LEFT JOIN Assets a ON l.loan_id = a.loan_id
                LEFT JOIN LoanPayments p ON l.loan_id = p.loan_id
                GROUP BY l.loan_id;
            ''')
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
    def get_all_customers():
        """Fetch all customers for dropdown"""
        query = "SELECT customer_id, name, account_number FROM Customers ORDER BY name"
        return DatabaseManager.fetch_data(query)

    @staticmethod
    def get_customer_by_id(customer_id):
        """Fetch full customer details by ID"""
        query = """
        SELECT customer_id, name, account_number, phone, address, reference_id
        FROM Customers 
        WHERE customer_id = ?
        """
        customer = DatabaseManager.fetch_data(query, (customer_id,))
        if customer:
            columns = ['customer_id', 'name', 'account_number', 'phone', 'address', 'reference_id']
            return dict(zip(columns, customer[0]))  # Return first record as dict
        return None

    @staticmethod
    def insert_loan(customer_id, loan_amount):
        """Insert a new loan and return the loan_id"""
        query = """
        INSERT INTO Loans 
        (customer_id, loan_amount) 
        VALUES (?, ?)
        """
        conn = DatabaseManager.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (customer_id, loan_amount))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def insert_asset(loan_id, description, weight):
        """Insert a new asset associated with a loan"""
        query = """
        INSERT INTO Assets 
        (loan_id, description, weight) 
        VALUES (?, ?, ?)
        """
        conn = DatabaseManager.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (loan_id, description, weight))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def insert_loan_payment(loan_id, payment_amount, interest_amount, amount_left, asset_description):
        """Insert a new loan payment with asset details."""
        query = """
        INSERT INTO LoanPayments (
            loan_id, payment_amount, interest_amount, 
            amount_left, asset_description, payment_date
        ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        DatabaseManager.execute_query(
            query, 
            (loan_id, payment_amount, interest_amount, amount_left, asset_description)
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
        SELECT description, weight
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