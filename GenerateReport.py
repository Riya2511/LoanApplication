from PyQt5.QtCore import QEvent, Qt, QDate
from PyQt5.QtWidgets import (
    QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QGroupBox, QMessageBox, QComboBox, 
    QLineEdit, QFormLayout, QDateEdit
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
        
        # Date range variables
        self.start_date = None
        self.end_date = None
        
        self.init_ui()
        
        # Hide elements initially
        self.customer_info_group.setVisible(False)
        self.loan_details_table.setVisible(False)
        self.generate_pdf_button.setEnabled(False)

    def init_ui(self):
        # Year Selection and Date Range
        year_layout = QHBoxLayout()
        
        # Year Dropdown
        year_layout.addWidget(QLabel("Select Year:"))
        self.year_dropdown = QComboBox()
        self.year_dropdown.setFixedWidth(150)
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
        
        year_layout.addWidget(self.year_dropdown)
        
        # Connect year selection change
        self.year_dropdown.currentIndexChanged.connect(self.on_year_selected)
        
        year_layout.addSpacing(30)
        
        # Start Date
        year_layout.addWidget(QLabel("Start Date:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("dd-MM-yyyy")
        self.start_date_edit.setFixedWidth(130)
        self.start_date_edit.setStyleSheet("""
            QDateEdit {
                font-size: 14px;
            }
            QCalendarWidget QToolButton {
                color: black;
                background-color: white;
                padding: 5px;
                margin: 3px;
            }
            QCalendarWidget QMenu {
                color: black;
                background-color: white;
            }
            QCalendarWidget QSpinBox {
                color: black;
            }
            QCalendarWidget QWidget {
                alternate-background-color: rgb(240, 240, 240);
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: black;
                background-color: white;
                selection-background-color: rgb(64, 64, 64);
                selection-color: white;
            }
        """)
        
        # Get earliest loan date from database, default to 10 years ago if none
        earliest_date_str = DatabaseManager.get_earliest_loan_date()
        if earliest_date_str:
            try:
                earliest_date = datetime.strptime(earliest_date_str.split()[0], "%Y-%m-%d")
                self.start_date_edit.setDate(QDate(earliest_date.year, earliest_date.month, earliest_date.day))
                self.start_date = earliest_date_str.split()[0]  # Store in YYYY-MM-DD format
            except:
                # Fallback to 10 years ago
                fallback_date = QDate.currentDate().addYears(-10)
                self.start_date_edit.setDate(fallback_date)
                self.start_date = fallback_date.toString("yyyy-MM-dd")
        else:
            # Default to 10 years ago if no loans
            fallback_date = QDate.currentDate().addYears(-10)
            self.start_date_edit.setDate(fallback_date)
            self.start_date = fallback_date.toString("yyyy-MM-dd")
        
        self.start_date_edit.dateChanged.connect(self.on_date_range_changed)
        year_layout.addWidget(self.start_date_edit)
        
        year_layout.addSpacing(10)
        
        # End Date
        year_layout.addWidget(QLabel("End Date:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("dd-MM-yyyy")
        self.end_date_edit.setFixedWidth(130)
        self.end_date_edit.setStyleSheet("""
            QDateEdit {
                font-size: 14px;
            }
            QCalendarWidget QToolButton {
                color: black;
                background-color: white;
                padding: 5px;
                margin: 3px;
            }
            QCalendarWidget QMenu {
                color: black;
                background-color: white;
            }
            QCalendarWidget QSpinBox {
                color: black;
            }
            QCalendarWidget QWidget {
                alternate-background-color: rgb(240, 240, 240);
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: black;
                background-color: white;
                selection-background-color: rgb(64, 64, 64);
                selection-color: white;
            }
        """)
        
        # Set to today's date
        today = QDate.currentDate()
        self.end_date_edit.setDate(today)
        self.end_date = today.toString("yyyy-MM-dd")
        
        self.end_date_edit.dateChanged.connect(self.on_date_range_changed)
        year_layout.addWidget(self.end_date_edit)
        
        year_layout.addStretch(1)
        
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
        self.start_date_edit.blockSignals(True)
        self.end_date_edit.blockSignals(True)
        
        # Update date range based on year selection
        if self.selected_year:
            # Set date range to the selected year
            self.start_date_edit.setDate(QDate(self.selected_year, 1, 1))
            self.end_date_edit.setDate(QDate(self.selected_year, 12, 31))
            self.start_date = f"{self.selected_year}-01-01"
            self.end_date = f"{self.selected_year}-12-31"
        else:
            # Reset to full range (earliest to today)
            earliest_date_str = DatabaseManager.get_earliest_loan_date()
            if earliest_date_str:
                try:
                    earliest_date = datetime.strptime(earliest_date_str.split()[0], "%Y-%m-%d")
                    self.start_date_edit.setDate(QDate(earliest_date.year, earliest_date.month, earliest_date.day))
                    self.start_date = earliest_date_str.split()[0]
                except:
                    fallback_date = QDate.currentDate().addYears(-10)
                    self.start_date_edit.setDate(fallback_date)
                    self.start_date = fallback_date.toString("yyyy-MM-dd")
            else:
                fallback_date = QDate.currentDate().addYears(-10)
                self.start_date_edit.setDate(fallback_date)
                self.start_date = fallback_date.toString("yyyy-MM-dd")
            
            today = QDate.currentDate()
            self.end_date_edit.setDate(today)
            self.end_date = today.toString("yyyy-MM-dd")
        
        # Reset customer selection
        self.customer_dropdown.setCurrentIndex(0)
        self.selected_customer_id = None
        # Clear search text
        self.customer_search.clear()
        
        # Re-enable signals
        self.customer_dropdown.blockSignals(False)
        self.customer_search.blockSignals(False)
        self.start_date_edit.blockSignals(False)
        self.end_date_edit.blockSignals(False)
        
        # Update summary data for selected year
        self.refresh_summary_data()
        # Update customer dropdown with customers from selected year
        self.populate_customer_dropdown()
        # Hide customer info but show loan details table with all loans
        self.customer_info_group.setVisible(False)
        self.loan_details_table.setVisible(True)
        self.update_group.setVisible(False)
        # Enable PDF button for all loans report
        self.generate_pdf_button.setEnabled(True)
        # Reset pagination and show all loans for the selected year
        self.current_page = 1
        self.all_loans_cache = []
        self.populate_loans_table()
    
    def on_date_range_changed(self):
        """Handle date range change"""
        # Update stored date values
        self.start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        self.end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        # Validate date range
        if self.start_date > self.end_date:
            QMessageBox.warning(self, "Invalid Date Range", "Start date cannot be after end date!")
            # Reset end date to start date
            self.end_date_edit.setDate(self.start_date_edit.date())
            self.end_date = self.start_date
            return
        
        # Block year dropdown signal
        self.year_dropdown.blockSignals(True)
        # Reset year selection when date range changes
        self.year_dropdown.setCurrentIndex(0)
        self.selected_year = None
        self.year_dropdown.blockSignals(False)
        
        # Reset pagination and refresh data
        self.current_page = 1
        self.all_loans_cache = []
        
        # Refresh summary and loans
        self.refresh_summary_data()
        if not self.selected_customer_id:
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
            # Enable PDF button for all loans report
            self.generate_pdf_button.setEnabled(True)
            
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
        
        # Always enable PDF generation (works for both all loans and individual customer)
        self.generate_pdf_button.setEnabled(True)
        
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
                self.all_loans_cache = DatabaseManager.fetch_loans_by_year(
                    year=self.selected_year,
                    start_date=self.start_date,
                    end_date=self.end_date
                )
            
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
            self.total_loans = DatabaseManager.get_total_loans_count(
                year=self.selected_year,
                start_date=self.start_date,
                end_date=self.end_date
            )
            
            # Calculate offset for pagination
            offset = (self.current_page - 1) * self.rows_per_page
            
            # Fetch only the current page's data from database
            loans_to_display = DatabaseManager.fetch_loans_by_year(
                year=self.selected_year, 
                limit=self.rows_per_page, 
                offset=offset,
                start_date=self.start_date,
                end_date=self.end_date
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
        """Generate a comprehensive PDF report based on current filters."""
        
        # Helper function to sanitize text - use ASCII only
        def sanitize_text(text):
            if text is None:
                return "N/A"
            try:
                text = str(text)
                return ''.join(char for char in text if ord(char) < 128)
            except:
                return "Text contains unsupported characters"
        
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Determine report type and generate accordingly
            if self.selected_customer_id:
                # Scenario 3: Individual customer report
                self.generate_customer_pdf_report(pdf, sanitize_text)
            else:
                # Scenario 1 & 2: All loans table report
                self.generate_all_loans_pdf_report(pdf, sanitize_text)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")
    
    def generate_all_loans_pdf_report(self, pdf, sanitize_text):
        """Generate PDF report with table of all loans (Scenarios 1 & 2)."""
        
        # Fetch all loans based on current filters (no pagination for PDF)
        all_loans = DatabaseManager.fetch_loans_by_year(
            year=self.selected_year,
            start_date=self.start_date,
            end_date=self.end_date
        )
        
        if not all_loans:
            QMessageBox.warning(self, "No Data", "No loans found for the selected filters.")
            return
        
        # Title based on filters
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 12, "LOAN REPORT", 0, 1, 'C')
        pdf.ln(5)
        
        # Filter information
        pdf.set_font('Arial', 'B', 12)
        if self.selected_year:
            pdf.cell(0, 8, f"Year: {self.selected_year}", 0, 1, 'C')
        else:
            # Show date range
            start_display = datetime.strptime(self.start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            end_display = datetime.strptime(self.end_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            pdf.cell(0, 8, f"Date Range: {start_display} to {end_display}", 0, 1, 'C')
        
        pdf.ln(3)
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 6, f"Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M')}", 0, 1, 'C')
        pdf.ln(8)
        
        # Summary statistics
        total_loan_amount = sum(float(loan[3]) if loan[3] else 0 for loan in all_loans)
        total_due_amount = sum(float(loan[4]) if loan[4] else 0 for loan in all_loans)
        
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 7, f"Total Loans: {len(all_loans)}", 0, 1)
        pdf.cell(0, 7, f"Total Loan Amount: Rs {format_indian_currency(total_loan_amount)}", 0, 1)
        pdf.cell(0, 7, f"Total Amount Due: Rs {format_indian_currency(total_due_amount)}", 0, 1)
        pdf.ln(8)
        
        # Table header
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(70, 130, 180)  # Steel blue
        pdf.set_text_color(255, 255, 255)  # White text
        
        # Column widths
        col_widths = [22, 45, 28, 35, 20, 22, 18]
        headers = ['Date', 'Customer', 'Ref ID', 'Assets', 'Weight(g)', 'Amount', 'Due']
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
        pdf.ln()
        
        # Table data
        pdf.set_font('Arial', '', 8)
        pdf.set_text_color(0, 0, 0)  # Black text
        
        fill = False
        for loan in all_loans:
            # loan structure: (loan_date, asset_descriptions, total_asset_weight, loan_amount, 
            #                  loan_amount_due, total_interest_amount, registered_reference_id, 
            #                  loan_id, customer_id, customer_name)
            
            try:
                loan_date = datetime.strptime(str(loan[0]).replace('00:00:00', '').strip(), "%Y-%m-%d").strftime("%d-%m-%Y")
            except:
                loan_date = str(loan[0])[:10]
            
            customer_name = sanitize_text(loan[9])[:25]  # Truncate if too long
            ref_id = sanitize_text(str(loan[6]) if loan[6] else "")[:15]
            assets = sanitize_text(str(loan[1]) if loan[1] else "")[:20]
            weight = f"{float(loan[2]):.2f}" if loan[2] else "0"
            amount = format_indian_currency(float(loan[3]) if loan[3] else 0)
            due = format_indian_currency(float(loan[4]) if loan[4] else 0)
            
            # Alternate row colors
            if fill:
                pdf.set_fill_color(240, 240, 240)
            else:
                pdf.set_fill_color(255, 255, 255)
            
            pdf.cell(col_widths[0], 7, loan_date, 1, 0, 'C', True)
            pdf.cell(col_widths[1], 7, customer_name, 1, 0, 'L', True)
            pdf.cell(col_widths[2], 7, ref_id, 1, 0, 'L', True)
            pdf.cell(col_widths[3], 7, assets, 1, 0, 'L', True)
            pdf.cell(col_widths[4], 7, weight, 1, 0, 'R', True)
            pdf.cell(col_widths[5], 7, amount, 1, 0, 'R', True)
            pdf.cell(col_widths[6], 7, due, 1, 0, 'R', True)
            pdf.ln()
            
            fill = not fill
            
            # Add new page if needed
            if pdf.get_y() > 270:
                pdf.add_page()
                # Repeat header
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(70, 130, 180)
                pdf.set_text_color(255, 255, 255)
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
                pdf.ln()
                pdf.set_font('Arial', '', 8)
                pdf.set_text_color(0, 0, 0)
        
        # Generate filename
        if self.selected_year:
            filename = f"loan_report_{self.selected_year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            filename = f"loan_report_{self.start_date}_to_{self.end_date}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        try:
            pdf.output(filename)
            QMessageBox.information(self, "Success", f"Report generated: {filename}")
        except Exception as output_error:
            safe_filename = f"loan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf.output(safe_filename)
            QMessageBox.information(self, "Success", f"Report generated: {safe_filename}")
    
    def generate_customer_pdf_report(self, pdf, sanitize_text):
        """Generate PDF report for individual customer (Scenario 3) with tabular format."""
        
        customer_info = DatabaseManager.get_customer_by_id(self.selected_customer_id)
        loans = DatabaseManager.fetch_loans_for_customer_to_generate_report(
            self.selected_customer_id, self.selected_year
        )
        
        if not loans:
            QMessageBox.warning(self, "No Data", "No loans found for this customer.")
            return
        
        # Title
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 12, "CUSTOMER LOAN REPORT", 0, 1, 'C')
        pdf.ln(3)
        
        # Filter information
        pdf.set_font('Arial', 'B', 11)
        if self.selected_year:
            pdf.cell(0, 7, f"Year: {self.selected_year}", 0, 1, 'C')
        else:
            start_display = datetime.strptime(self.start_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            end_display = datetime.strptime(self.end_date, "%Y-%m-%d").strftime("%d-%m-%Y")
            pdf.cell(0, 7, f"Date Range: {start_display} to {end_display}", 0, 1, 'C')
        
        pdf.ln(2)
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 6, f"Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M')}", 0, 1, 'C')
        pdf.ln(8)
        
        # Customer Information
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 8, "Customer Information", 0, 1)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 7, f"Name: {sanitize_text(customer_info.get('name', 'N/A'))}", 0, 1)
        pdf.cell(0, 7, f"Phone: {sanitize_text(customer_info.get('phone', 'N/A'))}", 0, 1)
        pdf.cell(0, 7, f"Address: {sanitize_text(customer_info.get('address', 'N/A'))}", 0, 1)
        pdf.ln(8)
        
        # Loan Details Table
        for idx, loan in enumerate(loans, 1):
            if idx > 1:
                pdf.ln(8)
            
            # Check if we need a new page
            if pdf.get_y() > 240:
                pdf.add_page()
            
            pdf.set_font('Arial', 'B', 13)
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(0, 8, f"Loan #{idx}", 0, 1, 'L', True)
            pdf.ln(3)
            
            # Loan Details Table Header
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(70, 130, 180)
            pdf.set_text_color(255, 255, 255)
            
            loan_col_widths = [30, 45, 35, 35, 45]
            loan_headers = ['Date', 'Reference ID', 'Weight (g)', 'Amount', 'Due']
            
            for i, header in enumerate(loan_headers):
                pdf.cell(loan_col_widths[i], 7, header, 1, 0, 'C', True)
            pdf.ln()
            
            # Loan Details Data
            pdf.set_font('Arial', '', 9)
            pdf.set_text_color(0, 0, 0)
            pdf.set_fill_color(255, 255, 255)
            
            try:
                loan_date = datetime.strptime(str(loan[0]).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d").strftime('%d-%m-%Y')
            except:
                loan_date = "Invalid"
            
            ref_id = sanitize_text(str(loan[6]) if loan[6] else "N/A")[:25]
            weight = f"{float(loan[2]):.2f}" if loan[2] else "0"
            loan_amount = format_indian_currency(float(loan[3]) if loan[3] else 0)
            due_amount = format_indian_currency(float(loan[4]) if loan[4] else 0)
            
            pdf.cell(loan_col_widths[0], 7, loan_date, 1, 0, 'C', True)
            pdf.cell(loan_col_widths[1], 7, ref_id, 1, 0, 'L', True)
            pdf.cell(loan_col_widths[2], 7, weight, 1, 0, 'R', True)
            pdf.cell(loan_col_widths[3], 7, loan_amount, 1, 0, 'R', True)
            pdf.cell(loan_col_widths[4], 7, due_amount, 1, 0, 'R', True)
            pdf.ln()
            
            # Assets Table
            pdf.ln(3)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 6, "Assets:", 0, 1)
            
            assets = DatabaseManager.fetch_loan_assets(loan[7])
            if assets:
                # Assets Table Header
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(70, 130, 180)
                pdf.set_text_color(255, 255, 255)
                
                asset_col_widths = [140, 50]
                asset_headers = ['Description', 'Weight (g)']
                
                for i, header in enumerate(asset_headers):
                    pdf.cell(asset_col_widths[i], 7, header, 1, 0, 'C', True)
                pdf.ln()
                
                # Assets Data
                pdf.set_font('Arial', '', 9)
                pdf.set_text_color(0, 0, 0)
                
                fill = False
                for desc, weight in assets:
                    if fill:
                        pdf.set_fill_color(240, 240, 240)
                    else:
                        pdf.set_fill_color(255, 255, 255)
                    
                    asset_desc = sanitize_text(str(desc))[:60]
                    pdf.cell(asset_col_widths[0], 6, asset_desc, 1, 0, 'L', True)
                    pdf.cell(asset_col_widths[1], 6, str(weight), 1, 0, 'R', True)
                    pdf.ln()
                    fill = not fill
                    
                    # Check for page break
                    if pdf.get_y() > 270:
                        pdf.add_page()
            else:
                pdf.set_font('Arial', 'I', 9)
                pdf.cell(0, 6, "No assets found", 0, 1)
            
            # Payment History Table
            pdf.ln(3)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 6, "Payment History:", 0, 1)
            
            payments = DatabaseManager.fetch_loan_payments(loan[7])
            if payments:
                # Sort payments by date (most recent first)
                payments = sorted(payments, key=lambda p: datetime.strptime(str(p['payment_date']).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d"), reverse=True)
                
                # Payment Table Header
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(70, 130, 180)
                pdf.set_text_color(255, 255, 255)
                
                payment_col_widths = [30, 50, 50, 60]
                payment_headers = ['Date', 'Amount', 'Interest', 'Mode']
                
                for i, header in enumerate(payment_headers):
                    pdf.cell(payment_col_widths[i], 7, header, 1, 0, 'C', True)
                pdf.ln()
                
                # Payment Data
                pdf.set_font('Arial', '', 9)
                pdf.set_text_color(0, 0, 0)
                
                fill = False
                for payment in payments:
                    if fill:
                        pdf.set_fill_color(240, 240, 240)
                    else:
                        pdf.set_fill_color(255, 255, 255)
                    
                    try:
                        payment_date = datetime.strptime(str(payment['payment_date']).replace('00:00:00', '').replace(' ', ''), "%Y-%m-%d").strftime('%d-%m-%Y')
                    except:
                        payment_date = "Invalid"
                    
                    payment_amt = format_indian_currency(float(payment['payment_amount']) if payment['payment_amount'] else 0)
                    interest_amt = format_indian_currency(float(payment['interest_amount']) if payment['interest_amount'] else 0)
                    payment_mode = sanitize_text(str(payment['payment_mode']) if payment['payment_mode'] else "N/A")[:25]
                    
                    pdf.cell(payment_col_widths[0], 6, payment_date, 1, 0, 'C', True)
                    pdf.cell(payment_col_widths[1], 6, payment_amt, 1, 0, 'R', True)
                    pdf.cell(payment_col_widths[2], 6, interest_amt, 1, 0, 'R', True)
                    pdf.cell(payment_col_widths[3], 6, payment_mode, 1, 0, 'L', True)
                    pdf.ln()
                    fill = not fill
                    
                    # Check for page break
                    if pdf.get_y() > 270:
                        pdf.add_page()
            else:
                pdf.set_font('Arial', 'I', 9)
                pdf.cell(0, 6, "No payments recorded", 0, 1)
        
        # Generate filename
        safe_name = ''.join(char for char in str(customer_info.get('name', 'unknown')) if char.isalnum() or char in ' _-')
        if not safe_name or safe_name.isspace():
            safe_name = "unknown"
        
        if self.selected_year:
            filename = f"customer_{safe_name}_{self.selected_year}_{datetime.now().strftime('%Y%m%d')}.pdf"
        else:
            filename = f"customer_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        try:
            pdf.output(filename)
            QMessageBox.information(self, "Success", f"Report generated: {filename}")
        except Exception as output_error:
            safe_filename = f"customer_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf.output(safe_filename)
            QMessageBox.information(self, "Success", f"Report generated: {safe_filename}")