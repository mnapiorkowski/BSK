# BSK* - zad. 2 (inżynieria wsteczna)

## 1. Znajdź flagę. Flaga jest w formacie "FLAG{...}". Opisz, w jaki sposób udało się uzyskać flagę.
*FLAG{gr3pp!ng-thr0ugh-str1ngs?-isn't-th4t-t0o-ez?}*

Wystarczy otworzyć program w IDA i wyszukać (`alt+T`) napis `"FLAG{"`. W ten sposób można znaleźć stałą `aFlagGr3ppNgThr`, której wartością jest napis zawierający flagę.

## 2. Flagę można również wyświetlić w grze. Opisz, jak sprawić, by niezmodyfikowana gra wyświetliła tę flagę.
Należy wpisać z klawiatury `"canihazflagplx"`, podejść do skrzynki na listy przy swoim domu i wcisnąć spację.

W sekcji `.data` znajduje się następujący fragment:
```
dq offset player_mailbox
dq offset aFlagGr3ppNgThr
```
To zasugerowało mi, że flaga ma jakiś związek z funkcją `player_mailbox`. Po zdeasemblowaniu tej funkcji zobaczyłem, że domyślny napis przy otwieraniu skrzynki pojawia się jeśli funkcja `check(5)` zwróci fałsz.

Zdeasemblowałem funkcję `check` i zobaczyłem, że `check(k)` sprawdza, czy pewien qword ma ustawiony `k`-ty bit na `1` (numerując bity od `0`).
Sprawdziłem cross-referencje do tego qworda (w IDA skrót klawiaturowy to `X`) i zobaczyłem, że korzystają z niego 3 funkcje - `check`, `mark` i `clear`.
Sprawdziłem cross-referencje do funkcji `mark` i przejrzałem je, szukając wywołania `mark(5)`. Znajduje się w funkcji `overworld_keypress`. 

Po zdeasemblowaniu tej funkcji zobaczyłem, że jeśli wciśnięty klawisz nie jest spacją, to sprawdzane jest, czy ten klawisz (jego numer w ASCII), 
XOR-owany z liczbą `0x6A` da w wyniku kolejną liczbę z pewnej tablicy bajtów (i tak 14 razy).
W tej tablicy znajdują się następujące liczby: `{0x9, 0xB, 0x4, 0x3, 0x2, 0xB, 0x10, 0xC, 0x6, 0xB, 0xD, 0x1A, 0x6, 0x12}`.
XOR-uję te liczby z `0x6A` i dostaję kolejno: `{0x63, 0x61, 0x6e, 0x69, 0x68, 0x61, 0x7a, 0x66, 0x6c, 0x61, 0x67, 0x70, 0x6c, 0x78}`, co odpowiada numerom ASCII znaków: 
`{c, a, n, i, h, a, z, f, l, a, g, p, l, x}`.

Zatem w grze wystarczy wpisać ten kod i wejść w interakcję ze skrzynką, aby funkcja `player_mailbox` przekazała funkcji `show_text` alternatywny tekst, czyli właśnie flagę.

## 3. Zmodyfikuj grę, aby można było chodzić przez ściany i inne obiekty, które normalnie blokują gracza.
W funkcji `object_can_move` usunąłem (zamieniłem na `NOP`-y) następujące instrukcje, wywołujące sprawdzanie kolizji:
```
.text:00000001400062FF                 mov     edx, edi
.text:0000000140006301                 mov     ecx, esi
.text:0000000140006303                 call    metatile_collision_at
.text:0000000140006308                 test    al, al
.text:000000014000630A                 jnz     short loc_140006350
```

## 4. Spraw, aby chodzić przez ściany dało się tylko trzymając klawisz Shift (wystarczy obsłużyć tylko jeden czyli lewy albo prawy).
Wykorzystałem wolne miejsce między funkcjami `get_object_facing_coords`, `object_at` i `object_can_move` na dopisanie własnych instrukcji.

Najpierw zmieniłem adres, pod który jest wykonywany skok, gdy zostanie wykryta kolizja w funkcji `object_can_move`:
```
.text:0000000140006303                 call    metatile_collision_at
.text:0000000140006308                 test    al, al
.text:000000014000630A                 jnz     short loc_140006291
```
Pod tym adresem umieściłem kolejny skok, do wolnego miejsca pod funkcją `get_object_facing_coords`:
```
.text:0000000140006291                 jmp     short loc_140006216
```
Tam umieściłem następujące instrukcje:
```
.text:0000000140006216                 xor     ecx, ecx
.text:0000000140006218                 call    cs:__imp_SDL_GetKeyboardState
.text:000000014000621E                 jmp     short loc_140006293
```
Po wykonaniu funkcji `SDL_GetKeyboardState`, w rejestrze `rax` znajduje się adres tablicy, w której zapisane są stany wszystkich klawiszy.
Następnie wykonywany jest skok pod wskazany adres, gdzie umieściłem instrukcje sprawdzające stan lewego Shifta, który ma kod `225`, czyli `0xE1`:
```
.text:0000000140006293                 cmp     byte ptr [rax+0E1h], 0
.text:000000014000629A                 jnz     short loc_14000630C
.text:000000014000629C                 nop
.text:000000014000629D                 nop
.text:000000014000629E                 jmp     short loc_14000631E
```
Jeśli jest wciśnięty, to wykonywany jest skok zaraz za instrukcję skoku, którą zmieniłem na początku - do instrukcji, które wykonują się, gdy nie ma kolizji.
W przeciwnym przypadku wykonywany jest skok do instrukcji skoku, który przenosi do instrukcji, które wykonują się, gdy zachodzi kolizja:
```
.text:000000014000631E                 jz      short loc_140006350
```