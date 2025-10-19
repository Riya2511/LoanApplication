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
                    phone VARCHAR NULL,
                    address TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Loans (
                    loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    registered_reference_id TEXT DEFAULT NULL,
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
                    loan_id INTEGER NOT NULL UNIQUE,
                    description TEXT NOT NULL,
                    weight DECIMAL(10, 2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (loan_id) REFERENCES Loans(loan_id) ON DELETE CASCADE
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
                    l.registered_reference_id AS registered_reference_id,
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
    def insert_loan(customer_id, loan_amount, loan_date, registered_reference_id):
        """Insert a new loan and return the loan_id"""
        query = """
        INSERT INTO Loans 
        (customer_id, loan_amount, created_at, registered_reference_id) 
        VALUES (?, ?, ?, ?)
        """
        conn = DatabaseManager.create_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, (customer_id, loan_amount, loan_date, registered_reference_id))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    @staticmethod
    def insert_asset(loan_id, description, weight):
        """Insert a new asset associated with a loan (one-to-one relationship)."""
        query = """
        INSERT INTO Assets (loan_id, description, weight) 
        VALUES (?, ?, ?)
        """
        return DatabaseManager.execute_query(query, (loan_id, description, weight))

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
        SELECT description, weight
        FROM Assets
        WHERE loan_id = ?
        """
        return DatabaseManager.fetch_data(query, (loan_id,))

    @staticmethod
    def fetch_loan_payments(loan_id):
        """Fetch all payments made for a given loan."""
        query = """
        SELECT payment_id, payment_date, payment_amount, amount_left, interest_amount, asset_description
        FROM LoanPayments
        WHERE loan_id = ?
        ORDER BY payment_date ASC
        """
        results = DatabaseManager.fetch_data(query, (loan_id,))
        return [
            {"payment_id": result[0], "payment_date": result[1], "payment_amount": result[2], "amount_left": result[3], "interest_amount": result[4], "asset_description": result[5]}
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
    def insert_loan_with_asset(customer_id, loan_amount, loan_date, registered_reference_id, description, weight):
        conn = None
        try:
            conn = DatabaseManager.create_connection()
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.cursor()

            # Insert Loan
            cursor.execute("""
                INSERT INTO Loans (customer_id, loan_amount, created_at, registered_reference_id)
                VALUES (?, ?, ?, ?)
            """, (customer_id, loan_amount, loan_date, registered_reference_id))
            loan_id = cursor.lastrowid

            # Insert Asset
            cursor.execute("""
                INSERT INTO Assets (loan_id, description, weight)
                VALUES (?, ?, ?)
            """, (loan_id, description, weight))

            conn.commit()
            return True, "Loan registered successfully"
        
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            return False, f"Database error: {str(e)}"
        
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

    @staticmethod
    def update_customer(customer_id, name, phone, address):
        """Update an existing customer's details."""
        query = """
        UPDATE Customers 
        SET name = ?, phone = ?, address = ?, updated_at = CURRENT_TIMESTAMP
        WHERE customer_id = ?
        """
        try:
            cursor = DatabaseManager.execute_query(query, (name, phone, address, customer_id))
            return cursor.rowcount > 0  # Return True if any row was updated
        except sqlite3.IntegrityError:
            return False  # Handle unique phone constraint

    @staticmethod
    def update_loan_assets(loan_id, description, weight):
        """Updates the asset details for a given loan."""
        # First check if an asset record exists for this loan
        check_query = "SELECT COUNT(*) FROM Assets WHERE loan_id = ?"
        result = DatabaseManager.fetch_data(check_query, (loan_id,))
        
        if result and result[0][0] > 0:
            # Update existing record
            update_query = """
            UPDATE Assets
            SET description = ?, weight = ?, updated_at = CURRENT_TIMESTAMP
            WHERE loan_id = ?
            """
            return DatabaseManager.execute_query(update_query, (description, weight, loan_id))
        else:
            # Insert new record
            insert_query = """
            INSERT INTO Assets (loan_id, description, weight)
            VALUES (?, ?, ?)
            """
            return DatabaseManager.execute_query(insert_query, (loan_id, description, weight))
    
    @staticmethod
    def update_loan(loan_id, loan_date, registered_reference_id, loan_amount):
        """Updates loan details."""
        query = """
        UPDATE Loans
        SET created_at = ?, registered_reference_id = ?, loan_amount = ?
        WHERE loan_id = ?
        """
        return DatabaseManager.execute_query(query, (loan_date, registered_reference_id, loan_amount, loan_id))

    # @staticmethod
    # def fetch_loan_details_to_edit(loan_id):
    #     """Fetches loan details for a given loan ID."""
    #     query = """
    #     SELECT loan_date, registered_reference_id, loan_amount
    #     FROM LoanView
    #     WHERE loan_id = ?
    #     """
    #     try: 
    #         conn = DatabaseManager.create_connection()
    #         cursor = conn.cursor()

    #         cursor.execute(query, (loan_id, ))
    #         result = cursor.fetchone()[0]
    #         if result:
    #             return {
    #                 "loan_date": result[0],
    #                 "registered_reference_id": result[1],
    #                 "loan_amount_left": result[2]
    #             }
    #     except sqlite3.Error as e:
    #         print(f"Database error while fetching load details to edit: {e}")
    #         return None
    #     finally:
    #         if conn:
    #             conn.close()
    
    @staticmethod
    def fetch_loan_details_to_edit(loan_id):
        """Fetch loan details along with the asset details."""
        query = """
        SELECT l.registered_reference_id, l.loan_amount, a.description, a.weight
        FROM Loans l
        LEFT JOIN Assets a ON l.loan_id = a.loan_id
        WHERE l.loan_id = ?
        """
        result = DatabaseManager.fetch_data(query, (loan_id,))
        if result:
            return {
                "registered_reference_id": result[0][0],
                "loan_amount": result[0][1],
                "description": result[0][2] if result[0][2] else "",
                "weight": result[0][3] if result[0][3] else "0.0"
            }
        return None

    @staticmethod
    def update_loan_payment_record(payment_id, payment_date, payment_amount, interest_amount, asset_description):
        """
        Update an existing loan payment record.
        
        Args:
            payment_id: ID of the payment to update
            payment_date: New payment date
            payment_amount: New payment amount
            interest_amount: New interest amount
            asset_description: New asset description
        """
        query = """
        UPDATE LoanPayments
        SET payment_date = ?,
            payment_amount = ?,
            interest_amount = ?,
            asset_description = ?
        WHERE payment_id = ?
        """
        
        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()
            cursor.execute(query, (payment_date, payment_amount, interest_amount, 
                                asset_description, payment_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error while updating payment: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update_loan_total_paid(loan_id, total_paid, loan_status):
        """
        Update the total amount paid on a loan and its status.
        
        Args:
            loan_id: ID of the loan to update
            total_paid: New total paid amount
            loan_status: New loan status ('Pending' or 'Completed')
        """
        query = """
        UPDATE Loans
        SET loan_amount_paid = ?,
            loan_status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE loan_id = ?
        """
        
        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()
            cursor.execute(query, (total_paid, loan_status, loan_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error while updating loan total: {e}")
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_summary_stats_to_generate_report(year=None):
        """
        Fetch total customers and total loan amount due, optionally filtered by year.
        
        Args:
            year: Optional year to filter by
        
        Returns:
            tuple: (total_customers, total_loan_due)
        """
        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()
            
            if year:
                # Count customers who had loans in the specified year
                query_customers = """
                    SELECT COUNT(DISTINCT customer_id) 
                    FROM Loans 
                    WHERE strftime('%Y', created_at) = ?
                """
                cursor.execute(query_customers, (str(year),))
                total_customers = cursor.fetchone()[0]
                
                # Get total loan amount due for loans created in the specified year
                query_loan_due = """
                    SELECT SUM(loan_amount_due) 
                    FROM LoanView 
                    WHERE strftime('%Y', loan_date) = ?
                """
                cursor.execute(query_loan_due, (str(year),))
                
            else:
                # Get total customers and loan amount due across all years
                query_customers = "SELECT COUNT(*) FROM Customers"
                cursor.execute(query_customers)
                total_customers = cursor.fetchone()[0]
                
                query_loan_due = "SELECT SUM(loan_amount_due) FROM LoanView"
                cursor.execute(query_loan_due)
            
            total_loan_due = cursor.fetchone()[0] or 0  # Handle NULL with 0
            
            return total_customers, float(total_loan_due)
        
        except sqlite3.Error as e:
            print(f"Database error while fetching summary stats: {e}")
            return 0, 0.0
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_customers_by_year(year=None):
        """
        Fetch customers, optionally filtered by those who had loans in a specific year.
        
        Args:
            year: Optional year to filter by
        
        Returns:
            list: List of tuples containing customer_id, name, phone
        """
        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()
            
            if year:
                # Get customers who had loans in the specified year
                query = """
                    SELECT DISTINCT c.customer_id, c.name, c.phone
                    FROM Customers c
                    JOIN Loans l ON c.customer_id = l.customer_id
                    WHERE strftime('%Y', l.created_at) = ?
                    ORDER BY c.name
                """
                cursor.execute(query, (str(year),))
            else:
                # Get all customers
                query = """
                    SELECT customer_id, name, phone
                    FROM Customers
                    ORDER BY name
                """
                cursor.execute(query)
            
            return cursor.fetchall()
        
        except sqlite3.Error as e:
            print(f"Database error while fetching customers by year: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def fetch_loans_for_customer_to_generate_report(customer_id, year=None):
        """
        Fetch all loans for a specific customer, optionally filtered by year.
        
        Args:
            customer_id: ID of the customer
            year: Optional year to filter by
        
        Returns:
            list: List of loan data from LoanView
        """
        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()
            
            if year:
                # Get loans for the specified customer in the specified year
                query = """
                    SELECT * FROM LoanView 
                    WHERE customer_id = ? 
                    AND strftime('%Y', loan_date) = ?
                    ORDER BY loan_date DESC
                """
                cursor.execute(query, (customer_id, str(year)))
            else:
                # Get all loans for the specified customer
                query = """
                    SELECT * FROM LoanView 
                    WHERE customer_id = ?
                    ORDER BY loan_date DESC
                """
                cursor.execute(query, (customer_id,))
            
            return cursor.fetchall()
        
        except sqlite3.Error as e:
            print(f"Database error while fetching loans for customer {customer_id}: {e}")
            return []
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_customer_loan_totals(customer_id, year=None):
        """Get total loan amount and total amount due for a specific customer."""
        conn = DatabaseManager.create_connection()
        cursor = conn.cursor()
        
        try:
            query_params = [customer_id]
            
            # Base query without year filter
            query = """
                SELECT 
                    SUM(l.loan_amount) as total_loan_amount,
                    SUM(l.loan_amount - COALESCE(
                        (SELECT SUM(p.payment_amount) FROM LoanPayments p WHERE p.loan_id = l.loan_id), 0
                    )) as total_amount_due
                FROM loans l
                WHERE l.customer_id = ?
            """
            
            # Add year filter if specified
            if year:
                query += " AND strftime('%Y', l.created_at) = ?"
                query_params.append(str(year))
                
            cursor.execute(query, query_params)
            result = cursor.fetchone()
            
            total_loan = float(result[0]) if result[0] else 0
            total_due = float(result[1]) if result[1] else 0
            
            return total_loan, total_due
            
        except Exception as e:
            print(f"Error fetching customer loan totals: {e}")
            return 0, 0
        finally:
            conn.close()

    @staticmethod
    def get_loan_amount_due(loan_id):
        """Get the amount due for a specific loan."""
        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT loan_amount_due FROM LoanView WHERE loan_id = ?", 
                (loan_id,)
            )
            result = cursor.fetchone()
            conn.close()
            return float(result[0]) if result else 0
        except Exception as e:
            print(f"Error fetching loan amount due: {e}")
            return float('inf')  # Return infinity if error, to ensure button remains disabled
    
    @staticmethod
    def fetch_loans_by_year(year=None):
        """
        Fetch all loans for a given year from all customers.
        If the date of any loan is not in the correct format, skip it and print a warning.
        
        Args:
            year: Optional year to filter by. If None, returns all loans.
        
        Returns:
            list: List of loan data from LoanView with customer name, with valid dates
            Format: (loan_date, asset_descriptions, total_asset_weight, loan_amount, 
                     loan_amount_due, total_interest_amount, registered_reference_id, 
                     loan_id, customer_id, customer_name)
        """
        try:
            conn = DatabaseManager.create_connection()
            cursor = conn.cursor()
            
            if year:
                # Get all loans for the specified year with customer name
                query = """
                    SELECT lv.*, c.name as customer_name
                    FROM LoanView lv
                    JOIN Customers c ON lv.customer_id = c.customer_id
                    WHERE strftime('%Y', lv.loan_date) = ?
                    ORDER BY lv.loan_date DESC
                """
                cursor.execute(query, (str(year),))
            else:
                # Get all loans regardless of year with customer name
                query = """
                    SELECT lv.*, c.name as customer_name
                    FROM LoanView lv
                    JOIN Customers c ON lv.customer_id = c.customer_id
                    ORDER BY lv.loan_date DESC
                """
                cursor.execute(query)
            
            all_loans = cursor.fetchall()
            valid_loans = []
            
            # Validate each loan's date format
            for loan in all_loans:
                loan_date = loan[0]  # loan_date is the first column in LoanView
                try:
                    # Try to parse the date - if it fails, skip this loan
                    if loan_date:
                        # Attempt to parse the date in various formats
                        loan_date_str = str(loan_date).replace('00:00:00', '').strip()
                        from datetime import datetime
                        datetime.strptime(loan_date_str, "%Y-%m-%d")
                        valid_loans.append(loan)
                    else:
                        print(f"WARNING: Loan ID {loan[7]} has NULL date, skipping...")
                except ValueError as e:
                    print(f"WARNING: Loan ID {loan[7]} has invalid date format '{loan_date}', skipping... Error: {e}")
                except Exception as e:
                    print(f"WARNING: Loan ID {loan[7]} encountered error during date validation, skipping... Error: {e}")
            
            return valid_loans
        
        except sqlite3.Error as e:
            print(f"Database error while fetching loans by year: {e}")
            return []
        finally:
            if conn:
                conn.close()
        
    