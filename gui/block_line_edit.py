from PyQt5.QtWidgets import QLineEdit


class BlockLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def focusInEvent(self, event):
        if self.parent:
            self.parent.block_focus_action()
        super().focusInEvent(event)