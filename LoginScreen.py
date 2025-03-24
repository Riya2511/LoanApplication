from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QPushButton, 
                             QLabel, QMessageBox, QDialog, QFormLayout, 
                             QHBoxLayout, QSizePolicy)
from PyQt5.QtCore import Qt
from DatabaseManager import DatabaseManager

class ChangePasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Password")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()

        self.old_password_input = QLineEdit()
        self.old_password_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Old Password:", self.old_password_input)

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        layout.addRow("New Password:", self.new_password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        layout.addRow("Confirm New Password:", self.confirm_password_input)

        button_layout = QHBoxLayout()
        change_button = QPushButton("Change Password")
        change_button.clicked.connect(self.change_password)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(change_button)
        button_layout.addWidget(cancel_button)
        layout.addRow(button_layout)

        self.setLayout(layout)

    def change_password(self):
        old_password = self.old_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        # Verify current password first
        if not DatabaseManager.verify_password(old_password):
            QMessageBox.warning(self, "Error", "Incorrect old password!")
            return

        # Check if new passwords match
        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "New passwords do not match!")
            return

        # Update password
        DatabaseManager.update_password(new_password)
        QMessageBox.information(self, "Success", "Password changed successfully!")
        self.accept()


class LoginScreen(QWidget):
    def __init__(self, on_login_callback):
        super().__init__()
        self.on_login_callback = on_login_callback  # Change to store the callback with new name
        self.init_ui()

    def init_ui(self):
        # Create main layout to center vertically
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addStretch(1)  # Add stretch to push content to center

        # Create a central widget to center the login form horizontally
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setSpacing(10)
        central_widget.setFixedWidth(300)

        # Title
        title_label = QLabel("Loan Management System")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        title_label.setAlignment(Qt.AlignCenter)
        central_layout.addWidget(title_label)

        # Password input
        password_label = QLabel("Enter System Password:")
        password_label.setStyleSheet("font-size: 14px;")
        central_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.returnPressed.connect(self.verify_password)  # Add Enter key support
        central_layout.addWidget(self.password_input)

        # Login button
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.verify_password)
        central_layout.addWidget(login_button)

        # Change Password button
        change_password_button = QPushButton("Change Password")
        change_password_button.clicked.connect(self.open_change_password_dialog)
        central_layout.addWidget(change_password_button)

        # Add central widget to main layout
        main_layout.addWidget(central_widget, alignment=Qt.AlignCenter)
        main_layout.addStretch(1)  # Add stretch to push content to center

    def verify_password(self):
        password = self.password_input.text()
        if DatabaseManager.verify_password(password):
            # Call the login success callback instead of directly switching pages
            self.on_login_callback()  # No need to pass user_id if you're not tracking specific users
        else:
            QMessageBox.warning(self, "Error", "Incorrect password!")

    def open_change_password_dialog(self):
        dialog = ChangePasswordDialog(self)
        dialog.exec_()