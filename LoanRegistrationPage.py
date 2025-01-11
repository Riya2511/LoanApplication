from PyQt5.QtCore import QEvent, Qt
from helper import StyledWidget
from DatabaseManager import DatabaseManager
from PyQt5.QtWidgets import (QPushButton, QLineEdit, QFormLayout, QMessageBox, 
                           QLabel, QHBoxLayout, QComboBox, QGroupBox, QVBoxLayout,
                           QScrollArea, QWidget, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtWidgets import QDateEdit
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QDateEdit, QSizePolicy

class AssetEntry(QGroupBox):
    def __init__(self, parent_widget=None, index=0):
        super().__init__()
        self.parent_widget = parent_widget
        self.index = index
        self.init_ui()
        
    def init_ui(self):
        self.setTitle(f"Asset {self.index + 1}")
        self.setMinimumHeight(300)
        self.setMaximumHeight(300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        main_layout = QVBoxLayout()
        input_layout = QVBoxLayout()

        # Style for input fields
        input_style = """
            QLineEdit {
                min-height: 30px;
                max-height: 30px;
                padding: 5px;
            }
        """

        # Reference ID
        reference_id_layout = QHBoxLayout()
        reference_id_label = QLabel("Reference ID:")
        self.reference_id_input = QLineEdit()
        self.reference_id_input.setPlaceholderText("Enter Reference ID")
        self.reference_id_input.setStyleSheet(input_style)
        reference_id_layout.addWidget(reference_id_label)
        reference_id_layout.addWidget(self.reference_id_input)
        input_layout.addLayout(reference_id_layout)

        # Description
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Enter Asset Description")
        self.description_input.setStyleSheet(input_style)
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.description_input)
        input_layout.addLayout(desc_layout)

        # Weight
        weight_layout = QHBoxLayout()
        weight_label = QLabel("Weight (g):")
        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText("Enter Asset Weight (g)")
        self.weight_input.setStyleSheet(input_style)
        weight_layout.addWidget(weight_label)
        weight_layout.addWidget(self.weight_input)
        input_layout.addLayout(weight_layout)

        remove_layout = QHBoxLayout()
        remove_layout.addStretch()
        self.remove_btn = QPushButton("Remove Asset")
        self.remove_btn.setFixedSize(120, 30)
        self.remove_btn.setStyleSheet("""
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
        self.remove_btn.clicked.connect(self.remove_asset)
        remove_layout.addWidget(self.remove_btn)
        input_layout.addLayout(remove_layout)

        main_layout.addLayout(input_layout)
        self.setLayout(main_layout)

    def get_data(self):
        return {
            'reference_id': self.reference_id_input.text().strip(),
            'description': self.description_input.text().strip(),
            'weight': self.weight_input.text().strip()
        }

    def remove_asset(self):
        if self.parent_widget:
            self.parent_widget.remove_asset_entry(self)

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
        self.customer_dropdown.addItem("Select Customer", None)  # Add default option
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

        # Add loan account number at loan level
        self.loan_account_input = QLineEdit()
        self.loan_account_input.setPlaceholderText("Enter Loan Account Number")
        loan_form_layout.addRow("Loan Account Number:", self.loan_account_input)
        
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

        self.loans_group = QGroupBox("Customer Loans")
        loans_layout = QVBoxLayout()
        
        self.loans_table = QTableWidget()
        self.loans_table.setColumnCount(7)
        self.loans_table.setHorizontalHeaderLabels([
            "Loan Date", 
            "Assets",
            "Total Weight (g)", 
            "Loan Amount (₹)", 
            "Amount Due (₹)",
            "Interest Paid (₹)",
            "Status"
        ])
        
        self.loans_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.loans_table.setSelectionMode(QTableWidget.SingleSelection)
        self.loans_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.loans_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
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

        self.content_layout.addStretch(1)

    def register_loan(self):
        try:
            loan_amount = float(self.loan_amount_input.text())
            if loan_amount <= 0:
                raise ValueError("Loan amount must be positive.")

            if not self.asset_entries:
                raise ValueError("Please add at least one asset.")

            loan_account_number = self.loan_account_input.text().strip()
            if not loan_account_number:
                raise ValueError("Loan account number cannot be empty.")

            loan_date = self.date_input.date().toString("yyyy-MM-dd")
            assets_data = []
            for asset_entry in self.asset_entries:
                data = asset_entry.get_data()
                if not data['reference_id']:
                    raise ValueError(f"Asset {asset_entry.index + 1}: Reference ID cannot be empty.")
                if not data['description']:
                    raise ValueError(f"Asset {asset_entry.index + 1}: Description cannot be empty.")
                try:
                    weight = float(data['weight'])
                    if weight <= 0:
                        raise ValueError(f"Asset {asset_entry.index + 1}: Weight must be positive.")
                    data['weight'] = weight
                    assets_data.append(data)
                except ValueError:
                    raise ValueError(f"Asset {asset_entry.index + 1}: Invalid weight value.")

        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
            return

        if not self.selected_customer_id:
            QMessageBox.warning(self, "Selection Error", "Please select a customer.")
            return
        
        success, message = DatabaseManager.insert_loan_with_assets(
            self.selected_customer_id,
            loan_amount,
            loan_date,
            loan_account_number,
            assets_data
        )

        if success:
            QMessageBox.information(self, "Success", "Loan registered successfully!")
            self.reset_form()
            self.update_loans_table()
        else:
            QMessageBox.critical(self, "Error", f"Failed to register loan: {str(e)}")

    def on_loan_amount_changed(self, text):
        try:
            amount = float(text)
            self.add_asset_btn.setEnabled(amount > 0)
        except ValueError:
            self.add_asset_btn.setEnabled(False)

    def add_asset_entry(self):
        asset_entry = AssetEntry(parent_widget=self, index=len(self.asset_entries))
        asset_entry.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.asset_entries.append(asset_entry)
        self.assets_layout.insertWidget(len(self.asset_entries) - 1, asset_entry)

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
        for entry in self.asset_entries[:]:
            self.remove_asset_entry(entry)

    def showEvent(self, event: QEvent):
        if event.type() == QEvent.Show:
            self.populate_customer_dropdown()
        super().showEvent(event)

    def populate_customer_dropdown(self):
        self.customer_dropdown.clear()
        self.customer_dropdown.addItem("Select Customer", None)  # Add default option
        customers = DatabaseManager.get_all_customers()
        if customers:
            for customer_id, name, account_number in customers:
                self.customer_dropdown.addItem(f"{name}", customer_id)

    def on_customer_selected(self, index):
        if index <= 0:  # Account for the "Select Customer" option
            self.selected_customer_id = None
            self.loan_form_group.setEnabled(False)
            self.update_customer_info()
            self.update_loans_table()
            return
            
        self.selected_customer_id = self.customer_dropdown.currentData()
        self.loan_form_group.setEnabled(True)
        self.update_customer_info()
        self.update_loans_table()

    def update_loans_table(self):
        if not self.selected_customer_id:
            self.loans_table.setRowCount(0)
            return
            
        loans = DatabaseManager.fetch_loans_for_customer(self.selected_customer_id)
        self.loans_table.setRowCount(len(loans))
        
        for row, loan in enumerate(loans):
            # Convert the date string from yyyy-MM-dd to dd-MM-yyyy
            try:
                # Parse the original date string
                date_parts = loan[0].split('-')
                if len(date_parts) == 3:
                    # Rearrange to dd-MM-yyyy format
                    formatted_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                else:
                    formatted_date = loan[0]  # Keep original if parsing fails
            except Exception:
                formatted_date = loan[0]  # Keep original if any error occurs
            
            # Update table with formatted date
            self.loans_table.setItem(row, 0, QTableWidgetItem(formatted_date))
            self.loans_table.setItem(row, 1, QTableWidgetItem(loan[1] or "N/A"))  # Assets
            self.loans_table.setItem(row, 2, QTableWidgetItem(f"{loan[2]:.2f}"))  # Total Weight
            self.loans_table.setItem(row, 3, QTableWidgetItem(f"{loan[3]:.2f}"))  # Loan Amount
            self.loans_table.setItem(row, 4, QTableWidgetItem(f"{loan[4]:.2f}"))  # Amount Due
            self.loans_table.setItem(row, 5, QTableWidgetItem(f"{loan[5]:.2f}"))  # Interest Paid
            
            status = "Completed" if float(loan[4]) <= 0 else "Pending"
            self.loans_table.setItem(row, 6, QTableWidgetItem(status))

    def update_customer_info(self):
        # Clear existing widgets
        layout = self.customer_info_group.layout()
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.selected_customer_id:
            # If no customer is selected, don't display anything
            return

        customer = DatabaseManager.get_customer_by_id(self.selected_customer_id)
        if customer:
            for key, value in customer.items():
                if key == "customer_id" or not value:
                    continue
                row = QHBoxLayout()
                row.addWidget(QLabel(f"{key.replace('_', ' ').title()}:"))
                row.addWidget(QLabel(str(value)))
                layout.addLayout(row)
        else:
            QMessageBox.warning(self, "Error", "Failed to load customer details.")