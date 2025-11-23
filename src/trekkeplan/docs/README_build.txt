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

Pakke sammen zip-fil for nedlasting fra GitHub
----------------------------------------------
Samle filene som skal zip'es sammen i folderen dist:
- Trekkeplan.exe (plassert hit under bygging)
- trekkeplan.cfg (kopier fra src/trekkeplan, men endre password til <passord>
- README.pdf (kopier fra src/trekkeplan/docs)

Pakk samme de 3 filene til:
trekkeplan.zip

Laste ZIP-fil opp til ny release på GitHub.
-------------------------------------------
https://github.com/RekaaSv/trekkeplan/releases
Draft a new release. -> Create new tag (eks. v1.1.0)
Attach binaries: Dra og slipp zip-filen her.
Publish release.



Sist oppdatert: 21.11.2025