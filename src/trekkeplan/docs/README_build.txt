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
pyinstaller src/trekkeplan/main.py `
  --onefile `
  --noconsole `
  --icon=src/trekkeplan/terning.ico `
  --add-data "src/trekkeplan/terning.ico;." `
  --add-data "src/trekkeplan/hjelp.pdf;." `
  --name Trekkeplan


---

Bygge fra .spec-filer (repeterbart)
-----------------------------------

Etter at .spec-filene er generert, kan du bygge med:

GUI uten konsoll:
python -m PyInstaller Trekkeplan.spec

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

Sist oppdatert: 21.11.2025