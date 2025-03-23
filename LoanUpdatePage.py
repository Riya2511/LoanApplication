from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import (
    QPushButton, QLineEdit, QFormLayout, QMessageBox, QLabel,
    QHBoxLayout, QComboBox, QGroupBox, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QDateEdit, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import QDate
from helper import StyledWidget
from DatabaseManager import DatabaseManager
from datetime import datetime

class PaymentEditDialog(QDialog):
    def __init__(self, parent, payment_id, payment_data):
        super().__init__(parent)
        self.payment_id = payment_id
        self.payment_data = payment_data
        self.setWindowTitle("Edit Payment")
        self.setMinimumWidth(400)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # Date field
        self.date_edit = QDateEdit()
        self.date_edit.setDisplayFormat("dd-MM-yyyy")
        self.date_edit.setCalendarPopup(True)

        # Parse the date format
        payment_date_str = self.payment_data['payment_date']
        try:
            # Split by spaces to separate date and time
            date_part = payment_date_str.split()[0]
            # Split the date part by hyphens
            date_parts = date_part.split('-')
            # Get year, month, day
            if len(date_parts) >= 3:
                year = int(date_parts[0])
                month = int(date_parts[1])
                day = int(date_parts[2])
            else:
                # Fallback to current date if can't parse
                current_date = QDate.currentDate()
                year = current_date.year()
                month = current_date.month()
                day = current_date.day()
        except Exception:
            # Fallback to current date if error
            current_date = QDate.currentDate()
            year = current_date.year()
            month = current_date.month()
            day = current_date.day()

        # Set the date in the date editor
        self.date_edit.setDate(QDate(year, month, day))
        form_layout.addRow("Payment Date:", self.date_edit)
        
        # Asset description
        self.asset_input = QLineEdit(self.payment_data.get('asset_description', ''))
        form_layout.addRow("Asset Description:", self.asset_input)
        
        # Payment amount
        self.amount_input = QLineEdit(str(self.payment_data['payment_amount']))
        form_layout.addRow("Payment Amount (₹):", self.amount_input)
        
        # Interest amount
        self.interest_input = QLineEdit(str(self.payment_data['interest_amount']))
        form_layout.addRow("Interest Amount (₹):", self.interest_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)

    def get_updated_data(self):
        date_obj = self.date_edit.date()
        day = date_obj.day()
        month = date_obj.month()
        year = date_obj.year()
        formatted_date = f"{day} 00:00:00-{month:02d}-{year}"  # Format as "22 00:00:00-06-2024"
        
        return {
            'payment_date': formatted_date,
            'asset_description': self.asset_input.text(),
            'payment_amount': float(self.amount_input.text()),
            'interest_amount': float(self.interest_input.text())
        }

class LoanUpdatePage(StyledWidget):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent, with_back_button=True, title="Repay Loan", switch_page_callback=switch_page_callback)
        self.selected_customer_id = None
        self.current_loan_id = None
        self.customer_info_group = None
        self.update_group = None
        self.assets_table = None
        self.repayment_table = None
        self.all_customers_data = []  # Add this line
        self.init_ui()
        
        # Hide tables initially
        self.loan_table.setVisible(False)
        self.customer_info_group.setVisible(False)

    def init_ui(self):
        # Customer Selection Section
        customer_layout = QVBoxLayout()  # Change to QVBoxLayout

        # Add search box
        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("Search customers...")
        self.customer_search.setFixedWidth(300)
        self.customer_search.textChanged.connect(self.filter_customers)
        customer_layout.addWidget(self.customer_search, alignment=Qt.AlignCenter)

        # Customer dropdown (existing code)
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
        customer_layout.addWidget(self.customer_dropdown, alignment=Qt.AlignCenter)

        self.content_layout.addLayout(customer_layout)

        # Add a placeholder item
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

        # Loan Table Section
        self.loan_table = QTableWidget()
        self.loan_table.setColumnCount(7)
        self.loan_table.setHorizontalHeaderLabels(
            ["Loan Date", "Registered Reference Id", "Asset Description", "Total Weight (g)", "Total Amount (₹)", "Amount Due (₹)", ""]
        )
        self.loan_table.setColumnWidth(1, 200)
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
        self.assets_table.setColumnCount(6)  # Reduced from 7 to 6 (removed reference_id)
        self.assets_table.setHorizontalHeaderLabels([
            "Asset Description", "Weight (g)", 
            "Amount Paid (₹)", "Interest (₹)", "Payment Date", ""
        ])
        self.assets_table.setColumnWidth(0, 250)  # Asset Description column
        self.assets_table.setColumnWidth(4, 120)  # Date column
        update_layout.addWidget(self.assets_table)

        # Repayment History
        repayment_layout = QVBoxLayout()
        repayment_header_layout = QHBoxLayout()
        repayment_label = QLabel("Repayment History:")
        repayment_header_layout.addWidget(repayment_label)
        repayment_header_layout.addStretch()
        repayment_layout.addLayout(repayment_header_layout)
        
        self.repayment_table = QTableWidget()
        self.repayment_table.setColumnCount(6)  # Added one column for edit button
        self.repayment_table.setHorizontalHeaderLabels(
            ["Payment Date", "Asset", "Amount Paid (₹)", "Interest Paid (₹)", "Remaining (₹)", ""]
        )
        self.repayment_table.setEditTriggers(QTableWidget.NoEditTriggers)
        repayment_layout.addWidget(self.repayment_table)
        
        update_layout.addLayout(repayment_layout)

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
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
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
        assets = DatabaseManager.fetch_loan_assets(loan_id)
        # repaid_assets = DatabaseManager.get_repaid_assets(loan_id)
        # unrepaid_assets = [(desc, weight) for desc, weight in assets 
        #                   if desc not in repaid_assets]
        
        self.assets_table.setRowCount(len(assets))
        
        for row_idx, (description, weight) in enumerate(assets):
            # Asset description
            self.assets_table.setItem(row_idx, 0, QTableWidgetItem(description))
            self.assets_table.setItem(row_idx, 1, QTableWidgetItem(f"{weight:,.2f}"))
            
            # Amount paid input
            amount_input = QLineEdit()
            amount_input.setPlaceholderText("Enter amount")
            self.assets_table.setCellWidget(row_idx, 2, amount_input)
            
            # Interest input
            interest_input = QLineEdit()
            interest_input.setPlaceholderText("Enter interest")
            self.assets_table.setCellWidget(row_idx, 3, interest_input)

            # Date input
            date_input = QDateEdit()
            date_input.setDisplayFormat("dd-MM-yyyy")
            date_input.setCalendarPopup(True)
            date_input.setDate(QDate.currentDate())
            date_input.setMinimumDate(QDate(2000, 1, 1))
            date_input.setMaximumDate(QDate.currentDate())
            self.assets_table.setCellWidget(row_idx, 4, date_input)
            
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
            self.assets_table.setCellWidget(row_idx, 5, repay_button)
            
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
            repayments = sorted(repayments, key=lambda repayment: repayment['payment_date'], reverse=True)
            for row_idx, repayment in enumerate(repayments):
                self.repayment_table.insertRow(row_idx)
                
                # Parse the unusual date format
                payment_date_str = repayment['payment_date']
                # Extract day, month, year
                day = payment_date_str.split()[0]  # Get "22" 
                month_year = payment_date_str.split('-')[-2:]  # Get ["06", "2024"]
                month = month_year[0]
                year = month_year[1]
                formatted_date = f"{day}-{month}-{year}"  # "22-06-2024"
                
                self.repayment_table.setItem(row_idx, 0, QTableWidgetItem(formatted_date))
                self.repayment_table.setItem(row_idx, 1, QTableWidgetItem(repayment.get("asset_description", "")))
                self.repayment_table.setItem(row_idx, 2, QTableWidgetItem(f"{float(repayment['payment_amount']):,.2f}"))
                self.repayment_table.setItem(row_idx, 3, QTableWidgetItem(f"{float(repayment['interest_amount']):,.2f}"))
                self.repayment_table.setItem(row_idx, 4, QTableWidgetItem(f"{float(repayment['amount_left']):,.2f}"))
                
                # Add edit button
                edit_button = QPushButton("Edit")
                edit_button.clicked.connect(lambda checked, pid=repayment.get('payment_id', row_idx), 
                                         pdata=repayment: self.edit_payment(pid, pdata))
                edit_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border-radius: 10px;
                        font-weight: bold;
                        font-size: 10px;
                        padding: 2px 5px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                self.repayment_table.setCellWidget(row_idx, 5, edit_button)
        else:
            self.repayment_table.setRowCount(1)
            self.repayment_table.setItem(0, 0, QTableWidgetItem("No repayments made"))
            for i in range(1, 6):  # Adjusted for extra column
                self.repayment_table.setItem(0, i, QTableWidgetItem("-"))

    def edit_payment(self, payment_id, payment_data):
        """Open dialog to edit a payment."""
        dialog = PaymentEditDialog(self, payment_id, payment_data)
        if dialog.exec_() == QDialog.Accepted:
            updated_data = dialog.get_updated_data()
            try:
                # Update the payment in the database
                self.update_payment(payment_id, updated_data)
                
                # Refresh the tables
                self.populate_repayment_table(self.current_loan_id)
                self.populate_loans_table()
                
                # Update delete button state
                amount_due = DatabaseManager.get_loan_amount_due(self.current_loan_id)
                self.delete_button.setEnabled(amount_due <= 0)
                if amount_due > 0:
                    self.delete_button.setToolTip("Loan can only be deleted when fully repaid (amount due ≤ 0)")
                else:
                    self.delete_button.setToolTip("Delete this loan")
                
                QMessageBox.information(self, "Success", "Payment updated successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update payment: {str(e)}")
    
    def update_payment(self, payment_id, updated_data):
        """Update a payment in the database."""
        # Call the database method to update the payment
        # Note: You'll need to add this method to DatabaseManager
        DatabaseManager.update_loan_payment_record(
            payment_id, 
            updated_data['payment_date'],
            updated_data['payment_amount'],
            updated_data['interest_amount'],
            updated_data['asset_description']
        )
        
        # Also update the total paid amount on the loan
        current_payments = DatabaseManager.fetch_loan_payments(self.current_loan_id)
        total_paid = sum(float(payment['payment_amount']) for payment in current_payments)
        
        # Update loan status based on total paid
        loan_amount = DatabaseManager.get_loan_amount(self.current_loan_id)
        loan_status = "Completed" if total_paid >= loan_amount else "Pending"
        
        # Update the loan record with new paid amount and status
        DatabaseManager.update_loan_total_paid(self.current_loan_id, total_paid, loan_status)

    def validate_inputs(self, row):
        """Validate payment inputs and enable/disable repay button."""
        amount_input = self.assets_table.cellWidget(row, 2)  # Updated index
        interest_input = self.assets_table.cellWidget(row, 3)  # Updated index
        repay_button = self.assets_table.cellWidget(row, 5)  # Updated index
        
        try:
            amount = float(amount_input.text() or 0)
            interest = float(interest_input.text() or 0)
            repay_button.setEnabled(amount > 0 and interest >= 0)
        except ValueError:
            repay_button.setEnabled(False)

    def handle_repayment(self, row):
        """Process asset repayment."""
        try:
            amount_input = self.assets_table.cellWidget(row, 2)  # Updated index
            interest_input = self.assets_table.cellWidget(row, 3)  # Updated index
            date_input = self.assets_table.cellWidget(row, 4)  # Updated index
            
            amount = float(amount_input.text())
            interest = float(interest_input.text())
            payment_date = date_input.date().toPyDate()
            asset_desc = self.assets_table.item(row, 0).text()

            # Validate total payments don't exceed loan amount
            total_paid = DatabaseManager.get_total_loan_payments(self.current_loan_id)
            loan_amount = DatabaseManager.get_loan_amount(self.current_loan_id)
            
            if total_paid + amount > loan_amount:
                raise ValueError(f"Total payments would exceed loan amount (₹{loan_amount:,.2f})")

            # Insert payment with the selected date
            DatabaseManager.insert_loan_payment(
                self.current_loan_id,
                payment_amount=amount,
                interest_amount=interest,
                amount_left=loan_amount - (total_paid + amount),
                asset_description=asset_desc,
                payment_date=payment_date
            )

            # Update loan paid amount
            DatabaseManager.update_loan_payment(self.current_loan_id, amount)
            
            # Refresh UI
            self.populate_assets_table(self.current_loan_id)
            self.populate_repayment_table(self.current_loan_id)
            self.populate_loans_table()
            amount_due = DatabaseManager.get_loan_amount_due(self.current_loan_id)
            self.delete_button.setEnabled(amount_due <= 0)
            if amount_due > 0:
                self.delete_button.setToolTip("Loan can only be deleted when fully repaid (amount due ≤ 0)")
            else:
                self.delete_button.setToolTip("Delete this loan")
            
            QMessageBox.information(self, "Success", "Payment recorded successfully!")
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process payment: {str(e)}")

    def showEvent(self, event: QEvent):
        """Handle page load event and refresh customer data."""
        if event.type() == QEvent.Show:
            self.populate_customer_dropdown()
            # Reset selection and hide elements
            self.customer_dropdown.setCurrentIndex(0)
            self.loan_table.setVisible(False)
            self.customer_info_group.setVisible(False)
            self.update_group.setVisible(False)
        super().showEvent(event)

    def populate_customer_dropdown(self):
        """Populate the dropdown with the latest customer data."""
        self.customer_dropdown.clear()
        self.all_customers_data = []  # Clear existing data
        
        # Add the initial placeholder
        self.customer_dropdown.addItem("Select a customer", None)
        
        customers = DatabaseManager.get_all_customers()
        if customers:
            for customer_id, name, phone in customers:
                display_text = f"{name} - {phone}" if phone else f"{name}"
                self.customer_dropdown.addItem(display_text, customer_id)
                # Store customer data for filtering
                self.all_customers_data.append({
                    'id': customer_id,
                    'name': name,
                    'phone': phone if phone else '',
                    'display': display_text
                })

    def on_customer_selected(self, index):
        """Display loans for the selected customer."""
        # Get the customer_id from the current selection
        self.selected_customer_id = self.customer_dropdown.currentData()
        
        # Show/hide elements based on selection
        has_selection = self.selected_customer_id is not None
        self.loan_table.setVisible(has_selection)
        self.customer_info_group.setVisible(has_selection)
        
        # Clear tables if no selection
        if not has_selection:
            self.loan_table.setRowCount(0)
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
        
        if not self.selected_customer_id:
            return 

        customer_info = DatabaseManager.get_customer_by_id(self.selected_customer_id)
        if customer_info:
            for key, value in customer_info.items():
                if key == "customer_id" or not value:
                    continue
                label = QLabel(f"{key.replace('_', ' ').title()}: {value}")
                customer_info_layout.addWidget(label)

    def populate_loans_table(self):
        """Populate the loan table with loans for the selected customer."""
        self.loan_table.setRowCount(0)  # Clear existing rows
        
        if not self.selected_customer_id:
            return 
            
        loans = DatabaseManager.fetch_loans_for_customer(self.selected_customer_id)
        
        if not loans:
            return
        loans = sorted(loans, key=lambda loan: loan[0], reverse=True)
        for row_idx, loan_data in enumerate(loans):
            self.loan_table.insertRow(row_idx)
            
            # Unpack loan data
            (loan_date, asset_descriptions, total_weight, loan_amount, 
            amount_due, interest_amount, registered_reference_id, loan_id, _) = loan_data
            
            # Parse the date format "2022-09-21-09-21 00:00:00"
            loan_date_str = loan_date
            try:
                # Split by spaces to separate date and time
                date_part = loan_date_str.split()[0]
                # Split the date part by hyphens
                date_parts = date_part.split('-')
                # Get year, month, day
                if len(date_parts) >= 3:
                    year = date_parts[0]
                    month = date_parts[1]
                    day = date_parts[2]
                    formatted_date = f"{day}-{month}-{year}"  # "21-09-2022"
                else:
                    formatted_date = loan_date_str  # Fallback to original if can't parse
            except Exception:
                formatted_date = loan_date_str  # Fallback to original if error
            
            # Set table items
            self.loan_table.setItem(row_idx, 0, QTableWidgetItem(formatted_date))
            self.loan_table.setItem(row_idx, 1, QTableWidgetItem(registered_reference_id))
            self.loan_table.setItem(row_idx, 2, QTableWidgetItem(asset_descriptions or ""))
            self.loan_table.setItem(row_idx, 3, QTableWidgetItem(f"{float(total_weight):,.2f}" if total_weight else "0.00"))
            self.loan_table.setItem(row_idx, 4, QTableWidgetItem(f"{float(loan_amount):,.2f}" if loan_amount else "0.00"))
            self.loan_table.setItem(row_idx, 5, QTableWidgetItem(f"{float(amount_due):,.2f}" if amount_due else "0.00"))
            
            # Add update button
            update_button = QPushButton("Repay Amount")
            update_button.clicked.connect(lambda checked, lid=loan_id: self.show_update_section(lid))
            self.loan_table.setCellWidget(row_idx, 6, update_button)

    def show_update_section(self, loan_id):
        """Show the update section with loan details and assets."""
        self.current_loan_id = loan_id
        self.update_group.setVisible(True)
        
        # Populate both tables with loan data
        self.populate_assets_table(loan_id)
        self.populate_repayment_table(loan_id)
        
        # Check amount due for this loan and enable/disable delete button
        amount_due = DatabaseManager.get_loan_amount_due(loan_id)
        self.delete_button.setEnabled(amount_due <= 0)
        
        # Optionally add a tooltip to inform the user why the button is disabled
        if amount_due > 0:
            self.delete_button.setToolTip("Loan can only be deleted when fully repaid (amount due ≤ 0)")
        else:
            self.delete_button.setToolTip("Delete this loan")

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
        self.current_loan_id = None  # Reset the current loan ID

    def filter_customers(self):
        """Filter dropdown options based on search box input"""
        search_text = self.customer_search.text().strip().lower()

        self.customer_dropdown.blockSignals(True)
        self.customer_dropdown.clear()
        
        # Always add the placeholder
        self.customer_dropdown.addItem("Select a customer", None)

        # Add matching customers
        matching_customers = []
        for customer in self.all_customers_data:
            if (search_text in customer['name'].lower() or 
                search_text in customer['phone'].lower()):
                matching_customers.append(customer)
                self.customer_dropdown.addItem(customer['display'], customer['id'])

        self.customer_dropdown.blockSignals(False)
        
        # If there's exactly one match, select that customer
        if len(matching_customers) == 1:
            self.customer_dropdown.setCurrentIndex(1)  # Index 1 because index 0 is the placeholder
        else:
            # Otherwise select the placeholder
            self.customer_dropdown.setCurrentIndex(0)
        