README_runtime.txt
==================

Kjøre og teste Trekkeplan GUI
------------------------------

Dette dokumentet beskriver hvordan du starter og bruker Trekkeplan-applikasjonen, både i vanlig modus og i debug-modus med konsoll.

---

Filer
-----

Etter bygging finner du følgende i dist-mappen:

- Trekkeplan.exe         → GUI uten konsoll (for sluttbrukere)
- Trekkeplan_debug.exe   → GUI med konsoll (for utvikling og feilsøking)

Begge versjoner inkluderer:
- trekkeplan.cfg         → konfigurasjonsfil
- app_icon.ico           → ikon for GUI og .exe
- version.txt            → versjonsinformasjon (vises i Egenskaper → Detaljer)

---

Kjøre GUI uten konsoll
-----------------------

Start `Trekkeplan.exe` ved å dobbeltklikke i Utforsker.

- Ingen svart terminalvindu vises
- GUI åpnes direkte
- Feilmeldinger vises kun i GUI (f.eks. via QMessageBox)

---

Kjøre GUI med konsoll (debug)
------------------------------

Start `Trekkeplan_debug.exe` ved å dobbeltklikke eller via terminal:

> dist\Trekkeplan_debug.exe

- Konsollvindu vises i bakgrunnen
- Du ser `print()`-utskrifter og feilmeldinger direkte
- Nyttig for utvikling og feilsøking

---

Feilsøking
----------

- Hvis GUI ikke starter:
  - Sjekk om `trekkeplan.cfg` finnes i samme mappe
  - Kjør `Trekkeplan_debug.exe` og se konsollutskrifter
  - Sjekk versjonsinfo og ikon i Egenskaper → Detaljer

- Hvis du får database- eller config-feil:
  - Feilmeldinger vises i GUI via dialogbokser
  - Konsoll gir mer teknisk info i debug-versjonen

---

Tips
----

- Du kan lage snarvei til `Trekkeplan.exe` på skrivebordet
- Versjonsnummer vises i GUI via "Om Trekkeplan"-knappen
- Debug-versjonen kan brukes til å teste edge cases og logikk

---

Sist oppdatert: 20. oktober 2025