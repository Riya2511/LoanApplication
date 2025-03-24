import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QStackedWidget, 
                             QLabel, QPushButton, QHBoxLayout, QFileDialog)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt
from DatabaseManager import DatabaseManager
from HomePage import HomePage
from RegisterCustomerPage import RegisterCustomerPage
from LoanRegistrationPage import LoanRegistrationPage
from LoanUpdatePage import LoanUpdatePage
from GenerateReport import GenerateReport
from LoginScreen import LoginScreen
from helper import verifyPendrive
from terms_dialog import TermsAndConditionsDialog
from binary_images import FAVICON_BASE64, LOGO_BASE64
import base64
import os
import shutil
import stat
import datetime

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loan Management System")
        favicon_data = base64.b64decode(FAVICON_BASE64)
        favicon_pixmap = QPixmap()
        favicon_pixmap.loadFromData(favicon_data)
        favicon = QIcon(favicon_pixmap)
        self.setWindowIcon(favicon)
        # Remove showMaximized() here as we'll do it after setup
        DatabaseManager.init_database()
        self.is_logged_in = False
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Top header with logo and terms
        header_layout = QHBoxLayout()
        
        # Logo
        logo_data = base64.b64decode(LOGO_BASE64)
        logo_pixmap = QPixmap()
        logo_pixmap.loadFromData(logo_data)
        
        logo_label = QLabel()
        logo_label.setPixmap(logo_pixmap.scaled(250, 20, transformMode=Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)
        
        header_layout.addStretch(1)
        
        # Backup Button - using a style that changes appearance when disabled
        self.backup_button = QPushButton("Backup Database")
        self.backup_button.setFixedHeight(30)
        self.backup_button.setFixedWidth(150)
        self.backup_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border-radius: 15px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
                border-radius: 15px;
            }
        """)
        self.backup_button.clicked.connect(self.backup_database)
        self.backup_button.setEnabled(False)
        header_layout.addWidget(self.backup_button)
        
        # Terms and Conditions Button
        terms_button = QPushButton("Terms and Conditions")
        terms_button.setFixedHeight(30)
        terms_button.setFixedWidth(200)
        terms_button.setStyleSheet(
            "background-color: #3498db; color: white; border-radius: 15px;"
        )
        terms_button.clicked.connect(self.show_terms)
        header_layout.addWidget(terms_button)
        
        main_layout.addLayout(header_layout)

        # Stacked Widget
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Create an instance of each page with the switch_page method
        self.login_screen = LoginScreen(self.on_login_success)
        
        # Add pages to the stacked widget
        self.stacked_widget.addWidget(self.login_screen)  # Index 0
        self.stacked_widget.addWidget(HomePage(self, self.switch_page))  # Index 1
        self.stacked_widget.addWidget(RegisterCustomerPage(self, self.switch_page))  # Index 2
        self.stacked_widget.addWidget(LoanRegistrationPage(self, self.switch_page))  # Index 3
        self.stacked_widget.addWidget(LoanUpdatePage(self, self.switch_page))  # Index 4
        self.stacked_widget.addWidget(GenerateReport(self, self.switch_page))  # Index 5

    def on_login_success(self, user_id=None):
        # Called when login is successful
        self.is_logged_in = True
        self.backup_button.setEnabled(True)
        self.switch_page(1)  # Switch to home page

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def backup_database(self):
        # Open file dialog to select destination
        dest_dir = QFileDialog.getExistingDirectory(
            self, 
            "Select Backup Location", 
            os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        
        if dest_dir:
            try:
                current_date = datetime.datetime.now()
                date_string = current_date.strftime("%Y-%m-%d %H:%M:%S")
                # Source database path
                src_path = os.path.join(os.getcwd(), "loanApp.db")
                # Destination path
                dest_path = os.path.join(dest_dir, f"loanApp_{date_string.replace('-', '_').replace(':', '_').replace(' ', '_')}.db")
                
                # Copy the file
                shutil.copy2(src_path, dest_path)
                
                # Remove hidden attribute in Windows
                if os.name == 'nt':
                    import subprocess
                    # Use attrib command to remove hidden attribute
                    subprocess.run(['attrib', '-H', dest_path], check=True)
                else:
                    # For non-Windows systems, ensure file permissions are set properly
                    os.chmod(dest_path, 0o644)  # Read/write for owner, read for others
                
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(
                    self, 
                    "Backup Successful", 
                    f"Database has been successfully backed up to:\n{dest_path}"
                )
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self, 
                    "Backup Failed", 
                    f"Could not backup database: {str(e)}"
                )

    def show_terms(self):
        dialog = TermsAndConditionsDialog(self)
        dialog.exec_()

def main():
    # Uncomment the following line if you want to verify pendrive
    # if not verifyPendrive():
    #     return
    app = QApplication(sys.argv)
    window = MainWindow()
    # Use showFullScreen() instead of showMaximized() for true full screen
    # Or keep window.showMaximized() but move it here
    window.showMaximized()
    window.show()  # This ensures the window is properly rendered
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()