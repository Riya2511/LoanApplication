from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import (
    QPushButton, QLineEdit, QFormLayout, QMessageBox, QLabel,
    QHBoxLayout, QComboBox, QGroupBox, QVBoxLayout, QTableWidget,
    QTableWidgetItem
)
from helper import StyledWidget
from DatabaseManager import DatabaseManager

class LoanUpdatePage(StyledWidget):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent, with_back_button=True, title="Update Loan", switch_page_callback=switch_page_callback)
        self.selected_customer_id = None
        self.customer_info_group = None
        self.update_group = None
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
        customer_info_layout = QVBoxLayout()
        self.customer_info_group.setLayout(customer_info_layout)
        self.content_layout.addWidget(self.customer_info_group)

        # Loan Table Section
        self.loan_table = QTableWidget()
        self.loan_table.setColumnCount(5)
        self.loan_table.setHorizontalHeaderLabels(
            ["Loan Date", "Asset Description", "Asset Weight (kg)", "Loan Amount (₹)", "Update"]
        )
        self.loan_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.loan_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.loan_table.setSelectionMode(QTableWidget.SingleSelection)
        self.loan_table.setFixedHeight(300)
        self.content_layout.addWidget(self.loan_table)

        # Update Section (hidden by default)
        self.update_group = QGroupBox("Update Loan Details")
        self.update_group.setVisible(False)
        update_layout = QFormLayout()

        self.asset_description_label = QLabel()
        update_layout.addRow("Asset Description:", self.asset_description_label)

        self.asset_weight_label = QLabel()
        update_layout.addRow("Asset Weight (kg):", self.asset_weight_label)

        self.loan_amount_left_label = QLabel()
        update_layout.addRow("Loan Amount Left (₹):", self.loan_amount_left_label)

        self.loan_amount_paid_input = QLineEdit()
        self.loan_amount_paid_input.setPlaceholderText("Enter Loan Amount Paid")
        update_layout.addRow("Loan Amount Paid (₹):", self.loan_amount_paid_input)

        # Repayment History Table
        self.repayment_table = QTableWidget()
        self.repayment_table.setColumnCount(3)
        self.repayment_table.setHorizontalHeaderLabels(["Payment Date", "Amount Paid (₹)", "Remaining Amount (₹)"])
        self.repayment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        update_layout.addRow("Repayment History:", self.repayment_table)

        # Buttons for update actions
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.setFixedWidth(100)
        self.save_button.setStyleSheet("margin-left: 10px; margin-right: 10px;")
        self.save_button.clicked.connect(self.save_loan_update)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setFixedWidth(100)
        self.delete_button.setStyleSheet("margin-left: 10px; margin-right: 10px;")
        self.delete_button.clicked.connect(self.delete_loan_entry)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedWidth(100)
        self.cancel_button.setStyleSheet("margin-left: 10px; margin-right: 10px;")
        self.cancel_button.clicked.connect(self.cancel_update)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.cancel_button)
        update_layout.addRow(button_layout)

        self.update_group.setLayout(update_layout)
        self.content_layout.addWidget(self.update_group)

        # Event connections
        self.customer_dropdown.currentIndexChanged.connect(self.on_customer_selected)
        self.content_layout.addStretch(1)

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
                self.customer_dropdown.addItem(f"{name} ({account_number})", customer_id)
        else:
            self.customer_dropdown.addItem("No customers found")

    def on_customer_selected(self, index):
        """Display loans for the selected customer."""
        if index < 0:
            return

        self.selected_customer_id = self.customer_dropdown.currentData()
        self.populate_loans_table()

    def populate_loans_table(self):
        """Populate the loan table with loans for the selected customer."""
        self.loan_table.setRowCount(0)
        loans = DatabaseManager.fetch_loans_for_customer(self.selected_customer_id)
        for row_idx, loan in enumerate(loans):
            self.loan_table.insertRow(row_idx)
            for col_idx, value in enumerate(loan[:-1]):  # Exclude loan ID
                self.loan_table.setItem(row_idx, col_idx, QTableWidgetItem(str(value)))
            update_button = QPushButton("Update")
            update_button.clicked.connect(lambda _, loan_id=loan[-1]: self.show_update_section(loan_id))
            self.loan_table.setCellWidget(row_idx, 4, update_button)

    def show_update_section(self, loan_id):
        """Show the update section with loan details."""
        loan_details = DatabaseManager.fetch_loan_details(loan_id)
        if loan_details:
            self.asset_description_label.setText(loan_details["asset_description"])
            self.asset_weight_label.setText(str(loan_details["asset_weight"]))
            self.loan_amount_left_label.setText(str(loan_details["loan_amount_left"]))
            self.update_group.setVisible(True)
            self.current_loan_id = loan_id  # Track the loan being updated

            repayments = DatabaseManager.fetch_loan_payments(loan_id)
            self.repayment_table.setRowCount(0)
            total_paid = 0
            if repayments:
                for row_idx, repayment in enumerate(repayments):
                    self.repayment_table.insertRow(row_idx)
                    self.repayment_table.setItem(row_idx, 0, QTableWidgetItem(str(repayment["payment_date"])))
                    self.repayment_table.setItem(row_idx, 1, QTableWidgetItem(str(repayment["payment_amount"])))
                    total_paid += repayment["payment_amount"]
            else:
                # Handle empty repayment history (no payments)
                self.repayment_table.setRowCount(1)
                self.repayment_table.setItem(0, 0, QTableWidgetItem("No repayments made"))
                self.repayment_table.setItem(0, 1, QTableWidgetItem("0"))
                self.repayment_table.setItem(0, 2, QTableWidgetItem(str(loan_details["loan_amount_left"])))

            # Calculate remaining amount
            remaining_amount = loan_details["loan_amount_left"] - total_paid
            self.loan_amount_left_label.setText(str(remaining_amount))  # Update the remaining amount label

    def save_loan_update(self):
        """Validate and save the updated loan information."""
        try:
            loan_amount_paid = float(self.loan_amount_paid_input.text())
            if loan_amount_paid <= 0:
                raise ValueError("Loan Amount Paid must be positive.")

            # Step 1: Insert the payment into the LoanPayments table
            payment_date = "CURRENT_TIMESTAMP"  # We'll use the current timestamp for the payment
            DatabaseManager.insert_loan_payment(
                loan_id=self.current_loan_id,
                payment_amount=loan_amount_paid,
                payment_date=payment_date
            )

            # Step 2: Update the loan's amount paid in Loans table
            DatabaseManager.update_loan_payment(
                loan_id=self.current_loan_id,
                amount_paid=loan_amount_paid
            )

            QMessageBox.information(self, "Success", "Loan payment updated successfully!")
            self.cancel_update()  # Hide the update section
            self.populate_loans_table()  # Refresh table
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update loan: {str(e)}")

    def delete_loan_entry(self):
        """Delete the selected loan entry."""
        confirmation = QMessageBox.question(
            self, "Confirm Delete", "Are you sure you want to delete this loan?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmation == QMessageBox.Yes:
            try:
                DatabaseManager.delete_loan(self.current_loan_id)
                QMessageBox.information(self, "Success", "Loan deleted successfully!")
                self.cancel_update()  # Hide the update section
                self.populate_loans_table()  # Refresh table
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete loan: {str(e)}")

    def cancel_update(self):
        """Hide the update section."""
        self.update_group.setVisible(False)
        self.loan_amount_paid_input.clear()