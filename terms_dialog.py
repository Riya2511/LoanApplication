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
                  
<p>1. <b>Acceptance of Terms:</b> By installing or using this Loan Application software (the "Software"), you (the "User") agree to be bound by these Terms and Conditions. If you do not agree with these terms, do not install or use the Software.
</p>

<p>2. <b>Software Description:</b> The Software is designed to help Users manage and track borrower information, including pending amounts, tenures, contact details, and other related data. The Software operates offline, with all data stored locally on the User’s device. No direct financial transactions are facilitated or processed through the Software.
</p>
<p>3. <b>License Grant:</b> Subject to these Terms and Conditions, we grant the User a non-exclusive, non-transferable, and revocable license to use the Software solely for internal business purposes.
</p>
<p>4. <b>Data Responsibility:</b>
    <p>4.1. The User acknowledges and agrees that they are solely responsible for the data entered, stored, and managed within the Software. </p>
    <p>4.2. The User is responsible for maintaining backups of their data. We are not liable for any data loss, corruption, or unauthorized access to data stored within the Software.</p>
</p>
<p>5. <b>User Restrictions:</b> The User shall not:
    <p>Decompile, reverse-engineer, disassemble, or attempt to derive the source code of the Software.</p>
    <p>Use the Software for unlawful purposes or in violation of any applicable laws.</p>
    <p>Distribute, resell, sublicense, or otherwise transfer the Software to any third party.</p>
</p>
<p>6. <b>Disclaimer of Warranties:</b> 
    <p>6.1. The Software is provided "as is" without any warranties, express or implied, including but not limited to implied warranties of merchantability or fitness for a particular purpose. </p>
    <p>6.2. We do not guarantee that the Software will be error-free or operate without interruptions. The User assumes all responsibility for the use of the Software and any results obtained from its use.</p>
</p>
<p>7. <b>Limitation of Liability:</b>
    <p>7.1. In no event shall we be liable for any direct, indirect, incidental, consequential, or punitive damages arising out of the use or inability to use the Software, even if we have been advised of the possibility of such damages. </p>
    <p>7.2. Our total liability, whether in contract, tort, or otherwise, shall not exceed the total amount paid by the User for the Software.</p>
</p>
<p>8. <b>Updates and Support:</b>
    <p>8.1. We may provide updates or enhancements to the Software at our discretion. The User agrees to install any critical updates to ensure proper functionality and security. </p>
    <p>8.2. Support services, if included, will be provided as per the terms of the purchased support plan.</p>
</p>
<p>9. <b>Termination:</b> We reserve the right to terminate this license and the User’s access to the Software if the User breaches these Terms and Conditions. Upon termination, the User must cease all use of the Software and delete all copies in their possession.
</p>
<p>10. <b>Intellectual Property:</b> All rights, title, and interest in the Software, including but not limited to copyrights, trademarks, and trade secrets, remain our property. The User is granted no rights or interests in the Software other than the limited license outlined in these terms.
</p>
<p>12. <b>Amendments:</b> We reserve the right to modify these Terms and Conditions at any time. The User will be notified of any material changes, and continued use of the Software after such notification constitutes acceptance of the updated terms.
</p>
<p>13. <b>Contact Information:</b> For any questions or concerns regarding these Terms and Conditions, please contact us at:
    <p><b>Email: </b></p>
    <p><b>Phone No.: +91- </b></p>
</p>

<p><b>By using the Software, you acknowledge that you have read, understood, and agree to be bound by these Terms and Conditions.</b></p>

         """
        
        terms_label = QLabel(terms_text)
        terms_label.setWordWrap(True)
        terms_label.setOpenExternalLinks(True)
        content_layout.addWidget(terms_label)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QDialog {
                border: 2px solid #3498db;
                border-radius: 15px; /* Rounded corners */
                background-color: white;
            }
        """)
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)