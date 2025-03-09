from helper import StyledWidget
from DatabaseManager import DatabaseManager
import sqlite3
import re
import csv
from PyQt5.QtWidgets import (QPushButton, QLineEdit, QFormLayout, QMessageBox, 
                           QLabel, QFileDialog, QHBoxLayout)
from PyQt5.QtCore import Qt

class RegisterCustomerPage(StyledWidget):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent, with_back_button=True, title="Register Customer", switch_page_callback=switch_page_callback)
        self.init_ui()

    def init_ui(self):
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        input_width = 300

        # Regular form inputs
        self.name_input = QLineEdit()
        self.name_input.setFixedWidth(input_width)
        self.phone_input = QLineEdit()
        self.phone_input.setFixedWidth(input_width)
        self.address_input = QLineEdit()
        self.address_input.setFixedWidth(input_width)

        # Error labels
        self.name_error = QLabel()
        self.name_error.setStyleSheet("color: red; font-size: 12px;")
        self.phone_error = QLabel()
        self.phone_error.setStyleSheet("color: red; font-size: 12px;")
        self.address_error = QLabel()
        self.address_error.setStyleSheet("color: red; font-size: 12px;")

        # Add fields to the form layout
        form_layout.addRow("Name:", self.name_input)
        form_layout.addRow("", self.name_error)
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

        # Add separator
        separator = QLabel("─" * 50)
        separator.setStyleSheet("color: #cccccc;")
        self.content_layout.addWidget(separator)

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
        self.content_layout.addLayout(csv_layout)

        self.content_layout.addStretch(1)


    def validate_csv_row(self, row, row_number):
        """Validate a single row from CSV"""
        row_number -= row_number
        errors = []
        
        # Name validation
        name = row[0].strip()
        if not name or len(name) < 2:
            errors.append(f"Row {row_number}: Invalid name (must be at least 2 characters)")

        # Phone validation
        phone = row[2].strip()
        if phone:
            if not re.match(r'^\d{10}$', phone):
                errors.append(f"Row {row_number}: Invalid phone number (must be 10 digits)")

        # Address validation
        address = row[3].strip()
        if address:
            if not address or len(address) < 5:
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

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error processing CSV file:\n{str(e)}")

    def validate_input(self):
        """Validate input fields"""
        self.name_error.clear()
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

        # Phone validation
        phone = self.phone_input.text().strip()
        phone_regex = r'^\d{10}$'
        if not phone:
            self.phone_error.setText("Phone is required")
            is_valid = False
        elif not re.match(phone_regex, phone):
            self.phone_error.setText("Invalid phone number")
            is_valid = False

        # Address validation
        address = self.address_input.text().strip()
        if address:
            # self.address_error.setText("Address is required")
            # is_valid = False
            if len(address) < 5:
                self.address_error.setText("Address is too short")
                is_valid = False

        return is_valid

    def register_customer(self):
        """Register customer in the database"""
        if not self.validate_input():
            return

        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.text().strip()

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
            else:
                QMessageBox.warning(self, "Error", "Failed to register customer. Please try again.")
        
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "A customer with this Account Number or Phone already exists.")
