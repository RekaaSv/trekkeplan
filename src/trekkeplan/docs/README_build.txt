README_build.txt
================

Bygge og pakke Trekkeplan GUI med PyInstaller
---------------------------------------------

Dette prosjektet bruker PyInstaller til å pakke Python-koden som en Windows .exe-fil.


Generere .spec-filer (kun første gang eller ved endringer)
-----------------------------------------------------------

Kjør dette i PyCharm-terminalen for å bygge EXE-fil og lage .spec-fil:

pyinstaller src/trekkeplan/main.py `
  --onefile `
  --noconsole `
  --icon=src/trekkeplan/terning.ico `
  --add-data "src/trekkeplan/terning.ico;." `
  --add-data "src/trekkeplan/hjelp.pdf;." `
  --name Trekkeplan


Bygge fra .spec-fil (repeterbart)
-----------------------------------

Etter at .spec-filene er generert, kan du bygge med den:

python -m PyInstaller Trekkeplan.spec


Opprydding etter bygging
-------------------------
Du kan slette midlertidige filer:
- build/
- __pycache__/


Hvis filstrukturen endrer seg, eller nye ressurs-filer, så *.spec regenereres.
Det gjøres ved å slette *.spec og byge med den første metoden
(som også lager ny *.spec fil).

Sist oppdatert: 21.11.2025