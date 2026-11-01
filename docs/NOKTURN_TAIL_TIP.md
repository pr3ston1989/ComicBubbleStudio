# Opcjonalna współrzędna końca ogonka

Bubble Studio 2.8.0 zapisuje dodatkowe dane wykrytych dymków.
Powiększanie, położenie i animacje są zadaniem czytnika Nokturn.

W pakiecie .nokturn-bubbles.zip każda strona ma dokument pages/00000.json
(i kolejne numery). Pole znajduje się w result.bubbles przy konkretnym dymku:

    "tail_tip": {"x": 0.45, "y": 0.62, "confidence": 0.95, "kind": "visible-outline"}

- x i y są znormalizowanymi współrzędnymi całej strony, od 0 do 1.
- W pikselach źródła: x * result.width oraz y * result.height.
- Wielokąt nadal używa współrzędnych prostokąta dymka, co jest innym układem.
- Punkt oznacza istniejący wierzchołek końca widocznego obrysu.
- Nie oznacza pozycji ust ani odtworzonej, niewidocznej części ogonka.
- confidence opisuje warunki geometryczne, nie udowodnione 95% trafności.
- Brak tail_tip jest prawidłowy i częsty, zwłaszcza dla niepewnych, złożonych,
  ciemnych, ramkowych i pozbawionych ogonka regionów.

Nokturn może wykorzystać punkt dowolnie: jako początek animacji, kotwicę
powiększenia albo tylko do zachowania związku ze stroną. Decyzje dotyczące
czytelności, marginesów ekranu i bezpiecznego położenia należą do czytnika.

Dodanie punktu nie zmienia geometrii dymka, tekstu, podziału ani kolejności.
Nieprawidłowe opcjonalne dane są pomijane przez walidator Studio bez odrzucania
poprawnej strony. Starsze czytniki również mogą je zignorować. Jeśli Nokturn
stosuje własną listę dozwolonych pól, przy wdrażaniu obsługi należy dopuścić
tail_tip; wcześniejszy walidator może je usuwać z odpowiedzi, choć pozostają
w surowym dokumencie pakietu.

Ta wersja Studio nie zmienia Nokturna ani APK. Prywatny prototyp wykorzystania
punktu posłużył do próby wykonalności; testowe zmiany czytnika zostały cofnięte.
