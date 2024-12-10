import sys
from DatabaseManager import DatabaseManager
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QStackedWidget
from HomePage import HomePage
from RegisterCustomerPage import RegisterCustomerPage
from LoanRegistrationPage import LoanRegistrationPage
from LoanUpdatePage import LoanUpdatePage
from GenerateReport import GenerateReport

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        DatabaseManager.init_database()
        self.setWindowTitle("Loan Management System")
        self.resize(800, 600)
        self.init_ui()

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
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()