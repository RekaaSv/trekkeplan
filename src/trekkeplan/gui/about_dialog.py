from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from trekkeplan import __version__

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.setWindowTitle("Om Trekkeplan")

        self.setMinimumWidth(280)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Trekkeplan & trekking"))
        layout.addWidget(QLabel(f"Versjon: {__version__}"))
        layout.addWidget(QLabel("Utviklet av Brikkesys/SvR"))
        close_btn = QPushButton("Lukk")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        self.setLayout(layout)