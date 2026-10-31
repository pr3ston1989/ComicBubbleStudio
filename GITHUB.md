# ComicBubbleStudio — Nokturn Bubble Studio

Samodzielne repozytorium narzędzia do przygotowania obrysów dymków i kolejności
czytania dla Nokturna. Bieżące wydanie: **2.5.3**.

## Pobieranie

- [Instalator Windows x64](https://github.com/pr3ston1989/ComicBubbleStudio/releases/download/v2.5.3/Nokturn-Bubble-Studio-2.5.3-Setup.exe)
- [Paczka ZIP Windows x64](https://github.com/pr3ston1989/ComicBubbleStudio/releases/download/v2.5.3/Nokturn-Bubble-Studio-2.5.3-windows-x64.zip)
- [Wydanie i sumy SHA-256](https://github.com/pr3ston1989/ComicBubbleStudio/releases/tag/v2.5.3)

Paczki zawierają program uruchamiający i instalujący zależności. Środowisko
Python i przypięte wagi modeli są pobierane podczas konfiguracji. Wagi modeli,
prywatne komiksy, wyniki i lokalne środowisko nie są dołączone do repozytorium.
Instrukcje sprzętowe i obsługa: [README.md](README.md).

## Sprawdzona jakość

Wersja 2.5.3: **97,05% na 298 stronach / 1834 przystankach**.
F1 wykrywania 95,61%; obrysy 96,40%;
kolejność par 99,16%. Na identycznych 298 stronach poprzednia
wersja uzyskuje 96,97%. Na zachowanych 292 stronach poprawa
wynosi 96,98% → 97,05%: odzyskano pięć kwestii
i naprawiono jeden obszar myśli. Cel 98% pozostaje nieosiągnięty.

To ocena agenta, nie niezależny pomiar ekspercki ani gwarancja dla każdego
komiksu. 173/298 stron jest całkowicie bez uwag. Metryka jest średnią
geometryczną F1, akceptacji obrysów i poprawności par kolejności; nie mierzy
dokładności OCR ani przeplatania głosów wewnątrz połączonych dymków.
Niepełne ogonki są dopuszczalne wyłącznie przy poprawnym korpusie i tekście.

Sześć nowych stron miało kompletny wzorzec zapisany z oryginałów przed
przewidywaniami. Reguły były zamrożone; wynik tej próby: 96,87%.
Wszystkie strony pozostają w mianowniku. Taka mała próba nie stanowi
statystycznego potwierdzenia uniwersalności. Nowe błędy nie zostały usunięte
przez dopasowywanie kodu do tej szóstki. Brak pogorszenia na każdej z 298 stron.

Zaliczono 492 testy programu, 13 pełnych kontroli GPU, walidację 298 wyników
czytnika, zapis/odczyt pakietu 12 rzeczywistych stron i osiem kontroli
dystrybucji. Kontrole GPU korzystały ponownie z poprawnych zapisanych
odpowiedzi modelu kontekstu. [Agregaty i ograniczenia](docs/quality-2.5.3.json).
Pełne raporty z oryginałami komiksów pozostają lokalne.

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
