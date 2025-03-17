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
        self.selected_year = None
        self.init_ui()
        
        # Hide elements initially
        self.customer_info_group.setVisible(False)
        self.loan_details_table.setVisible(False)
        self.generate_pdf_button.setEnabled(False)

    def init_ui(self):
        # Year Selection
        year_layout = QHBoxLayout()
        self.year_dropdown = QComboBox()
        self.year_dropdown.setFixedWidth(200)
        
        # Get current year
        current_year = datetime.now().year
        
        # Add years to dropdown (last 10 years)
        self.year_dropdown.addItem("All Years", None)
        for year in range(current_year, current_year - 10, -1):
            self.year_dropdown.addItem(str(year), year)
        
        year_layout.addWidget(QLabel("Select Year:"))
        year_layout.addWidget(self.year_dropdown)
        year_layout.addStretch(1)
        
        # Connect year selection change
        self.year_dropdown.currentIndexChanged.connect(self.on_year_selected)
        
        self.content_layout.addLayout(year_layout)

        # Summary Section (Total Customers and Loan Amount Due)
        summary_layout = QVBoxLayout()

        # Create a container for styling
        summary_container = QGroupBox()
        summary_container.setStyleSheet("""
            QGroupBox {
                border: 2px solid #4CAF50;
                border-radius: 10px;
                background-color: #f9f9f9;
                margin: 10px 0;
                padding: 10px;
            }
        """)

        summary_inner_layout = QVBoxLayout()

        # Labels with enhanced styling
        self.total_customers_label = QLabel("Total Customers: 0")
        self.total_loan_due_label = QLabel("Total Loan Amount Due (₹): 0.00")

        self.total_customers_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 22px; 
            color: #333; 
            text-align: center;
        """)
        self.total_loan_due_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 22px; 
            color: #FF5722; 
            text-align: center;
        """)

        # Add labels to the inner layout
        summary_inner_layout.addWidget(self.total_customers_label, alignment=Qt.AlignCenter)
        summary_inner_layout.addWidget(self.total_loan_due_label, alignment=Qt.AlignCenter)

        # Add inner layout to the container
        summary_container.setLayout(summary_inner_layout)

        # Center the summary container
        summary_layout.addWidget(summary_container, alignment=Qt.AlignCenter)

        # Add the summary layout to the main content layout
        self.content_layout.addLayout(summary_layout)

        # Call method to refresh summary data
        self.refresh_summary_data()

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

        # Add initial placeholder item
        self.customer_dropdown.addItem("Select a customer", None)

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

        # Update Loan Details Table headers
        self.loan_details_table = QTableWidget()
        self.loan_details_table.setColumnCount(7)  # Includes loan_account_number
        self.loan_details_table.setHorizontalHeaderLabels([
            "Loan Date", "Loan Account Number", "Total Assets", "Total Weight (g)", 
            "Total Amount (₹)", "Amount Due (₹)", ""
        ])
        self.loan_details_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.loan_details_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.loan_details_table.setSelectionMode(QTableWidget.SingleSelection)
        self.loan_details_table.setFixedHeight(200)
        self.content_layout.addWidget(self.loan_details_table)

        # Assets and Payments Section (hidden by default)
        self.update_group = QGroupBox("Loan Assets and Payments")
        self.update_group.setVisible(False)
        update_layout = QVBoxLayout()

        # Update Assets Table headers - Fix: remove reference_id column
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(2)  # Only description and weight
        self.assets_table.setHorizontalHeaderLabels([
            "Asset Description", "Weight (g)"
        ])
        self.assets_table.setColumnWidth(0, 250)
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

    def on_year_selected(self):
        """Handle year selection change"""
        self.selected_year = self.year_dropdown.currentData()
        # Reset customer selection
        self.customer_dropdown.setCurrentIndex(0)
        # Update summary data for selected year
        self.refresh_summary_data()
        # Update customer dropdown with customers from selected year
        self.populate_customer_dropdown()
        # Hide customer info and loan details
        self.customer_info_group.setVisible(False)
        self.loan_details_table.setVisible(False)
        self.update_group.setVisible(False)
        self.generate_pdf_button.setEnabled(False)

    def refresh_summary_data(self):
        """Refresh the summary statistics for total customers and loan amount due."""
        year = self.selected_year
        total_customers, total_loan_due = DatabaseManager.get_summary_stats_to_generate_report(year)

        # Update the labels
        self.total_customers_label.setText(f"Total Customers: {total_customers}")
        self.total_loan_due_label.setText(f"Total Loan Amount Due (₹): {total_loan_due:,.2f}")

    def populate_assets_table(self, loan_id):
        """Populate assets table with loan assets."""
        self.assets_table.setRowCount(0)
        assets = DatabaseManager.fetch_loan_assets(loan_id)
        
        for row_idx, (description, weight) in enumerate(assets):
            self.assets_table.insertRow(row_idx)
            self.assets_table.setItem(row_idx, 0, QTableWidgetItem(description))
            self.assets_table.setItem(row_idx, 1, QTableWidgetItem(f"{weight}"))

    def populate_loan_payments_table(self, loan_id):
        """Populate the loan payments table with payment history."""
        self.loan_payments_table.setRowCount(0)
        repayments = DatabaseManager.fetch_loan_payments(loan_id)
        
        if repayments:
            for row_idx, repayment in enumerate(repayments):
                self.loan_payments_table.insertRow(row_idx)
                
                payment_date = datetime.strptime(repayment['payment_date'], "%Y-%m-%d")
                formatted_date = payment_date.strftime("%d-%m-%Y")
                
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
            # Reset year selection to All Years
            self.year_dropdown.setCurrentIndex(0)
            self.populate_customer_dropdown()
            # Reset selection and hide elements
            self.customer_dropdown.setCurrentIndex(0)
            self.customer_info_group.setVisible(False)
            self.loan_details_table.setVisible(False)
            self.update_group.setVisible(False)
            self.generate_pdf_button.setEnabled(False)
        super().showEvent(event)

    def populate_customer_dropdown(self):
        """Populate the dropdown with the latest customer data."""
        self.customer_dropdown.clear()
        # Add the initial placeholder
        self.customer_dropdown.addItem("Select a customer", None)
        
        customers = DatabaseManager.get_customers_by_year(self.selected_year)
        if customers:
            for customer_id, name, account_number in customers:
                self.customer_dropdown.addItem(f"{name}", customer_id)

    def filter_customers(self, text):
        """Filter customers based on search text."""
        self.customer_dropdown.clear()
        # Always add the initial placeholder
        self.customer_dropdown.addItem("Select a customer", None)
        
        customers = DatabaseManager.get_customers_by_year(self.selected_year)
        
        filtered_customers = [
            (customer_id, name, account_number) 
            for customer_id, name, account_number in customers 
            if text.lower() in f"{name} {account_number}".lower()
        ]
        if filtered_customers:
            for customer_id, name, account_number in filtered_customers:
                self.customer_dropdown.addItem(f"{name} - {account_number}", customer_id)

    def on_customer_selected(self, index):
        """Display customer information and loans when a customer is selected."""
        self.selected_customer_id = self.customer_dropdown.currentData()
        
        # Show/hide elements based on selection
        has_selection = self.selected_customer_id is not None
        self.customer_info_group.setVisible(has_selection)
        self.loan_details_table.setVisible(has_selection)
        self.generate_pdf_button.setEnabled(has_selection)
        
        # Clear tables if no selection
        if not has_selection:
            self.loan_details_table.setRowCount(0)
            self.update_group.setVisible(False)
            return
            
        # Populate data if customer is selected
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
        self.loan_details_table.setRowCount(0)  # Clear existing rows
        
        if not self.selected_customer_id:
            return
            
        # Get loans filtered by year if selected
        loans = DatabaseManager.fetch_loans_for_customer_to_generate_report(self.selected_customer_id, self.selected_year)
        
        if not loans:
            return
        
        for row_idx, loan in enumerate(loans):
            self.loan_details_table.insertRow(row_idx)
            
            # Format the loan data for display
            loan_date = datetime.strptime(loan[0], "%Y-%m-%d").strftime("%d-%m-%Y")
            loan_account_number = loan[6]  # Get loan_account_number from the tuple
            asset_descriptions = loan[1]
            total_weight = f"{float(loan[2]):,.2f}" if loan[2] else "0.00"
            loan_amount = f"{float(loan[3]):,.2f}" if loan[3] else "0.00"
            amount_due = f"{float(loan[4]):,.2f}" if loan[4] else "0.00"
            
            # Set values in the table
            self.loan_details_table.setItem(row_idx, 0, QTableWidgetItem(loan_date))
            self.loan_details_table.setItem(row_idx, 1, QTableWidgetItem(loan_account_number))
            self.loan_details_table.setItem(row_idx, 2, QTableWidgetItem(asset_descriptions))
            self.loan_details_table.setItem(row_idx, 3, QTableWidgetItem(total_weight))
            self.loan_details_table.setItem(row_idx, 4, QTableWidgetItem(loan_amount))
            self.loan_details_table.setItem(row_idx, 5, QTableWidgetItem(amount_due))
            
            view_button = QPushButton("View More")
            view_button.clicked.connect(lambda checked, lid=loan[7]: self.show_loan_details(lid))
            self.loan_details_table.setCellWidget(row_idx, 6, view_button)

    def generate_pdf_report(self):
        """Generate a comprehensive PDF report for the selected customer."""
        if not self.selected_customer_id:
            QMessageBox.warning(self, "Error", "Please select a customer first.")
            return
        try:
            customer_info = DatabaseManager.get_customer_by_id(self.selected_customer_id)
            loans = DatabaseManager.fetch_loans_for_customer_to_generate_report(self.selected_customer_id, self.selected_year)

            pdf = FPDF()
            
            pdf.add_page()
            pdf.set_font('Arial', 'B', 16)
            
            # Add report title with year filter if applicable
            if self.selected_year:
                pdf.cell(0, 10, f"Customer Loan Report ({self.selected_year})", 0, 1)
            else:
                pdf.cell(0, 10, "Customer Loan Report (All Years)", 0, 1)

            # Customer Information
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, f"Name: {customer_info.get('name', 'N/A')}", 0, 1)
            pdf.cell(0, 10, f"Phone: {customer_info.get('phone', 'N/A')}", 0, 1)
            pdf.cell(0, 10, f"Address: {customer_info.get('address', 'N/A')}", 0, 1)

            # Loan Details
            for loan in loans:
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, "Loan Details", 0, 1)
                
                pdf.set_font('Arial', '', 12)
                loan_date = datetime.strptime(loan[0], "%Y-%m-%d")
                pdf.cell(0, 10, f"Loan Date: {loan_date.strftime('%d-%m-%Y')}", 0, 1)
                pdf.cell(0, 10, f"Loan Account Number: {loan[6]}", 0, 1)
                pdf.cell(0, 10, f"Total Weight: {float(loan[2])} g", 0, 1)
                pdf.cell(0, 10, f"Total Loan Amount: ₹{float(loan[3]):,.2f}", 0, 1)
                pdf.cell(0, 10, f"Amount Due: ₹{float(loan[4]):,.2f}", 0, 1)

                # Add assets
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "Assets:", 0, 1)
                assets = DatabaseManager.fetch_loan_assets(loan[7])  # Using loan_id
                pdf.set_font('Arial', '', 12)
                if assets:
                    for desc, weight in assets:
                        pdf.cell(0, 10, f"  Asset Description: {desc}", 0, 1)
                        pdf.cell(0, 10, f"  Weight: {weight}g", 0, 1)
                        pdf.ln(2)
                else:
                    pdf.cell(0, 10, "No assets found", 0, 1)

                # Add loan payments
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "Payment History:", 0, 1)
                payments = DatabaseManager.fetch_loan_payments(loan[7])
                pdf.set_font('Arial', '', 12)
                if payments:
                    for payment in payments:
                        payment_date = datetime.strptime(payment['payment_date'], "%Y-%m-%d")
                        pdf.cell(0, 10, f"Date: {payment_date.strftime('%d-%m-%Y')}", 0, 1)
                        pdf.cell(0, 10, f"Asset: {payment.get('asset_description', 'N/A')}", 0, 1)
                        pdf.cell(0, 10, f"Amount Paid: ₹{float(payment['payment_amount']):,.2f}", 0, 1)
                        pdf.cell(0, 10, f"Interest Paid: ₹{float(payment['interest_amount']):,.2f}", 0, 1)
                        pdf.cell(0, 10, f"Remaining Amount: ₹{float(payment['amount_left']):,.2f}", 0, 1)
                        pdf.ln(5)
                else:
                    pdf.cell(0, 10, "No payments recorded", 0, 1)

                pdf.ln(10)
                pdf.cell(0, 0, "_" * 50, 0, 1)  # Add separator line between loans

            # Generate year-specific filename if applicable
            if self.selected_year:
                filename = f"customer_loan_report_{customer_info.get('name', 'unknown')}_{self.selected_year}_{datetime.now().strftime('%Y%m%d')}.pdf"
            else:
                filename = f"customer_loan_report_{customer_info.get('name', 'unknown')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                
            pdf.output(filename)
            QMessageBox.information(self, "Success", f"Report generated: {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")