from PyQt5.QtCore import QEvent, Qt
from helper import StyledWidget, format_indian_currency
from DatabaseManager import DatabaseManager
from PyQt5.QtWidgets import (QPushButton, QLineEdit, QFormLayout, QMessageBox, 
                           QLabel, QHBoxLayout, QComboBox, QGroupBox, QVBoxLayout,
                           QScrollArea, QWidget, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtWidgets import QDateEdit
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QDateEdit, QSizePolicy

class LoanRegistrationPage(StyledWidget):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent, with_back_button=True, title="Register Loan", switch_page_callback=switch_page_callback)
        self.selected_customer_id = None
        self.customer_info_group = None
        self.asset_entries = []
        self.edit_loan_group = None  # Add this to track the edit loan group
        self.all_loans = []  # To store all loans for filtering
        self.init_ui()

    def init_ui(self):
        # Create a customer selection layout with search functionality
        customer_layout = QVBoxLayout()  # Changed to QVBoxLayout to stack search box and dropdown
        
        # Add a search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search customers...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                padding: 5px;
                min-height: 30px;
            }
        """)
        self.search_box.setFixedWidth(300)
        self.search_box.textChanged.connect(self.filter_customers)
        customer_layout.addWidget(self.search_box, alignment=Qt.AlignRight)
        
        # Customer dropdown in a horizontal layout
        dropdown_layout = QHBoxLayout()
        self.customer_dropdown = QComboBox()
        self.customer_dropdown.setFixedWidth(300)
        self.customer_dropdown.setStyleSheet("""
            QComboBox {
                font-size: 16px;
            }
            QComboBox QAbstractItemView {
                font-size: 16px;
                min-height: 30px;  /* This increases the line height of dropdown items */
            }
        """)
        dropdown_layout.addWidget(QLabel("Select Customer:"))
        dropdown_layout.addWidget(self.customer_dropdown)
        customer_layout.addLayout(dropdown_layout)
        
        self.content_layout.addLayout(customer_layout)

        self.customer_info_group = QGroupBox("Customer Information")
        # In the init_ui method, after creating the customer_info_group:
        self.customer_info_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.customer_info_group.setMinimumHeight(100)  # Set an appropriate minimum height
        self.customer_info_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d3d3d3;
                border-radius: 5px;
                margin-top: 10px;
                margin-bottom: 10px;
                padding: 20px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: white;
            }
        """)
        customer_info_layout = QVBoxLayout()
        self.customer_info_group.setLayout(customer_info_layout)
        self.content_layout.addWidget(self.customer_info_group)

        self.loan_form_group = QGroupBox("Loan Registration")
        loan_form_layout = QFormLayout()
        
        # Add date input at loan level
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setStyleSheet("""
            QDateEdit {
                min-height: 30px;
                max-height: 30px;
                padding: 5px;
                color: black;
            }
            QCalendarWidget QAbstractItemView {
                color: black;
            }
            QCalendarWidget QWidget {
                color: black;
            }
            QCalendarWidget QToolButton {
                color: black;
            }
        """)
        loan_form_layout.addRow("Loan Date:", self.date_input)

        # Add Registered Reference Id at loan level
        self.loan_account_input = QLineEdit()
        self.loan_account_input.setPlaceholderText("Enter Registered Reference Id")
        loan_form_layout.addRow("Registered Reference Id:", self.loan_account_input)
        
        self.loan_amount_input = QLineEdit()
        self.loan_amount_input.setPlaceholderText("Enter Loan Amount (₹)")
        loan_form_layout.addRow("Loan Amount (₹):", self.loan_amount_input)

        # Asset Description
        self.asset_description_input = QLineEdit()
        self.asset_description_input.setPlaceholderText("Enter Asset Description")
        loan_form_layout.addRow("Asset Description:", self.asset_description_input)

        # Asset Weight
        self.asset_weight_input = QLineEdit()
        self.asset_weight_input.setPlaceholderText("Enter Asset Weight (g)")
        loan_form_layout.addRow("Asset Weight (g):", self.asset_weight_input)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        self.register_loan_btn = QPushButton("Register Loan")
        self.register_loan_btn.clicked.connect(self.register_loan)
        loan_form_layout.addRow(self.register_loan_btn)
        
        self.loan_form_group.setLayout(loan_form_layout)
        self.loan_form_group.setEnabled(False)
        self.content_layout.addWidget(self.loan_form_group)
        
        self.customer_dropdown.currentIndexChanged.connect(self.on_customer_selected)

        self.loans_group = QGroupBox("Customer Loans")
        loans_layout = QVBoxLayout()
        
        # Add loan filter for Registered Reference ID
        filter_layout = QHBoxLayout()
        self.loan_filter = QLineEdit()
        self.loan_filter.setPlaceholderText("Filter by Registered Reference ID...")
        self.loan_filter.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 5px;
                min-height: 28px;
                max-width: 300px;
            }
        """)
        self.loan_filter.textChanged.connect(self.filter_loans)
        filter_layout.addWidget(QLabel("Search Loans:"))
        filter_layout.addWidget(self.loan_filter)
        filter_layout.addStretch()
        loans_layout.addLayout(filter_layout)
        
        self.loans_table = QTableWidget()
        self.loans_table.setColumnCount(10)  # Increased to 10 for Registered Reference Id and Delete Loan columns
        self.loans_table.setHorizontalHeaderLabels([
            "Loan Date", 
            "Registered Reference Id",  # New column
            "Assets",
            "Total Weight (g)", 
            "Loan Amount (₹)", 
            "Amount Due (₹)",
            "Interest Paid (₹)",
            "Status", 
            "Edit Loan",
            "Delete Loan"  # New column
        ])
        
        self.loans_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.loans_table.setSelectionMode(QTableWidget.SingleSelection)
        self.loans_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.loans_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Assets column
        self.loans_table.setColumnWidth(1, 180)
        self.loans_table.setAlternatingRowColors(True)
        self.loans_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 5px;
                border: 1px solid #d0d0d0;
            }
        """)
        
        loans_layout.addWidget(self.loans_table)
        self.loans_group.setLayout(loans_layout)
        self.content_layout.addWidget(self.loans_group)

        # Container for edit section that can be shown/hidden
        self.edit_section_wrapper = QWidget()
        self.edit_section_layout = QVBoxLayout()
        self.edit_section_wrapper.setLayout(self.edit_section_layout)
        self.content_layout.addWidget(self.edit_section_wrapper)
        
        # Initially hide the edit section
        self.edit_section_wrapper.setVisible(False)

        self.content_layout.addStretch(1)

    def register_loan(self):
        try:
            registered_reference_id = self.loan_account_input.text().strip()
            if not registered_reference_id:
                raise ValueError("Registered Reference Id cannot be empty.")

            loan_amount = self.loan_amount_input.text().strip()
            if not loan_amount:
                raise ValueError('Loan Amount cannot be empty.')
            loan_amount = float(loan_amount)
            if loan_amount <= 0:
                raise ValueError("Loan amount must be positive.")

            asset_description = self.asset_description_input.text().strip()
            if not asset_description:
                raise ValueError("Asset description cannot be empty.")

            asset_weight = self.asset_weight_input.text().strip()
            if not asset_weight: asset_weight = 0
            asset_weight = float(asset_weight)
            if asset_weight < 0:
                raise ValueError("Asset weight must be positive.")

            loan_date = self.date_input.date().toString("yyyy-MM-dd")

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
            return

        if not self.selected_customer_id:
            QMessageBox.warning(self, "Selection Error", "Please select a customer.")
            return
        
        success, message = DatabaseManager.insert_loan_with_asset(
            self.selected_customer_id, loan_amount, loan_date, registered_reference_id, 
            asset_description, asset_weight
        )

        if success:
            QMessageBox.information(self, "Success", "Loan registered successfully!")
            self.reset_form()
            self.update_loans_table()
        else:
            QMessageBox.critical(self, "Error", f"Failed to register loan: {message}")

    def remove_asset_entry(self, entry):
        self.assets_layout.removeWidget(entry)
        self.asset_entries.remove(entry)
        entry.deleteLater()
        for i, entry in enumerate(self.asset_entries):
            entry.index = i
            entry.setTitle(f"Asset {i + 1}")

    def reset_form(self):
        self.loan_amount_input.clear()
        self.loan_account_input.clear()
        self.asset_description_input.clear()
        self.asset_weight_input.clear()
        for entry in self.asset_entries[:]:
            self.remove_asset_entry(entry)

    def showEvent(self, event: QEvent):
        if event.type() == QEvent.Show:
            self.populate_customer_dropdown()
        super().showEvent(event)

    def populate_customer_dropdown(self):
        self.customer_dropdown.clear()
        # self.customer_dropdown.addItem("Select Customer", None)  # Add default option
        
        # Initialize customer data list
        self.all_customers_data = []
        
        customers = DatabaseManager.get_all_customers()
        if customers:
            for customer_id, name, phone in customers:
                self.customer_dropdown.addItem(f"{name}", customer_id)
                
                # Store customer data for filtering
                self.all_customers_data.append({
                    'id': customer_id,
                    'name': name,
                    'phone': phone if phone else ''
                })

    def on_customer_selected(self, index):
        # Clean up existing edit section if it exists
        self.remove_edit_section()
        
        if index < 0:  # If "Select Customer" is chosen
            self.selected_customer_id = None
            self.loan_form_group.setEnabled(False)
            self.update_customer_info()
            self.update_loans_table()
            self.edit_section_wrapper.setVisible(False)  # Hide edit section
            return

        self.selected_customer_id = self.customer_dropdown.currentData()
        self.loan_form_group.setEnabled(True)
        self.update_customer_info()
        self.update_loans_table()

    def remove_edit_section(self):
        # Remove any widgets in the edit section layout
        while self.edit_section_layout.count():
            item = self.edit_section_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.edit_section_wrapper.setVisible(False)

    def update_loans_table(self):
        if not self.selected_customer_id:
            self.loans_table.setRowCount(0)
            self.all_loans = []  # Clear stored loans
            return
            
        loans = DatabaseManager.fetch_loans_for_customer(self.selected_customer_id)
        loans = sorted(loans, key=lambda loan: loan[0], reverse=True)
        self.all_loans = loans  # Store all loans for filtering
        
        # Apply filter if there is text in the filter box
        self.filter_loans()

    def filter_loans(self):
        filter_text = self.loan_filter.text().strip().lower()
        
        if not self.all_loans:
            self.loans_table.setRowCount(0)
            return
            
        # Filter loans based on text in any displayed column
        if filter_text:
            filtered_loans = []
            for loan in self.all_loans:
                # Create searchable strings for each column
                date_str = loan[0]
                if " 00:00:00" in date_str:
                    date_str = date_str.split(" ")[0]
                    
                # Format date for searching
                try:
                    date_parts = date_str.split('-')
                    if len(date_parts) == 3:
                        formatted_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                    else:
                        formatted_date = date_str
                except:
                    formatted_date = date_str
                
                ref_id = loan[6] or "N/A"
                assets = loan[1] or "N/A"
                total_weight = f"{loan[2]}"
                loan_amount = f"{loan[3]}"
                amount_due = f"{loan[4]}"
                interest_paid = f"{loan[5]}"
                status = "Completed" if float(loan[4]) <= 0 else "Pending"
                
                # Check if filter text is in any of the columns
                searchable_values = [
                    formatted_date.lower(),
                    ref_id.lower(),
                    assets.lower(),
                    total_weight,
                    loan_amount,
                    amount_due,
                    interest_paid,
                    status.lower()
                ]
                
                if any(filter_text in value for value in searchable_values):
                    filtered_loans.append(loan)
        else:
            filtered_loans = self.all_loans
            
        # Update table with filtered loans
        self.loans_table.setRowCount(len(filtered_loans))
        
        for row, loan in enumerate(filtered_loans):
            # Handle date formatting correctly
            date_str = loan[0]
            if " 00:00:00" in date_str:
                # Remove time portion if it exists
                date_str = date_str.split(" ")[0]
                
            # Convert YYYY-MM-DD to DD-MM-YYYY format
            try:
                date_parts = date_str.split('-')
                if len(date_parts) == 3:
                    formatted_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                else:
                    formatted_date = date_str
            except:
                formatted_date = date_str
            
            self.loans_table.setItem(row, 0, QTableWidgetItem(formatted_date))
            self.loans_table.setItem(row, 1, QTableWidgetItem(loan[6] or "N/A"))  # Registered Reference Id
            self.loans_table.setItem(row, 2, QTableWidgetItem(loan[1] or "N/A"))  # Assets
            self.loans_table.setItem(row, 3, QTableWidgetItem(f"{format_indian_currency(loan[2])}"))  # Total Weight
            self.loans_table.setItem(row, 4, QTableWidgetItem(f"{format_indian_currency(loan[3])}"))  # Loan Amount
            self.loans_table.setItem(row, 5, QTableWidgetItem(f"{format_indian_currency(loan[4])}"))  # Amount Due
            self.loans_table.setItem(row, 6, QTableWidgetItem(f"{format_indian_currency(loan[5])}"))  # Interest Paid
            
            status = "Completed" if float(loan[4]) <= 0 else "Pending"
            self.loans_table.setItem(row, 7, QTableWidgetItem(status))

            # Add "Edit Loan" Button
            edit_button = QPushButton("Edit Loan")
            edit_button.setFixedSize(90, 30)
            edit_button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 11px;
                    margin-top: 5px;
                    margin-left: 5px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            edit_button.clicked.connect(lambda _, loan_id=loan[7]: self.open_edit_loan(loan_id))
            self.loans_table.setCellWidget(row, 8, edit_button)  # Column 8 for Edit Button

            # Add "Delete Loan" Button
            delete_button = QPushButton("Delete Loan")
            delete_button.setFixedSize(90, 30)

            # Check if loan is completed (amount due is 0 or less)
            is_completed = float(loan[4]) <= 0

            # Enable/disable the button based on status
            delete_button.setEnabled(is_completed)

            # Apply appropriate styling based on button state
            if is_completed:
                delete_button.setStyleSheet("""
                    QPushButton {
                        background-color: #F44336;
                        color: white;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 11px;
                        margin-top: 5px;
                        margin-left: 5px;
                    }
                    QPushButton:hover {
                        background-color: #D32F2F;
                    }
                """)
            else:
                delete_button.setStyleSheet("""
                    QPushButton {
                        background-color: #cccccc;
                        color: #666666;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 11px;
                        margin-top: 5px;
                        margin-left: 5px;
                    }
                """)

            delete_button.clicked.connect(lambda _, loan_id=loan[7]: self.delete_loan(loan_id))
            self.loans_table.setCellWidget(row, 9, delete_button)  # Column 9 for Delete Button
        
        # Set column widths - make Registered Reference Id column wider
        self.loans_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.loans_table.setColumnWidth(1, 180)  # Make Registered Reference Id column wider
        self.loans_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Assets column

    def update_customer_info(self):
        # Clear existing widgets
        layout = self.customer_info_group.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        if not self.selected_customer_id:
            # Add a placeholder label when no customer is selected
            placeholder = QLabel("No customer selected")
            placeholder.setAlignment(Qt.AlignCenter)
            layout.addWidget(placeholder)
            return

        customer = DatabaseManager.get_customer_by_id(self.selected_customer_id)
        if customer:
            for key, value in customer.items():
                if key == "customer_id" or not value:
                    continue
                row = QHBoxLayout()
                # Create labels with consistent styling using the helper method
                key_label = self.create_info_label(f"{key.replace('_', ' ').title()}:")
                value_label = self.create_info_label(str(value))
                row.addWidget(key_label)
                row.addWidget(value_label)
                layout.addLayout(row)
        else:
            QMessageBox.warning(self, "Error", "Failed to load customer details.")

    def open_edit_loan(self, loan_id):
        # First, remove any existing edit section
        self.remove_edit_section()
        self.edit_section_wrapper.setVisible(True)  # Make edit section visible
        
        loan_details = DatabaseManager.fetch_loan_details_to_edit(loan_id)

        if not loan_details:
            QMessageBox.warning(self, "Error", "Loan details not found.")
            return

        # Create and add new edit loan group to the edit section layout
        self.edit_loan_group = QGroupBox("Edit Loan Details")
        edit_loan_layout = QFormLayout()

        # Add date input
        self.edit_date_input = QDateEdit()
        self.edit_date_input.setCalendarPopup(True)
        
        # Try to parse the loan date if available
        try:
            date_parts = loan_details.get("loan_date", "").split('-')
            if len(date_parts) == 3:
                self.edit_date_input.setDate(QDate(int(date_parts[0]), int(date_parts[1]), int(date_parts[2])))
            else:
                self.edit_date_input.setDate(QDate.currentDate())
        except:
            self.edit_date_input.setDate(QDate.currentDate())
            
        edit_loan_layout.addRow("Loan Date:", self.edit_date_input)

        self.edit_loan_account_input = QLineEdit()
        self.edit_loan_account_input.setText(loan_details["registered_reference_id"])
        edit_loan_layout.addRow("Registered Reference Id:", self.edit_loan_account_input)

        self.edit_loan_amount_input = QLineEdit()
        self.edit_loan_amount_input.setText(str(loan_details["loan_amount"]))
        edit_loan_layout.addRow("Loan Amount (₹):", self.edit_loan_amount_input)

        self.edit_asset_description_input = QLineEdit()
        self.edit_asset_description_input.setText(loan_details["description"])
        edit_loan_layout.addRow("Asset Description:", self.edit_asset_description_input)

        self.edit_asset_weight_input = QLineEdit()
        self.edit_asset_weight_input.setText(str(loan_details["weight"]))
        edit_loan_layout.addRow("Asset Weight (g):", self.edit_asset_weight_input)

        # Save button
        save_button = QPushButton("Update Loan Details")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                min-height: 30px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        save_button.clicked.connect(lambda: self.save_edited_loan(loan_id))
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border-radius: 8px;
                font-weight: bold;
                min-height: 30px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        cancel_button.clicked.connect(self.remove_edit_section)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        edit_loan_layout.addRow("", button_layout)
        
        self.edit_loan_group.setLayout(edit_loan_layout)
        self.edit_section_layout.addWidget(self.edit_loan_group)

    def save_edited_loan(self, loan_id):
        try:
            loan_date = self.edit_date_input.date().toString("yyyy-MM-dd")
            registered_reference_id = self.edit_loan_account_input.text().strip()
            loan_amount = self.edit_loan_amount_input.text().strip()
            asset_description = self.edit_asset_description_input.text().strip()
            asset_weight = self.edit_asset_weight_input.text().strip()
            if not asset_weight: 
                asset_weight = 0

            # Validate inputs
            if not registered_reference_id:
                raise ValueError("Registered Reference Id cannot be empty.")
                
            if not asset_description:
                raise ValueError("Asset description cannot be empty.")

            # Validate numeric inputs
            if not loan_amount: 
                raise ValueError('Loan Amount cannot be empty.')
            loan_amount = float(loan_amount)
            if loan_amount <= 0:
                raise ValueError("Loan amount must be positive.")
                
            if not asset_weight: 
                raise ValueError('Asset weight cannot be empty.')
            asset_weight = float(asset_weight)
            if asset_weight < 0:
                raise ValueError("Asset weight must be positive.")

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
            return

        try:
            DatabaseManager.update_loan(loan_id, loan_date, registered_reference_id, loan_amount)
            
            DatabaseManager.update_loan_assets(loan_id, asset_description, asset_weight)
            
            QMessageBox.information(self, "Success", "Loan details updated successfully!")
            self.remove_edit_section()  
            self.update_loans_table()   
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update loan: {str(e)}")

    def delete_loan(self, loan_id):
        # Confirm with user before deleting
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion", 
            "Are you sure you want to delete this loan?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                DatabaseManager.delete_loan(loan_id)
                QMessageBox.information(self, "Success", "Loan deleted successfully!")
                self.update_loans_table()
                self.remove_edit_section()  # Remove edit section if it's showing the deleted loan
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete loan: {str(e)}")

    def filter_customers(self):
        """Filter dropdown options based on search box input"""
        search_text = self.search_box.text().strip().lower()

        self.customer_dropdown.blockSignals(True)
        self.customer_dropdown.clear()
        # self.customer_dropdown.addItem("Select Customer", None)  # Keep the default option

        # Add matching customers
        matching_customers = []
        for customer in self.all_customers_data:
            if (search_text in customer['name'].lower() or 
                (customer['phone'] and search_text in customer['phone'].lower())):
                matching_customers.append(customer)
                self.customer_dropdown.addItem(f"{customer['name']}", customer['id'])

        self.customer_dropdown.blockSignals(False)
        
        # If there's exactly one match, select that customer
        if len(matching_customers) == 1:
            self.customer_dropdown.setCurrentIndex(0)  # First item after "Select Customer"
            self.on_customer_selected(0)
            
    def create_info_label(self, text):
        """Helper method to create consistently styled labels for customer info"""
        label = QLabel(text)
        label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 3px;
            }
        """)
        return label