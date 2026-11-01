# Bubble Studio 2 — research i decyzje (2026-10-03)

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
