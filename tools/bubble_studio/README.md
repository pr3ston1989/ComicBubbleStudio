# Nokturn Bubble Studio 2.6.1

## Nowości 2.6.1 — naprawa korpusu po rozlaniu obrysu (2026-11-01)

**97,51% na wszystkich 316 stronach / 1975 oczekiwanych przystankach.**
Na identycznych 316 stronach wersja 2.6.0: **97,47%**.
Na wcześniejszych 310: 97,41% → 97,45%. To mały przyrost; cel 98–99% pozostaje nieosiągnięty.

| Miara — te same 316 stron | 2.6.0 | 2.6.1 |
|---|---:|---:|
| Wykrywanie F1 | 96,78% | 96,78% |
| Zaakceptowane wizualnie obrysy | 96,33% | 96,44% |
| Poprawne pary kolejności dopasowanych kwestii | 99,32% | 99,32% |
| Fałszywe przystanki / pominięcia | 61 / 66 | 61 / 66 |
| Odrzucone obrysy | 70 | 68 |
| Strony całkowicie bez uwag | 202/316 | 203/316 |

Naprawa szuka zwartego korpusu dymka w oryginalnych pikselach, gdy wcześniejszy
obrys objął puste tło kadru. Małe przerwy drukowanej linii domyka zależnie od
rozdzielczości. Wymaga stabilnego obszaru przy dwóch progach jasności,
potwierdzenia słów przez OCR, zachowania ich położenia i braku kolizji z innymi
kwestiami. Zmniejszenie wymaga mocnego dowodu rozlania na papier przy brzegach
kadru. Nie zmienia liczby przystanków, identyfikatorów, kotwic ani kolejności.
Błąd wycofuje cały nowy etap, a ręcznie zatwierdzone strony są chronione.
Poprawiono dwa korpusy, w tym jeden w skanie Azumangi; nie dodano wyjątków
dla tytułów, numerów stron ani oczekiwanych wyników.

Sześć nowych stron: 2 komiksy kolorowe, 2 mangi i 2 strony 4koma. Obrazy
wylosowano bez odrzucania trudnych stron, a komplet kwestii i kolejność
zapisano na podstawie oryginałów przed przewidywaniami. Wynik tej małej próby:
**99,41%**, 56/58 kwestii, bez nadmiarowych przystanków
i błędów kolejności. Pozostały pominięte głosowe MAAA oraz UGH bez dymków.
Nowe obrysy były identyczne w obu wersjach; dobry wynik tej szóstki nie jest
zasługą nowej poprawki ani dowodem takiej skuteczności na dowolnym komiksie.
Wszystkie strony weszły do wyniku 316.

Brak regresji na każdej z 316 stron. **534 testy** aplikacji i czytnika.
57 wcześniejszych modułów Python zachowano bajt po bajcie; wcześniejszy tor
GPU jest niezmieniony, dodano tylko końcowy etap. Sześć nowych stron przeszło
pełną analizę GPU. Sprawdzono format danych czytnika i zapis/odczyt pakietu.
Eksperymenty z szerszym łączeniem dymków i odzyskiwaniem krzyków odrzucono
z powodu błędnych ocen; nie są częścią wydania.

Wynik jest średnią geometryczną F1, akceptacji obrysów i zgodności par
kolejności, ocenioną przez agenta, a nie niezależnych ekspertów. To nie jest
dokładność transkrypcji OCR ani procent idealnych stron: bez uwag są
**203 z 316 stron (64,24%)**. Kryteria zachowano: mały brak ogonka jest
dozwolony tylko przy poprawnym korpusie i tekście. OCR/PDF pozostają dodatkiem;
główną funkcją jest przygotowanie dymków dla Nokturna.
Nie zmieniono modeli, wymagań sprzętowych ani sposobu instalacji.

Raport z przykładami i wykazem wszystkich stron:
PRACA/quality-2.6.1/PODSUMOWANIE.html.

## Nowości 2.6.0 — analiza scen i mniej fałszywych przystanków (2026-11-01)

**97,41% na wszystkich 310 stronach / 1917 oczekiwanych przystankach.**
Poprzednia wersja na tych samych stronach: **96,96%**.
Na dawnych 298 stronach: 97,05% → 97,51%. Cel 98–99% pozostaje nieosiągnięty.

| Miara — te same 310 stron | 2.5.3 | 2.6.0 |
|---|---:|---:|
| Wykrywanie F1 | 95,51% | 96,74% |
| Zaakceptowane wizualnie obrysy | 96,22% | 96,22% |
| Poprawne pary kolejności dopasowanych kwestii | 99,18% | 99,29% |
| Fałszywe przystanki | 109 | 61 |
| Pominięte kwestie | 65 | 64 |
| Błędne pary kolejności | 60 | 52 |
| Odrzucone obrysy dopasowanych kwestii | 70 | 70 |
| Strony całkowicie bez uwag | 177/310 | 198/310 |

Qwen3-VL-8B w zapisie NF4 sprawdza podejrzane obiekty w kontekście całej
strony oraz zbliżenia. Usunięcie wymaga dwóch ocen braku treści opowieści
i rzeczywistego dymka. Etap nie usuwa efektów dźwiękowych: wariant mylący
małe dymki z efektami został odrzucony. Odrzucono też szersze usuwanie
kolorowych tablic, które pomyliło podpis miejsca z szyldem. Nie ma wyjątków
dla nazw komiksów ani numerów stron.

Kolorowe odstępy między kadrami pomagają kolejności; tekst przekraczający
granicę wymaga potwierdzenia przypisania do sceny. Paski 4koma są chronione.
Pusty brzeg kadru można odciąć przy szukaniu fizycznie połączonego dymka,
z zachowaniem tekstu i wcześniejszych obrysów. Błąd etapu wycofuje jego
zmiany; ręcznie zatwierdzone strony są chronione.

Dwanaście nowych stron (4 komiksy, 4 manga, 4 strony Azumangi) wybrano przed
wynikami. Treść i kolejność wzorca zapisano przed przewidywaniami. Po kontroli
wszystkich 88 punktów na samych oryginałach poprawiono jedną współrzędną UMM,
bez zmiany kwestii, kolejności i kryteriów; pierwotny wzorzec i rejestr zachowano.
Wynik nowej dwunastki: **95,10%**.
Wszystkie strony pozostają w mianowniku; nie dostrojono kodu do nowych błędów.

Brak regresji na każdej z 310 stron. **525 testów**, sześć pełnych kontroli GPU
końcowej aplikacji, walidacja 310 dokumentów i ponowny odczyt pakietu 12 stron.
Wcześniejsze detektory zachowano: na 298 stronach przeliczono nowy etap,
12 nowych przeszło pełne modele GPU. Kontrole końcowej aplikacji odtworzyły
oczekiwane wyniki, również przy świeżych odpowiedziach nowego modelu.

To średnia geometryczna F1, akceptacji obrysów i zgodności par kolejności,
a nie odsetek idealnych stron. Ocena wizualna pochodzi od agenta, nie od
niezależnych ekspertów; nie mierzy transkrypcji OCR. Drobne braki ogonka są
dozwolone przy poprawnym korpusie i tekście. Największe rezerwy pozostają
w błędnych obrysach i pominiętych wypowiedziach poza dymkami.

Pierwsza dokładna analiza pobiera dodatkowo około **17,5 GB** danych modelu
i zapisuje około **6,4 GB** wag do dalszego lokalnego używania. Własne pliki
źródłowe usuwa po weryfikacji mniejszego zapisu. Sprawdzono świeżą analizę
bez Internetu i bez źródłowych wag. Obrazy pozostają na komputerze.
Zalecane 16 GB VRAM, 32 GB RAM i 60 GB wolnego SSD na pierwszą konfigurację,
plus miejsce na komiksy. Główną funkcją jest przygotowanie dymków do Nokturna;
eksport OCR pozostaje dodatkiem, domyślnie wyłączonym.

Raport z obrazami i wykazem wszystkich stron:
PRACA/quality-2.6.0/PODSUMOWANIE.html.

## Nowości 2.5.3 — krótkie podpisy i obszary myśli (2026-11-01)

Wynik na wszystkich **298 stronach / 1834 oczekiwanych przystankach: 97,05%**.
Cel 98% pozostaje nieosiągnięty. Na identycznych 298 stronach poprzednia
wersja ma 96,97%. Na dotychczasowych 292 stronach:
96,98% → 97,05%. Rozszerzenie próby jest oddzielone od wpływu kodu.
F1 wykrywania: 95,61%; obrysy: 96,40%;
kolejność par: 99,16%. 173/298 stron jest całkowicie bez uwag.
To ocena agenta, nie niezależny pomiar ekspercki ani dokładność transkrypcji OCR.

Na wcześniejszych 292 stronach odzyskano pięć pominiętych krótkich podpisów/
objaśnień i poprawiono jedną maskę obejmującą tło zamiast samej myśli. Każde
dodanie wymaga niezależnego OCR, dwóch kontroli treści oraz potwierdzenia
miejsca przez cały dotychczasowy prefiks i sufiks kolejności. Dwie odpowiedzi
modelu nie mogą same ustalić kolejności. Wariant błędnie wstawiający nazwę
postaci został odrzucony. Paski 4koma pozostają chronione.

Sześć nowych stron wybrano przed przewidywaniami, a wzorzec zapisano po
obejrzeniu samych oryginałów. Reguły były zamrożone przed próbą. Wszystkie
strony doliczono, w tym niemy fragment opowieści; wynik tej szóstki: 96,87%.
Nie dopasowano kodu do nowych błędów ujawnionych w tej próbie.
Brak pogorszeń na każdej z 298 stron. Zaliczono 492 testy programu.
Raport opisuje także pełne kontrole GPU i zgodność pakietów z czytnikiem.

Krótki ogonek nie dyskwalifikuje dymka przy poprawnym korpusie i tekście.
Główną funkcją jest przygotowanie dymków do Nokturna; PDF i eksport OCR są
dodatkami, eksport domyślnie wyłączony. Raport:
`PRACA/quality-2.5.3/PODSUMOWANIE.html`.

## Nowości 2.5.2 — mniej nadmiarowych wykryć (2026-10-30)

Wynik na wszystkich **292 stronach / 1793 oczekiwanych przystankach: 96,98%**.
Niezaokrąglony wynik to 96,97755885038801%; cel 97% pozostaje nieosiągnięty.
Na identycznych 292 stronach poprzednia wersja ma 96,88%, obecna 96,98%.
F1 wykrywania: 95,56%; akceptacja obrysów: 96,24%; kolejność: 99,17%.
166/292 stron (56,8%) jest całkowicie bez uwag. To ocena agenta na zachowanym
korpusie, nie niezależna gwarancja jakości ani dokładność transkrypcji OCR.

Usunięto 11 fałszywych wykryć: napisy na przedmiotach, zapowiedź redakcyjną,
reklamowe podpisy i odgłos mechaniczny poza dymkiem. Wymagane są mocne OCR
oraz dwie zgodne, osobne oceny obrazu. Chronione są fikcyjne profile postaci,
pojedyncze symboliczne słowa i wszystkie prawdziwe dymki/podpisy narracyjne.
Nie zmieniono geometrii ani kolejności zachowanych kwestii. Brak pogorszeń
na każdej z 292 stron. Ręcznie zatwierdzone strony i możliwość cofnięcia
korekty kontekstu pozostają chronione.

Sześć nowych stron wybrano przed przewidywaniami, po zamrożeniu reguł filtra.
Wszystkie doliczono, także strony z błędami: wynik tej małej próby to 98,30%.
Znaleziono dwa pominięte podpisy miejsca/czasu i jedną maskę obejmującą tło.
Kolejność wszystkich 184 par nowej próby jest poprawna, także w 4komie.
Próba jest zbyt mała, by uznać ją za statystyczne potwierdzenie uniwersalności.
Eksperyment zmniejszania masek tekstów bez dymków odrzucono; nie jest częścią
wydania. Dodatkowa wylosowana szóstka nie była analizowana ani doliczana.

Zaliczono 454 testy programu; cztery testy API pełnego serwera poza zakresem.
Pełne przebiegi GPU oraz zgodność pakietów i instalatora opisuje raport.
Główną funkcją jest przygotowanie dymków do Nokturna; eksport OCR pozostaje
dodatkiem domyślnie wyłączonym. Niepełny ogonek jest akceptowany wyłącznie
przy poprawnym korpusie, tekście i pozostałym obrysie, na wszystkich stronach.
Raport: `PRACA/quality-2.5.2/PODSUMOWANIE.html`.

## Nowości 2.5.1 — kolejność, korpusy i aktualne kryterium ogonków (2026-10-30)

Wynik na wszystkich **286 stronach / 1752 oczekiwanych przystankach: 96,85%**.
Cel 97% pozostaje nieosiągnięty. Przy tej samej próbie i aktualnym kryterium
poprzednia wersja uzyskuje 96,52%: wpływ kodu to +0,32 punktu procentowego.
F1 wykrywania: 95,22%; poprawne korpusy i tekst: 96,22%; kolejność: 99,15%.
163/286 stron jest całkowicie bez uwag. To ocena agenta na zachowanym korpusie,
nie gwarancja wyniku na nieznanym komiksie ani dokładność transkrypcji OCR.

Zgodnie z prośbą użytkownika niepełny ogonek/łącznik myśli nie dyskwalifikuje
dymka, jeśli korpus, słowa i reszta obrysu są poprawne. Oceniono ponownie 125
odrzuconych obrysów: 59 miało jedynie brak łącznika. Sama zmiana kryterium
przesuwa dawny punkt odniesienia z 95,34% do 96,52%; nie jest poprawą kodu.
Przy dawnej surowej ocenie obrysów kod daje 95,34% → 95,68%.

Poprawki usuwają 24 nadmiarowe wykrycia, naprawiają 13 błędnych par kolejności
i dwa błędne korpusy. Nie odnotowano pogorszenia na żadnej z 286 stron według
obu kryteriów. Model obrazu dodatkowo ocenia każdą proponowaną zamianę
prostokąta na fizyczny dymek. Ryzykowny eksperyment szerokiego przedłużania
ogonków odrzucono w całości. Dymki zatwierdzone ręcznie pozostają chronione.

Sześć nowych stron zawiera zachodni komiks, mangę i 4komę; włączono je w całości.
Na całych 286 stronach odtworzono nowe etapy po zachowanych wykryciach.
Oddzielnie sprawdzono 16 pełnych przebiegów kontrolnych bieżącej wersji.
Wcześniejszy zestaw 60 stron służył także odrzuceniu eksperymentu; nie jest już
świeżą niezależną próbą końcowej wersji. Zaliczono 431 testów programu.

Główną funkcją pozostaje przygotowanie dymków do Nokturna. PDF i eksport tekstu
są dodatkami; eksport domyślnie wyłączony. Zmieniono wersję silnika/checkpointów
na 2.5.1. Raport z oryginałami, obrysami i oceną każdej strony:
`PRACA/quality-2.5.1/PODSUMOWANIE.html`.

## Nowości 2.5.0 — walidacja, PDF i opcjonalny tekst (2026-10-29)

Główną funkcją pozostaje przygotowanie dymków do Nokturna.
Silnik 2.4.3 i jego checkpointy pozostają bez zmian. Dodatek eksportu jest
domyślnie wyłączony i nie zmienia obrysów, kolejności ani pakietów dymków.

Próba: **60 zupełnie nowych stron, 41 archiwów, 30 LTR i 30 RTL**;
30 stron z nieocenianych wcześniej tytułów. Dobór zamrożono przed analizą.
Wszystkie przeszły pełny przebieg GPU i pełną ocenę wizualną; bez dostrajania
silnika do tej próby. Wynik nowych 60: **95,67%** (F1 92,05%, obrysy 95,76%,
kolejność 99,33%). Braki 10, nadmiar 47, złe obrysy 14, błędne pary 8/1199.
**35/60 stron** jest całkowicie bez uwag. Reklam i trudnych stron nie wykluczano.

Wszystkie **280 stron / 1716 oczekiwanych kwestii: 95,32%** —
F1 94,49%, obrysy 92,51%, kolejność 99,06%. 131/280 stron bez uwag.
Wcześniejsze 220 wyników i wzorców zachowano identycznie; różnica wobec
95,23% wynika z rozszerzenia próby. To ocena agenta, bez eksperckich masek
pikselowych i bez pomiaru poprawności transkrypcji OCR.

PDF (skan, tekst lub strona mieszana) jest przetwarzany do CBZ z pakietem dla
Nokturna. Dodatkowy eksport: HTML + TXT, TXT lub Markdown, z numerami stron,
nazwami plików i kolejnością z aktualnego pakietu. Osobny przycisk „Tekst z
gotowych pakietów…” działa bez wczytywania modeli dymków. Podczas importu PDF
eksport łączy pasującą warstwę tekstową z OCR; istniejący CBZ eksportuje przez OCR.

Zaliczono **401 testów programu** (4 testy API pełnego serwera poza zakresem).
Rzeczywisty test GPU czterostronicowego PDF potwierdził, że włączenie eksportu
na gotowym komiksie zachowuje identyczne bajty pakietu, geometrię i kolejność.
Test obejmuje Unicode, skan, warstwę mieszaną, obrót i przycięcie. Syntetyczne
strony testu funkcji nie wchodzą do procentu oceny komiksów.
Raport: `PRACA/quality-2.5.0/PODSUMOWANIE.html`.

## Nowości 2.4.3 — myśli, wycieki i pierwszy człon dymka (2026-10-29)

Wynik na wszystkich 220 ocenionych stronach: **95,23%**;
wersja 2.4.2 na tym samym zestawie: 95,11%.
Na stałych wcześniejszych 214 stronach: 95,01% →
95,13%. To wizualna ocena próby przez agenta,
bez pomiaru transkrypcji OCR i bez gwarancji wyniku na nieznanym komiksie.

Dodano ostrożne odtwarzanie kółek myśli, naprawę dużego wycieku maski przy
zachowaniu słów oraz kolejność od pierwszego rzeczywistego członu dymka.
Naprawiono trzy odrzucone obrysy; błędne pary kolejności: 58 → 52.
Brak zaobserwowanych pogorszeń na każdej z 220 stron, 209 wyników bez zmian.
Sześć nowych stron włączono w całości do oceny; wykorzystano je w rozwoju.
Nowe etapy uruchomiono wszędzie; 15 pełnych przebiegów kontrolnych odtwarza
zatwierdzone wyniki. To nie jest 220 świeżych pełnych przebiegów GPU.
Zaliczono 386 testów programu. Raport: `PRACA/quality-2.4.3/PODSUMOWANIE.html`.

## Nowości 2.4.2 — 4koma, dymki połączone i końcówki (2026-10-29)

Wynik na wszystkich 214 ocenionych stronach: **95,01%**,
wcześniej 93,55% na tym samym zbiorze. Wykrywanie F1
95,04%, obrysy 91,27%, kolejność
98,89%. Brak zaobserwowanych pogorszeń na każdej stronie.
To wizualna ocena próby przez agenta, bez pomiaru transkrypcji OCR i bez gwarancji
wyniku na nieznanych tytułach. Wszystkie 1333 oczekiwane kwestie uwzględniono.

Poprawiono czytanie całych pasków 4koma z tytułami, kolejność sąsiednich dymków,
łączenie rzeczywistych członów dymka oraz kontynuację ogonków z obrazu. Katalogi
i wywiady mają osobną, ostrożną kontrolę obrazu i napisów. Nie łączy się samych
prostokątów tekstu na podstawie odległości. Ręcznie zatwierdzone strony są chronione.
214 stron przeliczono nowymi etapami; 12 stron Azumanga dodano do zestawu i
wykorzystano w rozwoju. 12 pełnych przebiegów kontrolnych odtwarza zatwierdzone
wyniki. To nie jest 214 świeżych pełnych przebiegów GPU ani niezależny holdout.
365 testów programu przeszły. Raport: `PRACA/quality-2.4.2/PODSUMOWANIE.html`.

## Nowości 2.4.1 — pełniejsze obrysy (2026-10-29)

Nowy końcowy etap uzupełnia rzeczywiste końcówki jasnych i czarnych dymków.
Odrzuca połączenia z rysunkiem, wieloma kreskami i sąsiednim tekstem. Zachowuje
liczbę kwestii, OCR, kierunek i kolejność; nie zmienia ręcznie zatwierdzonych stron.

Na wszystkich 202 ocenionych stronach: wykrywanie F1 **93,61%**,
geometrie **88,99%**, kolejność **98,56%**,
wskaźnik łączny **93,64%** (wcześniej 93,19%
na tych samych 202 stronach). Naprawiono 15 odrzuconych geometrii; nie wykryto
pogorszeń. Wynik jest oceną wizualną próby, nie gwarancją ani pomiarem transkrypcji OCR.
Zachowano 198 wcześniejszych stron i dodano cztery losowe. Nowy etap przeliczono
wszędzie, pełną analizę od nowa na sześciu kontrolach i czterech nowych stronach.
300 testów przeszło; raport: `PRACA/quality-2.4.1/PODSUMOWANIE.html`.

Lokalne przygotowanie dymków, myśli i narracji do czytnika Nokturn. Program
zapisuje rzeczywiste kontury albo obszary tekstu, kolejność oraz raport kontroli.
Oryginalne strony pozostają niezmienione. Webtoony pomijamy.

## Uruchomienie i instalacja

- **Na tym komputerze:** START.bat albo skrót „Nokturn Bubble Studio”.
- **Instalator EXE:** Nokturn-Bubble-Studio-2.6.1-Setup.exe zawiera całą małą
  paczkę programu. Wybierz folder; instalator utworzy skrót na pulpicie i w menu Start.
- **Paczka ZIP:** rozpakuj cały folder. INSTALUJ.bat kopiuje program do wybranego
  miejsca i tworzy skróty; START.bat uruchamia go bez instalowania skrótów.

Pierwszy start automatycznie przygotowuje prywatny Python i biblioteki, w tym
PyTorch CUDA. Nie wymaga konta Hugging Face, klucza API ani CUDA Toolkit.
Modele pobierają się przy pierwszym przygotowaniu stron i są później używane
z lokalnego cache. Ekran startowy pokazuje przygotowanie środowiska; szczegóły
są w logu. START_KONSOLA.bat uruchamia dotychczasowy tryb z widocznym logiem.

Wymagania: Windows x64, internet podczas przygotowania, aktualny sterownik
NVIDIA: 16 GB VRAM dla pełnej analizy kontekstu; 10 GB dla profilu Szybszy.
Zalecane 32 GB RAM oraz 60 GB wolnego SSD na pierwszą konfigurację **plus**
miejsce na kopie komiksów i raporty. Obliczenia sprawdzono na RTX 5070 Ti 16 GB.
Instalator nie instaluje sterownika NVIDIA. Nie wykonano próby na drugim,
czystym komputerze; EXE nie ma podpisu wydawcy.

## Przygotowanie komiksów

1. Dodaj CBZ/CBR, PDF lub foldery obrazów do WEJSCIE/Komiksy, WEJSCIE/Manga albo
   WEJSCIE/Manhua. Możesz też wskazać własny folder w panelu.
2. Wybierz „Przygotuj / wznów”. Manga w folderze Manga domyślnie ma RTL,
   pozostałe LTR. Nie jest to automatyczne wykrywanie języka.
3. Otwórz „Raport” i „Edytor konturów”. Sprawdź kompletność, obrysy i kolejność;
   samo wysokie confidence nie potwierdza jakości.
4. Kopiuj komiks i sąsiedni plik .nokturn-bubbles.zip z GOTOWE do biblioteki
   Nokturna. Dla folderu obrazów pakiet jest wewnątrz folderu.

```text
Seria\Tom 01.cbz
Seria\Tom 01.cbz.nokturn-bubbles.zip
```

Nie kopiuj PRACA, .runtime ani .nokturn-bubble-review do biblioteki. Pakiet
nie jest osobnym komiksem. Czytnik nie potrzebuje modeli ani GPU na serwerze.
W Nokturn wybierz Ustawienia → Czytanie dymków: pojedynczy dotknięty dymek
lub prowadzenie po kolei. Wymagany jest stronicowany układ i SmartView.

CBZ/ZIP, CBR/RAR, foldery obrazów i PDF są obsługiwane. PDF tworzy pochodny
CBZ z pakietem dymków; do Nokturna kopiuj tę parę plików. Pełny 7-Zip jest
wykrywany albo lokalnie przygotowywany z oficjalnego MSI. Nie zmieniaj źródeł
w trakcie przetwarzania.

## Nowości 2.4.0

Profil **Dokładny** z włączonym odzyskiwaniem myśli i kontrolą OCR analizuje
teraz kontekst całej strony lokalnym modelem Qwen3-VL-4B. Odróżnia galerie
okładek i reklamy, lepiej buduje listy opisów postaci oraz odzyskuje akapity
streszczenia. Dodatkowa skala OCR obejmuje pełne wiersze dużych skanów.
Pola kart postaci pozostają osobnymi przystankami, a całe karty czytają się
w kolejności odpowiadającej układowi strony i LTR/RTL.

Propozycje modelu ograniczają reguły OCR i geometrii. Pojedyncza klasyfikacja
wycinka nie usuwa istniejącego konturu. Etykieta „ilustracja” lub „strona
autorów” również nie uprawnia do usunięcia całej listy. Każdą zmianę analizy
można przywrócić w edytorze przyciskiem „Przywróć wykrycia sprzed analizy
strony”, również z Cofnij/Ponów. Strony wcześniej zatwierdzone pozostają
chronione. Wyniki automatu nadal wymagają kontroli.

Na pełnych **198 stronach i 1216 przystankach** odzyskano 42 kwestie: 38 pól
i akapitów na pięciu stronach opisowych i cztery akapity streszczenia.
Usunięto 244 nadmiary oraz 20 odwróceń kolejności. Poprawiło się 27 stron;
171 pozostałych wyników zachowano dokładnie. Nie wykryto pogorszenia żadnej
strony w mierzonych kryteriach. Reguły nie zawierają nazw tytułów ani
współrzędnych przykładów.

| Miara, identyczne 198 stron | 2.3.6 | 2.4.0 |
| --- | ---: | ---: |
| Wykrywanie — F1 | 83,40% | 93,59% |
| Akceptowane geometrie prawdziwych regionów | 86,94% | 87,76% |
| Poprawne pary kolejności dopasowanych kwestii | 97,97% | 98,55% |
| Wskaźnik łączny | 89,23% | 93,19% |
| Strony bez uwag we wszystkich kryteriach | 55/198 | 71/198 (35,86%) |

Braki: 98 → 56; nadmiary: 347 → 103; odwrócone pary: 83 → 63.
Wzrost akceptacji geometrii wynika z nowych prostokątów tekstu i przebudowy
pól opisowych. Istniejące ogonki dymków nie zostały naprawione w tej iteracji.
142 geometrie nadal odrzucone. Wskaźnik łączny jest średnią geometryczną
trzech miar, a nie odsetkiem bezbłędnych stron.

Pomiar obejmuje wszystkie dotychczasowe 182 strony oraz 16 nowych losowych
stron (osiem nowych serii mangi i osiem niewykorzystanych stron komiksów).
Pełne modele przeliczyły wszystkie 198 stron końcowym kodem. Nowy przebieg
semantyczny rozpoczął się z pustym cache i odtworzył ocenione wyniki.
Wszystkie wcześniejsze listy czytania zachowano. Błędną wcześniejszą ocenę
Sleepy Princess wycofano dla obu wersji: rzekomy ogonek był mankietem ubrania.
Nie zaliczono tej korekty jako poprawy algorytmu.

To ocena wizualna agenta, bez niezależnego eksperta i masek pikselowych.
Nie zmierzono transkrypcji OCR znak po znaku. Dymki złożone porządkuje się
według pierwszego członu, bez mierzenia wewnętrznego przeplatania głosów.
Próba nie reprezentuje całej biblioteki. Szczegóły, przykłady i wszystkie
strony: `PRACA/quality-2.4.0/PODSUMOWANIE.html`.

Nowy model pobiera się przy pierwszym przetwarzaniu w profilu Dokładny:
około 9 GB. Nie wymaga konta ani API. Obrazy pozostają na komputerze.
Wagi mają przypiętą wersję i sumy SHA-256. Etapy zwalniają pamięć GPU
kolejno; dla pełnej analizy kontekstu przyjmujemy 16 GB VRAM i zalecamy
32 GB RAM. Sprawdzony model przekracza 12 GB zajętej pamięci GPU w
największych zapytaniach, więc tej funkcji nie deklarujemy dla kart 10 GB.
Profil Szybszy zachowuje
dotychczasową analizę bez dodatkowego modelu kontekstu.

## Zmiany 2.3.6

Poprawiono współpracę kontroli obrysów z odzyskiwaniem myśli. Kontury
nakładające się na inne dymki są teraz sprawdzane przed szukaniem brakującego
tekstu. Odrzucona maska nie może już blokować kwestii poza jej końcowym obszarem.
Co najmniej trzy niezależne prostokąty tekstu, ułożone wyraźnym schodkiem
w jednym kadrze, czytają się od góry. Kolumny o wspólnej wysokości zachowują
LTR/RTL; mieszane grupy z dymkami zachowują regułę krótkiej odpowiedzi przy
dłuższej wypowiedzi. Reguły nie zawierają nazw tytułów ani współrzędnych stron.

Na ocenionej próbie odzyskano trzy myśli na jednej stronie Genikasuri.
Pozostałe 181 wyników zachowano dokładnie, podobnie jak wszystkie wcześniejsze
geometrie, kotwice i linie OCR. To poprawka wspólnej kolejności etapów, ale
rzeczywistą korzyść potwierdzono tutaj na jednym przypadku; nie jest to dowód
uniwersalności. Pozostają na tej stronie scalenie dolnej myśli i stary błąd
kolejności dolnych wypowiedzi.

Pomiar obejmuje **182/182 strony i 1131 oczekiwanych przystanków**. Zachowano
wszystkie wcześniejsze 170 definicji; dodano 12 losowych stron, w tym sześć
nowych serii mangi. Pełne modele GPU przeliczyły wszystkie strony końcowym
kodem. 236 testów programu przeszło; cztery testy API pełnego serwera są poza
zakresem samodzielnego narzędzia. Raport przechodzi kontrolę Playwright.

| Miara, ten sam zestaw 182 stron | 2.3.5 | 2.3.6 |
| --- | ---: | ---: |
| Wykrywanie — F1 | 82,28% | 82,42% |
| Akceptowane geometrie prawdziwych regionów | 87,78% | 87,81% |
| Poprawnie uporządkowane pary dopasowanych kwestii | 97,88% | 97,89% |
| Wskaźnik łączny | 89,08% | 89,15% |
| Strony bez uwag we wszystkich kryteriach | 49/182 | 49/182 (26,92%) |

Wzrost akceptacji geometrii wynika z nowych prostokątów tekstu — istniejące
kontury nie zostały naprawione w tej iteracji. Wzrost miary kolejności wynika
z dodania poprawnych par; wcześniejsze 81 odwróceń pozostają.
Braki: 100 → 97, nadmiary: 344; odrzucone geometrie:
126. Wszystkie te błędy pozostają w ocenie.

To szacunek na tej próbie, z wizualnych opisów agenta, bez niezależnej oceny
eksperckiej i masek pikselowych. Miara kolejności obejmuje obecne dopasowania;
braki obniżają F1. Dymki złożone oceniamy według początku, bez przeplatania
wewnętrznych członów. Nie mierzono transkrypcji OCR znak po znaku. Prostokąty
ukośnego tekstu przy sąsiednich blokach nadal wymagają kontroli. Wynik łączny
nie oznacza udziału bezbłędnych stron ani skuteczności całej biblioteki.

Szczegóły, wszystkie strony, wzorce i procenty obu wersji:
`PRACA/quality-2.3.6/PODSUMOWANIE.html`.

## Zmiany 2.3.5

Dodano odwracalny filtr reklamy wydarzenia z harmonogramem oraz sparowanych
podpisów Translation/Lettering poza kadrami. Wymaga kilku zgodnych dowodów
z OCR i położenia; pojedynczy tytuł, adres, hasło lub brak liter nie wystarcza.
Na ocenionej próbie usunął 12 wykryć reklamy i dwa podpisy, bez zmiany
pozostałych 168 wyników. Nie rozpoznaje wszystkich reklam: mozaiki okładek,
galerie i inne formaty nadal dają fałszywe przystanki. Powtarzające się tytuły
mogą wywołać ostrzeżenie, bez automatycznego usuwania.

Edytor udostępnia **„Przywróć wykrycia sprzed filtra tej strony”**. Przywrócenie
obejmuje regiony, kolejność i diagnostykę; działa Cofnij/Ponów. Szersza opcja
„Uwzględniaj także tekst poza dymkami” omija ten filtr. Zatwierdzone ręcznie
strony pozostają chronione jak wcześniej.

Na prośbę użytkownika każda iteracja ma mieć procentowy pomiar wszystkich
dotąd ocenionych stron. Teraz ręcznie opisano **170/170 stron, 1059 przystanków**,
w tym 32 nowe strony (20 losowych i 12 kontroli końcowych stron komiksów).
Wszystkie 19 wcześniejszych definicji zachowano. Pełne modele GPU przeliczyły
170 stron; 208 testów programu i rzeczywistych okien przeszło, cztery testy
API pełnego serwera są poza zakresem. Raport przechodzi kontrolę Playwright.

| Miara, ten sam zestaw 170 stron | 2.3.4 | 2.3.5 |
| --- | ---: | ---: |
| Wykrywanie — F1, z pominięciami i nadmiarem | 81,75% | 82,23% |
| Wizualnie akceptowane obrysy prawdziwych wykryć | 87,05% | 87,05% |
| Poprawnie uporządkowane pary dopasowanych kwestii | 97,72% | 97,72% |
| Wskaźnik łączny, średnia geometryczna trzech miar | 88,59% | 88,77% |
| Strony bez uwag we wszystkich kryteriach | 46/170 | 47/170 (27,65%) |

To **szacunek na tej próbie**, z wizualnych opisów agenta, bez niezależnej
oceny eksperckiej i bez wzorcowych masek pikselowych. Kolejność dotyczy tylko
dopasowanych przystanków, a nie odsetka całych stron; brakujące kwestie obniżają
F1. Nie mierzono zgodności transkrypcji OCR znak po znaku. Złożone dymki są
porządkowane według początku, bez oceny przeplatania tekstu wewnątrz płatów.

Pozostaje 94 brakujących i 323 dodatkowe przystanki, 79 odwróconych par oraz
125 niezaakceptowanych obrysów wśród 965 dopasowań. Kolejność LTR: 96,52%,
RTL: 98,60%. Duża liczba nadmiarów na reklamach i galeriach obniża szczególnie
wynik komiksów zachodnich. Nie należy przenosić tych procentów na całą bibliotekę.

Szczegóły, ocena każdej strony, wzorce i historia procentów:
`PRACA/quality-2.3.5/PODSUMOWANIE.html`.

## Zmiany 2.3.4

Rozdzielanie szerokich obszarów tekstu na osobne kolumny myśli i narracji.
Każda kolumna wymaga co najmniej dwóch czytelnych linii i szerokiego odstępu;
niepewne przypadki oraz kontury dymków pozostają bez zmian. W WITCHRIV i
Kagurabachi dwie osobne myśli nie są już jednym przystankiem. Wszystkie
wcześniejsze linie OCR pozostają objęte, a kolumny czytają się od prawej.
Reguła nie zawiera nazw tytułów ani współrzędnych konkretnej strony.

Pełne modele GPU przeliczyły 138 stron, w tym 20 nowych (10 manga, 10 komiksy).
Dwie strony poprawiono; 136 wyników, w tym wszystkie nowe kontrole, jest
identycznych z 2.3.3. To potwierdzenie na dwóch przykładach z różnych mang,
nie gwarancja rozpoznania wszystkich kolumn. 172 testy programu przeszły;
Playwright sprawdził raport na komputerze i telefonie oraz wszystkie obrazy.

Rozszerzona ręczna referencja obejmuje 19 stron i 113 przystanków; zachowano
wcześniejsze 13 definicji. Na tej samej rozszerzonej próbie odnalezione
przystanki wzrosły ze 102 do 104, brakujące spadły z 11 do 9, a kompletne
strony z 7 do 9. Pozostało 8 odwróconych par i 142 dodatkowe przystanki,
z których 135 pochodzi z dwóch reklam. Karta postaci ma tekst połączony
w zbyt duże bloki. Nowe trudne strony obniżają wyniki oceny; nie są ukrywane
ani usuwane z próby. To opisy agenta, nie niezależna ocena ekspercka.

Szczegóły i jawne listy: `PRACA/quality-2.3.4/PODSUMOWANIE.html`.

## Zmiany 2.3.3

Poprawiono kolejność krótkich i długich wypowiedzi we wspólnym kadrze,
obsługę nieobramowanych wypowiedzi nad wykrytą siatką kadrów oraz rozróżnienie
dwurzędowej siatki od dłuższych pasków 4-koma. Silnie nakładające się obszary
zachowują ostrożniejsze sortowanie. Zachowano ręczny tryb kolumnowy.
Przegląd zmian potwierdził poprawę rzeczywistego dialogu na 11 stronach;
4 inne zmiany porządkują nadal błędnie wykryte napisy/efekty.

Reguła tekstu poza dymkiem została sprawdzona także na narracji przy postaciach
i wypowiedzi nad samochodem. Oba obszary zachowują wszystkie linie OCR.
Zestaw porównawczy ma 118 stron i 800 regionów, w tym 20 nowych stron.

Dodano pełne listy 73 przystanków na 13 stronach. W tej konkretnej próbie
odwrócone pary wypowiedzi spadły z 16 do 7. Pozostały 1 pominięty przystanek
i 16 dodatkowych, z czego 12 pochodzi z jednej reklamy. 6/13 stron jest
kompletnych w zakresie tych kryteriów czytania; to nie ocena idealności obrysów.
Referencje i interpretacje połączonych dymków są jawne w raporcie.

Laboratorium zapisuje dokładne kotwice tekstu i pozwala sprawdzać samą
kolejność bez ponownego liczenia obrysów. Wynik zachowuje pochodzenie
oryginalnych obliczeń oraz osobną informację o przeliczeniu układu.

## Zmiany 2.3.2

Dodano ostrożne odzyskiwanie długiego ogonka na rastrowym tle. Nowy obszar
musi mieć stabilne oparcie w obrazie, zachować korpus dymka oraz tekst i mieścić
się w ograniczeniu przyrostu powierzchni. Nie dopasowujemy sztucznego trójkąta.
Próba porównawcza obejmuje 98 stron, w tym 41 nowych stron mangi i komiksów
kolorowych. Kierunki RTL/LTR, narracja, czarne i kolorowe dymki mają osobne
przykłady kolejności. To nadal nie jest gwarancja bezbłędności każdego stylu.

Pliki pomocnicze macOS `__MACOSX` i `._*` nie są już traktowane jako strony.
W dostarczonym 2000AD usuwa to 32 pozorne strony; prawdziwe obrazy pozostają
w oryginalnej kolejności. Filtr działa dla CBZ, CBR i folderów obrazów.

## Zmiany 2.3.1 i kontrola jakości

Wersja 2.3.1 ogranicza obrys obejmujący rysunek do samego tekstu wyłącznie
przy zgodnych dowodach: detektor wskazuje tekst poza dymkiem, obrys ma
nieregularny kształt i niejednolite wnętrze, a mniejszy obszar zachowuje
wszystkie pozycje słów z OCR. Poprawne dymki kolorowe i półprzezroczyste
nie są odrzucane przez samą niejednolitość tła. Oryginalny obrys zostaje
w diagnostyce, a identyfikator i miejsce wypowiedzi w kolejności pozostają.

Do oceny kolejnych zmian dodano `regression_gate`: porównuje wynik z zamrożoną
wersją, blokuje każdą niezatwierdzoną zmianę i wymaga potwierdzenia, że korekta
nie ucina odczytanych słów. Jest to kontrola na zdefiniowanej próbce, nie
gwarancja braku błędów na dowolnym komiksie.

Funkcje wprowadzone w 2.3:

- Poprawiona kolejność wierszy/kolumn, kadry bez wypowiedzi, ukośne kadry
  i przypisanie do kadru według tekstu zamiast ogonka.
- Niezależny przebieg OCR potrafi odzyskać myśli poza dymkami, także tam,
  gdzie nie wykryto ramki kadru. Ta opcja jest w panelu domyślnie włączona.
- Tekst bez balonu nie dostaje sztucznego obrysu. Niepewne i kolidujące maski
  ustępują obszarom tekstu i trafiają do kontroli.
- Nowy przycisk **„Losuj i testuj strony…”**: próbka różnych tytułów,
  oryginał obok wyniku, numery kolejności, rejestr błędów i eksport oceny JSON.
- Ikona, ekran startowy z postępem, instalator i skróty.

**JAKOSC.md** opisuje powtarzalną metodę doszlifowywania, konkretne poprawki,
próbki, pomiar kolejności i ograniczenia. To narzędzie do iteracyjnej pracy,
nie obietnica automatycznej perfekcji. Reklamy, SFX, nazwy postaci, otwarte
balony i ogonki nadal mogą wymagać korekty. Odzyskiwanie OCR dotyczy alfabetu
łacińskiego; japoński tekst pionowy wymaga osobnego profilu.

Pełne „Uwzględniaj także tekst poza dymkami” jest osobną, szerszą opcją i może
objąć tytuły/reklamy. Kontrola OCR nie usuwa dymków tylko dlatego, że nie udało
się odczytać liter. W nowej analizie pomijane mogą być znane SFX z nieudanym
obrysem; takie decyzje są zapisane w diagnostyce. Zatwierdzone strony zachowujemy.

## Ręczne korekty

„Edytor konturów” lub SPRAWDZ.bat. Wybierz pakiet obok komiksu. Zielony to
kontur, pomarańczowy obszar bez bezpiecznego obrysu, żółty wybór. Numery są kolejnością.

- Dodaj/zastąp kontur punktami. Enter kończy, Escape anuluje, Backspace cofa punkt.
- Usuń fałszywe regiony, dodaj pominięte kwestie i przestaw kolejność.
- Ctrl+Z/Ctrl+Y: cofnij/ponów; +/− i Ctrl+kółko: powiększenie.
- Po sprawdzeniu oznacz stronę „Sprawdzona” i zapisz. Każda zmiana cofa zatwierdzenie.

Pierwsza poprzednia wersja pakietu pozostaje jako .before-review. Raport HTML
jest migawką automatu; zapisane korekty widać w edytorze. Sprawdź również strony
bez ostrzeżeń. Zatrzymanie kolejki zachowuje ukończone checkpointy.

## Ustawienia serii i aktualizacja

Opcjonalny bubble-studio.json w folderze serii:

```json
{"direction":"rtl","layout":"columns","quality":"precise","include_free_text":false,"skip":false}
```

layout: auto/rows/columns/single; quality: precise/fast. `columns` jest przydatne
dla 4-koma. Ustawienia dziedziczą się od WEJSCIE w dół. Webtoon/Webtoons/Webtoony
i .yacreaderlibrary są pomijane niezależnie.

Zamknij program przed aktualizacją. Instalator zachowuje WEJSCIE, GOTOWE, PRACA
i prywatny .runtime; zastępowane pliki programu kopiuje do .updates/DATA.
Nowy pipeline przelicza niezatwierdzone strony, a zatwierdzone korekty chroni.
Poprzedni pakiet odkłada jako .before-upgrade-DATA. Nie używaj --discard-verified
bez świadomej decyzji o odrzuceniu zatwierdzonych korekt.

Na inny komputer można przenieść mały ZIP/EXE i pobrać zależności od nowa albo
przenieść **cały zainstalowany folder z ukrytym .runtime**. START naprawia
ścieżki prywatnego Python po przeniesieniu. Drugi komputer nadal potrzebuje
zgodnego Windows, GPU i sterownika. Utwórz tam skrót przez INSTALUJ.bat albo
`INSTALUJ.ps1 -UseSource`.

## Modele, prywatność i narzędzia dla zaawansowanych

RT-DETR + YOLO26 + YOLOv8m + MA-Net + SAM 2.1 large, lokalny RapidOCR/ONNX na CPU.
Zachowano przypięte rewizje i sprawdzanie SHA wag. Nie wysyłamy komiksów do API.
Źródła i uwagi dotyczące licencji są w RESEARCH.md; wygląd produktu nie zmienia
warunków licencyjnych zależności i danych treningowych.

PRZETWORZ.bat uruchamia kolejkę, DIAGNOSTYKA.bat sprawdza rzeczywiste obliczenia CUDA.
Logi są w tools/bubble_studio/.runtime. Dostępne są runner, benchmark,
quality_lab i evaluate jako moduły tools.bubble_studio. --offline używa cache;
--recover-dialogue włącza odzyskiwanie; --text-guard off wyłącza ostrzeżenia OCR.
Przykłady porównywania wersji i referencyjnych masek są w JAKOSC.md.

Budowa paczki: Windows PowerShell 5.1, `scripts/build_setup.ps1 -PythonPath SCIEZKA`.
ZIP i samorozpakowujący instalator EXE trafiają do dist; zawierają program,
grafikę i instrukcje, bez komiksów, raportów użytkownika i wielogigabajtowego runtime.

## Dodatkowy eksport do tłumaczenia

Eksport jest wyłączony przy starcie. W sekcji „Dodatkowy eksport tekstu do
tłumaczenia” zaznacz „Zapisuj także tekst” i wybierz format. Przy HTML powstają
pliki `.tekst.html`, `.tekst.txt` i audyt `.tekst.json` obok gotowego komiksu.
Każda strona ma numer i nazwę oryginalnej strony/pliku; każdy dymek numer
z pakietu Nokturna. Ręczne korekty kolejności są respektowane przy kolejnym
eksporcie. HTML otworzysz w przeglądarce i skopiujesz z formatowaniem do edytora.

Przycisk „Tekst z gotowych pakietów…” korzysta z folderu „Gotowe komiksy i
pakiety”. Najpierw zapisz i zamknij edytor dymków. Eksport nie uruchamia detektora
ani nie zapisuje pakietu dymków. Błąd eksportu nie usuwa gotowych dymków.
Eksport całego tomu może potrwać; zatrzymanie nie publikuje niepełnego tekstu
bieżącego tomu, wcześniejsze ukończone pliki pozostają.

Opcja pozostałych napisów dopisuje osobną sekcję pod dymkami danej strony.
Nie gwarantuje ich dokładnego przeplatania z dialogiem. Puste i niepewne odczyty
są oznaczone. Transkrypcja wymaga sprawdzenia, zwłaszcza przy piśmie odręcznym,
językach innych niż łacińskie, tekście pionowym i odstępach między słowami.
Nie oceniano jej procentowo w wyniku jakości dymków.

PDF jest renderowany lokalnie (200 dpi, maks. 3200 pikseli na dłuższym boku).
Obsługiwane są skany, tekst kopiowalny i strony mieszane oraz obrót/CropBox.
Chroniony hasłem PDF wymaga wcześniejszego usunięcia hasła. Kolejność stron
zachowuje kolejność PDF. Oryginalny PDF nie jest zmieniany. W trakcie importu
z włączonym eksportem używana jest pasująca warstwa tekstowa i OCR; eksport
już gotowego CBZ używa OCR, bez szukania oryginalnego PDF na dysku.

Opcje konsolowe: `--text-export html|txt|md` (domyślnie `off`),
`--export-all-text`; do gotowego pliku lub folderu `--export-only --input ...`.
