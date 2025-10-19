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
        
        # Pagination variables
        self.current_page = 1
        self.rows_per_page = 50
        self.total_loans = 0
        self.all_loans_cache = []  # Cache for filtered loans (for search)
        
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

        # Pagination Controls
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch(1)
        
        # Rows per page selector
        pagination_layout.addWidget(QLabel("Rows per page:"))
        self.rows_per_page_combo = QComboBox()
        self.rows_per_page_combo.addItems(["10", "20", "50", "100"])
        self.rows_per_page_combo.setCurrentText("50")  # Default to 50
        self.rows_per_page_combo.currentTextChanged.connect(self.on_rows_per_page_changed)
        self.rows_per_page_combo.setFixedWidth(80)
        pagination_layout.addWidget(self.rows_per_page_combo)
        
        pagination_layout.addSpacing(20)
        
        # Previous button
        self.prev_button = QPushButton("◄")
        self.prev_button.setFixedSize(40, 30)
        self.prev_button.clicked.connect(self.go_to_previous_page)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        pagination_layout.addWidget(self.prev_button)
        
        # Page info label
        self.page_info_label = QLabel("Page 1 of 1")
        self.page_info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.page_info_label.setFixedWidth(120)
        self.page_info_label.setAlignment(Qt.AlignCenter)
        pagination_layout.addWidget(self.page_info_label)
        
        # Next button
        self.next_button = QPushButton("►")
        self.next_button.setFixedSize(40, 30)
        self.next_button.clicked.connect(self.go_to_next_page)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        pagination_layout.addWidget(self.next_button)
        
        self.content_layout.addLayout(pagination_layout)

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
        
        # Block signals temporarily to prevent cascading calls
        self.customer_dropdown.blockSignals(True)
        self.customer_search.blockSignals(True)
        
        # Reset customer selection
        self.customer_dropdown.setCurrentIndex(0)
        self.selected_customer_id = None
        # Clear search text
        self.customer_search.clear()
        
        # Re-enable signals
        self.customer_dropdown.blockSignals(False)
        self.customer_search.blockSignals(False)
        
        # Update summary data for selected year
        self.refresh_summary_data()
        # Update customer dropdown with customers from selected year
        self.populate_customer_dropdown()
        # Hide customer info but show loan details table with all loans
        self.customer_info_group.setVisible(False)
        self.loan_details_table.setVisible(True)
        self.update_group.setVisible(False)
        self.generate_pdf_button.setEnabled(False)
        # Reset pagination and show all loans for the selected year
        self.current_page = 1
        self.all_loans_cache = []
        self.populate_loans_table()

    def on_rows_per_page_changed(self, value):
        """Handle rows per page selection change"""
        self.rows_per_page = int(value)
        self.current_page = 1  # Reset to first page
        self.populate_loans_table()
    
    def go_to_previous_page(self):
        """Navigate to the previous page"""
        if self.current_page > 1:
            self.current_page -= 1
            self.populate_loans_table()
    
    def go_to_next_page(self):
        """Navigate to the next page"""
        total_pages = self.get_total_pages()
        if self.current_page < total_pages:
            self.current_page += 1
            self.populate_loans_table()
    
    def get_total_pages(self):
        """Calculate total number of pages"""
        if self.rows_per_page == 0:
            return 1
        return max(1, (self.total_loans + self.rows_per_page - 1) // self.rows_per_page)
    
    def update_pagination_controls(self):
        """Update pagination button states and labels"""
        total_pages = self.get_total_pages()
        
        # Update page info label
        self.page_info_label.setText(f"Page {self.current_page} of {total_pages}")
        
        # Enable/disable buttons
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < total_pages)

    def refresh_summary_data(self):
        """Refresh the summary statistics for total customers and loan amount due."""
        year = self.selected_year
        total_customers, total_loan_due = DatabaseManager.get_summary_stats_to_generate_report(year)

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
            repayments = sorted(repayments, key=lambda payment: datetime.strptime(str(payment['payment_date']).replace('00:00:00', '').replace(' ', ''), "%d-%m-%Y"), reverse=True)
            for row_idx, repayment in enumerate(repayments):
                self.loan_payments_table.insertRow(row_idx)

                payment_date = datetime.strptime(repayment['payment_date'].replace('00:00:00', '').replace(' ', ''), "%d-%m-%Y")
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
            # Block signals temporarily to prevent cascading calls
            self.year_dropdown.blockSignals(True)
            self.customer_dropdown.blockSignals(True)
            self.customer_search.blockSignals(True)
            
            # Reset year selection to All Years
            self.year_dropdown.setCurrentIndex(0)
            self.selected_year = None
            self.populate_customer_dropdown()
            # Reset selection
            self.customer_dropdown.setCurrentIndex(0)
            self.selected_customer_id = None
            self.customer_search.clear()
            
            # Re-enable signals
            self.year_dropdown.blockSignals(False)
            self.customer_dropdown.blockSignals(False)
            self.customer_search.blockSignals(False)
            
            # Reset pagination
            self.current_page = 1
            self.all_loans_cache = []
            
            # Hide customer info but show loan details table with all loans
            self.customer_info_group.setVisible(False)
            self.loan_details_table.setVisible(True)
            self.update_group.setVisible(False)
            self.generate_pdf_button.setEnabled(False)
            
            # Refresh summary data
            self.refresh_summary_data()
            
            # Show all loans initially
            self.populate_loans_table()
        super().showEvent(event)

    def populate_customer_dropdown(self):
        """Populate the dropdown with the latest customer data."""
        # Block signals to prevent triggering on_customer_selected during dropdown update
        self.customer_dropdown.blockSignals(True)
        
        self.customer_dropdown.clear()
        # Add the initial placeholder
        self.customer_dropdown.addItem("Select a customer", None)
        
        customers = DatabaseManager.get_customers_by_year(self.selected_year)
        if customers:
            for customer_id, name, account_number in customers:
                self.customer_dropdown.addItem(f"{name}", customer_id)
        
        # Re-enable signals
        self.customer_dropdown.blockSignals(False)

    def filter_customers(self, text):
        """Filter customers based on search text."""
        # Block signals to prevent triggering on_customer_selected during dropdown update
        self.customer_dropdown.blockSignals(True)
        
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
                self.customer_dropdown.addItem(f"{name} - {account_number}" if account_number else f"{name}", customer_id)
            if len(filtered_customers) == 1:
                self.customer_dropdown.setCurrentIndex(1)  # First item after "Select Customer"
        
        # Re-enable signals
        self.customer_dropdown.blockSignals(False)
        
        # If no customer is selected, refresh the all loans view with the search filter
        if not self.selected_customer_id:
            # Reset to first page when search changes
            self.current_page = 1
            self.all_loans_cache = []  # Clear cache to force refresh
            self.populate_loans_table()

    def on_customer_selected(self, index):
        """Display customer information and loans when a customer is selected."""
        self.selected_customer_id = self.customer_dropdown.currentData()
        
        # Show/hide elements based on selection
        has_selection = self.selected_customer_id is not None
        self.customer_info_group.setVisible(has_selection)
        
        # Always show loan details table
        self.loan_details_table.setVisible(True)
        
        # Only enable PDF generation if customer is selected
        self.generate_pdf_button.setEnabled(has_selection)
        
        # Hide the detail section when changing selection
        self.update_group.setVisible(False)
        
        if has_selection:
            # Populate data if customer is selected
            self.populate_customer_info()
        
        # Always populate loans table (will show all loans or customer loans based on selection)
        self.populate_loans_table()

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
        """Populate the loan table with loans for the selected customer or all loans."""
        self.loan_details_table.setRowCount(0)  # Clear existing rows
        
        # Determine if we're showing all loans or customer-specific loans
        if self.selected_customer_id:
            # Show loans for specific customer
            self.show_customer_loans()
        else:
            # Show all loans from the database (filtered by year if selected)
            self.show_all_loans()
    
    def show_customer_loans(self):
        """Show loans for the selected customer."""
        # Update table to remove customer name column if present
        if self.loan_details_table.columnCount() == 8:
            self.loan_details_table.setColumnCount(7)
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
        
        # Get loans filtered by year if selected
        loans = DatabaseManager.fetch_loans_for_customer_to_generate_report(self.selected_customer_id, self.selected_year)
        
        if not loans:
            return
            
        loans = sorted(loans, key=lambda loan: datetime.strptime(str(loan[0]).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d"), reverse=True)
        for row_idx, loan in enumerate(loans):
            self.loan_details_table.insertRow(row_idx)
            
            # Format the loan data for display
            loan_date = datetime.strptime((loan[0]).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d").strftime("%d-%m-%Y")
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
    
    def show_all_loans(self):
        """Show all loans from the database (filtered by year if selected) with pagination."""
        # Update table to add customer name column
        if self.loan_details_table.columnCount() == 7:
            self.loan_details_table.setColumnCount(8)
            self.loan_details_table.setHorizontalHeaderLabels([
                "Customer Name", "Loan Date", "Registered Reference Id", "Total Assets", 
                "Total Weight (g)", "Total Amount (₹)", "Amount Due (₹)", ""
            ])
            self.loan_details_table.setColumnWidth(0, 150)
            self.loan_details_table.setColumnWidth(1, 120)
            self.loan_details_table.setColumnWidth(2, 180)
            self.loan_details_table.setColumnWidth(3, 150)
            self.loan_details_table.setColumnWidth(4, 120)
            self.loan_details_table.setColumnWidth(5, 120)
            self.loan_details_table.setColumnWidth(6, 120)
            self.loan_details_table.setColumnWidth(7, 100)
        
        search_text = self.customer_search.text().lower()
        
        # If there's a search filter, we need to fetch all and filter in Python
        if search_text:
            # Use cache if available, otherwise fetch all
            if not self.all_loans_cache:
                self.all_loans_cache = DatabaseManager.fetch_loans_by_year(self.selected_year)
            
            # Filter by customer name
            filtered_loans = [
                loan for loan in self.all_loans_cache 
                if search_text in loan[9].lower()  # loan[9] is customer_name
            ]
            
            # Update total count for pagination
            self.total_loans = len(filtered_loans)
            
            # Get the page slice
            start_idx = (self.current_page - 1) * self.rows_per_page
            end_idx = start_idx + self.rows_per_page
            loans_to_display = filtered_loans[start_idx:end_idx]
        else:
            # No search filter - use database pagination for better performance
            self.total_loans = DatabaseManager.get_total_loans_count(self.selected_year)
            
            # Calculate offset for pagination
            offset = (self.current_page - 1) * self.rows_per_page
            
            # Fetch only the current page's data from database
            loans_to_display = DatabaseManager.fetch_loans_by_year(
                self.selected_year, 
                limit=self.rows_per_page, 
                offset=offset
            )
            
            # Clear cache when not searching
            self.all_loans_cache = []
        
        # Update pagination controls
        self.update_pagination_controls()
        
        if not loans_to_display:
            return
        
        # Display the loans for the current page
        for row_idx, loan in enumerate(loans_to_display):
            self.loan_details_table.insertRow(row_idx)
            
            # Format the loan data for display
            # loan structure: (loan_date, asset_descriptions, total_asset_weight, loan_amount, 
            #                  loan_amount_due, total_interest_amount, registered_reference_id, 
            #                  loan_id, customer_id, customer_name)
            customer_name = loan[9]
            loan_date = datetime.strptime((loan[0]).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d").strftime("%d-%m-%Y")
            registered_reference_id = loan[6]
            asset_descriptions = loan[1]
            total_weight = f"{format_indian_currency(float(loan[2]))}" if loan[2] else "0.00"
            loan_amount = f"{format_indian_currency(float(loan[3]))}" if loan[3] else "0.00"
            amount_due = f"{format_indian_currency(float(loan[4]))}" if loan[4] else "0.00"
            
            # Set values in the table
            self.loan_details_table.setItem(row_idx, 0, QTableWidgetItem(customer_name))
            self.loan_details_table.setItem(row_idx, 1, QTableWidgetItem(loan_date))
            self.loan_details_table.setItem(row_idx, 2, QTableWidgetItem(registered_reference_id))
            self.loan_details_table.setItem(row_idx, 3, QTableWidgetItem(asset_descriptions))
            self.loan_details_table.setItem(row_idx, 4, QTableWidgetItem(total_weight))
            self.loan_details_table.setItem(row_idx, 5, QTableWidgetItem(loan_amount))
            self.loan_details_table.setItem(row_idx, 6, QTableWidgetItem(amount_due))
            
            view_button = QPushButton("View More")
            view_button.clicked.connect(lambda checked, lid=loan[7]: self.show_loan_details(lid))
            self.loan_details_table.setCellWidget(row_idx, 7, view_button)

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
            
            # Helper function to sanitize text - use ASCII only, completely remove problematic characters
            def sanitize_text(text):
                if text is None:
                    return "N/A"
                try:
                    # Convert to string first
                    text = str(text)
                    # Remove all non-ASCII characters
                    return ''.join(char for char in text if ord(char) < 128)
                except:
                    # If any error, return safe text
                    return "Text contains unsupported characters"
            
            # Add report title with year filter if applicable
            if self.selected_year:
                pdf.cell(0, 10, f"Customer Loan Report ({self.selected_year})", 0, 1)
            else:
                pdf.cell(0, 10, "Customer Loan Report (All Years)", 0, 1)

            # Customer Information
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, f"Name: {sanitize_text(customer_info.get('name', 'N/A'))}", 0, 1)
            pdf.cell(0, 10, f"Phone: {sanitize_text(customer_info.get('phone', 'N/A'))}", 0, 1)
            pdf.cell(0, 10, f"Address: {sanitize_text(customer_info.get('address', 'N/A'))}", 0, 1)

            # Loan Details
            for loan in loans:
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, "Loan Details", 0, 1)
                
                pdf.set_font('Arial', '', 12)
                # Sanitize date format
                try:
                    loan_date = datetime.strptime(str(loan[0]).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d")
                    formatted_date = loan_date.strftime('%d-%m-%Y')
                except:
                    formatted_date = "Invalid date"
                    
                pdf.cell(0, 10, f"Loan Date: {formatted_date}", 0, 1)
                pdf.cell(0, 10, f"Registered Reference Id: {sanitize_text(str(loan[6]))}", 0, 1)
                
                # Handle numeric values safely
                try:
                    weight = float(loan[2]) if loan[2] else 0
                    pdf.cell(0, 10, f"Total Weight: {weight} g", 0, 1)
                except:
                    pdf.cell(0, 10, "Total Weight: Error calculating", 0, 1)
                    
                try:
                    loan_amount = float(loan[3]) if loan[3] else 0
                    pdf.cell(0, 10, f"Total Loan Amount: Rs{format_indian_currency(loan_amount)}", 0, 1)
                except:
                    pdf.cell(0, 10, "Total Loan Amount: Error calculating", 0, 1)
                    
                try:
                    due_amount = float(loan[4]) if loan[4] else 0
                    pdf.cell(0, 10, f"Amount Due: Rs{format_indian_currency(due_amount)}", 0, 1)
                except:
                    pdf.cell(0, 10, "Amount Due: Error calculating", 0, 1)

                # Add assets
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "Assets:", 0, 1)
                try:
                    assets = DatabaseManager.fetch_loan_assets(loan[7])  # Using loan_id
                    pdf.set_font('Arial', '', 12)
                    if assets:
                        for desc, weight in assets:
                            pdf.cell(0, 10, f"  Asset Description: {sanitize_text(str(desc))}", 0, 1)
                            try:
                                weight_val = float(weight) if weight else 0
                                pdf.cell(0, 10, f"  Weight: {weight_val}g", 0, 1)
                            except:
                                pdf.cell(0, 10, "  Weight: Error calculating", 0, 1)
                            pdf.ln(2)
                    else:
                        pdf.cell(0, 10, "No assets found", 0, 1)
                except Exception as asset_error:
                    pdf.cell(0, 10, f"Error retrieving assets: {sanitize_text(str(asset_error))}", 0, 1)

                # Add loan payments
                pdf.ln(5)
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "Payment History:", 0, 1)
                try:
                    payments = DatabaseManager.fetch_loan_payments(loan[7])
                    pdf.set_font('Arial', '', 12)
                    if payments:
                        payments = sorted(payments, key=lambda payment: datetime.strptime(str(payment['payment_date']).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d"), reverse=True)
                        for payment in payments:
                            try:
                                payment_date = datetime.strptime(
                                    str(payment['payment_date']).replace('00:00:00', '').replace(' ', ''), 
                                    "%Y-%m-%d"
                                )
                                formatted_payment_date = payment_date.strftime('%d-%m-%Y')
                            except:
                                formatted_payment_date = "Invalid date"
                                
                            pdf.cell(0, 10, f"Date: {formatted_payment_date}", 0, 1)
                            pdf.cell(0, 10, f"Asset: {sanitize_text(str(payment.get('asset_description', 'N/A')))}", 0, 1)
                            
                            try:
                                payment_amount = float(payment['payment_amount']) if payment['payment_amount'] else 0
                                pdf.cell(0, 10, f"Amount Paid: Rs{format_indian_currency(payment_amount)}", 0, 1)
                            except:
                                pdf.cell(0, 10, "Amount Paid: Error calculating", 0, 1)
                                
                            try:
                                interest_amount = float(payment['interest_amount']) if payment['interest_amount'] else 0
                                pdf.cell(0, 10, f"Interest Paid: Rs{format_indian_currency(interest_amount)}", 0, 1)
                            except:
                                pdf.cell(0, 10, "Interest Paid: Error calculating", 0, 1)
                                
                            try:
                                amount_left = float(payment['amount_left']) if payment['amount_left'] else 0
                                pdf.cell(0, 10, f"Remaining Amount: Rs{format_indian_currency(amount_left)}", 0, 1)
                            except:
                                pdf.cell(0, 10, "Remaining Amount: Error calculating", 0, 1)
                                
                            pdf.ln(5)
                    else:
                        pdf.cell(0, 10, "No payments recorded", 0, 1)
                except Exception as payment_error:
                    pdf.cell(0, 10, f"Error retrieving payments: {sanitize_text(str(payment_error))}", 0, 1)

                pdf.ln(10)
                pdf.cell(0, 0, "_" * 50, 0, 1)  # Add separator line between loans

            # Generate sanitized filename
            safe_name = ''.join(char for char in str(customer_info.get('name', 'unknown')) if char.isalnum() or char in ' _-')
            if not safe_name or safe_name.isspace():
                safe_name = "unknown"
                
            if self.selected_year:
                filename = f"customer_loan_report_{safe_name}_{self.selected_year}_{datetime.now().strftime('%Y%m%d')}.pdf"
            else:
                filename = f"customer_loan_report_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
                
            # Replace rupee symbol with "Rs" in the entire document
            try:
                pdf.output(filename)
                QMessageBox.information(self, "Success", f"Report generated: {filename}")
            except Exception as output_error:
                error_msg = str(output_error)
                QMessageBox.critical(self, "Error", f"Failed to write PDF: {error_msg}")
                # Try with even safer filename if that was the issue
                try:
                    safe_filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    pdf.output(safe_filename)
                    QMessageBox.information(self, "Success", f"Report generated with safe name: {safe_filename}")
                except Exception as last_error:
                    QMessageBox.critical(self, "Critical Error", "Cannot generate PDF with any filename. Check file permissions.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")