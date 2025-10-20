from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
import sys
import ctypes

def hent_versjonsinfo():
    exe_path = sys.executable if getattr(sys, 'frozen', False) else __file__
    size = ctypes.windll.version.GetFileVersionInfoSizeW(exe_path, None)
    if size == 0:
        return "Ukjent versjon"
    res = ctypes.create_string_buffer(size)
    ctypes.windll.version.GetFileVersionInfoW(exe_path, 0, size, res)
    r = ctypes.c_void_p()
    l = ctypes.c_uint()
    ctypes.windll.version.VerQueryValueW(res, '\\', ctypes.byref(r), ctypes.byref(l))
    if l.value == 0:
        return "Ukjent versjon"
    vs_fixedfileinfo = ctypes.cast(r, ctypes.POINTER(ctypes.c_uint32 * (l.value // 4))).contents
    major = vs_fixedfileinfo[4] >> 16
    minor = vs_fixedfileinfo[4] & 0xFFFF
    build = vs_fixedfileinfo[5] >> 16
    revision = vs_fixedfileinfo[5] & 0xFFFF
    return f"{major}.{minor}.{build}.{revision}"

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.setWindowTitle("Om Trekkeplan")

        self.setMinimumWidth(280)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Trekkeplan & trekking"))
        layout.addWidget(QLabel(f"Versjon: {hent_versjonsinfo()}"))
        layout.addWidget(QLabel("Utviklet av Brikkesys/SvR"))
        close_btn = QPushButton("Lukk")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        self.setLayout(layout)