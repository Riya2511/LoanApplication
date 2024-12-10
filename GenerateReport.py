from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QGroupBox, QMessageBox
)
from helper import StyledWidget
from DatabaseManager import DatabaseManager
from fpdf import FPDF

class GenerateReport(StyledWidget):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent, with_back_button=True, title="Generate Report", switch_page_callback=switch_page_callback)
        self.init_ui()

    def init_ui(self):
        # Table to display customers and their loan data
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(5)
        self.customer_table.setHorizontalHeaderLabels(
            ["Cust ID", "Cust Name", "Total Loan Amount (₹)", "Total Pending Amount (₹)", "Generate Report"]
        )
        self.customer_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.customer_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.customer_table.setSelectionMode(QTableWidget.SingleSelection)
        self.customer_table.setFixedHeight(300)
        self.content_layout.addWidget(self.customer_table)

        # Load customer data into the table
        self.populate_customer_table()

        self.content_layout.addStretch(1)

    def populate_customer_table(self):
        """Populate the customer table with customer data."""
        self.customer_table.setRowCount(0)
        customers = DatabaseManager.get_all_customers()
        for row_idx, customer in enumerate(customers):
            customer_id, name, account_number = customer
            # Fetch total loan amount and total pending amount for the customer
            total_loan_amount, total_pending_amount = self.get_customer_loan_data(customer_id)
            
            self.customer_table.insertRow(row_idx)
            self.customer_table.setItem(row_idx, 0, QTableWidgetItem(str(customer_id)))
            self.customer_table.setItem(row_idx, 1, QTableWidgetItem(name))
            self.customer_table.setItem(row_idx, 2, QTableWidgetItem(str(total_loan_amount)))
            self.customer_table.setItem(row_idx, 3, QTableWidgetItem(str(total_pending_amount)))

            # Add a button to generate the report for each customer
            report_button = QPushButton("Generate Report")
            report_button.clicked.connect(lambda _, cust_id=customer_id: self.generate_report(cust_id))
            self.customer_table.setCellWidget(row_idx, 4, report_button)

    def get_customer_loan_data(self, customer_id):
        """Fetch total loan amount and total pending amount for a customer."""
        query = """
        SELECT 
            SUM(Loans.loan_amount) AS total_loan_amount,
            SUM(Loans.loan_amount + Loans.interest_amount - Loans.loan_amount_paid) AS total_pending_amount
        FROM Loans
        WHERE Loans.customer_id = ?
        """
        result = DatabaseManager.fetch_data(query, (customer_id,))
        if result:
            total_loan_amount, total_pending_amount = result[0]
            return total_loan_amount if total_loan_amount else 0, total_pending_amount if total_pending_amount else 0
        return 0, 0

    def generate_report(self, customer_id):
        """Generate and download a detailed UTF-8 encoded PDF for a customer."""
        # Fetch customer details
        customer = DatabaseManager.get_customer_by_id(customer_id)
        if not customer:
            QMessageBox.warning(self, "Error", "Customer not found.")
            return
        
        name = customer['name']
        account_number = customer['account_number']

        # Fetch loan details for the customer
        loans = DatabaseManager.fetch_loans_for_customer(customer_id)
        if not loans:
            QMessageBox.warning(self, "Error", "No loans found for this customer.")
            return
        
        # Create PDF instance
        pdf = FPDF()
        pdf.add_page()

        # Add a font that supports UTF-8 (DejaVuSans)
        pdf.add_font('DejaVuSans', '', 'fonts\\DejaVuSans.ttf', uni=True)
        pdf.set_font("DejaVuSans", size=12)

        # Title
        pdf.cell(200, 10, txt=f"Loan Report for {name} ({account_number})", ln=True, align="C")

        # Customer general details
        pdf.ln(10)  # Line break
        pdf.cell(200, 10, txt="Customer Details:", ln=True)
        pdf.cell(200, 10, txt=f"Customer Name: {name}", ln=True)
        pdf.cell(200, 10, txt=f"Account Number: {account_number}", ln=True)

        # Loan details
        pdf.ln(10)
        pdf.cell(200, 10, txt="Loan Details:", ln=True)

        # Add table header
        pdf.cell(50, 10, 'Loan Date', border=1, align='C')
        pdf.cell(50, 10, 'Amount (₹)', border=1, align='C')
        pdf.cell(50, 10, 'Amount Paid (₹)', border=1, align='C')
        pdf.cell(50, 10, 'Pending Amount (₹)', border=1, align='C')
        pdf.ln(10)

        total_loan_amount = 0
        total_pending_amount = 0

        for loan in loans:
            loan_date = loan[0]
            loan_amount = loan[2]
            loan_paid = loan[3]
            loan_pending = loan_amount + loan[4] - loan_paid
            total_loan_amount += loan_amount
            total_pending_amount += loan_pending

            pdf.cell(50, 10, str(loan_date), border=1, align='C')
            pdf.cell(50, 10, str(loan_amount), border=1, align='C')
            pdf.cell(50, 10, str(loan_paid), border=1, align='C')
            pdf.cell(50, 10, str(loan_pending), border=1, align='C')
            pdf.ln(10)

            # Asset details for each loan
            assets = DatabaseManager.fetch_loan_assets(loan[5])  # loan_id = loan[5]
            pdf.cell(200, 10, txt="Assets attached to this loan:", ln=True)
            for asset in assets:
                asset_desc = asset[0]
                asset_weight = asset[1]
                pdf.cell(200, 10, txt=f"Asset Description: {asset_desc}, Weight: {asset_weight} kg", ln=True)

            # Repayment details for each loan
            repayments = DatabaseManager.fetch_loan_payments(loan[5])  # loan_id = loan[5]
            if repayments:
                pdf.cell(200, 10, txt="Repayment History:", ln=True)
                pdf.cell(50, 10, 'Payment Date', border=1, align='C')
                pdf.cell(50, 10, 'Amount Paid (₹)', border=1, align='C')
                pdf.cell(50, 10, 'Remaining Amount (₹)', border=1, align='C')
                pdf.ln(10)

                total_paid = 0
                for repayment in repayments:
                    payment_date = repayment[0]
                    payment_amount = repayment[1]
                    total_paid += payment_amount
                    remaining_amount = loan_pending - total_paid

                    pdf.cell(50, 10, str(payment_date), border=1, align='C')
                    pdf.cell(50, 10, str(payment_amount), border=1, align='C')
                    pdf.cell(50, 10, str(remaining_amount), border=1, align='C')
                    pdf.ln(10)
            else:
                pdf.cell(200, 10, txt="No repayment history available.", ln=True)

        # Total loan and pending amounts
        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Total Loan Amount: ₹{total_loan_amount}", ln=True)
        pdf.cell(200, 10, txt=f"Total Pending Amount: ₹{total_pending_amount}", ln=True)

        # Save the PDF to a file
        report_filename = f"{name}_Loan_Report.pdf"
        pdf.output(report_filename)

        # Inform user
        QMessageBox.information(self, "Report Generated", f"Loan report generated successfully! Download: {report_filename}")
