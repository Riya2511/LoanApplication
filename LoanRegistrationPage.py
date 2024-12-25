from PyQt5.QtCore import QEvent, Qt
from helper import StyledWidget
from DatabaseManager import DatabaseManager
from PyQt5.QtWidgets import (QPushButton, QLineEdit, QFormLayout, QMessageBox, 
                           QLabel, QHBoxLayout, QComboBox, QGroupBox, QVBoxLayout,
                           QScrollArea, QWidget)

class AssetEntry(QGroupBox):
    def __init__(self, parent_widget=None, index=0):
        super().__init__()
        self.parent_widget = parent_widget
        self.index = index
        self.init_ui()

    def init_ui(self):
        self.setTitle(f"Asset {self.index + 1}")
        self.setMinimumHeight(150)
        
        main_layout = QVBoxLayout()
        input_layout = QHBoxLayout()
        
        # Description section
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Enter Asset Description")
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.description_input)
        input_layout.addLayout(desc_layout)
        
        # Add some spacing
        input_layout.addSpacing(20)
        
        # Weight section
        weight_layout = QHBoxLayout()
        weight_label = QLabel("Weight (g):")
        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText("Enter Asset Weight (g)")
        weight_layout.addWidget(weight_label)
        weight_layout.addWidget(self.weight_input)
        input_layout.addLayout(weight_layout)
        
        main_layout.addLayout(input_layout)
        
        # Remove button at bottom
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        remove_btn = QPushButton("Remove Asset")
        remove_btn.setFixedSize(120, 30)
        remove_btn.setStyleSheet("""
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
        remove_btn.clicked.connect(self.remove_asset)
        bottom_layout.addWidget(remove_btn)
        
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

    def remove_asset(self):
        if self.parent_widget:
            self.parent_widget.remove_asset_entry(self)

    def get_data(self):
        return {
            'description': self.description_input.text().strip(),
            'weight': self.weight_input.text().strip()
        }

class LoanRegistrationPage(StyledWidget):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent, with_back_button=True, title="Register Loan", switch_page_callback=switch_page_callback)
        self.selected_customer_id = None
        self.customer_info_group = None
        self.asset_entries = []
        self.init_ui()

    def init_ui(self):
        customer_layout = QHBoxLayout()
        self.customer_dropdown = QComboBox()
        self.customer_dropdown.setFixedWidth(300)
        customer_layout.addWidget(QLabel("Select Customer:"))
        customer_layout.addWidget(self.customer_dropdown)
        self.content_layout.addLayout(customer_layout)

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

        self.loan_form_group = QGroupBox("Loan Registration")
        loan_form_layout = QFormLayout()
        
        self.loan_amount_input = QLineEdit()
        self.loan_amount_input.setPlaceholderText("Enter Loan Amount (₹)")
        self.loan_amount_input.textChanged.connect(self.on_loan_amount_changed)
        loan_form_layout.addRow("Loan Amount (₹):", self.loan_amount_input)

        self.assets_group = QGroupBox("Assets")
        assets_layout = QVBoxLayout()
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.assets_layout = QVBoxLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content)
        self.scroll.setMinimumHeight(300)
        assets_layout.addWidget(self.scroll)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        self.add_asset_btn = QPushButton("+ Add Asset")
        self.add_asset_btn.setFixedSize(90, 30)
        self.add_asset_btn.setEnabled(False)
        self.add_asset_btn.setStyleSheet("""
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
        self.add_asset_btn.clicked.connect(self.add_asset_entry)
        bottom_layout.addWidget(self.add_asset_btn)
        
        assets_layout.addLayout(bottom_layout)
        self.assets_group.setLayout(assets_layout)
        loan_form_layout.addRow(self.assets_group)
        
        self.register_loan_btn = QPushButton("Register Loan")
        self.register_loan_btn.clicked.connect(self.register_loan)
        loan_form_layout.addRow(self.register_loan_btn)
        
        self.loan_form_group.setLayout(loan_form_layout)
        self.loan_form_group.setEnabled(False)
        self.content_layout.addWidget(self.loan_form_group)
        
        self.customer_dropdown.currentIndexChanged.connect(self.on_customer_selected)
        self.content_layout.addStretch(1)

    def on_loan_amount_changed(self, text):
        try:
            amount = float(text)
            self.add_asset_btn.setEnabled(amount > 0)
        except ValueError:
            self.add_asset_btn.setEnabled(False)

    def add_asset_entry(self):
        asset_entry = AssetEntry(parent_widget=self, index=len(self.asset_entries))
        self.asset_entries.append(asset_entry)
        self.assets_layout.insertWidget(len(self.asset_entries) - 1, asset_entry)

    def remove_asset_entry(self, entry):
        self.assets_layout.removeWidget(entry)
        self.asset_entries.remove(entry)
        entry.deleteLater()
        for i, entry in enumerate(self.asset_entries):
            entry.index = i
            entry.setTitle(f"Asset {i + 1}")

    def register_loan(self):
        try:
            loan_amount = float(self.loan_amount_input.text())
            if loan_amount <= 0:
                raise ValueError("Loan amount must be positive.")

            if not self.asset_entries:
                raise ValueError("Please add at least one asset.")

            assets_data = []
            for asset_entry in self.asset_entries:
                data = asset_entry.get_data()
                if not data['description']:
                    raise ValueError(f"Asset {asset_entry.index + 1}: Description cannot be empty.")
                try:
                    weight = float(data['weight'])
                    if weight <= 0:
                        raise ValueError(f"Asset {asset_entry.index + 1}: Weight must be positive.")
                    assets_data.append((data['description'], weight))
                except ValueError:
                    raise ValueError(f"Asset {asset_entry.index + 1}: Invalid weight value.")

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
            return

        if not self.selected_customer_id:
            QMessageBox.warning(self, "Selection Error", "Please select a customer.")
            return

        try:
            loan_id = DatabaseManager.insert_loan(self.selected_customer_id, loan_amount)
            for description, weight in assets_data:
                DatabaseManager.insert_asset(loan_id, description, weight)
            QMessageBox.information(self, "Success", "Loan registered successfully!")
            self.reset_form()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to register loan: {str(e)}")

    def reset_form(self):
        self.loan_amount_input.clear()
        for entry in self.asset_entries[:]:
            self.remove_asset_entry(entry)

    def showEvent(self, event: QEvent):
        if event.type() == QEvent.Show:
            self.populate_customer_dropdown()
        super().showEvent(event)

    def populate_customer_dropdown(self):
        self.customer_dropdown.clear()
        customers = DatabaseManager.get_all_customers()
        if customers:
            for customer_id, name, account_number in customers:
                self.customer_dropdown.addItem(f"{name}", customer_id)
        else:
            self.customer_dropdown.addItem("No customers found")

    def on_customer_selected(self, index):
        if index < 0:
            return
        self.selected_customer_id = self.customer_dropdown.currentData()
        self.update_customer_info()

    def update_customer_info(self):
        layout = self.customer_info_group.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        customer = DatabaseManager.get_customer_by_id(self.selected_customer_id)
        if customer:
            for key, value in customer.items():
                if key == "customer_id" or not value:
                    continue
                row = QHBoxLayout()
                row.addWidget(QLabel(f"{key.replace('_', ' ').title()}:"))
                row.addWidget(QLabel(str(value)))
                layout.addLayout(row)
            self.loan_form_group.setEnabled(True)
        else:
            QMessageBox.warning(self, "Error", "Failed to load customer details.")