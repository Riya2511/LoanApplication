import sys
from DatabaseManager import DatabaseManager
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QStackedWidget
from HomePage import HomePage
from RegisterCustomerPage import RegisterCustomerPage
from LoanRegistrationPage import LoanRegistrationPage
from LoanUpdatePage import LoanUpdatePage
from GenerateReport import GenerateReport
from helper import verifyPendrive

class MainWindow(QWidget):
    def __init__(self):
        
        super().__init__()
        self.setWindowTitle("Loan Management System")
        # self.resize(1920, 1080)
        self.showMaximized()
        self.init_ui()
        DatabaseManager.init_database()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # Add pages
        pages = [
            HomePage(self, self.switch_page),
            RegisterCustomerPage(self, self.switch_page),  # Page 1
            LoanRegistrationPage(self, self.switch_page),  # Page 2
            LoanUpdatePage(self, self.switch_page),
            GenerateReport(self, self.switch_page),
        ]

        for page in pages:
            self.stacked_widget.addWidget(page)

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

def main():
    # if not verifyPendrive():
    #     return
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()