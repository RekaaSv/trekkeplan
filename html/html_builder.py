import logging
import os
from collections import defaultdict


class HtmlBuilder:
    @staticmethod
    def ul(rows):
        """Lag en <ul>-liste med én kolonne"""
        html = "<ul>\n"
        for row in rows:
            html += f"  <li>{row[0]}</li>\n"
        html += "</ul>"
        return html

    @staticmethod
    def ol(rows):
        """Lag en <ol>-liste med én kolonne"""
        html = "<ol>\n"
        for row in rows:
            html += f"  <li>{row[0]}</li>\n"
        html += "</ol>"
        return html

    @staticmethod
    def table(rows, columns, border=1):
        logging.info("html.table")
        """Lag en <table> med kolonnenavn og rader"""
        html = f"<table border='{border}'>\n  <tr>"
        for col in columns:
            html += f"<th>{col}</th>"
        html += "</tr>\n"

        for row in rows:
            html += "  <tr>" + "".join(f"<td>{celle}</td>" for celle in row) + "</tr>\n"
        html += "</table>"
        return html

    @staticmethod
    def definition_list(rows, columns):
        """Lag en <dl> med første kolonne som <dt> og resten som <dd>"""
        html = "<dl>\n"
        for row in rows:
            html += f"  <dt>{row[0]}</dt>\n"
            for celle in row[1:]:
                html += f"  <dd>{celle}</dd>\n"
        html += "</dl>"
        return html

    def grouped_rows_in_single_table(rows, columns, group_by_index: int, heading_tag="strong", border=1):
        grupper = {}
        visningsindekser = [i for i in range(len(columns)) if i != group_by_index]

        html = f"<table border='{border}'>\n"
        for row in rows:
            nøkkel = row[group_by_index]
            if nøkkel not in grupper:
                grupper[nøkkel] = []
                # legg inn overskrift som egen rad
                html += f"  <tr><td colspan='{len(visningsindekser)}'><{heading_tag}>{nøkkel}</{heading_tag}></td></tr>\n"
            grupper[nøkkel].append(row)
            html += "  <tr>" + "".join(f"<td>{row[i]}</td>" for i in visningsindekser) + "</tr>\n"

        html += "</table>"
        return html

    @staticmethod
    def download(html, file_name):
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        path = os.path.join(downloads_path, file_name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        # Open file.
        os.startfile(path)


