from helper import StyledWidget
from DatabaseManager import DatabaseManager
import sqlite3
import re
import csv
from PyQt5.QtWidgets import (QPushButton, QLineEdit, QFormLayout, QMessageBox, 
                           QLabel, QFileDialog, QHBoxLayout, QComboBox, QVBoxLayout, QSizePolicy, QFrame, QCompleter)
from PyQt5.QtCore import Qt

class RegisterCustomerPage(StyledWidget):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent, with_back_button=True, title="Register Customer", switch_page_callback=switch_page_callback)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()  # Main layout for left (register) & right (edit) sections
        
        # Left section: Register customer
        register_layout = self.create_register_section()
        layout.addLayout(register_layout)

        # Add vertical separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)  # Vertical line
        separator.setFrameShadow(QFrame.Sunken)  # Slight shadow effect
        separator.setStyleSheet("border: 1px solid #000000; margin: 0 20px;")  # Thin border & spacing
        layout.addWidget(separator)

        # Right section: Edit customer
        edit_layout = self.create_edit_section()
        layout.addLayout(edit_layout)  # Now it correctly adds a QVBoxLayout

        self.content_layout.addLayout(layout)
        self.content_layout.addStretch(1)

        self.load_customers()

    def create_register_section(self):
        """Creates the registration section UI"""
        register_layout = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        input_width = 300

        heading_label = QLabel("Register Customer")
        heading_label.setAlignment(Qt.AlignLeft)
        heading_label.setStyleSheet("""
            background-color: #f0f0f0; 
            border: 2px solid #cccccc; 
            border-radius: 8px; 
            padding: 8px; 
            font-size: 16px; 
            font-weight: bold;
        """)
        register_layout.addWidget(heading_label, alignment=Qt.AlignLeft)

        # Input fields
        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()

        for field in [self.name_input, self.phone_input, self.address_input]:
            field.setFixedWidth(input_width)

        # Error labels
        self.name_error = QLabel()
        self.phone_error = QLabel()
        self.address_error = QLabel()

        for label in [self.name_error, self.phone_error, self.address_error]:
            label.setStyleSheet("color: red; font-size: 12px;")

        # Add to layout
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("", self.name_error)
        form_layout.addRow("Phone:", self.phone_input)
        form_layout.addRow("", self.phone_error)
        form_layout.addRow("Address:", self.address_input)
        form_layout.addRow("", self.address_error)

        register_layout.addLayout(form_layout)

        # Submit button
        submit_btn = QPushButton("Register Customer")
        submit_btn.setFixedWidth(input_width)
        submit_btn.clicked.connect(self.register_customer)
        register_layout.addWidget(submit_btn)

        # Add separator
        separator = QLabel("─" * 50)
        separator.setStyleSheet("color: #cccccc;")
        register_layout.addWidget(separator)

        # CSV Upload Section
        csv_layout = QHBoxLayout()
        self.csv_label = QLabel("Or upload customers via CSV:")
        self.csv_label.setStyleSheet("font-weight: bold;")
        csv_layout.addWidget(self.csv_label)
        
        self.upload_btn = QPushButton("Upload CSV")
        self.upload_btn.setFixedWidth(input_width)
        self.upload_btn.clicked.connect(self.upload_csv)
        csv_layout.addWidget(self.upload_btn)
        
        csv_layout.addStretch()
        register_layout.addLayout(csv_layout)

        register_layout.addStretch(1)

        return register_layout

    def create_edit_section(self):
        """Creates the edit section UI"""
        edit_layout = QVBoxLayout()

        heading_label = QLabel("Edit Customer Details")
        heading_label.setAlignment(Qt.AlignCenter)
        heading_label.setStyleSheet("""
            background-color: #f0f0f0; 
            border: 2px solid #cccccc; 
            border-radius: 8px; 
            padding: 8px; 
            font-size: 16px; 
            font-weight: bold;
        """)
        heading_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        edit_layout.addWidget(heading_label, alignment=Qt.AlignLeft)

        # Increase spacing between heading and dropdown
        edit_layout.addSpacing(15)  

        # Create dropdown with search function
        self.customer_dropdown = QComboBox()
        self.customer_dropdown.setFixedWidth(300)
        self.customer_dropdown.setEditable(True)  # Make it editable to allow search
        self.customer_dropdown.setInsertPolicy(QComboBox.NoInsert)  # Don't add entered text as a new item
        self.customer_dropdown.completer().setCompletionMode(QCompleter.PopupCompletion)  # Show popup with matching items
        self.customer_dropdown.completer().setFilterMode(Qt.MatchContains)  # Match if text appears anywhere
        self.customer_dropdown.editTextChanged.connect(self.filter_customers)  # Connect to filter function
        self.customer_dropdown.currentIndexChanged.connect(self.load_customer_details)

        edit_layout.addWidget(self.customer_dropdown)

        # Edit form
        form_layout = QFormLayout()
        self.edit_name_input = QLineEdit()
        self.edit_phone_input = QLineEdit()
        self.edit_address_input = QLineEdit()

        for field in [self.edit_name_input, self.edit_phone_input, self.edit_address_input]:
            field.setFixedWidth(300)

        # Error labels for the edit section
        self.edit_name_error = QLabel()
        self.edit_phone_error = QLabel()
        self.edit_address_error = QLabel()

        for label in [self.edit_name_error, self.edit_phone_error, self.edit_address_error]:
            label.setStyleSheet("color: red; font-size: 12px;")

        form_layout.addRow("Name:", self.edit_name_input)
        form_layout.addRow("", self.edit_name_error)
        form_layout.addRow("Phone:", self.edit_phone_input)
        form_layout.addRow("", self.edit_phone_error)
        form_layout.addRow("Address:", self.edit_address_input)
        form_layout.addRow("", self.edit_address_error)

        edit_layout.addLayout(form_layout)

        # Increase vertical spacing
        edit_layout.addSpacing(20)  

        # Save button
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setFixedWidth(300)
        self.save_btn.clicked.connect(self.save_customer_changes)
        edit_layout.addWidget(self.save_btn)

        return edit_layout
    
    def filter_customers(self, text):
        """Filter customers as user types in the dropdown"""
        if not hasattr(self, 'all_customers_data'):
            # First time, store all customers
            self.all_customers_data = []
            for i in range(self.customer_dropdown.count()):
                name = self.customer_dropdown.itemText(i)
                id = self.customer_dropdown.itemData(i)
                customer = DatabaseManager.get_customer_by_id(id)
                if customer:
                    self.all_customers_data.append({
                        'id': id,
                        'name': customer['name'],
                        'phone': customer['phone'] or '',
                        'address': customer['address'] or '',
                        'display': name
                    })
        
        # Clear current items except the one being edited
        current_text = self.customer_dropdown.currentText()
        self.customer_dropdown.blockSignals(True)
        self.customer_dropdown.clear()
        
        # Filter and add matching items
        for customer in self.all_customers_data:
            if (text.lower() in customer['name'].lower() or 
                text.lower() in customer['phone'].lower() or 
                text.lower() in customer['address'].lower()):
                self.customer_dropdown.addItem(customer['display'], customer['id'])
        
        self.customer_dropdown.setEditText(current_text)
        self.customer_dropdown.blockSignals(False)


    def validate_csv_row(self, row, row_number):
        """Validate a single row from CSV"""
        row_number -= row_number
        errors = []
        
        # Name validation
        name = row[0].strip()
        if not name or len(name) < 2:
            errors.append(f"Row {row_number}: Invalid name (must be at least 2 characters)")

        # Phone validation - only if provided
        phone = row[2].strip()
        if phone:
            if not re.match(r'^\d{10}$', phone):
                errors.append(f"Row {row_number}: Invalid phone number (must be 10 digits)")

        # Address validation
        address = row[3].strip()
        if address:
            if len(address) < 5:
                errors.append(f"Row {row_number}: Invalid address (must be at least 5 characters)")

        return errors, (name, phone, address)

    def upload_csv(self):
        """Handle CSV file upload and processing"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_name:
            return

        try:
            valid_rows = []
            all_errors = []
            duplicates = set()
            
            with open(file_name, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                next(csv_reader, None)  # Skip header row
                
                for row_number, row in enumerate(csv_reader, 2):  # Start at 2 to account for header
                    if len(row) < 4:
                        all_errors.append(f"Row {row_number}: Insufficient columns")
                        continue
                        
                    errors, validated_data = self.validate_csv_row(row, row_number)
                    
                    if errors:
                        all_errors.extend(errors)
                    else:
                        # Check for duplicates within the CSV
                        account_number = validated_data[1]
                        phone = validated_data[2]
                        
                        if account_number in duplicates:
                            all_errors.append(f"Row {row_number}: Duplicate account number")
                        elif phone in duplicates:
                            all_errors.append(f"Row {row_number}: Duplicate phone number")
                        else:
                            duplicates.add(account_number)
                            duplicates.add(phone)
                            valid_rows.append(validated_data)

            if all_errors:
                error_msg = "\n".join(all_errors)
                QMessageBox.warning(self, "Validation Errors", 
                                  f"Found the following errors:\n\n{error_msg}")
                return

            # Insert valid rows into database
            success_count = 0
            error_count = 0
            
            query = """
            INSERT INTO Customers (name, phone, address) 
            VALUES (?, ?, ?)
            """
            
            for row in valid_rows:
                try:
                    cursor = DatabaseManager.execute_query(query, row)
                    if cursor:
                        success_count += 1
                    else:
                        error_count += 1
                except sqlite3.IntegrityError:
                    error_count += 1
                    all_errors.append(f"Duplicate account number or phone: {row[1]}, {row[2]}")

            result_message = f"Successfully imported {success_count} customers.\n"
            if error_count > 0:
                result_message += f"Failed to import {error_count} customers."
                if all_errors:
                    result_message += "\n\nErrors:\n" + "\n".join(all_errors)
                QMessageBox.warning(self, "Import Results", result_message)
            else:
                QMessageBox.information(self, "Success", result_message)
                self.load_customers() 

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error processing CSV file:\n{str(e)}")

    def validate_input(self, name, phone, address, is_edit=False):
        """Validates input fields separately for Register & Edit sections."""
        if is_edit:
            self.edit_name_error.clear()
            self.edit_phone_error.clear()
            self.edit_address_error.clear()
        else:
            self.name_error.clear()
            self.phone_error.clear()
            self.address_error.clear()

        is_valid = True

        # Name validation
        if not name or len(name) < 2:
            error_msg = "Name must be at least 2 characters"
            if is_edit:
                self.edit_name_error.setText(error_msg)
            else:
                self.name_error.setText(error_msg)
            is_valid = False

        # Phone validation: only validate if provided
        if phone:  # Only validate if phone is not empty
            phone_regex = r'^[1-9]\d{9}$'
            if not re.match(phone_regex, phone):
                error_msg = "Phone number must be 10 digits and cannot start with 0"
                if is_edit:
                    self.edit_phone_error.setText(error_msg)
                else:
                    self.phone_error.setText(error_msg)
                is_valid = False

        # Address validation (optional)
        if address and len(address) < 5:
            error_msg = "Address must be at least 5 characters"
            if is_edit:
                self.edit_address_error.setText(error_msg)
            else:
                self.address_error.setText(error_msg)
            is_valid = False

        return is_valid

    def register_customer(self):
        """Registers a new customer"""
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()

        if not self.validate_input(name, phone, address):
            return

        query = """
        INSERT INTO Customers (name, phone, address) 
        VALUES (?, ?, ?)
        """

        try:
            cursor = DatabaseManager.execute_query(query, (name, phone, address))
            if cursor:
                QMessageBox.information(self, "Success", "Customer registered successfully!")
                self.name_input.clear()
                self.phone_input.clear()
                self.address_input.clear()
                self.load_customers()  # Refresh dropdown
            else:
                QMessageBox.warning(self, "Error", "Failed to register customer.")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Phone number already exists.")

    def load_customers(self):
        """Loads customer names into dropdown"""
        self.customer_dropdown.clear()
        customers = DatabaseManager.get_all_customers()
        for customer in customers:
            self.customer_dropdown.addItem(f"{customer[1]}", customer[0])
        
        # Reset stored customers data whenever we reload
        if hasattr(self, 'all_customers_data'):
            delattr(self, 'all_customers_data')

    def load_customer_details(self):
        """Loads customer details into the edit form"""
        customer_id = self.customer_dropdown.currentData()
        if not customer_id:
            return

        customer = DatabaseManager.get_customer_by_id(customer_id)
        if customer:
            self.edit_name_input.setText(customer["name"])
            self.edit_phone_input.setText(customer["phone"] if customer["phone"] else "")
            self.edit_address_input.setText(customer["address"] if customer["address"] else "")

    def save_customer_changes(self):
        """Updates customer details"""
        customer_id = self.customer_dropdown.currentData()
        if not customer_id:
            QMessageBox.warning(self, "Error", "Please select a customer to edit.")
            return

        name = self.edit_name_input.text().strip()
        phone = self.edit_phone_input.text().strip()
        address = self.edit_address_input.text().strip()

        if not self.validate_input(name, phone, address, is_edit=True):
            return

        if DatabaseManager.update_customer(customer_id, name, phone, address):
            QMessageBox.information(self, "Success", "Customer details updated successfully!")
            self.load_customers()  # Refresh dropdown
        else:
            QMessageBox.warning(self, "Error", "Failed to update customer. Phone might already exist.")
