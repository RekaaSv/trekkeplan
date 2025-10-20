README_build.txt
================

Bygge og pakke Trekkeplan GUI med PyInstaller
---------------------------------------------

Dette prosjektet bruker PyInstaller til å pakke Python-koden som en Windows .exe-fil.
Vi har to versjoner:

1. Trekkeplan.exe – GUI uten konsoll (for sluttbrukere)
2. Trekkeplan_debug.exe – GUI med konsoll (for utvikling og feilsøking)

Felles innhold:
- Ikon: terning.ico
- Konfigurasjon: trekkeplan.cfg
- Versjonsinfo: version.txt (vises i Egenskaper → Detaljer)

---

Generere .spec-filer (kun første gang eller ved endringer)
-----------------------------------------------------------

Kjør disse i PyCharm-terminalen for å lage .spec-filer:

GUI uten konsoll:
> pyinstaller main.py --onefile --noconsole --icon=terning.ico --add-data "trekkeplan.cfg;." --add-data "terning.ico;." --version-file=version.txt --name Trekkeplan

GUI med konsoll:
> pyinstaller main.py --onefile --icon=terning.ico --add-data "trekkeplan.cfg;." --add-data "terning.ico;." --version-file=version.txt --name Trekkeplan_debug

---

Bygge fra .spec-filer (repeterbart)
-----------------------------------

Etter at .spec-filene er generert, kan du bygge med:

GUI uten konsoll:
> python -m PyInstaller Trekkeplan.spec

GUI med konsoll:
> python -m PyInstaller Trekkeplan_debug.spec

---

Opprydding etter bygging
-------------------------

Du kan slette midlertidige filer med:
- build/
- dist/
- __pycache__/
- *.spec (hvis du vil regenerere dem)

---

Tips
----

- Du kan lage egne .bat-filer for bygging og opprydding hvis du ønsker én-klikks prosess.
- Versjonsnummeret vises i GUI via `version.txt` og leses fra .exe-filen.
- Ikonet vises i Utforsker og i tittellinjen på GUI-vinduet.

---

Sist oppdatert: 20. oktober 2025