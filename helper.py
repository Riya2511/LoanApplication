from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QScrollArea
)
from PyQt5.QtCore import Qt
import os
import wmi
import win32file
import hashlib

class StyledWidget(QWidget):
    def __init__(self, parent=None, with_back_button=False, title="", switch_page_callback=None):
        super().__init__(parent)
        self.switch_page_callback = switch_page_callback
        self.setup_ui(with_back_button, title)

    def setup_ui(self, with_back_button=False, title=""):
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f4f4;
                font-family: Arial, sans-serif;
                font-size: 14px;  /* Base font size for all widgets */
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                font-size: 14px;  /* Explicit size for buttons */
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QLabel {
                font-size: 16px;
                color: #2c3e50;
            }
            QLineEdit, QComboBox, QComboBox QAbstractItemView {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 14px;  /* Explicit size for input elements */
            }
            QLabel.error {
                color: red;
                font-size: 14px;  /* Change error labels too */
            }
            /* Add these additional selectors to catch more elements */
            QHeaderView::section {
                font-size: 14px;
            }
            QTableView {
                font-size: 14px;
            }
            QCheckBox, QRadioButton {
                font-size: 14px;
            }
            QMenu, QMenuBar {
                font-size: 14px;
            }
            QTabBar::tab {
                font-size: 14px;
            }
            /* Style for info sections (customer info, etc.) */
            QGroupBox QLabel {
                font-size: 16px;
            }
            /* For labels within HBox layouts (typically used for displaying info) */
            QHBoxLayout > QLabel {
                font-size: 16px;
            }
            /* Ensure all information display labels have consistent sizing */
            .info-label {
                font-size: 16px;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Top section with back button and title
        if with_back_button and self.switch_page_callback:
            top_layout = QHBoxLayout()
            back_btn = QPushButton("← Back")
            back_btn.clicked.connect(self.back_button_clicked)
            
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

    def back_button_clicked(self):
        # Always go to HomePage (index 1)
        if self.switch_page_callback:
            self.switch_page_callback(1)
    
    def create_info_label(self, text):
        """Helper method to create consistently styled information labels"""
        label = QLabel(text)
        label.setStyleSheet("font-size: 16px;")
        label.setProperty("class", "info-label")
        return label
    
def format_indian_currency(amount):
    """
    Convert a number to Indian currency format.
    
    Args:
        amount (float or int): The number to be formatted
    
    Returns:
        str: Formatted number in Indian currency style
    """
    try:
        # Convert to float and handle potential None or zero values
        amount = float(amount) if amount is not None else 0.0
        
        # Split into integer and decimal parts
        integer_part, decimal_part = f"{amount:.2f}".split('.')
        # Handle negative numbers
        is_negative = integer_part.startswith('-')
        if is_negative:
            integer_part = integer_part[1:]
        
        # Reverse the integer part for easier processing
        reversed_integer = integer_part[::-1]
        
        # Add commas in Indian number format (every 2 digits after first 3)
        formatted_integer = []
        for i, digit in enumerate(reversed_integer):
            if i != 0 and i != 1 and i % 2 != 0 and i < len(reversed_integer):
                formatted_integer.append(',')
            formatted_integer.append(digit)
        
        # Reverse back and join
        final_integer = ''.join(formatted_integer)[::-1]
        
        # Add negative sign back if needed
        if is_negative:
            final_integer = f'-{final_integer}'
        
        # Combine integer and decimal parts
        return f"{final_integer}.{decimal_part}"
    
    except (TypeError, ValueError):
        return str(amount)

def hashSerialNumber(serialNumber: str):
    dataEncoded = str(serialNumber).encode("utf-8")
    sha256Hash = hashlib.sha256()
    sha256Hash.update(dataEncoded)
    return sha256Hash.hexdigest()

def getPendriveSerialNumber():
    try:
        # current_drive = os.path.splitdrive(os.path.abspath(__file__))[0] + "\\" #prev
        current_drive = os.path.splitdrive(os.getcwd())[0].lower()
        # print("current_drive prev : ",current_drive)
        drive_type = win32file.GetDriveType(current_drive)
        # print("Current :  jay   : ",current_drive)
        print("current_drive now : ",current_drive)
        if drive_type != 2:
            print("Current drive is not a removable drive")
            return None
        c = wmi.WMI()
        # for disk in c.Win32_LogicalDisk(DeviceID=current_drive.replace("\\", "")):
        for disk in c.Win32_LogicalDisk(DeviceID=current_drive):

            if hasattr(disk, "VolumeSerialNumber"):
                return disk.VolumeSerialNumber

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def verifyPendrive():
    try:
        current_serialNumber = getPendriveSerialNumber()
        if current_serialNumber is None:
            print("Could not retrieve current drive serial number")
            return False
        # current_drive = os.path.splitdrive(os.path.abspath(__file__))[0] + "\\"
        # auth_file_path = os.path.join(os.getcwd() + '\\', "auth.py")
        # if not os.path.exists(auth_file_path):
        #     print("Authentication file not found")
        #     return False
        # with open(auth_file_path, 'r') as f:
        #     stored_hash = f.read().strip()
        from auth import auth
        current_hash = hashSerialNumber(current_serialNumber)
        
        return current_hash == auth
    except Exception as e:
        print(f"Error verifying pendrive: {e}")
        return False