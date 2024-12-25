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
        self.current_loan_id = None
        self.customer_info_group = None
        self.loan_details_table = None
        self.update_group = None
        self.assets_table = None
        self.loan_payments_table = None
        self.init_ui()

    def init_ui(self):
        # Customer Selection Section with Search Functionality
        customer_layout = QHBoxLayout()
        self.customer_dropdown = QComboBox()
        self.customer_dropdown.setFixedWidth(300)
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
            ["Loan Date", "Total Assets", "Total Weight (g)", "Total Amount (₹)", "Amount Due (₹)", ""]
        )
        self.loan_details_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.loan_details_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.loan_details_table.setSelectionMode(QTableWidget.SingleSelection)
        self.loan_details_table.setFixedHeight(200)
        self.content_layout.addWidget(self.loan_details_table)

        # Assets and Payments Section (hidden by default)
        self.update_group = QGroupBox("Loan Assets and Payments")
        self.update_group.setVisible(False)
        update_layout = QVBoxLayout()

        # Assets Table
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(2)
        self.assets_table.setHorizontalHeaderLabels(
            ["Asset Description", "Weight (g)"]
        )
        update_layout.addWidget(self.assets_table)

        # Loan Payments Table
        payments_label = QLabel("Payment History:")
        update_layout.addWidget(payments_label)
        
        self.loan_payments_table = QTableWidget()
        self.loan_payments_table.setColumnCount(5)
        self.loan_payments_table.setHorizontalHeaderLabels(
            ["Payment Date", "Asset", "Amount Paid (₹)", "Interest Paid (₹)", "Remaining (₹)"]
        )
        self.loan_payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        update_layout.addWidget(self.loan_payments_table)

        # Close button
        button_layout = QHBoxLayout()
        self.close_button = QPushButton("Close")
        self.close_button.setFixedWidth(100)
        self.close_button.setFixedHeight(25)
        self.close_button.clicked.connect(self.hide_detail_section)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ff0000;
            }
        """)
        button_layout.addWidget(self.close_button)
        update_layout.addLayout(button_layout)

        self.update_group.setLayout(update_layout)
        self.content_layout.addWidget(self.update_group)

        # Buttons for Report Generation
        report_button_layout = QHBoxLayout()
        self.generate_pdf_button = QPushButton("Generate PDF Report")
        self.generate_pdf_button.clicked.connect(self.generate_pdf_report)
        report_button_layout.addWidget(self.generate_pdf_button)
        self.content_layout.addLayout(report_button_layout)

        # Connect dropdown selection
        self.customer_dropdown.currentIndexChanged.connect(self.on_customer_selected)

        self.content_layout.addStretch(1)

    def populate_assets_table(self, loan_id):
        """Populate assets table with loan assets."""
        self.assets_table.setRowCount(0)
        assets = DatabaseManager.fetch_loan_assets(loan_id)
        
        for row_idx, (description, weight) in enumerate(assets):
            self.assets_table.insertRow(row_idx)
            self.assets_table.setItem(row_idx, 0, QTableWidgetItem(description))
            self.assets_table.setItem(row_idx, 1, QTableWidgetItem(f"{weight:,.2f}"))

    def populate_loan_payments_table(self, loan_id):
        """Populate the loan payments table with payment history."""
        self.loan_payments_table.setRowCount(0)
        repayments = DatabaseManager.fetch_loan_payments(loan_id)
        
        if repayments:
            for row_idx, repayment in enumerate(repayments):
                self.loan_payments_table.insertRow(row_idx)
                
                payment_date = datetime.strptime(repayment['payment_date'], "%Y-%m-%d %H:%M:%S")
                formatted_date = payment_date.strftime("%d-%m-%Y %H:%M:%S")
                
                self.loan_payments_table.setItem(row_idx, 0, QTableWidgetItem(formatted_date))
                self.loan_payments_table.setItem(row_idx, 1, QTableWidgetItem(repayment.get("asset_description", "")))
                self.loan_payments_table.setItem(row_idx, 2, QTableWidgetItem(f"{float(repayment['payment_amount']):,.2f}"))
                self.loan_payments_table.setItem(row_idx, 3, QTableWidgetItem(f"{float(repayment['interest_amount']):,.2f}"))
                self.loan_payments_table.setItem(row_idx, 4, QTableWidgetItem(f"{float(repayment['amount_left']):,.2f}"))
        else:
            self.loan_payments_table.insertRow(0)
            self.loan_payments_table.setItem(0, 0, QTableWidgetItem("No payments made"))
            for i in range(1, 5):
                self.loan_payments_table.setItem(0, i, QTableWidgetItem("-"))

    def show_loan_details(self, loan_id):
        """Show the loan details section with assets and payments."""
        self.current_loan_id = loan_id
        self.update_group.setVisible(True)
        
        self.populate_assets_table(loan_id)
        self.populate_loan_payments_table(loan_id)

    def hide_detail_section(self):
        """Hide the loan details section."""
        self.update_group.setVisible(False)

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
        customer_info_layout = self.customer_info_group.layout()
        while customer_info_layout.count():
            child = customer_info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        customer_info = DatabaseManager.get_customer_by_id(self.selected_customer_id)
        if customer_info:
            for key, value in customer_info.items():
                if key == "customer_id" or not value:
                    continue
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
            
            view_button = QPushButton("View More")
            view_button.clicked.connect(lambda checked, lid=loan[-2]: self.show_loan_details(lid))
            self.loan_details_table.setCellWidget(row_idx, 5, view_button)

    def generate_pdf_report(self):
        """Generate a comprehensive PDF report for the selected customer."""
        if not self.selected_customer_id:
            QMessageBox.warning(self, "Error", "Please select a customer first.")
            return

        try:
            customer_info = DatabaseManager.get_customer_by_id(self.selected_customer_id)
            loans = DatabaseManager.fetch_loans_for_customer(self.selected_customer_id)

            pdf = FPDF()
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
            for loan in loans:
                pdf.ln(10)
                pdf.set_font('DejaVuSans', '', 14)
                pdf.cell(0, 10, "Loan Details", ln=True)
                
                pdf.set_font('DejaVuSans', '', 12)
                loan_date = datetime.strptime(loan[0], "%Y-%m-%d %H:%M:%S")
                pdf.cell(0, 10, f"Loan Date: {loan_date.strftime('%d-%m-%Y %H:%M:%S')}", ln=True)
                pdf.cell(0, 10, f"Total Weight: {float(loan[2]):,.2f} g", ln=True)
                pdf.cell(0, 10, f"Total Loan Amount: ₹{float(loan[3]):,.2f}", ln=True)
                pdf.cell(0, 10, f"Amount Due: ₹{float(loan[4]):,.2f}", ln=True)

                # Add assets
                pdf.ln(5)
                pdf.set_font('DejaVuSans', '', 12)
                pdf.cell(0, 10, "Assets:", ln=True)
                assets = DatabaseManager.fetch_loan_assets(loan[-2])
                if assets:
                    for desc, weight in assets:
                        pdf.cell(0, 10, f"- {desc}: {weight:,.2f}g", ln=True)
                else:
                    pdf.cell(0, 10, "No assets found", ln=True)

                # Add loan payments
                pdf.ln(5)
                pdf.cell(0, 10, "Payment History:", ln=True)
                payments = DatabaseManager.fetch_loan_payments(loan[-2])
                if payments:
                    pdf.set_font('DejaVuSans', '', 10)
                    for payment in payments:
                        payment_date = datetime.strptime(payment['payment_date'], "%Y-%m-%d %H:%M:%S")
                        pdf.multi_cell(0, 10, 
                            f"Date: {payment_date.strftime('%d-%m-%Y %H:%M:%S')}\n"
                            f"Asset: {payment.get('asset_description', 'N/A')}\n"
                            f"Amount Paid: ₹{float(payment['payment_amount']):,.2f}\n"
                            f"Interest Paid: ₹{float(payment['interest_amount']):,.2f}\n"
                            f"Remaining Amount: ₹{float(payment['amount_left']):,.2f}\n"
                        )
                        pdf.ln(5)
                else:
                    pdf.cell(0, 10, "No payments recorded", ln=True)

                pdf.ln(10)
                pdf.cell(0, 0, "_" * 50, ln=True)  # Add separator line between loans

            # Save PDF
            filename = f"customer_loan_report_{customer_info.get('name', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf.output(filename)
            QMessageBox.information(self, "Success", f"Report generated: {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")
            