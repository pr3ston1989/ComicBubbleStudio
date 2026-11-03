# Nokturn Bubble Studio 2.11.2

**[Instrukcja obsługi i zalecane ustawienia](tools/bubble_studio/INSTRUKCJA.html)**. W aplikacji otworzysz ją przyciskiem **Instrukcja**.

## Nowości 2.11.1 — dodatkowe zabezpieczenia kolejności

**97,75% na tych samych 498 stronach / 3252 przystankach**.
Wersja 2.11.0: **97,74%**. Zysk wynosi **0,014 punktu procentowego**;
nie jest to duży skok jakości ani wynik nowej niezależnej próby.

- Usunięto **6 błędnych par kolejności na trzech stronach**: Pop Kill,
  Class of Brains i Sunshine Sketch. Pozostałe 495 wyników bez zmian.
  Wszystkie obrysy, wykryte teksty, kadry i dane końcówek ogonków zachowano.
- Dwa sąsiednie dymki w tej samej kolumnie można uporządkować od góry tylko
  wtedy, gdy pełne obrysy i tekst potwierdzają rozdzielenie pionowe, oba należą
  do tego samego kadru i nie ma między nimi innego rozmówcy. Reguła działa
  w komiksie LTR i mandze RTL; nie zmienia kolejności obok siebie.
- Gdy detektor nie znalazł kadrów, ale wcześniejsze grupowanie scen wymieszało
  ich dialogi, dwie stabilne szerokie ramki mogą potwierdzić relację nad/pod.
  Potrzebne są zgodne granice przy dwóch progach obrazu, pełne przypisanie
  tekstu i obrysu oraz brak nakładania ramek. Zachowano lokalną kolejność
  dialogów. Przy niejednoznaczności pozostaje wcześniejszy wynik.
- Okno „Układ tytułu…” pokazuje teraz również ustawienia odziedziczone
  z folderu serii. Zmiana samego kierunku nie wyłącza już odziedziczonego 4koma.
  Dla tytułu spoza folderu wejściowego okno wyjaśnia zakres odczytanych ustawień.
- Wykrywanie F1 **96,31%**, zgodność par kolejności **99,24%**, obrysy **97,73%**.
  Błędne pary: **111 → 105 z 13832**. Strony bez wszystkich badanych uwag:
  **306 → 308 z 498 (61,85%)**. Wzorców ani kryteriów tolerancji nie zmieniano.
  Wskaźnik łączny nie oznacza procentu idealnych stron ani dokładności OCR;
  ocena agenta, nie niezależny audyt ekspercki.
- Pełne testy aplikacji, porównanie każdej strony, kontrole bieżącego GPU,
  test rzeczywistego okna z odziedziczonym 4koma oraz kontrola instalatora
  i zapisu paczek. Jawne układy, ręczne i zatwierdzone poprawki chronione.
  Brak nowych wywołań modeli w dodanych etapach kolejności.

Webtoony poza zakresem. Animacje powiększania pozostają w Nokturnie.
Prywatne komiksy, modele, obrazy testowe i wzorce nie są publikowane.

## Nowości 2.11.0 — 4koma dla wybranego tytułu i siedem nowych serii

**97,74% na wszystkich 498 stronach / 3252 przystankach**.
Wersja 2.10.1 na identycznych 498 stronach: **97,57%**.
Zysk z kodu: 0,166 punktu procentowego. Starszy wynik 97,79% dotyczył mniejszego
zbioru 470 stron; nie jest bezpośrednim punktem odniesienia dla rozszerzonej próby.

- Dodano **„Układ tytułu…”**: dla konkretnego pliku komiksu/PDF albo folderu jednej
  serii można wybrać Automatyczny lub **4koma — całe pionowe historyjki**, a także
  kierunek czytania. Osobny wybór tytułu nie zmienia sąsiednich archiwów.
  Zmiana ustawienia przelicza niesprawdzone strony; zatwierdzone korekty zachowuje.
- Tryb 4koma porządkuje całe kolumny przy czterech rozpoznanych kadrach oraz
  wariancie z ramką tytułu. Zachowuje kolejność wewnątrz kadru. Nie nadaje
  arbitralnej kolejności stronom o niezgodnej lub niejednoznacznej geometrii.
  Domyślnie pozostaje automatyczne rozpoznawanie; deklaracja użytkownika nie jest
  wynikiem uwzględnionym w podanych procentach automatu.
- Automat rozpoznaje także małą ramkę tytułu nad czterema kadrami.
  Wymagane zgodne kolumny, jednoznaczne przypisanie wszystkich wykrytych tekstów
  i potwierdzenie osobnych historyjek przez model. Usunięto **70 błędnych par
  kolejności** na dwóch stronach Sunshine Sketch. Pozostałe 496 wyników bez zmian.
  Zachowano wszystkie wykrycia, obrysy, teksty, kadry i dane końcówek ogonków.
- Nowe tytuły: Sunshine Sketch, Kimi ni Todoke, The Sandman, Promethea,
  Watchmen, Uzumaki i Here. Losowa próba: **28 stron, 19 archiwów**, w tym nieme
  strony, materiał redakcyjny i rozkładówki. Kod 2.10.1 zamrożono przed losowaniem;
  wzorce każdej partii zapisano przed predykcjami odpowiadających jej stron.
  Wszystkie strony zachowano, wzorca nie poprawiano po predykcjach.
  Zamrożony automat: **96,18%**. Po poprawce na tych samych stronach: **97,26%**.
  Ponieważ błędy tej próby posłużyły do poprawki, drugi wynik jest wynikiem
  rozwojowym, nie niezależnym sprawdzianem nieznanych stron.
- Wszystkie 498: F1 **96,31%**, kolejność **99,20%**, wizualna akceptacja
  obrysów **97,73%**. Błędne pary 181 → 111 z 13832. **306/498 stron bez uwag**;
  w nowej próbie 8/28. Łączny wskaźnik nie oznacza odsetka idealnych stron
  ani dokładności przepisywania OCR. Ocena agenta, nie niezależny audyt.
  Dla eksperymentalnych kompozycji Here i Promethei możliwe są inne interpretacje
  kolejności; zastosowaną interpretację zapisano przed predykcjami.
- Rozbudowana historia analizy jest zachowywana w osobnym elemencie paczki
  z kontrolą SHA-256. Standardowy dokument strony nadal spełnia limit 2 MB
  czytnika. Studio odczytuje pełną historię; obrysy, teksty i możliwość kontroli
  pozostają zachowane. Nie trzeba zmieniać czytnika Nokturn.
- 682 testy, 7 pełnych analiz kontrolnych GPU oraz 2 dodatkowe z zadeklarowanym
  4koma; walidacja i przenośny zapis wszystkich 498 dokumentów. Nowe okno
  sprawdzono wizualnie, zapis ustawienia wykonano przez rzeczywisty interfejs.

Użycie: **Układ tytułu… → Wybierz komiks… / Wybierz folder serii… →
4koma — całe pionowe historyjki → kierunek → Zapisz ustawienia tytułu**.
Potem uruchom „Przygotuj / wznów”. Dla pliku ustawienie jest zapisywane obok
niego jako `nazwa.cbz.bubble-studio.json`; dla folderu jako `bubble-studio.json`.
Folder powinien obejmować jedną serię. Wrócenie do „Automatyczny” usuwa deklarację
4koma dla tego tytułu. Pliki oryginalnego komiksu pozostają nietknięte.
Webtoony są poza zakresem; stronicowe 4koma pozostaje w zakresie.
Prywatne komiksy, nagrania, obrazy testowe i modele nie są publikowane.

## Nowości 2.10.1 — nagłówki 4koma przy swoich historyjkach

**97,79% na wszystkich 470 stronach / 2950 przystankach**;
wersja 2.10.0 na identycznym zestawie: **97,77%**.
Zysk z kodu: 0.020 punktu procentowego. Na wcześniejszych 462: 97,75% → 97,77%.

- Naprawiono wtrącanie nagłówka kolejnej historyjki między nagłówek i dialogi
  poprzedniej: 7 błędnych par kolejności mniej na jednej wcześniejszej stronie.
  Pozostałe 469 stron bez zmian; brak zmierzonej regresji na każdej stronie.
- Wymagane wcześniejsze potwierdzenie 4koma przez model, kompletne 2–3 kolumny
  po cztery kadry, pojedyncze istniejące nagłówki i jednoznaczne przypisanie tekstu.
  Przesuwane są wyłącznie nagłówki. Zachowano wzajemną kolejność dialogów,
  wszystkie obrysy, teksty i dane końcówek ogonków. Bez dodatkowych wywołań modeli.
- Nowa mała próba: 6 losowych stron Azumangi + 2 Midnight X-Men; **98,49%**,
  **5/8 stron bez uwag**, zero nakładania ze starymi 462. Znane tytuły;
  ukierunkowana kontrola, nie dowód uniwersalności. Nowy etap nie zmienił tych 8 wyników.
- Kod zamrożony przed losowaniem. Oryginalny wzorzec 103 przystanków zachowano;
  audyt surowych oryginałów skorygował 3 fizyczne grupowania do 104 przystanków,
  bez usuwania ani przesuwania punktów tekstu. Obie wersje mają wspólny wzorzec.
  Korekty wzorca nie są zyskiem algorytmu.
- F1 wszystkich stron **96,62%**, kolejność **99,23%**,
  obrysy **97,54%**. Błędne pary 97 → 90 z 11685.
  **298/470 stron bez uwag**. Wskaźnik łączny nie oznacza procentu idealnych stron
  ani dokładności OCR; to ocena agenta, nie niezależny audyt ekspercki.
- Pozostaje kolejność pojedynczej historyjki obok dużej ilustracji — nowa próba
  zachowała taki błąd. Nie dostrajano kodu po obejrzeniu wyników nowej próby.
  Krótkie kwestie i napisy na przedmiotach nadal oceniane według starych kryteriów.
- 637 różnych testów: 636 w pełnym przebiegu + test okna Tk zaliczony osobno;
  4 testy zewnętrznego API pominięte. 3 pełne kontrole bieżącego silnika GPU,
  8 pełnych nowych analiz GPU, walidacja 470 dokumentów, 8 stron zapisu/odczytu
  paczki i 8 kontroli instalatora. 116 wcześniejszych plików Python bez zmian.

Zakres: dane Bubble Studio. Animacje i powiększanie pozostają w Nokturnie.
Webtoony oraz długie pionowe paski poza zakresem na życzenie użytkownika;
stronicowe 4koma pozostaje w zakresie. Prywatne komiksy, nagrania, wzorce
z obrazami i modele nie są publikowane.

## Nowości 2.10.0 — kolejność cienkich kadrów i duża próba 100 stron (2026-11-01)

**97,75% na wszystkich 462 stronach / 2846 przystankach.**
Na identycznym zestawie wersja 2.9.0: **97,72%**.
Zysk z kodu: 0,021 punktu procentowego. Na wcześniejszych 362:
97,76% → 97,79%. Drobne poprawki dają już niewielkie zyski.

Nowy etap rozpoznaje także bardzo cienkie jasne przerwy między kadrami,
gdy wspiera je ciągła ciemna ramka i stabilność przy dwóch progach jasności.
Wymaga pełnego przypisania tekstów, co najmniej trzech grup oraz konfliktu
z dotychczasowym przypisaniem do kadru. Nie przecina tekstu, nie zmienia
obrysów ani końcówek ogonków i zachowuje kolejność wewnątrz grup. Chroni
ręczne poprawki, strony zweryfikowane i rozpoznane paski 4koma. Oryginał
wyniku można odtworzyć. Nie ma wyjątków nazw tytułów, stron czy współrzędnych.
Usunięto siedem błędnych par kolejności na jednej wcześniejszej stronie;
na pozostałych 461 wyniki pozostały identyczne. Każda strona bez regresji.

**100 nowych losowych stron: 97,52%.**
Kod zamrożono przed losowaniem. Seed 2026110110; 36 stron ze wszystkich
11 dostępnych komiksów zachodnich, 56 z 28 losowo wybranych archiwów mang
oraz 8 z Azumangi. Łącznie 40 archiwów. Wszystkie wpisy były dopuszczone,
w tym okładki, reklamy i strony puste. Żadnej trudnej strony nie usunięto.
Nowość sprawdzono według SHA i par archiwum/wpis wobec dotychczasowych 362.
To nowe strony znanych tytułów, a nie test generalizacji na nowych seriach.

| Miara — 100 nowych stron | Wynik |
|---|---:|
| Wykrywanie F1 | 95,45% |
| Akceptacja dopasowanych obrysów | 98,85% |
| Poprawne pary kolejności | 98,30% |
| Trafienia / wzorcowe fizyczne przystanki | 524 / 547 |
| Nadmiarowe / pominięte przystanki w F1 | 27 / 23 |
| Odrzucone obrysy / błędne pary kolejności | 6 / 31 |
| Strony bez uwag, łącznie ze stronami bez kwestii | 55/100 |
| Strony z treścią bez uwag | 41/84 (48,81%) |

Dodatkowa kontrola punktów tekstu wykazała 21 całkowicie nieobjętych kwestii
oraz dwa połączone dymki rozbite na części, mimo zachowania wszystkich
punktów tekstu. Pokryto 619/641 punktów; nie jest to pomiar dokładności OCR
ani pokrycia każdego słowa. Pozostały krótkie reakcje bez obrysu, etykiety
postaci, nagłówki, fałszywe oczy/twarze, napisy na przedmiotach, SFX i maski
podążające za rysunkiem. W 4koma wykryto także zbyt wczesne odczytanie tytułu
lewego paska: siedem błędnych par mimo zachowanej kolejności dialogów prawego.
Na nowych 100 stronach poprawka nie zmieniła żadnego wyniku.

Pierwotny wzorzec partii po dziesięć stron zapisano z oryginałów przed ich
wykrywaniem; żadnych nakładek detektora nie oglądano podczas anotowania.
Audyt natywnych oryginałów skorygował grupowanie na ośmiu stronach, jeden
błąd przypisania kolejności do kadru i jeden punkt postawiony obok liter.
Wszystkie teksty zachowano. Oryginalny wzorzec557, korekty, obrazy dowodowe
i pomiar pierwotny **97,14%** pozostają zachowane.
Wspólny wzorzec547 stosuje się do obu wersji; zmiana wzorca nie jest zyskiem
z kodu. Wyników samego detektora nie poprawiano ręcznie.

Opisowy przedział po 3000 losowaniach całych archiwów tej próby:
96,59%–98,24%. Opisuje wyłącznie zmienność obecnej
biblioteki; nie uwzględnia błędów ocen ani brakujących stylów i języków.
Szczególnie potrzebne są inne 4koma, pionowy japoński, webtoony, europejski
BD i gorsze skany. Aktualna próba to głównie wydania i tłumaczenia angielskie.

Wszystkie 462: F1 **96,61%**, obrysy **97,49%**,
kolejność **99,16%**; TP2748, FP95, FN98, 69 odrzuconych
obrysów i 93 błędne pary / 11027. Bez uwag 292/462 (63,20%). Średnia
geometryczna tych trzech miar jest oceną agenta, nie niezależnym audytem,
dokładnością transkrypcji OCR ani procentem idealnych stron. Połączone
korpusy są jednym przystankiem; miara nie ocenia pełnego wewnętrznego
przeplotu kwestii. Drobny brak ogonka pozostaje dopuszczalny.

**610 testów Studio**, 100 pełnych analiz GPU, trzy kontrole pełnego
aktualnego silnika, walidacja wszystkich 462 stron, zapis/odczyt ośmiu stron
paczki i osiem kontroli instalatora. 114 wcześniejszych plików Python
zachowano bajtowo; dodano tylko nowy etap, testy, wywołanie i wersję silnika.
Studio nadal przygotowuje dane dymków; powiększanie i animacje realizuje
Nokturn. Źródeł Nokturna nie zmieniano. OCR/PDF pozostaje dodatkiem.

Raport prywatny: PRACA/quality-2.10.0/PODSUMOWANIE.html.
Modele, komiksy, nagrania i podglądy nie trafiają do publicznej paczki.

## Nowości 2.9.0 — mniej fałszywych dymków i uczciwa nowa próba (2026-11-01)

**97,76% na wszystkich 362 stronach / 2299 fizycznych przystankach.**
Na identycznych 362 stronach wersja 2.8.0: **97,73%**.
Zysk z kodu to 0,028 punktu procentowego. Na wcześniejszych 350 stronach:
97,75% → 97,78%. Jest to mała poprawa, nie osiągnięcie celu 98–99%.

Filtr wymaga równocześnie regularnej dwuwymiarowej siatki co najmniej czterech
niewielkich okrągłych regionów, różnych symboli z prostych kresek, zbliżonych
rozmiarów i dwóch pobliskich pewnych odczytów mechanicznego BEEP/BIP/PIP/BIEP
poza regionami czytania. Usunął cztery przyciski błędnie uznane za dymki.
Żadna nazwa tytułu, numer strony ani współrzędna konkretnego przykładu nie
steruje filtrem. To celowo wąski warunek dla tablic przycisków; nie jest
uniwersalnym rozpoznawaniem scenografii. Zachowuje oryginał do odtworzenia,
chroni dane ręczne i zweryfikowane, a pozostałe obrysy i ich względną
kolejność pozostawia identyczne. Na każdej z 362 stron brak regresji
wykrywania, kolejności i zaakceptowanych obrysów wobec 2.8.0.

**12 nowych losowych stron: 97,28%**, TP93/96, FP3, FN3,
19 błędnych par kolejności / 383 (95,04% poprawnych).
Wszystkie 93 dopasowane obrysy zaakceptowane wizualnie; 6/12 stron bez uwag.
Wzorzec treści, grupowania i kolejności zapisano z oryginałów przed
przewidywaniami. Kod poprawki zamrożono przed oglądaniem nowych wyników.
Żadnej strony ani błędu nie usunięto z próby. Wersje dały na niej identyczny
wynik: nowy filtr nie miał powodu zadziałać. Dwa trudne układy kadrów
odpowiadają za wszystkie 19 nowych pomyłek kolejności; pozostają do poprawy.
Pominięto pojedyncze A, goły pytajnik i dymek z wielokropkiem; dodatkowo
wykryto fragment twarzy, telefonu i fizycznej tabliczki. Próba potwierdza,
że wynik ogólny nie oznacza bezbłędnego automatu na każdym nowym komiksie.

| Miara — wszystkie 362 strony, wersja 2.9.0 | Wynik |
|---|---:|
| Wykrywanie F1 | 96,89% |
| Akceptacja dopasowanych obrysów | 97,17% |
| Poprawne pary kolejności dopasowanych przystanków | 99,25% |
| Nadmiarowe / pominięte przystanki | 68 / 75 |
| Odrzucone obrysy / błędne pary | 63 / 69 |
| Strony bez uwag | 236/362 (65,19%) |

Wynik łączny to średnia geometryczna F1, akceptacji obrysów i poprawności
par kolejności. To ocena agenta, nie niezależny audyt ani dokładność OCR;
nie oznacza procentu idealnych stron i nie mierzy przeplotu tekstów wewnątrz
połączonych korpusów. Niepełny ogonek jest akceptowany, gdy tekst i korpus
są prawidłowe. Języki i style nadal wymagają szerszego badania: szczególnie
oryginalny pionowy japoński, inne 4koma, webtoony, BD i uszkodzone skany.

Odrzucony eksperyment odzyskiwania krótkiego tekstu przez OCR proponował też
napisy na przedmiotach i SFX; nie został włączony do silnika. Bezpieczniejsze
odzyskiwanie krótkich reakcji oraz hierarchia nietypowych kadrów pozostają
najważniejszymi kierunkami dalszej pracy.

**593 testy Studio**, 12 pełnych analiz nowych stron i trzy pełne kontrole
aktualnego silnika GPU. Dane paczek sprawdzone dla wszystkich 362 stron,
osobny zapis/odczyt ośmiu stron i osiem kontroli dystrybucji/instalatora.
Studio przygotowuje dane dymków, w tym opcjonalne tail_tip. Skala,
powiększanie i animacja pozostają zadaniem Nokturna; jego źródeł nie zmieniano.
OCR/PDF nadal jest dodatkiem. Komiksy, nagrania, modele i raporty z ich
prywatnymi podglądami nie trafiają do publicznej paczki.

Raport lokalny: PRACA/quality-2.9.0/PODSUMOWANIE.html.

## Nowości 2.8.0 — dane końcówki ogonka i nowa próba (2026-11-01)

**97,75% na wszystkich 350 stronach / 2203 przystankach.**
Na identycznym zestawie wersja 2.7.0 uzyskuje dokładnie ten sam wynik.
Na wcześniejszych 334 wynik pozostaje 97,75%. Ta iteracja rozszerza eksport
danych dymków; nie zmienia sposobu powiększania ani animacji w Nokturnie.

Opcjonalne pole tail_tip zapisuje koniec widocznego obrysu we współrzędnych
całej strony. Nie zmienia żadnego obrysu, tekstu, podziału ani kolejności.
Zapisano 258 punktów na 121 stronach. Przy niepewnym, ciemnym, złożonym lub
ramkowym kształcie punktu może nie być. Nie odtwarzamy niewidocznej końcówki
ani pozycji ust. confidence opisuje dowody geometryczne, nie skalibrowane
prawdopodobieństwo poprawności. Kontrola rozwojowej próby 77 punktów ujawniła
jeden błąd przy krawędzi postaci. Ogólny warunek odrzucania prostych brzegów
ramki wykluczył go i dziewięć innych niepewnych przypadków; pozostałe 67
obejrzano. Nie jest to niezależny pomiar trafności wszystkich 258 punktów.

Bubble Studio przygotowuje dane. Decyzję o skali, położeniu, powiększaniu
i animacji podejmuje oddzielnie Nokturn. Testową integrację czytnika cofnięto;
jego źródła przywrócono bajt po bajcie. Prototyp pozostał wyłącznie prywatnym
eksperymentem i nie jest częścią wydania. Opis pola i przeliczania współrzędnych:
docs/NOKTURN_TAIL_TIP.md. Starszy czytnik może pominąć nieznane pole.

Nowe 16 losowych stron: po trzy z dwóch dotąd nietestowanych serii, osiem
z czterech komiksów zachodnich i dwie z Azumangi. Wzorzec treści i kolejności
zapisano przed przewidywaniami. Zachowano okładkę i milczącą ilustrację.
Wynik: **97,90%**, TP89/91, FP7, FN2, jeden błędny obrys i jedna błędna
para kolejności; 13/16 stron bez uwag. Pozostały m.in. cztery fałszywe dymki
na przyciskach, pominięte ACK, rozbity zielony korpus, region SFX i zamieniona
ramka narratora. Jedną błędną etykietę grupującą dwa oddzielne korpusy
poprawiono na nieoznaczonym oryginale. Zachowano pierwotny wzorzec90 i oba
pomiary; korekta jest wspólna dla obu wersji i nie jest poprawą z kodu.

| Miara — wszystkie 350, identyczna w 2.7.0 i 2.8.0 | Wynik |
|---|---:|
| Wykrywanie F1 | 96,80% |
| Akceptacja obrysów | 97,04% |
| Poprawne pary kolejności dopasowanych przystanków | 99,43% |
| Nadmiarowe / pominięte fizyczne przystanki | 69 / 72 |
| Odrzucone obrysy / błędne pary | 63 / 50 |
| Strony bez uwag | 229/350 (65,43%) |

Korpus obejmuje 103 archiwa i 102 rodziny tytułów oraz cztery strony z nagrań.
Kierunki: 164 LTR i 186 RTL. Jest szeroki dla sprawdzonych wydań angielskich,
ale nierówny: jedna seria 4koma, mało starych skanów, komiksy zachodnie
skupione w 12 tytułach. Nie potwierdza takiego wyniku dla oryginalnego
japońskiego zapisu pionowego, chińskiego/koreańskiego, webtoonów, europejskiego
BD, fotografowanych stron, zniszczonych skanów i innych stylów 4koma.

**577 testów Studio**, dwie pełne kontrole silnika GPU, 16 nowych stron pełnym
GPU, zgodność starszego walidatora na 350 dokumentach, zapis/odczyt pakietu
i testy instalatora. 62 wcześniejsze moduły wnioskowania zachowano bajt po
bajcie. Ocena agenta nie oznacza procentu idealnych stron ani dokładności
transkrypcji OCR. Fizyczne przystanki nie mierzą pełnego przeplotu kwestii
wewnątrz połączonych korpusów. Cel 98–99% nadal przed nami.
OCR/PDF jest dodatkiem; główną funkcją są dymki dla Nokturna.

Raport: PRACA/quality-2.8.0/PODSUMOWANIE.html.

## Nowości 2.7.0 — kolejność kadrów i zachowanie tekstu (2026-11-01)

**97,75% na wszystkich 334 stronach / 2112 fizycznych przystankach.**
Na dokładnie tych samych stronach i identycznym wzorcu wersja 2.6.1:
**97,58%**. Przyrost z kodu to
0.170 punktu procentowego.
Cel 98–99% nadal nie został osiągnięty.

| Miara — te same 334 strony | 2.6.1 | 2.7.0 |
|---|---:|---:|
| Wykrywanie F1 | 96,71% | 96,87% |
| Zaakceptowane wizualnie obrysy | 96,72% | 96,96% |
| Poprawne pary kolejności dopasowanych kwestii | 99,33% | 99,42% |
| Nadmiarowe przystanki / pominięcia fizycznych przystanków | 67 / 72 | 62 / 70 |
| Błędne pary kolejności | 57 | 49 |
| Odrzucone obrysy | 67 | 62 |
| Strony bez uwag | 214/334 | 216/334 |

Najwyższy priorytet: komfort automatycznej lektury. Stabilne ramki drukowanych
kadrów korygują kolejność, kiedy detektor omyłkowo rozbił jeden wysoki/skośny
kadr na części. Wszystkie teksty muszą mieć potwierdzone przypisanie do kadru;
wewnętrzna kolejność pozostaje zachowana, a tryby 4koma i ręcznie zatwierdzone
strony są chronione. Na zachowanym korpusie usunięto osiem błędnych par.

Drugi etap wykorzystuje graf oryginalnych pikseli i wszystkie odrębne bloki
tekstu, zamiast samej wspólnej ramki tekstu. Naprawia korpusy, ogranicza
zniekształcone maski myśli bez obwiedni i łączy części tylko przy potwierdzeniu
wspólnego papieru. Kontrola lokalnych fragmentów chroni przed dodaniem
rysunku postaci. Każde dotychczasowe słowo musi zostać zachowane; łączenie
nie przeskakuje innej wypowiedzi. Nie ma wyjątków dla tytułów i numerów stron.
Błąd wycofuje nowy etap. Wcześniejsze etapy rozpoznawania zachowano.
Nie zmieniono modeli GPU; SciPy jest teraz jawną, przypiętą zależnością.

**555 testów** aplikacji/czytnika, brak regresji na każdej z 334 stron.
Cztery kontrole końcowej aplikacji pełnym GPU oraz 18 dodatkowych stron.
Pierwsze 14 służyło końcowej regresji etapu kolejności; kolejne cztery strony
z nagrań miały zamrożone źródła i wzorzec treści przed przewidywaniami.
Wyniki na nowych stronach są identyczne w obu wersjach, więc ich dobre
rezultaty nie są przyrostem z nowej poprawki. Nowa klasyczna plansza ujawniła
pięć błędnych par kolejności; nowa współczesna — pominięty nagłówek MANHATTAN.
Wszystkie błędy pozostały w mianowniku.

Zachowano oryginalne wzorce i udokumentowano korekty fizycznego grupowania:
jeden ciągły korpus w starych 316 oraz trzy pary połączonych korpusów
w ostatnich czterech. Nie usunięto tekstów ani punktów. Obie wersje porównano
według identycznego poprawionego wzorca; poprawa etykiet nie jest zasługą kodu.
Dla nowych czterech zachowano także pomiar pierwotnych 56 przystanków.

**216/334 (64,67%) stron jest bez uwag.**
Wynik łączny jest średnią geometryczną F1, akceptacji obrysów i zgodności par
kolejności, ocenioną przez agenta, a nie niezależnych ekspertów. Nie jest
dokładnością OCR ani procentem idealnych stron. Małe braki ogonków nadal
akceptujemy przy poprawnym korpusie i tekście. Dodatkowa diagnostyka odróżnia
teksty faktycznie nieobjęte od rozbitych/połączonych przystanków; pokrycie
punktów tekstu (97,89%) nie zastępuje wyniku łącznego.

Analiza obu nagrań Google: narracja również jest powiększana; prostokąt
z fragmentem rysunku bywa czytelny; cienkie połączenie nie zawsze oznacza
jeden krok lektury. Brak jawnej współrzędnej końca ogonka w naszym pakiecie.
Czytnik Nokturn już rozwija wycinek z pierwotnego prostokąta; film nie dowodzi
stałego zakotwiczenia w końcu ogonka. Nie zmieniano czytnika w tej iteracji.

Lokalne raporty: PRACA/quality-2.7.0/PODSUMOWANIE.html oraz ANALIZA_NAGRAN.html.
Prywatne nagrania, komiksy i modele nie są publikowane. Eksport OCR/PDF
pozostaje opcjonalny; główną funkcją jest przygotowanie dymków dla Nokturna.

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
- **Instalator EXE:** Nokturn-Bubble-Studio-2.8.0-Setup.exe zawiera całą małą
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
