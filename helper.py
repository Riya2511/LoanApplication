from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QScrollArea
)
from PyQt5.QtCore import Qt
import os
import wmi
import win32api
import win32file
import hashlib
import ctypes

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
        auth_file_path = os.path.join(os.getcwd() + '\\', ".auth")
        if not os.path.exists(auth_file_path):
            print("Authentication file not found")
            return False
        with open(auth_file_path, 'r') as f:
            stored_hash = f.read().strip()
        current_hash = hashSerialNumber(current_serialNumber)
        
        return current_hash == stored_hash
    except Exception as e:
        print(f"Error verifying pendrive: {e}")
        return False

 