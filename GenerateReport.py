from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QGroupBox, QMessageBox, QComboBox, 
    QLineEdit, QFormLayout
)
from helper import StyledWidget
from DatabaseManager import DatabaseManager
from fpdf import FPDF
from datetime import datetime

class GenerateReport(StyledWidget):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent, with_back_button=True, title="Generate Report", switch_page_callback=switch_page_callback)
        self.selected_customer_id = None
        self.customer_info_group = None
        self.loan_details_table = None
        self.loan_payments_table = None
        self.init_ui()

    def init_ui(self):
        # Customer Selection Section with Search Functionality
        customer_layout = QHBoxLayout()
        self.customer_dropdown = QComboBox()
        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("Search Customer")
        self.customer_search.textChanged.connect(self.filter_customers)
        
        customer_layout.addWidget(QLabel("Select Customer:"))
        customer_layout.addWidget(self.customer_dropdown)
        customer_layout.addWidget(self.customer_search)
        self.content_layout.addLayout(customer_layout)

        # Customer Information Group Box
        self.customer_info_group = QGroupBox("Customer Information")
        self.customer_info_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d3d3d3;
                border-radius: 5px;
                margin-top: 10px;
                margin-bottom: 10px;
                padding-top: 20px;
                background-color: white;
            }
        """)
        customer_info_layout = QVBoxLayout()
        self.customer_info_group.setLayout(customer_info_layout)
        self.content_layout.addWidget(self.customer_info_group)

        # Loan Details Table
        self.loan_details_table = QTableWidget()
        self.loan_details_table.setColumnCount(6)
        self.loan_details_table.setHorizontalHeaderLabels(
            ["Loan Date", "Asset Description", "Asset Weight (kg)", "Total Amount (₹)", "Amount Due (₹)", ""]
        )
        self.loan_details_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.loan_details_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.loan_details_table.setSelectionMode(QTableWidget.SingleSelection)
        self.content_layout.addWidget(self.loan_details_table)

        # Loan Payments Table (initially hidden)
        self.loan_payments_table = QTableWidget()
        self.loan_payments_table.setColumnCount(3)
        self.loan_payments_table.setHorizontalHeaderLabels(
            ["Payment Date", "Amount Paid (₹)", "Remaining Amount (₹)"]
        )
        self.loan_payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.loan_payments_table.setVisible(False)
        self.content_layout.addWidget(self.loan_payments_table)

        # Buttons for Report Generation
        button_layout = QHBoxLayout()
        self.generate_pdf_button = QPushButton("Generate PDF Report")
        self.generate_pdf_button.clicked.connect(self.generate_pdf_report)
        button_layout.addWidget(self.generate_pdf_button)
        self.content_layout.addLayout(button_layout)

        # Connect dropdown selection
        self.customer_dropdown.currentIndexChanged.connect(self.on_customer_selected)
        self.loan_details_table.cellClicked.connect(self.show_loan_payments)

        self.content_layout.addStretch(1)

    def showEvent(self, event: QEvent):
        """Handle page load event and refresh customer data."""
        if event.type() == QEvent.Show:
            self.populate_customer_dropdown()
        super().showEvent(event)

    def populate_customer_dropdown(self):
        """Populate the dropdown with the latest customer data."""
        self.customer_dropdown.clear()
        customers = DatabaseManager.get_all_customers()
        if customers:
            for customer_id, name, account_number in customers:
                self.customer_dropdown.addItem(f"{name}", customer_id)
        else:
            self.customer_dropdown.addItem("No customers found")

    def filter_customers(self, text):
        """Filter customers based on search text."""
        self.customer_dropdown.clear()
        customers = DatabaseManager.get_all_customers()
        
        filtered_customers = [
            (customer_id, name, account_number) 
            for customer_id, name, account_number in customers 
            if text.lower() in f"{name} {account_number}".lower()
        ]
        if filtered_customers:
            for customer_id, name, account_number in filtered_customers:
                self.customer_dropdown.addItem(f"{name} - {account_number}", customer_id)
        else:
            self.customer_dropdown.addItem("No matching customers found")

    def on_customer_selected(self, index):
        """Display customer information and loans when a customer is selected."""
        if index < 0:
            return

        self.selected_customer_id = self.customer_dropdown.currentData()
        self.populate_customer_info()
        self.populate_loans_table()

    def populate_customer_info(self):
        """Populate customer information in the customer info group."""
        # Clear existing labels
        customer_info_layout = self.customer_info_group.layout()
        while customer_info_layout.count():
            child = customer_info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        customer_info = DatabaseManager.get_customer_by_id(self.selected_customer_id)
        if customer_info:
            for key, value in customer_info.items():
                label = QLabel(f"{key.replace('_', ' ').title()}: {value}")
                customer_info_layout.addWidget(label)

    def populate_loans_table(self):
        """Populate the loan table with loans for the selected customer."""
        self.loan_details_table.setRowCount(0)
        loans = DatabaseManager.fetch_loans_for_customer(self.selected_customer_id)
        
        for row_idx, loan in enumerate(loans):
            self.loan_details_table.insertRow(row_idx)
            for col_idx, value in enumerate(loan[:-2]):
                if col_idx == 0:
                    value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    value = value.strftime("%d-%m-%Y %H:%M:%S")
                elif col_idx in (2, 3, 4):
                    value = f"{float(value):,.2f}" if value else "0.00"
                self.loan_details_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            
            details_button = QPushButton("Loan Payments")
            details_button.clicked.connect(lambda _, loan_id=loan[-2]: self.show_loan_payments(row_idx, 5, loan_id))
            self.loan_details_table.setCellWidget(row_idx, 5, details_button)

    def show_loan_payments(self, row, column, loan_id=None):
        """Show loan payments for the selected loan."""
        if not loan_id:
            loan_id = self.loan_details_table.item(row, 5).data(Qt.UserRole)
        
        self.loan_payments_table.setRowCount(0)
        self.loan_payments_table.setVisible(True)
        
        repayments = DatabaseManager.fetch_loan_payments(loan_id)
        if repayments:
            for row_idx, repayment in enumerate(repayments):
                self.loan_payments_table.insertRow(row_idx)
                value = datetime.strptime(repayment['payment_date'], "%Y-%m-%d %H:%M:%S")
                value = value.strftime("%d-%m-%Y %H:%M:%S")
                
                self.loan_payments_table.setItem(row_idx, 0, QTableWidgetItem(value))
                self.loan_payments_table.setItem(row_idx, 1, QTableWidgetItem(str(repayment["payment_amount"])))
                self.loan_payments_table.setItem(row_idx, 2, QTableWidgetItem(str(repayment["amount_left"])))
        else:
            self.loan_payments_table.insertRow(0)
            self.loan_payments_table.setItem(0, 0, QTableWidgetItem("No payments made"))
            self.loan_payments_table.setItem(0, 1, QTableWidgetItem("0"))
            self.loan_payments_table.setItem(0, 2, QTableWidgetItem("N/A"))

    def generate_pdf_report(self):
        """Generate a comprehensive PDF report for the selected customer."""
        if not self.selected_customer_id:
            QMessageBox.warning(self, "Error", "Please select a customer first.")
            return

        try:
            # Fetch customer information
            customer_info = DatabaseManager.get_customer_by_id(self.selected_customer_id)
            loans = DatabaseManager.fetch_loans_for_customer(self.selected_customer_id)

            # Create PDF with custom font
            pdf = FPDF()
            # Add custom font - make sure to provide the full path to the .ttf file
            pdf.add_font('DejaVuSans', '', 'fonts\\DejaVuSans.ttf', uni=True)
            
            pdf.add_page()
            pdf.set_font('DejaVuSans', '', 16)
            pdf.cell(0, 10, "Customer Loan Report", ln=True)

            # Customer Information
            pdf.set_font('DejaVuSans', '', 12)
            pdf.cell(0, 10, f"Name: {customer_info.get('name', 'N/A')}", ln=True)
            pdf.cell(0, 10, f"Account Number: {customer_info.get('account_number', 'N/A')}", ln=True)
            pdf.cell(0, 10, f"Phone: {customer_info.get('phone', 'N/A')}", ln=True)
            pdf.cell(0, 10, f"Address: {customer_info.get('address', 'N/A')}", ln=True)

            # Loan Details
            pdf.ln(10)
            pdf.set_font('DejaVuSans', '', 14)
            pdf.cell(0, 10, "Loan Details", ln=True)

            for loan in loans:
                pdf.set_font('DejaVuSans', '', 12)
                pdf.cell(0, 10, f"Loan Date: {loan[0]}", ln=True)
                pdf.cell(0, 10, f"Asset Description: {loan[1]}", ln=True)
                pdf.cell(0, 10, f"Asset Weight: {loan[2]} kg", ln=True)
                pdf.cell(0, 10, f"Total Loan Amount: ₹{float(loan[3]):,.2f}", ln=True)
                pdf.cell(0, 10, f"Amount Due: ₹{float(loan[5]):,.2f}", ln=True)

                # Fetch and add loan payments
                payments = DatabaseManager.fetch_loan_payments(loan[-2])
                if payments:
                    pdf.set_font('DejaVuSans', '', 12)
                    pdf.cell(0, 10, "Loan Payments:", ln=True)
                    pdf.set_font('DejaVuSans', '', 10)
                    for payment in payments:
                        pdf.cell(0, 10, 
                            f"Date: {payment['payment_date']}, "
                            f"Amount: ₹{payment['payment_amount']:,.2f}, "
                            f"Remaining: ₹{payment['amount_left']:,.2f}", 
                            ln=True
                        )

                pdf.ln(10)

            # Save PDF
            filename = f"customer_loan_report_{customer_info.get('name', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf.output(filename)
            QMessageBox.information(self, "Success", f"Report generated: {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")
            """Generate a comprehensive PDF report for the selected customer."""
            if not self.selected_customer_id:
                QMessageBox.warning(self, "Error", "Please select a customer first.")
                return

            try:
                # Fetch customer information
                customer_info = DatabaseManager.get_customer_by_id(self.selected_customer_id)
                loans = DatabaseManager.fetch_loans_for_customer(self.selected_customer_id)

                # Create PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "Customer Loan Report", ln=True)

                # Customer Information
                pdf.set_font("Arial", "", 12)
                pdf.cell(0, 10, f"Name: {customer_info['name']}", ln=True)
                pdf.cell(0, 10, f"Account Number: {customer_info['account_number']}", ln=True)
                pdf.cell(0, 10, f"Phone: {customer_info['phone']}", ln=True)
                pdf.cell(0, 10, f"Address: {customer_info['address']}", ln=True)

                # Loan Details
                pdf.ln(10)
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, "Loan Details", ln=True)

                for loan in loans:
                    pdf.set_font("Arial", "", 12)
                    pdf.cell(0, 10, f"Loan Date: {loan[0]}", ln=True)
                    pdf.cell(0, 10, f"Asset Description: {loan[1]}", ln=True)
                    pdf.cell(0, 10, f"Asset Weight: {loan[2]} kg", ln=True)
                    pdf.cell(0, 10, f"Total Loan Amount: ₹{float(loan[3]):,.2f}", ln=True)
                    pdf.cell(0, 10, f"Amount Due: ₹{float(loan[5]):,.2f}", ln=True)

                    # Fetch and add loan payments
                    payments = DatabaseManager.fetch_loan_payments(loan[-2])
                    if payments:
                        pdf.set_font("Arial", "B", 12)
                        pdf.cell(0, 10, "Loan Payments:", ln=True)
                        pdf.set_font("Arial", "", 10)
                        for payment in payments:
                            pdf.cell(0, 10, 
                                f"Date: {payment['payment_date']}, "
                                f"Amount: ₹{payment['payment_amount']:,.2f}, "
                                f"Remaining: ₹{payment['amount_left']:,.2f}", 
                                ln=True
                            )

                    pdf.ln(10)

                # Save PDF
                filename = f"customer_loan_report_{customer_info['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf.output(filename)
                QMessageBox.information(self, "Success", f"Report generated: {filename}")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")