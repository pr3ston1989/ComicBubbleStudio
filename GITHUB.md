# ComicBubbleStudio — Nokturn Bubble Studio

Samodzielne repozytorium narzędzia do przygotowania obrysów dymków i kolejności
czytania dla Nokturna. Bieżące wydanie: **2.5.2**.

## Pobieranie

- [Instalator Windows x64](https://github.com/pr3ston1989/ComicBubbleStudio/releases/download/v2.5.2/Nokturn-Bubble-Studio-2.5.2-Setup.exe)
- [Paczka ZIP Windows x64](https://github.com/pr3ston1989/ComicBubbleStudio/releases/download/v2.5.2/Nokturn-Bubble-Studio-2.5.2-windows-x64.zip)
- [Wydanie i sumy SHA-256](https://github.com/pr3ston1989/ComicBubbleStudio/releases/tag/v2.5.2)

Paczki zawierają program uruchamiający i instalujący zależności. Środowisko
Python i przypięte wagi modeli są pobierane podczas konfiguracji. Wagi modeli,
prywatne komiksy, wyniki i lokalne środowisko nie są dołączone do repozytorium.
Instrukcje sprzętowe i obsługa: [README.md](README.md).

## Sprawdzona jakość

Na zachowanych 292 stronach / 1793 oczekiwanych przystankach: **96,98%** łącznie.
F1 wykrywania 95,56%; akceptacja obrysów 96,24%; poprawność par kolejności 99,17%.
Przy identycznym zestawie i kryterium poprzednia wersja ma 96,88%.
To ocena agenta na lokalnym korpusie, nie niezależny pomiar ekspercki ani
gwarancja jakości każdego komiksu. 166/292 stron jest całkowicie bez uwag.
Cel 97% nie został osiągnięty: niezaokrąglony wynik 96,97755885038801%.

Niepełny ogonek jest dopuszczalny przy poprawnym korpusie i tekście. Kryterium
jest jednakowe dla wszystkich stron i obu porównywanych wersji. Średnia
geometryczna obejmuje F1 wykrywania, wizualną akceptację obrysów i poprawność
par kolejności. Nie mierzy dokładności transkrypcji OCR ani przeplatania głosów
wewnątrz połączonych fizycznie dymków. Sześć nowych stron dało 98,30%; taka mała
próba nie jest statystycznym potwierdzeniem uniwersalności.

Zaliczono 454 testy programu i 15 pełnych kontroli GPU; poprawne odpowiedzi
modelu kontekstu wykorzystywano ponownie z pamięci. Wszystkie 292 wyniki
zwalidowano dla czytnika Nokturna, wykonano zapis/odczyt 12 rzeczywistych stron
oraz osiem kontroli dystrybucji. Szczegóły agregatów:
[docs/quality-2.5.2.json](docs/quality-2.5.2.json).
Pełne raporty z obrazami pozostają lokalne u właściciela korpusu.

## Testy i budowanie

W skonfigurowanym środowisku programu, z zainstalowanym pytest:

```powershell
python -m pytest tests web/backend/tests -q -k "not external_api"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/build_setup.ps1 -PythonPath SCIEZKA_DO_PYTHON
```

Cztery testy API pełnego serwera Nokturna wymagają jego osobnego środowiska
i nie należą do kontroli samodzielnego narzędzia. Testy okien wymagają Tcl/Tk.
Budowanie odtwarza manifest, ZIP i instalator w `dist`.

Główną funkcją jest przygotowanie dymków do Nokturna. Obsługa PDF i eksport
OCR są dodatkami; eksport tekstu jest domyślnie wyłączony. Modele i biblioteki
zachowują własne licencje; źródła opisano w [RESEARCH.md](RESEARCH.md)
i [assets/PROVENANCE.md](assets/PROVENANCE.md).
