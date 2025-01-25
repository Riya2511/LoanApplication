from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton,                               QScrollArea, QWidget)
from PyQt5.QtCore import Qt

class TermsAndConditionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Terms and Conditions")
        
        # Set fixed width and height
        self.setFixedSize(450, 500)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Scroll area for terms with fixed dimensions
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedSize(420, 400)  # Slightly smaller than dialog
        
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # Terms content
        terms_text = """
<h2>Terms and Conditions for Loan Management System</h2>
                  
<h3>1. User Responsibilities</h3>
         
Users are responsible for maintaining the confidentiality of their system password and protecting sensitive customer information.
                  
<h3>2. Data Privacy</h3>
         
All customer data must be handled with utmost confidentiality and in compliance with local data protection regulations.
                  
<h3>3. System Usage</h3>
         
This system is intended solely for authorized personnel of the financial institution. Unauthorized access is strictly prohibited.
                  
<h3>4. Data Accuracy</h3>
         
Users must ensure the accuracy and completeness of all entered information.
                  
<h3>5. System Integrity</h3>
         
Any attempts to manipulate or compromise the system's functionality are forbidden.
                  
<h3>6. Liability</h3>
         
The organization is not responsible for misuse of the system by unauthorized personnel.
         """
        
        terms_label = QLabel(terms_text)
        terms_label.setWordWrap(True)
        terms_label.setOpenExternalLinks(True)
        content_layout.addWidget(terms_label)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)