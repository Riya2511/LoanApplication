import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, QStackedWidget, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt

# Database interaction function
def fetch_data(query):
    conn = sqlite3.connect("my_database.db")
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data

# Card Widget
class Card(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setStyleSheet("""
            background-color: #f7f7f7; 
            border: 1px solid #ccc; 
            border-radius: 8px; 
            padding: 20px; 
            margin: 10px;
        """)
        label = QLabel(title)
        label.setStyleSheet("font-size: 16px; font-weight: bold;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

# Main Window
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loan Application")
        self.resize(800, 600)

        # Layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Outer Bordered Rectangle
        bordered_frame = QFrame()
        bordered_frame.setStyleSheet("border: 2px solid black; padding: 10px;")
        bordered_layout = QVBoxLayout()
        bordered_frame.setLayout(bordered_layout)
        main_layout.addWidget(bordered_frame)

        # Cards
        options = [
            ("Register Customer", self.show_customers),
            ("Register Loan", self.show_loans),
            ("Update Loan", self.update_loans),
            ("Get Report", self.show_assets),
        ]

        for option, callback in options:
            button = QPushButton(option)
            button.setStyleSheet("font-size: 14px; padding: 10px;")
            button.clicked.connect(callback)
            card = Card(option)
            card.layout().addWidget(button)
            bordered_layout.addWidget(card)

        # Pages
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages)

        # Add pages for each functionality
        self.pages.addWidget(self.create_page("Customers", "SELECT * FROM Customers"))
        self.pages.addWidget(self.create_page("Loans", "SELECT * FROM Loans"))
        self.pages.addWidget(self.create_page("Update Loan", "SELECT * FROM Loans"))
        self.pages.addWidget(self.create_page("Assets", "SELECT * FROM Assets"))

    def create_page(self, title, query):
        """Create a page to display query results."""
        page = QWidget()
        layout = QVBoxLayout()
        page.setLayout(layout)

        label = QLabel(title)
        label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(label)

        data = fetch_data(query)
        table = QTableWidget()
        if data:
            table.setRowCount(len(data))
            table.setColumnCount(len(data[0]))
            for i, row in enumerate(data):
                for j, cell in enumerate(row):
                    table.setItem(i, j, QTableWidgetItem(str(cell)))
        else:
            table.setRowCount(0)
            table.setColumnCount(0)
        layout.addWidget(table)

        return page

    def show_customers(self):
        self.pages.setCurrentIndex(0)

    def show_loans(self):
        self.pages.setCurrentIndex(1)

    def update_loans(self):
        self.pages.setCurrentIndex(2)

    def show_assets(self):
        self.pages.setCurrentIndex(3)

# Run Application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
