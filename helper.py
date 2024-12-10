from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QScrollArea
)
from PyQt5.QtCore import Qt

class StyledWidget(QWidget):
    def __init__(self, parent=None, with_back_button=False, title="", switch_page_callback=None):
        super().__init__(parent)
        self.switch_page = switch_page_callback
        self.setup_ui(with_back_button, title)

    def setup_ui(self, with_back_button=False, title=""):
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f4f4;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QLabel {
                font-size: 16px;
                color: #2c3e50;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QLabel.error {
                color: red;
                font-size: 12px;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Top section with back button and title
        if with_back_button and self.switch_page:
            top_layout = QHBoxLayout()
            back_btn = QPushButton("← Back")
            back_btn.clicked.connect(lambda: self.switch_page(0))  # Always go back to home
            
            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("font-size: 20px; font-weight: bold;")

            top_layout.addWidget(back_btn)
            top_layout.addStretch(1)
            top_layout.addWidget(title_label)
            top_layout.addStretch(1)

            main_layout.addLayout(top_layout)

        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setAlignment(Qt.AlignCenter)
        
        # Max width for content
        content_layout.addStretch(1)
        content_layout.setContentsMargins(20, 10, 20, 10)
        
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.content_layout = content_layout
        self.scroll_content = scroll_content

