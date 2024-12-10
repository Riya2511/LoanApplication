from helper import StyledWidget
from PyQt5.QtWidgets import ( QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame )
from PyQt5.QtCore import Qt

class HomePage(StyledWidget):
    def __init__(self, parent, switch_page_callback):
        super().__init__(parent, switch_page_callback=switch_page_callback)
        self.switch_page = switch_page_callback
        self.init_ui()

    def init_ui(self):
        title = QLabel("Loan Management System")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        self.content_layout.addWidget(title)

        options = [
            ("Register Customer", 1),
            ("Register Loan", 2),
            ("Repay Loan", 3),
            ("Generate Report", 4)
        ]

        grid_layout = QHBoxLayout()
        self.content_layout.addLayout(grid_layout)

        for text, page_index in options:
            card = QFrame()
            card.setFixedSize(300, 150)  # Fixed size for consistent layout
            card.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 10px;
                    padding: 10px;
                    margin: 10px;
                }
                QFrame:hover {
                    background-color: #f1f1f1;
                }
            """)
            card_layout = QVBoxLayout()
            card.setLayout(card_layout)

            label = QLabel(text)
            label.setFixedHeight(70)
            label.setAlignment(Qt.AlignCenter)
            button = QPushButton("Go to " + text)
            button.clicked.connect(lambda checked, idx=page_index: self.switch_page(idx))

            card_layout.addStretch(1)
            card_layout.addWidget(label)
            card_layout.addWidget(button)
            card_layout.addStretch(1)

            grid_layout.addWidget(card)

        self.content_layout.addStretch(1)

