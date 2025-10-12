from PyQt5.QtGui import QPalette, QColor, QBrush
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QTableWidgetItem

def sett_seleksjonsfarge(widget, bakgrunn=QColor(0, 120, 215), tekst=QColor(Qt.white)):
    """Setter seleksjonsfarge for både aktiv og inaktiv tilstand."""
    palett = widget.palette()
    for state in (QPalette.Active, QPalette.Inactive):
        palett.setColor(state, QPalette.Highlight, bakgrunn)
        palett.setColor(state, QPalette.HighlightedText, tekst)
    widget.setPalette(palett)

def marker_rader(tabell, rad_filter_fn, farge=QColor(220, 235, 255), scroll_til_første=True):
    print("marker_rader start")
    """
    Farger rader som oppfyller rad_filter_fn(tabell, rad) med gitt farge.
    tabell: QTableWidget
    rad_filter_fn: funksjon som returnerer True for valgbare rader
    farge: bakgrunnsfarge for valgbare rader
    scroll_til_første: om første valgbar rad skal scrolles til
    """
    hvit = QBrush(Qt.white)
    markering = QBrush(farge)
    første = None

    for rad in range(tabell.rowCount()):
        er_valgbar = rad_filter_fn(tabell, rad)
        bakgrunn = markering if er_valgbar else hvit
        for kol in range(tabell.columnCount()):
            celle = tabell.item(rad, kol)
            if celle:
                celle.setBackground(bakgrunn)
        if er_valgbar and første is None:
            første = tabell.item(rad, 0)

    if første and scroll_til_første:
        tabell.scrollToItem(første, tabell.PositionAtTop)

def lag_knapp(text, bredde=100, høyde=30):
    """Oppretter en knapp med standard størrelse og tekst."""
    knapp = QPushButton(text)
    knapp.setFixedSize(bredde, høyde)
    return knapp

def lag_celle(text, editable=False):
    """Oppretter en celle med tekst og valgfri redigerbarhet."""
    celle = QTableWidgetItem(text)
    if not editable:
        celle.setFlags(celle.flags() & ~Qt.ItemIsEditable)
    return celle