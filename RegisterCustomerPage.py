from helper import StyledWidget
from DatabaseManager import DatabaseManager
import sqlite3
import re
from PyQt5.QtWidgets import QPushButton, QLineEdit, QFormLayout, QMessageBox, QLabel

class RegisterCustomerPage(StyledWidget):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent, with_back_button=True, title="Register Customer", switch_page_callback=switch_page_callback)
        self.init_ui()

    def init_ui(self):
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        input_width = 300

        self.name_input = QLineEdit()
        self.name_input.setFixedWidth(input_width)
        self.account_number_input = QLineEdit()
        self.account_number_input.setFixedWidth(input_width)
        self.phone_input = QLineEdit()
        self.phone_input.setFixedWidth(input_width)
        self.address_input = QLineEdit()
        self.address_input.setFixedWidth(input_width)

        # Error labels
        self.name_error = QLabel()
        self.name_error.setStyleSheet("color: red; font-size: 12px;")
        self.account_number_error = QLabel()
        self.account_number_error.setStyleSheet("color: red; font-size: 12px;")
        self.phone_error = QLabel()
        self.phone_error.setStyleSheet("color: red; font-size: 12px;")
        self.address_error = QLabel()
        self.address_error.setStyleSheet("color: red; font-size: 12px;")

        # Add fields to the form layout
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("", self.name_error)
        form_layout.addRow("Account Number:", self.account_number_input)
        form_layout.addRow("", self.account_number_error)
        form_layout.addRow("Phone:", self.phone_input)
        form_layout.addRow("", self.phone_error)
        form_layout.addRow("Address:", self.address_input)
        form_layout.addRow("", self.address_error)

        self.content_layout.addLayout(form_layout)

        # Submit button
        submit_btn = QPushButton("Register Customer")
        submit_btn.setFixedWidth(input_width)
        submit_btn.clicked.connect(self.register_customer)
        self.content_layout.addWidget(submit_btn)

        self.content_layout.addStretch(1)

    def validate_input(self):
        """Validate input fields"""
        self.name_error.clear()
        self.account_number_error.clear()
        self.phone_error.clear()
        self.address_error.clear()

        is_valid = True

        # Name validation
        name = self.name_input.text().strip()
        if not name:
            self.name_error.setText("Name is required")
            is_valid = False
        elif len(name) < 2:
            self.name_error.setText("Name must be at least 2 characters")
            is_valid = False

        # Account number validation
        account_number = self.account_number_input.text().strip()
        account_number_regex = r'^\d{10,20}$'  # Example: 10 to 20 digits
        if not account_number:
            self.account_number_error.setText("Account Number is required")
            is_valid = False
        elif not re.match(account_number_regex, account_number):
            self.account_number_error.setText("Account Number must be 10-20 digits")
            is_valid = False

        # Phone validation
        phone = self.phone_input.text().strip()
        phone_regex = r'^\+?1?\d{10,12}$'
        if not phone:
            self.phone_error.setText("Phone is required")
            is_valid = False
        elif not re.match(phone_regex, phone):
            self.phone_error.setText("Invalid phone number")
            is_valid = False

        # Address validation
        address = self.address_input.text().strip()
        if not address:
            self.address_error.setText("Address is required")
            is_valid = False
        elif len(address) < 5:
            self.address_error.setText("Address is too short")
            is_valid = False

        return is_valid

    def register_customer(self):
        """Register customer in the database"""
        if not self.validate_input():
            return

        name = self.name_input.text().strip()
        account_number = self.account_number_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()

        query = """
        INSERT INTO Customers (name, account_number, phone, address) 
        VALUES (?, ?, ?, ?)
        """
        
        try:
            cursor = DatabaseManager.execute_query(query, (name, account_number, phone, address))
            if cursor:
                QMessageBox.information(self, "Success", "Customer registered successfully!")
                self.name_input.clear()
                self.account_number_input.clear()
                self.phone_input.clear()
                self.address_input.clear()
            else:
                QMessageBox.warning(self, "Error", "Failed to register customer. Please try again.")
        
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "A customer with this Account Number or Phone already exists.")
