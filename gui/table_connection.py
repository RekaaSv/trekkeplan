class TableConnection:
    def __init__(self, table_source, table_dest, inx_source, inx_dest):
        """
        kilde_tabell: QTableWidget med utvalg
        mål_tabell: FilteredTable som skal filtreres
        kilde_kol_index: kolonne i kilde som gir filterverdi
        mål_kol_index: kolonne i mål som skal matches
        """
        self.kilde = table_source
        self.table_dest = table_dest
        self.kilde_kol_index = inx_source
        self.inx_dest = inx_dest
#        print(f"Kilde-tabell: {type(self.kilde)}")
#        print(f"Kilde-tabell: {type(self.table_dest)}")
        self.koble_signal()

    def koble_signal(self):
        # Bruker itemSelectionChanged for robusthet
        self.kilde.itemSelectionChanged.connect(self.oppdater_filter)
#        print("koble_signal slutt")

    def oppdater_filter(self):
#        print("oppdater_filter() ble kalt")
        utvalg = self.kilde.selectionModel().selectedRows()
        if not utvalg:
            self.table_dest.filter_verdier.clear()
            self.table_dest.marker_valgbare_rader()
            self.table_dest.clearSelection()
            return

        rad = utvalg[0].row()
        verdi = self.kilde.item(rad, self.kilde_kol_index).text()
        self.table_dest.sett_filter(self.inx_dest, verdi)