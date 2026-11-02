# Jakość Nokturn Bubble Studio

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


## Nowości 2.3.6

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


## Pomiar całego zestawu od 2.3.5 — 28 października 2026

Oceniono wizualnie wszystkie 170 unikalnych stron dotąd przeanalizowanych,
łącznie 1059 przystanków. Wzorzec zawiera kompletne listy, również puste dla
reklam i stron bez kwestii. 32 nowe strony to 20 losowych z kolejnych tytułów
oraz 12 kontroli końcowych stron sześciu komiksów. Próba celowo zawiera trudne
przypadki i nie jest reprezentatywną próbą całej biblioteki. Nie jest to też
niezależna referencja ekspercka. Niejednoznaczne interpretacje zapisano per strona.

Wynik 2.3.5: F1 wykrywania 82,23%, wizualna akceptowalność obrysów 87,05%,
kolejność 97,72%, wskaźnik łączny 88,77%. Na tej samej próbie 2.3.4 osiąga
odpowiednio 81,75%, 87,05%, 97,72%, 88,59%. Przyrost łączny: 0,18 punktu
procentowego. Strony bez uwag we wszystkich kryteriach: 46→47/170 (27,65%).
Nie porównywać tych wartości bezpośrednio ze starszymi ocenami z 19 stron.

Wykrywanie: 965 dopasowanych / 1059 oczekiwanych; 94 braki, 323 nadmiary.
Precyzja 74,92%, czułość 91,12%. F1=2TP/(2TP+FP+FN). Dopasowanie jest
jeden-do-jednego i wymaga wszystkich punktów złożonego dymka. Wielka maska
obejmująca kilka tekstów nie zalicza ich jako kilku prawidłowych wykryć.

Obrysy: 840/965 wizualnie zaakceptowanych geometrii dopasowanych prawdziwych
regionów. Werdykt obejmuje korpus, istotne ogonki, zalewanie rysunku i scalanie.
Nie jest to IoU ani dokładność pikselowa. Każda ocena jest związana z hashem
faktycznej geometrii; nowy obrys wymaga nowej oceny. Nieocenione dopasowane
obrysy blokują wyliczenie wyniku łącznego. Fałszywe regiony obniżają F1.

Kolejność: 3391/3470 poprawnych par wśród dopasowanych kwestii (79 odwróceń).
LTR 1414/1465=96,52%, RTL 1977/2005=98,60%. Brakujące kwestie są karane przez
F1, a kolejność nie jest oceną kompletności. Zły kierunek lub wadliwa numeracja
odrzuca wszystkie pary strony. Dymek złożony oceniamy według początku;
przeplatanie jego członów przez inne głosy nie jest mierzone tym wskaźnikiem.

Łączny wskaźnik = pierwiastek trzeciego stopnia z iloczynu F1, akceptacji
obrysów i kolejności. Równe wagi są jawną konwencją raportowania, nie
prawdopodobieństwem bezbłędnego działania. Zawsze podawać komponenty,
liczby błędów, udział stron bez uwag i pokrycie oceny, obok jednej liczby.
Nie mierzono poprawności transkrypcji OCR znak po znaku.

Każda następna iteracja ma zachować dotychczasowe strony i definicje, dodać
nowe kontrole, ocenić kompletne listy i nowe geometrie oraz przeliczyć obie
porównywane wersje na tym samym rozszerzonym wzorcu. Zmianę definicji lub
poprawkę błędnej adnotacji trzeba jawnie zapisać; nie wolno usuwać trudnych
stron, podmieniać prawdy wynikiem automatu ani liczyć niezmienności jako sukcesu.
Raport `quality-history.json` zapisuje hashe definicji, liczby i różnicę w pp.

```powershell
python -m tools.bubble_studio.quality_metrics --reference tests/full_page_reading.json --contours tests/contour_review.json --results PRACA/quality-2.3.5/candidate --output PRACA/quality-2.3.5/release-metrics.json
```

Filtr 2.3.5: reklama wydarzenia wymaga braku wykrytych kadrów, ogłoszenia
crossoveru, wielu dat i tygodni oraz przestrzennie powiązanego READ NOW/FOR FREE.
Kredyty wymagają pary Translation:/Lettering: z nazwiskami, zgodnego OCR,
małego prostokąta i położenia poza większością powierzchni kadru. To ograniczony
format, potwierdzony na jednej reklamie i jednej stronie kredytów. 168 wyników
zachowano dokładnie. Mozaika Sabriny (123 fałszywe regiony) i nowe galerie
pozostają jawnymi błędami; powtórzenia tytułów dają jedynie ostrzeżenie.

Filtr zapisuje pełny poprzedni wynik, kotwice, OCR i ocenę; edytor przywraca
je jednym przyciskiem z Cofnij/Ponów. Szerszy tryb include-free-text omija filtr.
Gate porównuje zachowaną migawkę z niezależnym baseline, a listę 14 dozwolonych
usunięć zapisano oddzielnie od deklaracji kandydata. 170 świeżych obliczeń GPU
ma zweryfikowane hashe kodu i obrazu. 208 testów programu przeszło, w tym
rzeczywisty przycisk przywracania w oknach 1250×900 i 1024×768.

Raport: `PRACA/quality-2.3.5/PODSUMOWANIE.html`.


## Uzupełnienie 2.3.4 — niezależne kolumny tekstu, 28 października 2026

138 stron przeliczono pełnymi modelami GPU końcowym kodem; 20 stron jest
nowych: 10 z pięciu kolejnych serii mangi oraz 10 niewykorzystanych stron
pięciu komiksów zachodnich. Próbę zamrożono przed opracowaniem reguły.
Baseline to 2.3.3: wcześniejsze 118 wyników końcowych i świeże obliczenia
20 nowych stron na zamrożonych źródłach 2.3.3. Pochodzenie starych wyników
(GPU i przeliczenie układu) zachowano jawnie. Nowe wyniki nie korzystają
z odtwarzania układu ani z pamięci wcześniejszych geometrii.

Zmieniono dokładnie dwie strony, obie manga: Kagurabachi s.3 i WITCHRIV s.18.
Wspólny szeroki prostokąt obejmował dwie odrębne kolumny myśli. OCR potwierdza
co najmniej dwie linie na kolumnę, szeroki odstęp i zachowanie każdej linii.
Podział dotyczy tylko tekstu bez konturu dymka; nie zmienia modeli, masek,
przypisań do kadru ani reguł kolejności. Niepewne litery, most między kolumnami,
pojedyncze linie, SFX i ułożenie jedno pod drugim blokują podział. Kierunek
LTR/RTL sprawdzono w testach; dwa rzeczywiste poprawione przykłady są RTL.
Pozostałe 136 wyników zachowano dokładnie, w tym wszystkie 20 nowych stron.

`regression_gate` dopuszcza tylko dwa ręcznie obejrzane podziały z zapisanymi
prostokątami i mapowaniem identyfikatorów. Chroni każdą inną geometrię oraz
metadane; niezależnie wymaga zachowania pozycji wszystkich linii OCR baseline.
Nie ufa samemu komunikatowi kandydata o udanym podziale. Testy obejmują
ucięcie słów mimo zmienionej polityki, niepewne OCR, brak strony/mapowania,
zduplikowane mapowanie i zmianę chronionego obiektu.

Pełna referencja ma 19 stron i 113 przystanków. Wszystkie wcześniejsze
13 definicji zachowano; dodano Kagurabachi i pięć nowych stron kontrolnych,
w tym cztery z opisem treści i negatywny przykład reklamy Sabriny. Ręczne
opisy agenta są jawne i korygowalne; nie stanowią niezależnej oceny eksperckiej.
Porównanie 2.3.3 z 2.3.4 na tej samej rozszerzonej referencji: 102→104
odnalezione, 11→9 brakujących, 7→9 kompletnych stron. Bez zmiany pozostają
142 dodatkowe regiony i 8 odwróconych par. 135 fałszywych regionów pochodzi
z dwóch reklam (123 Sabrina, 12 Deadman). Większość braków karty postaci
Pop Kill to złączone przystanki, a nie brak liter we wspólnym obszarze.
Żadna opisana strona nie pogorszyła obecności, dodatkowych przystanków,
odwróceń ani wskazanych punktów obrysu. Tych wyników nie należy porównywać
bezpośrednio z metrykami starszej, węższej próby 13 stron.

172 testy programu przeszły; cztery testy API pełnego serwera wyłączono.
Playwright sprawdza 138 obrazów, zapis oceny, eksport, nawigację, głębokie
odnośniki, odświeżanie, telefon i komputer. Dystrybucja przechodzi osiem
kontroli ZIP/EXE, aktualizacji, zachowania danych i odrzucenia uszkodzonej
paczki. Nadal nie wykonano instalacji na drugim czystym komputerze.
Raport: `PRACA/quality-2.3.4/PODSUMOWANIE.html`.


## Uzupełnienie 2.3.3 — pełne listy czytania, 28 października 2026

Próba ma 118 stron i 800 regionów. Dodano 20 nowych stron: 10 stron z 5
kolejnych serii mangi i 10 stron z 5 komiksów zachodnich. Regułę obrysu
opracowano na poprzednich 98 stronach. Nowa kontrola pełnych stron obejmuje
73 przystanki na 13 jawnie opisanych stronach, w tym 4 z nowej próby.
Są to ręczne opisy agenta na podstawie oryginałów, a nie niezależna referencja
ekspercka. Wcześniejsze częściowe kotwice pozostają dodatkowym testem.

Listy zawierają wszystkie przyjęte wypowiedzi/narrację, także samą interpunkcję.
Połączone lobami dymki to jeden przystanek z kilkoma punktami. Szyldy, efekty
poza dymkami i reklamy są wyłączone; niejednoznaczne wybory opisano w danych.
Dopasowanie jest jeden-do-jednego i nie korzysta z oczekiwanej kolejności.
Jeden wielki obrys nie może zaliczyć kilku osobnych wypowiedzi. Strona reklamy
ma referencję pustą, więc jej fałszywe regiony są normalnie liczone jako błędy.

Na tych 13 stronach: 72/73 przystanki odnalezione, 1 brakujący i 16 dodatkowych,
w tym 12 na jednej reklamie. Liczba odwróconych par spadła z 16 do 7 (LTR 8→0,
RTL 8→7). 6/13 stron jest kompletnych w zakresie obecności, braku dodatkowych
przystanków i kolejności. Liczba ta nie ocenia pełnej wierności obrysów.
Żadna z opisanych stron nie pogorszyła tych miar. Wskazane punkty nadmiarowego
obrysu: 2 błędy przed poprawką, 0 po. To celowo dobrana próba z trudnymi
przypadkami, nie estymacja skuteczności w całej bibliotece.

Zmiany kolejności są ogólne: różne wysokości tekstu we wspólnym kadrze,
nieobramowany górny dialog przed dolną siatką oraz ostrożniejsze rozpoznawanie
dwurzędowej siatki jako kolumn. Dla zagnieżdżonych obrysów lub kotwic zostaje
wcześniejsze, bardziej zachowawcze sortowanie. Ręczny tryb kolumnowy i
dotychczasowe testy 4-koma pozostają. Wszystkie 15 stron ze zmienioną kolejnością
obejrzano osobno: 11 poprawia dialog, 4 porządkują istniejące fałszywe regiony
i nie są zaliczone jako poprawa rozpoznania wypowiedzi. Cztery z 11 stron są nowe.

Obrys tekstu poza dymkiem poprawiono w dwóch kolejnych, różnych tytułach:
narracja przy postaciach i wypowiedź nad samochodem. Oba przypadki zachowują
wszystkie 8/3 linii OCR. Pozostałe 798 geometrii zachowano dokładnie; liczba
przystanków nie zmieniła się. 101 całych stron ma identyczny wynik.
Porównanie wyników dopuszcza wyłącznie konkretne, obejrzane geometrie i
permutacje, zachowując pewność, źródło i powiązania z fizycznymi kadrami.

Pochodzenie obliczeń jest rozdzielone jawnie. Pełne modele GPU przeliczyły
118 stron. Zapisano dokładne kotwice tekstu; odtworzenie wcześniejszego układu
dało identyczny wynik na 118/118 stron. Końcowe zabezpieczenie nakładania
przeliczono jako sam układ. Następnie 42 strony przeliczono ponownie GPU
końcowym kodem: wszystkie zmienione strony, wszystkie 20 nowych stron,
poprzednie kotwice i odrzucone przypadki. Każde pole wynikowej geometrii oraz
kotwice były identyczne z powtórzeniem układu. Pliki `raw-inference-proof.json`,
`fresh-gpu-proof.json` i `layout_replay` w wynikach zachowują te rozróżnienia;
wynik z pamięci nie jest opisywany jako nowa inferencja GPU.

157 testów przeszło; 4 testy API pełnego serwera są poza zakresem programu.
Pełne listy i ocena: `tests/full_page_reading.json` oraz moduł
`tools.bubble_studio.reading_benchmark`. Szybkie powtórzenie samego układu:
`tools.bubble_studio.reading_replay` (wymaga zapisanych kotwic i nieedytowanej
pełnej strony). Zmieniona definicja referencji blokuje porównanie ocen.

Pozostają m.in. układ prawego wysokiego kadru w Aztec, odwrócenie w Stop!,
pominięta myśl WITCHRIV oraz zegary, szyldy, reklamy i zduplikowane obszary.
Nie rozszerzono automatycznie reguł, aby ukryć te błędy. Materiał jest głównie
anglojęzyczny; webtoony i wszystkie języki nie mają potwierdzonej skuteczności.

## Uzupełnienie 2.3.2 — 28 października 2026

Do porównania dodano 41 nowych stron: 20 stron z 10 kolejnych serii mangi
oraz 21 stron z 11 komiksów zachodnich. Wraz z poprzednią próbą daje to
98 stron i 651 regionów. Regułę odzyskiwania ogonka zamrożono przed przeglądem
nowej próby. Kontrola nowych stron objęła plansze podglądowe, a cztery strony
z narracją RTL, połączonymi dymkami, kolorowymi i czarnymi balonami sprawdzono
w większym powiększeniu oraz dodano do ręcznych kotwic kolejności.

Nowy wariant szukania zamkniętego wnętrza rozdziela cienkie, białe przejścia
w rastrze od właściwego papieru dymka. Stosujemy go tylko jako ograniczone
rozszerzenie istniejącego konturu: zgodne tło przy dwóch tolerancjach, brak
wycieku do brzegu, prawie pełne pokrycie korpusu, długi i wąski przyrost
3–20% oraz potwierdzenie, że stara granica cięcia nie ma oparcia w obrazie.
Wynik jest sumą starej maski i tego rozszerzenia. Pięć punktów oznaczonych
na oryginale sprawdza objęcie ogonka i wykluczenie pobliskiego tła; rasteryzacja
obu wyników osobno chroni korpus. Kolejność pozostaje oparta na tekście.

W 2000AD potwierdzono 32 wpisy AppleDouble z nagłówkiem metadanych macOS,
udające pliki JPG. Filtr pomija `__MACOSX` i `._*` w CBZ/CBR oraz folderach.
Porównanie indeksów wszystkich 102 archiwów zachowało kolejność i rozmiary
2440 prawdziwych stron. Wszystkie 32 prawdziwe obrazy w zmienionym archiwum
przeszły dodatkową kontrolę odczytu. Niczego nie usuwamy z oryginalnych plików.

Nowe przykłady i obserwacje są w `tests/reading_examples.json`,
`tests/contour_examples.json` oraz `tests/known_visual_issues.json`.
45 kotwic na 8 stronach sprawdza kompletność tych wypowiedzi i ich kolejność.
Przykład Hatori zachowuje dodatkowy, błędny przystanek na szyldzie — liczba
ta jest jawna w raporcie, nie ukrywamy jej jako poprawnej detekcji.
132 testy przeszły; 4 testy API pełnego serwera pozostają poza zakresem
samodzielnego programu. Dokładny wynik porównania GPU jest w raporcie
`PRACA/quality-2.3.2/regression.json`.

Porównanie końcowe przeszło: jedna zaakceptowana korekta ogonka, 650 innych
regionów i 97 całych stron identycznych. Wszystkie 41 nowych stron zachowało
wynik bazowy. Ręczne punkty wskazują trzy brakujące miejsca ogonka w bazie
i brak tych ubytków po poprawce. Oba punkty tła pozostały poza konturem.
W raporcie można teraz linkować do konkretnej strony przez jej SHA-256;
nawigacja i odświeżenie zachowują wskazaną stronę.

Nie mamy pełnych referencji obrysów dla całej biblioteki. Większa próba
obejmuje różne style i oba kierunki, ale głównie tekst angielski. Nie dowodzi
uniwersalnego OCR wszystkich języków; webtoony pozostają poza tym wydaniem.
Nowo zauważone błędy obrysu postaci/samochodu, zegara, szyldów i reklam
pozostawiono jako jawne przypadki do kolejnych, osobno ocenianych poprawek.

## Uzupełnienie 2.3.1 — 28 października 2026

Wąska korekta tekstu na tle rysunku wymaga łącznie: wysokiej pewności etykiety
tekstu poza dymkiem, nieregularnego kształtu, silnej niezgodności tła poza
literami i przestrzennego potwierdzenia zachowania wszystkich linii OCR.
Nie stosujemy samej jednorodności koloru, ponieważ psułoby to prawdziwe,
półprzezroczyste i kolorowe dymki. Mniejszy region zachowuje treść, identyfikator
i kotwicę kolejności; stary kontur pozostaje w diagnostyce.

Próba obejmuje dotychczasowe 49 stron oraz 8 nowych stron z 4 innych serii
(seed 20261031). Każda ma wynik z wersji 2.3.0 i nowej wersji. Jedyna dopuszczona
zmiana dotyczy potwierdzonego błędu obrysu myśli w „Hey! Devil Girl!”. Wszystkie
inne regiony, ich kolejność, kadry, geometria oraz pewność są chronione dokładnym
porównaniem. Nowych stron nie użyto do wybierania reguły. Wynik tej kontroli
jest zapisany w PRACA/quality-2.3.1/regression.json.

Wynik końcowy: 57 stron, 358 regionów; 56 stron i 357 regionów bez zmian.
Jedna zaakceptowana korekta zmniejsza prostokąt obejmujący rysunek do 52,3%
poprzedniej powierzchni, zachowując wszystkie 6 linii OCR i kolejność.
Osiem nowych stron pozostało identycznych. Przeszły 122 testy; 4 testy API
pełnego serwera Nokturn są poza zakresem samodzielnej aplikacji. Playwright
potwierdził działanie przeglądu wszystkich 57 stron, nawigacji, eksportu,
zapisu ocen i układu na dużym oraz małym ekranie. Na 4 opisanych stronach
zachowano wszystkie 16 kotwic wypowiedzi bez odwrócenia kolejności.
To kontrola regresji na tej próbie, nie dowód bezbłędności całej biblioteki.
Oględziny nowej próby ujawniły też istniejący fałszywy obrys drzwi w Red Cat
Ramen (056-bf2f031a0804); ta wersja go nie zmienia. Pozostają problemy
z niektórymi ogonkami, obrysami w Salamander i materiałami katalogowymi.

Przykład uruchomienia blokady publikacji:

```text
python -m tools.bubble_studio.regression_gate --baseline PRACA\baza --candidate PRACA\nowa --policy tests\regression_policy_2_3_1.json --output PRACA\regression.json
```

Niepowodzenie porównania kończy polecenie błędem. Reguły dopuszczają tylko
konkretne, obejrzane korekty; nie wolno rozszerzać ich automatycznie po każdej
niezgodności. Brak OCR, inny obraz, zmienione przypisanie do kadru, kolejność
lub obcięta linia tekstu blokują wydanie. To nie zastępuje niezależnej referencji
masek ani nie dowodzi braku regresji na wszystkich możliwych stylach.

Poniżej zachowano opis rozwoju i wyników wersji 2.3.0.

## Cel i metoda

Pracujemy w pętli: losowanie → zamrożenie próbki i wersji kodu → prawdziwe modele
GPU → porównanie oryginału z wynikiem → zapis błędów → poprawka → regresja →
nowe, wcześniej nieoglądane tytuły. Zwiększenie liczby obrysów nie oznacza poprawy.
Nie tworzymy referencji z wyniku tego samego automatu.

Laboratorium losuje książki osobno dla komiksów i mangi. Kierunek wynika z
konwencji folderu; nie jest rozpoznaniem języka. Seed, nazwa tomu, strona,
oryginalny wpis archiwum i SHA-256 pozwalają wrócić do tego samego przypadku.
Całe tytuły zostają odłożone jako holdout. `--exclude-manifest` wyklucza też
inne rozdziały już użytej serii mangi. Nieczytelne archiwa/obrazy trafiają do
listy błędów. Uszkodzonej strony nie zaliczamy jako strony bez wypowiedzi.

Raport pokazuje oryginał i obrysy obok siebie. Zawiera oceny: obrys/ogonek,
pominięta kwestia, fałszywy region/SFX, kolejność, podział/połączenie. Uwagi
zapisują się w przeglądarce; eksport JSON zachowuje je poza nią.

## Co sprawdzać na każdej stronie

1. Kompletność: małe wypowiedzi, myśli poza dymkami, narracja, sama interpunkcja,
   czarne balony, tekst na rysunku i granicach kadrów.
2. Obrys: tusz, wklęsłości, długie ogonki, wyspy poza balonem, ucięte litery,
   przypadkowo objęta twarz/ubranie/tło. Bez dopasowywania sztucznych elips.
3. Kolejność: kadry, LTR/RTL, ukośne kadry, brak ramek, 4-koma, rozkładówka.
   Fizycznie połączony balon może być jednym przystankiem; ustal to samo
   w predykcji i referencji.
4. Klasyfikacja: dialog i myśl kontra SFX, nazwa postaci, szyld, tytuł,
   okładka lub reklama. OCR potwierdza litery, nie rozumienie fabuły.
5. Użytkowanie: powiększenie nie ucina słów; korekta, cofanie, zapis,
   przerwanie i wznowienie nie gubią danych; oryginał ma ten sam SHA-256.

## Zmiany z 27 października 2026

- Poprawiony współczynnik H/W w obliczaniu przerw. Poprzednio przekazywano W/H.
- Puste kadry dalej ograniczają kolejność; dwie ukośnie położone kwestie nie
  tworzą automatycznie pionowych pasków. Wysoki kadr nie pochłania całego
  kolejnego rzędu. Jawny profil `columns` pozostaje dostępny dla 4-koma.
- Kolejność i przypisanie do kadru opierają się na położeniu tekstu zamiast
  zasięgu ogonka. Kontur służy wyświetlaniu.
- Niezależny, kafelkowany przebieg OCR odzyskuje tekst, którego RT-DETR nie
  zaproponował. Odzyskiwanie może działać również bez wykrytej ramki kadru.
- Nowe regiony bez obramowania pozostają tekstem. Blokada oznak katalogu/reklamy
  ogranicza dodatkowe propozycje OCR, ale nie jest uniwersalnym klasyfikatorem.
- Małe znane efekty, np. CHRP/POSE, nie stają się odzyskanym dialogiem. Efekt
  błędnie wykryty jako balon można pominąć tylko po niepowodzeniu kontroli obrysu;
  prawdziwy balon z samym „SNORT” pozostaje.
- Większe wycinki SAM dają miejsce długim ogonkom. Maska słabo związana
  z krawędziami obrazu nie jest publikowana jako pewny obrys.
- Kontury kolidujące z inną wypowiedzią ustępują obszarom tekstu; odrzucone
  wielokąty pozostają w diagnostyce. Cały kadr z tekstem i podejrzane duże maski
  wokół nazw własnych są ograniczane do tekstu. To świadome zabezpieczenia,
  nie automatyczne naprawienie każdego takiego konturu.
- Ocena pakietów mierzy dodatkowo odwrócone pary kolejności i zgodność kierunku.

## Dowody i granice próby

Pierwsza próbka: seed 20261027, 24 strony / 12 tytułów, w tym 8 stron początkowo
odłożonych. Po pierwszych dwóch iteracjach także te strony ujawniły problemy
i posłużyły do kolejnej poprawki. Nie są już nietkniętym testem końcowym.
Druga próbka: seed 20261029, 17 poprawnie odczytanych stron / 9 nowych tomów;
jedna inna strona archiwum 2000AD była nieczytelna i jest w dzienniku błędów.
Ten przebieg obejmował 41 stron. Ujawnił jeszcze przeplatanie górnego i środkowego
kadru w Godzilli przy nakładających się prostokątach detektora. Doprecyzowano
wyrównanie początku rzędu względem krótszego kadru i dodano test tego przypadku.
Ostatnia próbka, seed 20261030, dodaje 8 stron z 4 nowych serii mangi. Końcowy
przebieg obejmuje **49 stron z 25 tomów**: 41 użytych podczas doszlifowywania
i 8 odłożonych do tej ostatniej kontroli. Pliki i wyniki są w PRACA/quality-20261027,
w folderach sample-49 i release-final. Nie przypisujemy całej tej próbie statusu
nietkniętego benchmarku.
Pierwszy sampler zachował jeden poprawny obraz z częściowo nieczytelnego tomu;
obecny sampler zatwierdza dopiero cały udany wybór stron tomu.

Na czterech konkretnych stronach zdefiniowano 16 kotwic wypowiedzi po oglądzie
stron (`tests/reading_examples.json`). Pozwalają wykazać poprawę kolejności
i odzyskanie pominiętej myśli, lecz nie zastępują anotacji obrysów. Skrypt
`scripts/check_reading_examples.py` porównuje te przykłady z dowolnym przebiegiem.

Testy obejmują geometrię, realny mały RT-DETR z losowymi wagami na CPU, format
pakietów, ochronę oryginałów i zatwierdzonych korekt, edytor Tk, układ panelu,
odzyskiwanie OCR i zabezpieczenia obrysów. Cztery testy API serwera Nokturn
wyłączono z próby samodzielnego Studio, ponieważ dystrybucja nie zawiera serwera.
Playwright kontroluje raport, wszystkie obrazy, nawigację, klawiaturę,
zapis ocen, eksport JSON, powiększenie i układ komputer/telefon.

Próba wybranych kotwic przed poprawkami: jedna brakująca kwestia i dwie
odwrócone pary kolejności. Po poprawkach wszystkie 16 kotwic jest obecnych
w zamierzonej kolejności. To cztery przykłady regresji; nie procent skuteczności
na wszystkich 49 stronach. Zestaw testów programu: 107 testów, z czterema
odrębnymi testami API serwera wyłączonymi z tej dystrybucji.

Okna Tk uruchomiono i sprawdzono rzeczywistą geometrię elementów. Próba
przechwycenia natywnego okna przez computer-use nie uzyskała zatwierdzenia
w czasie oczekiwania; nie zaliczamy tego jako pełnej wizualnej kontroli okien.
Nie wykonano instalacji na drugim, czystym komputerze ani testu każdej karty GPU.

## Powtarzanie i mierzenie poprawy

W panelu wybierz „Losuj i testuj strony…” i folder biblioteki. Każde uruchomienie
tworzy nową próbkę. W celu porównania wersji używaj **tego samego sample.json**:

```text
python -m tools.bubble_studio.quality_lab sample --source D:\Komiksy --output PRACA\probka --seed 42
python -m tools.bubble_studio.quality_lab run --images PRACA\probka --output PRACA\wersja-a --split development --recover-dialogue
python -m tools.bubble_studio.quality_lab run --images PRACA\probka --output PRACA\wersja-b --split development --recover-dialogue
python -m tools.bubble_studio.quality_lab run --images PRACA\probka --output PRACA\kontrola --split holdout --recover-dialogue
```

W dystrybucji Python jest w tools/bubble_studio/.runtime/venv/Scripts/python.exe.
Najpierw uruchom START, aby go przygotować. Nowy wynik wymaga nowego folderu;
wznowienie sprawdza hash obrazu, kodu wnioskowania i ustawienia.

Do pomiaru masek popraw wszystkie regiony wybranych stron w edytorze i dopiero
wtedy zatwierdź. Zachowaj automat i referencję jako osobne pakiety. `evaluate`
mierzy precision/recall przy IoU 0,5, IoU dopasowanych masek, boundary F z tolerancją
3 px, inwersje kolejności oraz tekstowe regiony referencji. Kolejność oceniamy
tylko na dopasowanych regionach i czytamy razem z przeoczeniami.

## Dalsze doszlifowywanie

Rejestr błędów trzeba rozszerzać o nowe style i języki, a poprawki kontrolować
na nowych tytułach. Pozostają trudne: otwarte balony na marginesie, długie
ogonki, ciasno stykające się dymki, bardzo ozdobne litery, szyldy oraz intencja
krótkich tekstów. Nie deklarujemy procentowej skuteczności ani perfekcji.
OCR odzyskiwania jest przeznaczony dla alfabetu łacińskiego; nie jest pełnym
profilem dla japońskiego tekstu pionowego.

Modele nie uczą się samoczynnie z ocen ani nie zmieniają własnego kodu w tle.
Po zebraniu dobrych referencji można porównać inne modele lub dostroić segmenter;
taką zmianę trzeba ponownie ocenić na odłożonych tytułach. Zatwierdzone pakiety
użytkownika pozostają chronione przed automatycznym przeliczeniem.
