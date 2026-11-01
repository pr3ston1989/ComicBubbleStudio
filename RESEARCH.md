# Bubble Studio 2 — research i decyzje (2026-10-03)

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


### Źródła modelu 8B

- [Oficjalny Qwen3-VL-8B, Apache 2.0](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct).
- [Obsługa Windows i CUDA w bitsandbytes](https://huggingface.co/docs/bitsandbytes/main/en/installation).
- Przypięte dane i SHA-256: assets/scene-model.json, rewizja 0c351dd01ed87e9c1b53cbc748cba10e6187ff3b.
- Transformers 4.57.6, bitsandbytes 0.50.2, Accelerate 1.15.0; bez wykonywania kodu repozytorium modelu.
- Na identycznych 298 stronach i przy tych samych zabezpieczeniach audyt 8B usunął 33 fałszywe przystanki bez regresji. Wariant 4B nadal pomijał trzy prawidłowe kwestie i został odrzucony.
- Osiem świeżych odpowiedzi po zapisie i ponownym wczytaniu NF4 zgadzało się dokładnie z modelem przed zapisem. Osobno sprawdzono działanie bez źródłowych wag i bez Internetu.

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

## Aktualizacja 2.4.0 — lokalne rozumienie stron (2026-10-28)

Włączono [Qwen3-VL-4B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct),
rewizja ebb281ec70b05090aa6165b016eac8ec08e71b17, licencja Apache-2.0.
Transformers 4.57.6, BF16, SDPA, deterministyczne generowanie bez próbkowania.
13 plików modelu i ich SHA-256 opisuje assets/context-model.json. Model działa
lokalnie; pobieramy tylko dane, bez trust_remote_code i bez wykonywania kodu
repozytorium. Cache wiąże wersję, instrukcję i rzeczywiste piksele wejścia.

Odrzucono usuwanie całych stron na podstawie etykiet credits/illustration:
usuwało rzeczywiste tytuły i drobne kwestie. Odrzucono pojedyncze usuwanie
konturów na podstawie roli wycinka: tracone były dwa wąskie dymki i podpis
miejsca. Zabezpieczenie zachowuje wszystkie indywidualne kontury.

Profile wymagają co najmniej trzech rozpoznanych etykiet pól oraz klasyfikacji
całej strony. OCR w skali do 2200 px uzupełnia odczyt natywnych kafli; nie
zastępuje go. Model może zasugerować granice akapitów, lecz nie łączy różnych
pól. Identyfikatory linii muszą istnieć i być unikalne. Recap wymaga spójnej
kolumny prozy, dodatniej propozycji narracji, co najmniej trzech wierszy i
100 liter; wyklucza tekst prawny. Odpowiedzi modelu nie są oceną poprawności.

Wyniki, nieudane propozycje, wszystkie instrukcje, hash wejść, niezależny pełny
przebieg i porównania są w PRACA/quality-2.4.0. Większość zysku pochodzi z
usunięcia nadmiarów galerii; osobno wykazano 42 odzyskane przystanki i zmianę
kolejności. Nie potwierdzono poprawy istniejących ogonków.


## Aktualizacja 2.2 — kontrola bez zmiany dobrych masek (2026-10-04)

Rozszerzono test o Dandadan (62 strony: pełne rozdziały 189 i 205 oraz 24
próbki tomu 10), Azumangę (32 próbki omnibusu) i Astro City (30 stron z zeszytów
1/4/9/14/18). Dodano poprzednie 24 strony pięciu serii: 148 stron, 917 regionów.
Domyślny etap OCR zachował istniejące wyniki geometryczne dokładnie; oznaczył
32 regiony z niepotwierdzonym tekstem. Nie są to 32 udowodnione błędy: są tam
również poprawne „!”, „…” i małe wypowiedzi. Nie zmieniano sposobu segmentacji.

Źródło OCR: [RapidOCR](https://github.com/RapidAI/RapidOCR),
[oficjalna dokumentacja](https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/usage/).
Użyto rapidocr-onnxruntime 1.4.4 z dołączonymi wagami PP-OCRv4, onnxruntime
1.23.2, CPU, cztery wątki. Wagi są sprawdzane SHA-256 przed wczytaniem.
Domyślne modele nie stanowią uniwersalnego OCR wszystkich języków i krojów pisma.

Odrzucono eksperyment usuwania regionów bez czytelnego OCR i bez silnego
komponentowego dowodu liter. Usunął 17 regionów w zestawie; kontrola wzrokowa
wykazała utratę prawidłowej interpunkcji i krótkich wypowiedzi. Filtr nie jest
dostępny w wydaniu 2.2. Kontrola OCR tylko zapisuje diagnostykę i ostrzeżenia.
Rozpoznany tekst etykiety/znaku nie dowodzi, że obiekt jest dymkiem — takie
fałszywe wykrycia pozostają do ręcznej kontroli.

Opcjonalne odzyskiwanie: label=free-text, score>=0.55, >=92% box wewnątrz
wykrytego kadru, brak >60% pokrycia przez istniejący region, co najmniej trzy
łacińskie litery OCR z pewnością >=0.85 i wielowyrazowa wypowiedź lub interpunkcja.
W czterech stronach Azumangi dodano 2/1/3/1 wypowiedzi; istniejące geometrie
porównano przed/po. Same SLAM/CLENCH zostały wykluczone. Dodane regiony są
prostokątami tekstowymi, nie fikcyjnymi balonami. To heurystyka, nie semantyczne
rozróżnienie dialogu/SFX/scenografii; domyślnie wyłączona.

Astro City sprawdzono wzrokowo na wszystkich 30 podglądach, wybrane kolorowe
strony w większym powiększeniu. Fioletowe, różowe, kremowe i zielone pola
tekstowe miały użyteczne kontury już w 2.1, więc nie rozluźniano walidacji
koloru. Pozostają pojedyncze etykiety scenografii i SFX, nieregularne ogonki,
kolejność oraz możliwe przeoczenia. Nie wykonano pełnej ręcznej referencji masek;
liczby konturów i brak prostokąta nie dowodzą kompletności ani jakości komercyjnej.

## Aktualizacja 2.1 — lokalne testy GPU (2026-10-04)

Sprawdzono istniejący pipeline na Windows / RTX 5070 Ti 16 GB, PyTorch
2.10.0+cu128, rzeczywistych przypiętych wagach RT-DETR, SAM 2.1, YOLO26 i YOLOv8m.
Pierwsza próbka obejmuje 12 stron pięciu serii: Amazing Spider-Man, Vampirella,
Aquaman, Dandadan i My Dress-Up Darling. Wersja 2.0 zwróciła 97 regionów,
z czego 46 prostokątów. To liczba wyników automatu, a nie liczba prawdziwych dymków.

Potwierdzony wzrokowo błąd walidacji: luźny text box obejmował czarne fragmenty
obramowania, narożniki poza balonem oraz niekiedy litery sąsiedniego dymka.
Algorytm traktował kontrastowe komponenty jako litery i odrzucał poprawne maski.
Komponenty na brzegu text box i fragmenty bez zgodnego otaczającego tła nie są
teraz wiarygodnym dowodem tekstu. Kontrolę przeprowadza się po dwupikselowym
rozszerzeniu na tusz/antyaliasing. Nadal możliwe są niedokładne boxes i przeoczenia.

### Dodatkowe metody i decyzje

- [MA-Net TOONTRA](https://huggingface.co/toontra-research/toontra-manet-bubble-segmentation):
  model wycinków RGB, ResNet34, letterbox 512×512, normalizacja ImageNet i próg
  z checkpointu. Testowany na dostarczonych stronach, włączony jako kandydat,
  nie zamiennik całej detekcji. Autor podaje Dice/IoU własnego zbioru mang;
  nie przenosimy ich na Marvel/DC. Wagi Apache-2.0, dane mają osobne warunki.
  Rewizja f2f1c4eb1b2f7c492146da82d51fa474f54560cc, SHA-256
  6350601676c9e2b5448cf4cf109fb459a1f805d4101cfe34d4db47661f28df21.
  Wczytywany wyłącznie state_dict przez torch.load(weights_only=True), bez remote code.
- Zamknięte wnętrza koloru: dominujący kolor w obszarze tekstu, komponenty
  połączone, wypełnienie otworów po literach, zgodność dwóch tolerancji ≥0,96
  i obecność kontrastowych krawędzi. Nie są to generowane elipsy. Sygnał
  obrazu pozwala uzyskać gładkie krawędzie i cienkie, długie ogonki.
- Wybór maski: obecność krawędzi i objęcie wiarygodnych liter, z małym udziałem
  pewności modelu. Pewność różnych modeli nie jest skalibrowana między nimi.
- Połączony balon może być większy od pojedynczej detekcji jego części.
Detekcje tekstu objęte istniejącym wielokątem nie tworzą drugiego przystanku.
  Zamknięty kontur może odzyskać także tekst bez wykrytego balonu.

Mechanika komponentów/morfologii opiera się na
[OpenCV](https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html).
[Google opisuje Bubble Zoom](https://blog.google/products-and-platforms/platforms/google-play/google-play-books-introduces-bubble-zoom/)
jako system wytrenowany do identyfikacji dymków i ich powiększania. Publiczny
opis nie podaje porównywalnego benchmarku krawędzi ani wag; nie deklarujemy
osiągnięcia lub przekroczenia jego jakości na podstawie liczby konturów.

### Kontrola poza próbką rozwojową

Kolejne 12 stron tych samych pięciu serii wykorzystano dopiero do kontroli,
po pierwszych poprawkach. Kontrola wykazała wyciek bieli otwartego dymka mangi
do marginesu i rysunku. Zaostrzono generator koloru: wymaga zamknięcia także
przy rzeczywistym brzegu strony. Wyuczone segmentery nadal obsługują fizyczne
ucięcie balonu; reguła generatora koloru nie zmienia tej zasady walidatora.
Po tej poprawce powtórzono kontrolę. To walidacja użyta do dalszej poprawki,
a nie nietknięty test końcowy ani zbiór referencyjnych masek.

Dodano benchmark pełnego pipeline i evaluate.py: dopasowanie regionów 1:1,
przeoczenia, dodatkowe regiony, IoU i boundary F-score. Oceniane są tylko ręcznie
zatwierdzone strony tego samego wydania. Nie wygenerowano niezależnych ręcznych
masek wszystkich próbek, więc nie raportujemy procentowej accuracy ani recall
na komiksach. Kontury, ogonki, fałszywe wykrycia i kolejność wymagają kontroli.

Poniżej zachowano wcześniejszy audyt 1.x/2.0 i jego ograniczenia jako kontekst.

### Wyniki końcowego przebiegu 2.1

| Zestaw | Strony | Regiony 2.0 | Prostokąty 2.0 | Regiony 2.1 | Prostokąty 2.1 |
|---|---:|---:|---:|---:|---:|
| Rozwój | 12 | 97 | 46 | 75 | 1 |
| Kontrola po poprawce wycieku | 12 | 96 | 36 | 75 | 0 |

Łącznie 82 → 1 prostokąt; to zmiana struktury wyników, nie 98,8% accuracy.
Różnica regionów wynika m.in. z łączenia fizycznie połączonych balonów i usuwania
powtórnych detekcji i pomijania obiektów bez wykrytego tekstu. Pominięte obiekty
są w diagnostyce i wymagają sprawdzenia pod kątem przeoczeń detektora tekstu.
Nadal są fałszywe dymki na SFX/podpisach/ilustracjach, niedokładne ogonki
i otwarte balony. Wzrokowa kontrola nie zastępuje pełnej anotacji.

Dodatkowo przetworzono cały Aquaman 29 (25 stron), wyeksportowano i zweryfikowano
pakiet Nokturn oraz identyczność kopii oryginału: 144 kontury, 1 prostokąt,
24 strony wskazane przez automat do kontroli. Czas przetwarzania stron i eksportu
wyniósł 55,4 s, bez pierwszej instalacji i ładowania modeli; nie jest to benchmark
sprzętu. Pakiet nie został ręcznie zatwierdzony. Wszystkie obliczenia lokalne.

## Problem, nie marketing

W dostarczonym Aquamanie 29: 25 stron, 198 regionów typu bubble, z czego 135
miało kontur, a 63 prostokąt awaryjny (31,8%). Dodatkowe 50 regionów typu text
obejmowało także okładkę i reklamy. To audyt struktury wyników, **nie pomiar
dokładności** — nie ma ręcznie oznaczonych masek referencyjnych.

Wersja 1 ignorowała maski YOLO, choć model je zwracał. SAM dostawał tylko
prostokąt, a walidator wymagał objęcia 94% całego prostokąta tekstu, łącznie
z pustymi narożnikami. Odrzucał też maski na fizycznym brzegu strony.

## Porównanie źródeł pierwotnych

| Kandydat | Rola i dowody | Decyzja |
|---|---|---|
| [ogkalu RT-DETR v2](https://huggingface.co/ogkalu/comic-text-and-bubble-detector) | Autor opisuje ok. 11 tys. obrazów: manga, webtoon, manhua, komiksy zachodnie. Zwraca obszary dymków i tekstu, nie kontury. | Zachować jako szeroki detektor, także na nakładających się kaflach. |
| [ShadowB YOLO26 Manga109](https://huggingface.co/ShadowB/Manga109-panel-balloon-text-yolov26-segmentation) | Rzeczywiste maski kadrów, tekstu i balonów; podział danych według książek. Autor zastrzega generalizację poza mangę. | Wykorzystać maski w natywnej rozdzielczości, nie tylko boxes. Nie traktować metryk Manga109 jako jakości dla Marvel/DC. |
| [Jzahrani YOLOv8m](https://huggingface.co/Jzahrani/yolov8m_seg-speech-bubble) | Przykłady kolorowych komiksów i mang, bez publicznego solidnego benchmarku. Autor ostrzega o falujących krawędziach. | Dodatkowy segmenter, eksperymentalny i opcjonalny; kandydat do porównania, nie gwarantowana poprawa. |
| [SAM 2.1](https://huggingface.co/docs/transformers/v4.57.1/model_doc/sam2) | Segmentacja z box + punktami dodatnimi/ujemnymi; ogólny model, bez rozumienia dialogu. | Kontrolowane doprecyzowanie; większy wycinek i ponowna próba tylko przy problemach. |
| [SAM 3/3.1](https://github.com/facebookresearch/sam3) | Segmentacja po pojęciu/box/points. Dostęp do wag wymaga akceptacji i tokena. SAM 3.1 koncentruje się także na śledzeniu wideo. | Nie domyślnie: nie spełnia wymogu bezobsługowej instalacji, brak dowodu przewagi w obrysie dymków. |
| [Magi](https://github.com/ragavsachdeva/magi) | Kadry, tekst, postacie, dopasowanie tekstu do mówiącego. Repo ogranicza modele/dane do badań akademickich; przykłady używają remote code. | Nie włączać do domyślnego narzędzia o aspiracjach komercyjnych. |

Implementacja odczytu masek: [oficjalne API Ultralytics](https://docs.ultralytics.com/tasks/segment).
Przypisanie autora wypowiedzi i kontur są różnymi problemami. Zachowujemy ogonki,
pozycję na stronie i oryginalny rysunek; nie deklarujemy automatycznej identyfikacji
postaci. Ogólny VLM nie jest potrzebny do wyznaczania pixel-perfect maski.

## Próba na rzeczywistych stronach

CPU, imgsz 1280, conf 0,35, natywne maski; identyczne obrazy Aquamana,
przypięte rewizje wag i Ultralytics 8.4.43. Bez SAM, walidacji ani oceny ground truth:

| Strona | Maski YOLO26 Manga109 | Maski dodatkowego YOLOv8m |
|---|---:|---:|
| 4 | 13 | 16 |
| 6 | 9 | 9 |
| 22 | 0 | 3 |
| 23 | 2 | 2 |

Ocena wizualna: drugi model pomaga na kolorowej stronie i na stronie 22 z białym
tłem/różnymi kolorami. Na stronie 23 łączy dwa połączone balony w jeden obszar;
na stronie 6 ma przeoczenia i drobną wyspę poza dymkiem. Kontury bywają falujące,
ogonki nie zawsze pełne. Z tego powodu dodatkowy model domyślnie uczestniczy
w ensemble, ale można go wyłączyć. Te liczby nie dowodzą dokładności ani
uniwersalności; nie porównujemy ich do całego v1 jako miary accuracy.

## Plan wdrożenia

1. Maski wyspecjalizowane + RT-DETR; walidacja tekstu i granic, retry SAM,
   diagnostyka źródła maski i prostokąta awaryjnego. Bez generowania liter/rysunku.
2. Konfiguracja serii, profile szybki/dokładny, kolejka z postępem, przerwanie
   i wznowienie; oryginały nietknięte; webtoony pomijane.
3. Kontrola redakcyjna: powiększenie, ręczny wielokąt, cofanie, kolejność,
   przechodzenie do stron wymagających sprawdzenia, bez utraty zatwierdzonych korekt.
4. Testy regresji, próba prawdziwego modelu na dostarczonych stronach,
   ZIP przenośny i instrukcja aktualizacji. Pełny pipeline CUDA trzeba sprawdzić
   na drugim komputerze — tutaj nie ma docelowej karty.

## Jak uczciwie ocenić poprawę

Minimum 30 stron z każdej klasy: zachodni kolorowy, zachodni B&W, manga B&W,
kolorowa manga/manhua w układzie stron. Osobno małe dymki, połączone dymki,
czarne balony, krzyk, brak obramowania, captions, pionowy tekst, 4-koma i rozkładówki.
Ręcznie zaznaczyć obrysy i kolejność. Mierzyć przeoczenia/fałszywe wykrycia,
IoU maski, boundary F-score, ucięte litery/ogonki i poprawność kolejności.
Liczba konturów oraz pewność modelu **nie zastępują** tych miar.

Komercyjny efekt wymaga kontroli redakcyjnej. Przy dalszych problemach najlepszym
krokiem będzie fine-tuning segmentera na poprawkach z własnego, zróżnicowanego
zbioru, a nie dodawanie kolejnych ogólnych chatbotów. Wymaga to praw do danych
i osobnego procesu treningu; tej wersji nie przedstawiamy jako wytrenowanej na
bibliotece użytkownika.

## Licencje i bezpieczeństwo

Modele pobierane z przypiętych rewizji; YOLO sprawdzany SHA-256 przed load.
SHA chroni integralność, nie dowodzi bezpieczeństwa serializacji pickle.
Nie przyjmujemy dowolnych plików .pt ani remote Python code. SAM/RT-DETR safetensors.
Komiksy nie opuszczają komputera; cache lokalny, telemetria wyłączona.
Jzahrani GPL-3.0; ShadowB deklaruje MIT dla repo wag, ale dane mają osobne warunki;
Ultralytics ma osobną licencję AGPL/enterprise. Przed komercyjną dystrybucją potrzebny
jest przegląd licencji całego zestawu. „Poziom komercyjny” wyglądu nie oznacza
automatycznie prawa do komercyjnego wykorzystania modeli lub komiksów.

## Obsługa PDF 2.5.0 — źródła i decyzje

- [PDFium API](https://pypdfium2.readthedocs.io/en/stable/python_api.html),
  [pypdfium2 5.14.0](https://pypi.org/project/pypdfium2/5.14.0/).
- Przypięta wersja 5.14.0; renderowanie i mapowanie prostokątów tekstu przez
  `bitmap.get_posconv(page)`, z obsługą obrotu i przycięcia. Import sekwencyjny.
- Warstwa tekstowa eksportu nie jest przekazywana do silnika dymków.
- Deterministyczny CBZ, skróty źródła i checkpointów, atomowe publikowanie.
- Zachowane oryginały i wersja silnika. Brak zmian wspólnych modułów czytnika.
