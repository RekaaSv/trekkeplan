from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import Qt
from datetime import datetime, date, time, timedelta

class DrawPlanTableItem(QTableWidgetItem):
    def __init__(self, display_text: str, sort_value, alignment: Qt.AlignmentFlag):
        super().__init__(display_text)
        self.setBackground(QColor("white"))
        self.setData(Qt.UserRole, sort_value)
        self.setTextAlignment(alignment)

    def __lt__(self, other):
        if isinstance(other, QTableWidgetItem):
            a = self.data(Qt.UserRole)
            b = other.data(Qt.UserRole)
            try:
                return a < b
            except TypeError:
                pass
        return super().__lt__(other)

    @classmethod
    def from_value(cls, value):
        """Velger visning, sorteringsverdi og justering basert på type. None vises som blankt."""
        if value is None:
            return cls("", "", Qt.AlignLeft | Qt.AlignVCenter)

        if isinstance(value, datetime):
            return cls(value.strftime("%H:%M:%S"), value, Qt.AlignCenter)
        elif isinstance(value, date):
            return cls(value.strftime("%d.%m.%Y"), value, Qt.AlignCenter)
        elif isinstance(value, time):
            return cls(value.strftime("%H:%M:%S"), value, Qt.AlignCenter)
        elif isinstance(value, timedelta):
            total_seconds = int(value.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            if hours > 0:
                display = f"{hours}:{minutes:02}:{seconds:02}"
            else:
                display = f"{minutes}:{seconds:02}"
            return cls(display, value, Qt.AlignRight | Qt.AlignVCenter)
        elif isinstance(value, int):
            return cls(str(value), value, Qt.AlignRight | Qt.AlignVCenter)
        elif isinstance(value, str):
            return cls(value, value.lower(), Qt.AlignLeft | Qt.AlignVCenter)
        else:
            return cls(str(value), str(value), Qt.AlignLeft | Qt.AlignVCenter)
