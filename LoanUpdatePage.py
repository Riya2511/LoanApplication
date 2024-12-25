from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import (
    QPushButton, QLineEdit, QFormLayout, QMessageBox, QLabel,
    QHBoxLayout, QComboBox, QGroupBox, QVBoxLayout, QTableWidget,
    QTableWidgetItem
)
from helper import StyledWidget
from DatabaseManager import DatabaseManager
from datetime import datetime

class LoanUpdatePage(StyledWidget):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent, with_back_button=True, title="Repay Loan", switch_page_callback=switch_page_callback)
        self.selected_customer_id = None
        self.current_loan_id = None
        self.customer_info_group = None
        self.update_group = None
        self.assets_table = None
        self.repayment_table = None
        self.init_ui()

    def init_ui(self):
        # Customer Selection Section
        customer_layout = QHBoxLayout()
        self.customer_dropdown = QComboBox()
        self.customer_dropdown.setFixedWidth(300)
        customer_layout.addWidget(QLabel("Select Customer:"))
        customer_layout.addWidget(self.customer_dropdown)
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

        # Loan Table Section
        self.loan_table = QTableWidget()
        self.loan_table.setColumnCount(6)
        self.loan_table.setHorizontalHeaderLabels(
            ["Loan Date", "Total Assets", "Total Weight (g)", "Total Amount (₹)", "Amount Due (₹)", ""]
        )
        self.loan_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.loan_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.loan_table.setSelectionMode(QTableWidget.SingleSelection)
        self.loan_table.setFixedHeight(200)
        self.content_layout.addWidget(self.loan_table)

        # Assets and Payments Section (hidden by default)
        self.update_group = QGroupBox("Loan Assets and Payments")
        self.update_group.setVisible(False)
        update_layout = QVBoxLayout()

        # Assets Table
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(5)
        self.assets_table.setHorizontalHeaderLabels(
            ["Asset Description", "Weight (g)", "Amount Paid (₹)", "Interest (₹)", ""]
        )
        update_layout.addWidget(self.assets_table)

        # Repayment History
        repayment_label = QLabel("Repayment History:")
        update_layout.addWidget(repayment_label)
        
        self.repayment_table = QTableWidget()
        self.repayment_table.setColumnCount(5)
        self.repayment_table.setHorizontalHeaderLabels(
            ["Payment Date", "Asset", "Amount Paid (₹)", "Interest Paid (₹)", "Remaining (₹)"]
        )
        self.repayment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        update_layout.addWidget(self.repayment_table)

        button_layout = QHBoxLayout()
        self.delete_button = QPushButton("Delete Loan")
        self.delete_button.setFixedWidth(100)
        self.delete_button.setFixedHeight(25)
        self.delete_button.clicked.connect(self.delete_loan_entry)
        self.delete_button.setStyleSheet("""
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
        
        self.cancel_button = QPushButton("Close")
        self.cancel_button.setFixedWidth(100)
        self.cancel_button.setFixedHeight(25)
        self.cancel_button.clicked.connect(self.cancel_update)
        self.cancel_button.setStyleSheet("""
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
        
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.cancel_button)
        update_layout.addLayout(button_layout)

        self.update_group.setLayout(update_layout)
        self.content_layout.addWidget(self.update_group)

        self.customer_dropdown.currentIndexChanged.connect(self.on_customer_selected)
        self.content_layout.addStretch(1)

    def populate_assets_table(self, loan_id):
        """Populate assets table with input fields for payments."""
        # Get all assets and filter out those that have been repaid
        assets = DatabaseManager.fetch_loan_assets(loan_id)
        repaid_assets = DatabaseManager.get_repaid_assets(loan_id)  # You'll need to add this method
        
        # Filter out repaid assets
        unrepaid_assets = [(desc, weight) for desc, weight in assets 
                          if desc not in repaid_assets]
        
        self.assets_table.setRowCount(len(unrepaid_assets))
        
        for row_idx, (description, weight) in enumerate(unrepaid_assets):
            # Asset description
            self.assets_table.setItem(row_idx, 0, QTableWidgetItem(description))
            # Weight
            self.assets_table.setItem(row_idx, 1, QTableWidgetItem(f"{weight:,.2f}"))
            
            # Amount paid input
            amount_input = QLineEdit()
            amount_input.setPlaceholderText("Enter amount")
            self.assets_table.setCellWidget(row_idx, 2, amount_input)
            
            # Interest input
            interest_input = QLineEdit()
            interest_input.setPlaceholderText("Enter interest")
            self.assets_table.setCellWidget(row_idx, 3, interest_input)
            
            # Repay button
            repay_button = QPushButton("Repay")
            repay_button.setEnabled(False)
            repay_button.clicked.connect(lambda checked, r=row_idx: self.handle_repayment(r))
            repay_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 15px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:enabled:hover {
                    background-color: #45a049;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                }
            """)

            self.assets_table.setCellWidget(row_idx, 4, repay_button)
            
            # Connect input validation
            amount_input.textChanged.connect(
                lambda text, r=row_idx: self.validate_inputs(r)
            )
            interest_input.textChanged.connect(
                lambda text, r=row_idx: self.validate_inputs(r)
            )

    def populate_repayment_table(self, loan_id):
        """Populate the repayment table with payment history for a specific loan."""
        self.repayment_table.setRowCount(0)
        repayments = DatabaseManager.fetch_loan_payments(loan_id)
        
        if repayments:
            for row_idx, repayment in enumerate(repayments):
                self.repayment_table.insertRow(row_idx)
                
                # Format payment date
                payment_date = datetime.strptime(repayment['payment_date'], "%Y-%m-%d %H:%M:%S")
                formatted_date = payment_date.strftime("%d-%m-%Y %H:%M:%S")
                
                # Add payment details to table
                self.repayment_table.setItem(row_idx, 0, QTableWidgetItem(formatted_date))
                self.repayment_table.setItem(row_idx, 1, QTableWidgetItem(repayment.get("asset_description", "")))
                self.repayment_table.setItem(row_idx, 2, QTableWidgetItem(f"{float(repayment['payment_amount']):,.2f}"))
                self.repayment_table.setItem(row_idx, 3, QTableWidgetItem(f"{float(repayment['interest_amount']):,.2f}"))
                self.repayment_table.setItem(row_idx, 4, QTableWidgetItem(f"{float(repayment['amount_left']):,.2f}"))
        else:
            self.repayment_table.setRowCount(1)
            self.repayment_table.setItem(0, 0, QTableWidgetItem("No repayments made"))
            for i in range(1, 5):
                self.repayment_table.setItem(0, i, QTableWidgetItem("-"))

    def validate_inputs(self, row):
        """Validate payment inputs and enable/disable repay button."""
        amount_input = self.assets_table.cellWidget(row, 2)
        interest_input = self.assets_table.cellWidget(row, 3)
        repay_button = self.assets_table.cellWidget(row, 4)
        
        try:
            amount = float(amount_input.text() or 0)
            interest = float(interest_input.text() or 0)
            repay_button.setEnabled(amount > 0 and interest >= 0)
        except ValueError:
            repay_button.setEnabled(False)

    def handle_repayment(self, row):
        """Process asset repayment."""
        try:
            amount_input = self.assets_table.cellWidget(row, 2)
            interest_input = self.assets_table.cellWidget(row, 3)
            amount = float(amount_input.text())
            interest = float(interest_input.text())
            asset_desc = self.assets_table.item(row, 0).text()

            # Validate total payments don't exceed loan amount
            total_paid = DatabaseManager.get_total_loan_payments(self.current_loan_id)
            loan_amount = DatabaseManager.get_loan_amount(self.current_loan_id)
            
            if total_paid + amount > loan_amount:
                raise ValueError(f"Total payments would exceed loan amount (₹{loan_amount:,.2f})")

            # Insert payment
            DatabaseManager.insert_loan_payment(
                self.current_loan_id,
                payment_amount=amount,
                interest_amount=interest,
                amount_left=loan_amount - (total_paid + amount),
                asset_description=asset_desc
            )

            # Update loan paid amount
            DatabaseManager.update_loan_payment(self.current_loan_id, amount)
            
            # Refresh UI
            self.populate_assets_table(self.current_loan_id)  # This will now hide the repaid asset
            self.populate_repayment_table(self.current_loan_id)
            self.populate_loans_table()
            
            QMessageBox.information(self, "Success", "Payment recorded successfully!")
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process payment: {str(e)}")

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

    def on_customer_selected(self, index):
        """Display loans for the selected customer."""
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
        self.loan_table.setRowCount(0)
        loans = DatabaseManager.fetch_loans_for_customer(self.selected_customer_id)
        for row_idx, loan in enumerate(loans):
            self.loan_table.insertRow(row_idx)
            for col_idx, value in enumerate(loan[:-2]):
                if col_idx == 0:
                    value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    value = value.strftime("%d-%m-%Y %H:%M:%S")
                elif col_idx in (2, 3, 4):
                    value = f"{float(value):,.2f}" if value else "0.00"
                self.loan_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            
            update_button = QPushButton("Update Amount")
            update_button.clicked.connect(lambda checked, lid=loan[-2]: self.show_update_section(lid))
            self.loan_table.setCellWidget(row_idx, 5, update_button)

    def show_update_section(self, loan_id):
        """Show the update section with loan details and assets."""
        self.current_loan_id = loan_id
        self.update_group.setVisible(True)
        
        self.populate_assets_table(loan_id)
        self.populate_repayment_table(loan_id)

    def delete_loan_entry(self):
        """Delete the selected loan entry."""
        msg_box = QMessageBox(
            QMessageBox.Question,
            "Confirm Delete",
            "Are you sure you want to delete this loan?",
            QMessageBox.Yes | QMessageBox.No,
            self
        )
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QPushButton {
                min-width: 80px;
                min-height: 24px;
                padding: 4px 8px;
                margin: 8px;
                border-radius: 4px;
                background-color: #4CAF50;
                color: white;
            }
            QMessageBox QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        if msg_box.exec_() == QMessageBox.Yes:
            try:
                DatabaseManager.delete_loan(self.current_loan_id)
                QMessageBox.information(self, "Success", "Loan deleted successfully!")
                self.cancel_update()
                self.populate_loans_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete loan: {str(e)}")

    def cancel_update(self):
        """Hide the update section."""
        self.update_group.setVisible(False)