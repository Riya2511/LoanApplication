import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QStackedWidget, 
                             QLabel, QPushButton, QHBoxLayout)
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
from terms_dialog import TermsAndConditionsDialog  # Import the dialog

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loan Management System")
        favicon = QIcon("./websculptors.jpg")
        self.setWindowIcon(favicon)
        self.showMaximized()
        DatabaseManager.init_database()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Top header with logo and terms
        header_layout = QHBoxLayout()
        
        # Logo (replace with your actual logo path)
        logo_label = QLabel()
        logo_pixmap = QPixmap("./websculptors.jpg")  # Replace with actual path
        logo_label.setPixmap(logo_pixmap.scaled(350, 150, transformMode=Qt.SmoothTransformation))
        header_layout.addWidget(logo_label)
        
        header_layout.addStretch(1)
        
        # Terms and Conditions Button
        terms_button = QPushButton("Terms and Conditions")
        terms_button.setFixedHeight(30)
        terms_button.setFixedWidth(200)
        terms_button.setStyleSheet(
            "background-color: #3498db; color: white"
        )
        terms_button.clicked.connect(self.show_terms)
        header_layout.addWidget(terms_button)
        
        main_layout.addLayout(header_layout)

        # Stacked Widget
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        # Create an instance of each page with the switch_page method
        self.login_screen = LoginScreen(self.switch_page)
        
        # Add pages to the stacked widget
        self.stacked_widget.addWidget(self.login_screen)  # Index 0
        self.stacked_widget.addWidget(HomePage(self, self.switch_page))  # Index 1
        self.stacked_widget.addWidget(RegisterCustomerPage(self, self.switch_page))  # Index 2
        self.stacked_widget.addWidget(LoanRegistrationPage(self, self.switch_page))  # Index 3
        self.stacked_widget.addWidget(LoanUpdatePage(self, self.switch_page))  # Index 4
        self.stacked_widget.addWidget(GenerateReport(self, self.switch_page))  # Index 5

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def show_terms(self):
        dialog = TermsAndConditionsDialog(self)
        dialog.exec_()

def main():
    # Uncomment the following line if you want to verify pendrive
    # if not verifyPendrive():
    #     return
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()