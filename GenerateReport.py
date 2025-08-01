from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QGroupBox, QMessageBox, QComboBox, 
    QLineEdit, QFormLayout
)
from helper import StyledWidget, format_indian_currency
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
        
        # Cache for data to avoid repeated DB calls
        self.all_loans_cache = []
        self.all_customers_cache = []
        self.loans_by_customer_cache = {}
        self.data_loaded = False
        
        self.init_ui()
        
        # Hide elements initially
        self.customer_info_group.setVisible(False)
        self.generate_pdf_button.setEnabled(True)  # Enable since we can generate reports for all loans

    def init_ui(self):
        # Year Selection
        year_layout = QHBoxLayout()
        self.year_dropdown = QComboBox()
        self.year_dropdown.setFixedWidth(200)
        self.year_dropdown.setStyleSheet("""
            QComboBox {
                font-size: 16px;
            }
            QComboBox QAbstractItemView {
                font-size: 16px;
                min-height: 30px;  /* This increases the line height of dropdown items */
            }
        """)
        # Get current year
        current_year = datetime.now().year
        
        # Add years to dropdown (last 10 years)
        self.year_dropdown.addItem("All Years", None)
        for year in range( current_year+5, current_year, -1): 
            self.year_dropdown.addItem(str(year), year)

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
        self.customer_dropdown.setFixedWidth(500)
        self.customer_dropdown.setStyleSheet("""
            QComboBox {
                font-size: 16px;
            }
            QComboBox QAbstractItemView {
                font-size: 16px;
                min-height: 30px;  /* This increases the line height of dropdown items */
            }
        """)
        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("Search Customer")
        self.customer_search.textChanged.connect(self.filter_customers)
        
        customer_layout.addWidget(QLabel("Select Customer:"))
        customer_layout.addWidget(self.customer_search)
        customer_layout.addWidget(self.customer_dropdown)
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

         # Create labels for total loan amount and total amount due (add these)
        self.total_customer_loan_label = QLabel("Total Loan Amount (₹): 0.00")
        self.total_customer_due_label = QLabel("Total Amount Due (₹): 0.00")
        
        # Apply styling to make them stand out (add these)
        self.total_customer_loan_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 16px; 
            color: #2196F3;
        """)
        self.total_customer_due_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 16px; 
            color: #FF5722;
        """)
        
        customer_info_layout.addWidget(self.total_customer_loan_label)
        customer_info_layout.addWidget(self.total_customer_due_label)

        self.customer_info_group.setLayout(customer_info_layout)
        self.content_layout.addWidget(self.customer_info_group)

        # Update Loan Details Table headers
        self.loan_details_table = QTableWidget()
        self.loan_details_table.setColumnCount(7)  # Includes registered_reference_id
        self.loan_details_table.setHorizontalHeaderLabels([
            "Loan Date", "Registered Reference Id", "Total Assets", "Total Weight (g)", 
            "Total Amount (₹)", "Amount Due (₹)", ""
        ])
        self.loan_details_table.setColumnWidth(1, 200)
        self.loan_details_table.setColumnWidth(2, 150)
        self.loan_details_table.setColumnWidth(3, 150)
        self.loan_details_table.setColumnWidth(4, 150)
        self.loan_details_table.setColumnWidth(5, 150)
        self.loan_details_table.setColumnWidth(6, 150)


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

    def load_all_data(self):
        """Load all data once and cache it for fast filtering."""
        if self.data_loaded:
            return
            
        # Load all loans once
        self.all_loans_cache = DatabaseManager.fetch_all_loans_to_generate_report(None)  # Get all years
        
        # Load all customers once
        self.all_customers_cache = DatabaseManager.get_customers_by_year(None)  # Get all customers
        
        # Pre-process loans by customer for faster customer-specific filtering
        self.loans_by_customer_cache = {}
        for loan in self.all_loans_cache:
            customer_id = loan[8]  # Assuming customer_id is at index 8
            if customer_id not in self.loans_by_customer_cache:
                self.loans_by_customer_cache[customer_id] = []
            self.loans_by_customer_cache[customer_id].append(loan)
        
        self.data_loaded = True

    def filter_loans_by_year(self, loans, year):
        """Filter loans by year on the client side."""
        if not year:
            return loans
            
        filtered_loans = []
        for loan in loans:
            try:
                loan_date = datetime.strptime(str(loan[0]).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d")
                if loan_date.year == year:
                    filtered_loans.append(loan)
            except (ValueError, TypeError):
                # Include corrupted dates only when showing all years
                continue
                
        return filtered_loans

    def filter_customers_by_year(self, customers, year):
        """Filter customers by year based on cached loan data."""
        if not year:
            return customers
            
        # Get customer IDs who had loans in the specified year
        customer_ids_with_loans = set()
        year_filtered_loans = self.filter_loans_by_year(self.all_loans_cache, year)
        for loan in year_filtered_loans:
            customer_ids_with_loans.add(loan[8])  # customer_id at index 8
            
        # Filter customers
        filtered_customers = [
            customer for customer in customers 
            if customer[0] in customer_ids_with_loans
        ]
        
        return filtered_customers

    def get_summary_stats_from_cache(self, year):
        """Calculate summary stats from cached data."""
        filtered_loans = self.filter_loans_by_year(self.all_loans_cache, year)
        
        # Count unique customers
        unique_customers = set()
        total_due = 0
        
        for loan in filtered_loans:
            unique_customers.add(loan[8])  # customer_id
            try:
                due_amount = float(loan[4]) if loan[4] else 0  # amount_due
                total_due += due_amount
            except (ValueError, TypeError):
                continue
                
        return len(unique_customers), total_due

    def on_year_selected(self):
        """Handle year selection change using cached data."""
        self.selected_year = self.year_dropdown.currentData()
        # Reset customer selection
        self.customer_dropdown.setCurrentIndex(0)
        # Update summary data for selected year from cache
        self.refresh_summary_data()
        # Update customer dropdown with customers from selected year using cache
        self.populate_customer_dropdown()
        # Hide customer info but show all loans for the selected year
        self.customer_info_group.setVisible(False)
        self.loan_details_table.setVisible(True)
        self.update_group.setVisible(False)
        self.generate_pdf_button.setEnabled(True)  # Always enable PDF generation
        # Populate all loans for the selected year using cache
        self.populate_all_loans_table()

    def refresh_summary_data(self):
        """Refresh the summary statistics using cached data."""
        if not self.data_loaded:
            return
            
        total_customers, total_loan_due = self.get_summary_stats_from_cache(self.selected_year)

        # Update the labels
        self.total_customers_label.setText(f"Total Customers: {total_customers}")
        self.total_loan_due_label.setText(f"Total Loan Amount Due (₹): {format_indian_currency(total_loan_due)}")

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
            repayments = sorted(repayments, key=lambda payment: datetime.strptime(str(payment['payment_date']).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d"), reverse=True)
            for row_idx, repayment in enumerate(repayments):
                self.loan_payments_table.insertRow(row_idx)
                
                payment_date = datetime.strptime(repayment['payment_date'].replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d")
                formatted_date = payment_date.strftime("%d-%m-%Y")
                
                self.loan_payments_table.setItem(row_idx, 0, QTableWidgetItem(formatted_date))
                self.loan_payments_table.setItem(row_idx, 1, QTableWidgetItem(repayment.get("asset_description", "")))
                self.loan_payments_table.setItem(row_idx, 2, QTableWidgetItem(f"{format_indian_currency(float(repayment['payment_amount']))}"))
                self.loan_payments_table.setItem(row_idx, 3, QTableWidgetItem(f"{format_indian_currency(float(repayment['interest_amount']))}"))
                self.loan_payments_table.setItem(row_idx, 4, QTableWidgetItem(f"{format_indian_currency(float(repayment['amount_left']))}"))
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
            # Load all data once for fast filtering
            self.load_all_data()
            
            # Reset year selection to All Years
            self.year_dropdown.setCurrentIndex(0)
            self.populate_customer_dropdown()
            # Reset selection and show all loans initially
            self.customer_dropdown.setCurrentIndex(0)
            self.customer_info_group.setVisible(False)
            self.loan_details_table.setVisible(True)
            self.update_group.setVisible(False)
            self.generate_pdf_button.setEnabled(True)  # Always enable PDF generation
            
            # Refresh summary and populate loans
            self.refresh_summary_data()
            self.populate_all_loans_table()
        super().showEvent(event)

    def populate_customer_dropdown(self):
        """Populate the dropdown with cached customer data."""
        self.customer_dropdown.clear()
        # Add the initial placeholder
        self.customer_dropdown.addItem("Select a customer", None)
        
        if not self.data_loaded:
            return
            
        # Filter customers based on selected year using cache
        customers = self.filter_customers_by_year(self.all_customers_cache, self.selected_year)
        
        if customers:
            for customer_id, name, account_number in customers:
                self.customer_dropdown.addItem(f"{name}", customer_id)

    def filter_customers(self, text):
        """Filter customers based on search text using cached data."""
        self.customer_dropdown.clear()
        # Always add the initial placeholder
        self.customer_dropdown.addItem("Select a customer", None)
        
        if not self.data_loaded:
            return
        
        # Filter customers based on selected year using cache
        customers = self.filter_customers_by_year(self.all_customers_cache, self.selected_year)
        
        filtered_customers = [
            (customer_id, name, account_number) 
            for customer_id, name, account_number in customers 
            if text.lower() in f"{name} {account_number if account_number else ''}".lower()
        ]
        if filtered_customers:
            for customer_id, name, account_number in filtered_customers:
                self.customer_dropdown.addItem(f"{name} - {account_number}" if account_number else f"{name}", customer_id)
            if len(filtered_customers) == 1:
                self.customer_dropdown.setCurrentIndex(1)  # First item after "Select Customer"

    def on_customer_selected(self, index):
        """Display customer information and loans when a customer is selected."""
        self.selected_customer_id = self.customer_dropdown.currentData()
        
        # Show/hide elements based on selection
        has_selection = self.selected_customer_id is not None
        self.customer_info_group.setVisible(has_selection)
        self.loan_details_table.setVisible(True)  # Always show the table
        self.generate_pdf_button.setEnabled(True)  # Always enable PDF generation
        
        # Clear update group when customer selection changes
        self.update_group.setVisible(False)
        
        if has_selection:
            # Populate data if customer is selected
            self.populate_customer_info()
            self.populate_loans_table()
        else:
            # Show all loans if no customer is selected
            self.populate_all_loans_table()

    def populate_customer_info(self):
        """Populate customer information in the customer info group."""
        customer_info_layout = self.customer_info_group.layout()
        
        # Clear existing widgets except the total labels
        while customer_info_layout.count() > 2:  # Keep first 2 widgets (total labels)
            child = customer_info_layout.takeAt(2)
            if child.widget():
                child.widget().deleteLater()
        
        customer_info = DatabaseManager.get_customer_by_id(self.selected_customer_id)
        
        # Calculate totals for the selected customer
        total_loan, total_due = DatabaseManager.get_customer_loan_totals(
            self.selected_customer_id, self.selected_year)
        
        # Update the total labels
        self.total_customer_loan_label.setText(f"Total Loan Amount (₹): {format_indian_currency(total_loan)}")
        self.total_customer_due_label.setText(f"Total Amount Due (₹): {format_indian_currency(total_due)}")
        
        # Add the rest of customer info
        if customer_info:
            for key, value in customer_info.items():
                if key == "customer_id" or not value:
                    continue
                label = QLabel(f"{key.replace('_', ' ').title()}: {value}")
                customer_info_layout.addWidget(label)

    def populate_loans_table(self):
        """Populate the loan table with loans for the selected customer using cached data."""
        self.loan_details_table.setRowCount(0)  # Clear existing rows
        
        if not self.selected_customer_id or not self.data_loaded:
            return
            
        # Get loans for customer from cache
        customer_loans = self.loans_by_customer_cache.get(self.selected_customer_id, [])
        
        # Filter by year
        loans = self.filter_loans_by_year(customer_loans, self.selected_year)
        
        if not loans:
            return
            
        # Sort loans by date with error handling for corrupted dates
        def safe_date_parse(loan):
            try:
                return datetime.strptime(str(loan[0]).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d")
            except (ValueError, TypeError):
                # Return a very old date for corrupted entries so they appear at the bottom
                return datetime(1900, 1, 1)
        
        loans = sorted(loans, key=safe_date_parse, reverse=True)
        
        for row_idx, loan in enumerate(loans):
            self.loan_details_table.insertRow(row_idx)
            
            # Format the loan data for display with error handling
            try:
                loan_date = datetime.strptime((loan[0]).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d").strftime("%d-%m-%Y")
            except (ValueError, TypeError):
                loan_date = f"Invalid Date: {str(loan[0])}"  # Show the corrupted date as-is
                
            registered_reference_id = loan[6]  # Get registered_reference_id from the tuple
            asset_descriptions = loan[1]
            total_weight = f"{format_indian_currency(float(loan[2]))}" if loan[2] else "0.00"
            loan_amount = f"{format_indian_currency(float(loan[3]))}" if loan[3] else "0.00"
            amount_due = f"{format_indian_currency(float(loan[4]))}" if loan[4] else "0.00"
            
            # Set values in the table
            self.loan_details_table.setItem(row_idx, 0, QTableWidgetItem(loan_date))
            self.loan_details_table.setItem(row_idx, 1, QTableWidgetItem(registered_reference_id))
            self.loan_details_table.setItem(row_idx, 2, QTableWidgetItem(asset_descriptions))
            self.loan_details_table.setItem(row_idx, 3, QTableWidgetItem(total_weight))
            self.loan_details_table.setItem(row_idx, 4, QTableWidgetItem(loan_amount))
            self.loan_details_table.setItem(row_idx, 5, QTableWidgetItem(amount_due))
            
            view_button = QPushButton("View More")
            view_button.clicked.connect(lambda checked, lid=loan[7]: self.show_loan_details(lid))
            self.loan_details_table.setCellWidget(row_idx, 6, view_button)

    def populate_all_loans_table(self):
        """Populate the loan table with all loans using cached data."""
        self.loan_details_table.setRowCount(0)  # Clear existing rows
        
        if not self.data_loaded:
            return
        
        # Filter loans by year from cache
        loans = self.filter_loans_by_year(self.all_loans_cache, self.selected_year)
        
        if not loans:
            return
            
        # Sort loans by date with error handling for corrupted dates
        def safe_date_parse(loan):
            try:
                return datetime.strptime(str(loan[0]).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d")
            except (ValueError, TypeError):
                # Return a very old date for corrupted entries so they appear at the bottom
                return datetime(1900, 1, 1)
        
        loans = sorted(loans, key=safe_date_parse, reverse=True)
        
        for row_idx, loan in enumerate(loans):
            self.loan_details_table.insertRow(row_idx)
            
            # Format the loan data for display with error handling
            try:
                loan_date = datetime.strptime((loan[0]).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d").strftime("%d-%m-%Y")
            except (ValueError, TypeError):
                loan_date = f"Invalid Date: {str(loan[0])}"  # Show the corrupted date as-is
                
            registered_reference_id = loan[6]  # Get registered_reference_id from the tuple
            asset_descriptions = loan[1]
            total_weight = f"{format_indian_currency(float(loan[2]))}" if loan[2] else "0.00"
            loan_amount = f"{format_indian_currency(float(loan[3]))}" if loan[3] else "0.00"
            amount_due = f"{format_indian_currency(float(loan[4]))}" if loan[4] else "0.00"
            
            # Set values in the table
            self.loan_details_table.setItem(row_idx, 0, QTableWidgetItem(loan_date))
            self.loan_details_table.setItem(row_idx, 1, QTableWidgetItem(registered_reference_id))
            self.loan_details_table.setItem(row_idx, 2, QTableWidgetItem(asset_descriptions))
            self.loan_details_table.setItem(row_idx, 3, QTableWidgetItem(total_weight))
            self.loan_details_table.setItem(row_idx, 4, QTableWidgetItem(loan_amount))
            self.loan_details_table.setItem(row_idx, 5, QTableWidgetItem(amount_due))
            
            view_button = QPushButton("View More")
            view_button.clicked.connect(lambda checked, lid=loan[7]: self.show_loan_details(lid))
            self.loan_details_table.setCellWidget(row_idx, 6, view_button)

    def generate_pdf_report(self):
        """Generate a modern tabular PDF report for the displayed data using cached data."""
        try:
            if self.selected_customer_id:
                # Generate customer-specific report using cache
                customer_info = DatabaseManager.get_customer_by_id(self.selected_customer_id)
                customer_loans = self.loans_by_customer_cache.get(self.selected_customer_id, [])
                loans = self.filter_loans_by_year(customer_loans, self.selected_year)
                report_title = f"CUSTOMER LOAN REPORT"
                if self.selected_year:
                    report_title += f" - {self.selected_year}"
            else:
                # Generate report for all loans using cache
                customer_info = None
                loans = self.filter_loans_by_year(self.all_loans_cache, self.selected_year)
                report_title = f"ALL LOANS REPORT"
                if self.selected_year:
                    report_title += f" - {self.selected_year}"
                else:
                    report_title += " - ALL YEARS"
            
            if not loans:
                QMessageBox.warning(self, "Error", "No loan data found for the current filter.")
                return

            pdf = FPDF()
            pdf.add_page()
            
            # Helper function to sanitize text
            def sanitize_text(text):
                if text is None:
                    return "N/A"
                try:
                    text = str(text)
                    return ''.join(char for char in text if ord(char) < 128)
                except:
                    return "Text contains unsupported characters"
            
            # Color scheme
            header_color = (41, 128, 185)  # Blue
            alternate_row_color = (245, 245, 245)  # Light gray
            text_color = (52, 73, 94)  # Dark gray
            
            # Header Section with styling
            pdf.set_fill_color(*header_color)
            pdf.set_text_color(255, 255, 255)  # White text
            pdf.set_font('Arial', 'B', 20)
            
            # Title with background
            pdf.cell(0, 15, report_title, 0, 1, 'C', True)
            pdf.ln(5)
            
            # Customer Information Section (only for customer-specific reports)
            if customer_info:
                pdf.set_fill_color(240, 240, 240)
                pdf.set_text_color(*text_color)
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, "CUSTOMER INFORMATION", 0, 1, 'L', True)
                pdf.ln(2)
                
                # Customer details in a neat format
                pdf.set_font('Arial', '', 11)
                customer_data = [
                    ["Name:", sanitize_text(customer_info.get('name', 'N/A'))],
                    ["Phone:", sanitize_text(customer_info.get('phone', 'N/A'))],
                    ["Address:", sanitize_text(customer_info.get('address', 'N/A'))],
                    ["Account No:", sanitize_text(customer_info.get('account_number', 'N/A'))]
                ]
                
                for label, value in customer_data:
                    pdf.set_font('Arial', 'B', 10)
                    pdf.cell(40, 8, label, 0, 0)
                    pdf.set_font('Arial', '', 10)
                    pdf.cell(0, 8, value, 0, 1)
                
                pdf.ln(5)
                
                # Summary Section for customer
                total_loan, total_due = DatabaseManager.get_customer_loan_totals(
                    self.selected_customer_id, self.selected_year)
                
                pdf.set_fill_color(46, 204, 113)  # Green
                pdf.set_text_color(255, 255, 255)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "CUSTOMER SUMMARY", 0, 1, 'L', True)
                pdf.ln(2)
                
                pdf.set_text_color(*text_color)
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(100, 8, f"Total Loan Amount: Rs {format_indian_currency(total_loan)}", 0, 0)
                pdf.cell(0, 8, f"Total Amount Due: Rs {format_indian_currency(total_due)}", 0, 1)
                pdf.ln(8)
            else:
                # Summary Section for all loans using cache
                total_customers, total_loan_due = self.get_summary_stats_from_cache(self.selected_year)
                
                pdf.set_fill_color(46, 204, 113)  # Green
                pdf.set_text_color(255, 255, 255)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "OVERALL SUMMARY", 0, 1, 'L', True)
                pdf.ln(2)
                
                pdf.set_text_color(*text_color)
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(100, 8, f"Total Customers: {total_customers}", 0, 0)
                pdf.cell(0, 8, f"Total Amount Due: Rs {format_indian_currency(total_loan_due)}", 0, 1)
                pdf.ln(8)
            
            # Loans Table Header
            pdf.set_fill_color(*header_color)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 10, "LOAN DETAILS", 0, 1, 'L', True)
            pdf.ln(2)
            
            # Table headers
            pdf.set_font('Arial', 'B', 9)
            headers = ["Date", "Ref ID", "Assets", "Weight(g)", "Amount(Rs)", "Due(Rs)"]
            col_widths = [25, 35, 45, 25, 30, 30]  # Column widths
            
            pdf.set_fill_color(52, 73, 94)  # Dark blue-gray
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
            pdf.ln()
            
            # Sort loans by date (most recent first) with error handling
            def safe_date_parse_pdf(loan):
                try:
                    return datetime.strptime(str(loan[0]).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d")
                except (ValueError, TypeError):
                    # Return a very old date for corrupted entries so they appear at the bottom
                    return datetime(1900, 1, 1)
            
            loans = sorted(loans, key=safe_date_parse_pdf, reverse=True)
            
            # Table rows
            pdf.set_text_color(*text_color)
            pdf.set_font('Arial', '', 8)
            
            for row_idx, loan in enumerate(loans):
                # Alternate row colors
                if row_idx % 2 == 0:
                    pdf.set_fill_color(*alternate_row_color)
                else:
                    pdf.set_fill_color(255, 255, 255)
                
                # Format data
                try:
                    loan_date = datetime.strptime(str(loan[0]).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d")
                    formatted_date = loan_date.strftime("%d/%m/%y")
                except:
                    formatted_date = "Invalid"
                
                ref_id = sanitize_text(str(loan[6])[:12] + "..." if len(str(loan[6])) > 12 else str(loan[6]))
                assets = sanitize_text(str(loan[1])[:15] + "..." if len(str(loan[1])) > 15 else str(loan[1]))
                weight = f"{float(loan[2]):.1f}" if loan[2] else "0.0"
                amount = f"{float(loan[3]):.0f}" if loan[3] else "0"
                due = f"{float(loan[4]):.0f}" if loan[4] else "0"
                
                row_data = [formatted_date, ref_id, assets, weight, amount, due]
                
                for i, data in enumerate(row_data):
                    align = 'C' if i in [0, 3, 4, 5] else 'L'  # Center align for date, weight, amounts
                    pdf.cell(col_widths[i], 7, str(data), 1, 0, align, True)
                pdf.ln()

            # Footer
            pdf.ln(10)
            pdf.set_font('Arial', 'I', 8)
            pdf.set_text_color(128, 128, 128)
            pdf.cell(0, 5, f"Report Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", 0, 1, 'C')
            
            # Generate filename
            if customer_info:
                safe_name = ''.join(char for char in str(customer_info.get('name', 'unknown')) if char.isalnum() or char in ' _-')
                if not safe_name or safe_name.isspace():
                    safe_name = "unknown"
                    
                if self.selected_year:
                    filename = f"Loan_Report_{safe_name}_{self.selected_year}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                else:
                    filename = f"Loan_Report_{safe_name}_All_Years_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            else:
                # All loans report
                if self.selected_year:
                    filename = f"All_Loans_Report_{self.selected_year}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                else:
                    filename = f"All_Loans_Report_All_Years_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                
            try:
                pdf.output(filename)
                QMessageBox.information(self, "Success", f"Modern tabular report generated successfully!\n\nFile: {filename}")
            except Exception as output_error:
                # Fallback with safe filename
                safe_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf.output(safe_filename)
                QMessageBox.information(self, "Success", f"Report generated with safe name: {safe_filename}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")