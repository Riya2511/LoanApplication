from PyQt5.QtCore import QEvent
from helper import StyledWidget
from DatabaseManager import DatabaseManager
from PyQt5.QtWidgets import QPushButton, QLineEdit, QFormLayout, QMessageBox, QLabel, QHBoxLayout, QComboBox, QGroupBox, QVBoxLayout

class LoanRegistrationPage(StyledWidget):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent, with_back_button=True, title="Register Loan", switch_page_callback=switch_page_callback)
        self.selected_customer_id = None
        self.customer_info_group = None
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

        # Loan Registration Group Box
        self.loan_form_group = QGroupBox("Loan Registration")
        loan_form_layout = QFormLayout()
        
        self.loan_amount_input = QLineEdit()
        self.loan_amount_input.setPlaceholderText("Enter Loan Amount (₹)")
        loan_form_layout.addRow("Loan Amount (₹):", self.loan_amount_input)
        
        self.interest_amount_input = QLineEdit()
        self.interest_amount_input.setPlaceholderText("Enter Interest Amount (₹)")
        loan_form_layout.addRow("Interest Amount (₹):", self.interest_amount_input)
        
        self.asset_description_input = QLineEdit()
        self.asset_description_input.setPlaceholderText("Enter Asset Description")
        loan_form_layout.addRow("Asset Description:", self.asset_description_input)
        
        self.asset_weight_input = QLineEdit()
        self.asset_weight_input.setPlaceholderText("Enter Asset Weight (kg)")
        loan_form_layout.addRow("Asset Weight (kg):", self.asset_weight_input)
        
        self.register_loan_btn = QPushButton("Register Loan")
        self.register_loan_btn.clicked.connect(self.register_loan)
        loan_form_layout.addRow(self.register_loan_btn)
        
        self.loan_form_group.setLayout(loan_form_layout)
        self.content_layout.addWidget(self.loan_form_group)
        self.loan_form_group.setEnabled(False)
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
                self.customer_dropdown.addItem(f"{name}", customer_id)
        else:
            self.customer_dropdown.addItem("No customers found")

    def on_customer_selected(self, index):
        """Display selected customer details."""
        if index < 0:
            return

        self.selected_customer_id = self.customer_dropdown.currentData()
        self.update_customer_info()

    def update_customer_info(self):
        """Update customer information in the info box."""
        layout = self.customer_info_group.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        customer = DatabaseManager.get_customer_by_id(self.selected_customer_id)
        if customer:
            for key, value in customer.items():
                row = QHBoxLayout()
                row.addWidget(QLabel(f"{key.replace('_', ' ').title()}:"))
                row.addWidget(QLabel(str(value)))
                layout.addLayout(row)
            self.loan_form_group.setEnabled(True)
        else:
            QMessageBox.warning(self, "Error", "Failed to load customer details.")

    def register_loan(self):
        """Validate and register the loan details."""
        try:
            loan_amount = float(self.loan_amount_input.text())
            interest_amount = float(self.interest_amount_input.text())
            asset_description = self.asset_description_input.text().strip()
            asset_weight = float(self.asset_weight_input.text())

            if not asset_description:
                raise ValueError("Asset description cannot be empty.")
            if loan_amount <= 0 or interest_amount <= 0 or asset_weight <= 0:
                raise ValueError("All numeric values must be positive.")
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
            return

        if not self.selected_customer_id:
            QMessageBox.warning(self, "Selection Error", "Please select a customer.")
            return

        try:
            loan_id = DatabaseManager.insert_loan(
                self.selected_customer_id, loan_amount, interest_amount
            )
            DatabaseManager.insert_asset(
                loan_id, asset_description, asset_weight
            )
            QMessageBox.information(self, "Success", "Loan registered successfully!")
            self.reset_form()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to register loan: {str(e)}")

    def reset_form(self):
        """Clear the input fields."""
        self.loan_amount_input.clear()
        self.interest_amount_input.clear()
        self.asset_description_input.clear()
        self.asset_weight_input.clear()
