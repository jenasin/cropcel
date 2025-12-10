# UAT Testovaci scenare - Tekro sklizen

**Aplikace:** http://localhost:8501
**Datum:** 2024-12-09

---

## Testovaci ucty

| Role | Uzivatelske jmeno | Heslo |
|------|-------------------|-------|
| Admin | adminpetr | heslo (zkuste standardni heslo nebo kontaktujte admina) |
| Editor | agronom | heslo |
| Watcher | zemedelec | heslo |

> **Poznamka:** Hesla jsou v demo rezimu. Zkuste: `heslo`, `password`, `123456` nebo `admin`

---

## TC-01: Prihlaseni a odhlaseni

### TC-01.1: Uspesne prihlaseni jako Admin
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Otevrete http://localhost:8501 | Zobrazi se prihlasovaci stranka s logem "Tekro sklizen" | |
| 2 | Zadejte uzivatelske jmeno: `adminpetr` | Pole se vyplni | |
| 3 | Zadejte heslo | Heslo je maskovane | |
| 4 | Kliknete na "Prihlasit se" | Zobrazi se Dashboard a bocni menu se vsemi polozkami | |
| 5 | Overeni role | V boku je zobrazeno "ADMIN" s cervenym symbolem | |

### TC-01.2: Uspesne prihlaseni jako Editor
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Prihlaste se jako `agronom` | Dashboard se zobrazi | |
| 2 | Overeni role | V boku je zobrazeno "EDITOR" se zlutym symbolem | |
| 3 | Overeni menu | Menu obsahuje mene polozek nez Admin (chybi Uzivatele, Pristup k podnikum) | |

### TC-01.3: Uspesne prihlaseni jako Watcher
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Prihlaste se jako `zemedelec` | Dashboard se zobrazi | |
| 2 | Overeni role | V boku je zobrazeno "WATCHER" se zelenym symbolem | |
| 3 | Overeni menu | Menu obsahuje pouze: Dashboard, Odrudy, Pole, Souhrn plodin, Plodiny | |

### TC-01.4: Neuspesne prihlaseni
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Zadejte spatne uzivatelske jmeno | - | |
| 2 | Zadejte spatne heslo | - | |
| 3 | Kliknete "Prihlasit se" | Zobrazi se chybova hlaska "Nespravne uzivatelske jmeno nebo heslo" | |

### TC-01.5: Odhlaseni
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Prihlaste se jako libovolny uzivatel | Dashboard se zobrazi | |
| 2 | Kliknete na "Odhlasit se" v bocnim menu | Zobrazi se prihlasovaci stranka | |

---

## TC-02: Dashboard

### TC-02.1: Zobrazeni Dashboard
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Prihlaste se a prejdete na Dashboard | Stranka se nacte bez chyb | |
| 2 | Overeni obsahu | Zobrazi se prehledove statistiky/grafy | |
| 3 | Overeni responzivity | Pri zmene velikosti okna se obsah spravne prizpusobi | |

---

## TC-03: Sprava Odrud

### TC-03.1: Zobrazeni seznamu odrud
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Odrudy" v menu | Zobrazi se seznam odrud | |
| 2 | Overeni tabulky | Data se zobrazi v tabulce | |

### TC-03.2: Pridani nove odrudy (pouze Admin/Editor)
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Prihlaste se jako Admin nebo Editor | - | |
| 2 | Prejdete na Odrudy | - | |
| 3 | Vyplnte formular pro novou odrudu | - | |
| 4 | Kliknete na tlacitko pro ulozeni | Nova odruda se zobrazi v seznamu | |

### TC-03.3: Editace odrudy (pouze Admin/Editor)
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Vyberte existujici odrudu | - | |
| 2 | Zmente nektere udaje | - | |
| 3 | Ulozte zmeny | Zmeny se projevi v seznamu | |

### TC-03.4: Omezeni pro Watcher
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Prihlaste se jako `zemedelec` (Watcher) | - | |
| 2 | Prejdete na Odrudy | Data se zobrazi pouze pro cteni | |
| 3 | Overeni | Formular pro pridani/editaci neni dostupny | |

---

## TC-04: Sprava Poli

### TC-04.1: Zobrazeni seznamu poli
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Pole" v menu | Zobrazi se seznam poli | |
| 2 | Overeni dat | Tabulka obsahuje informace o polich | |

### TC-04.2: Pridani noveho pole (Admin/Editor)
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na moznost pridat pole | Formular se zobrazi | |
| 2 | Vyplnte povinne udaje | - | |
| 3 | Ulozte | Pole se prida do seznamu | |

### TC-04.3: Filtrovani poli
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Pouzijte dostupne filtry | Seznam se omezi dle filtru | |

---

## TC-05: Sprava Pozemku

### TC-05.1: Zobrazeni pozemku
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Pozemky" v menu | Zobrazi se seznam pozemku | |

### TC-05.2: CRUD operace pozemku
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Vytvoreni noveho pozemku | Pozemek se prida | |
| 2 | Editace pozemku | Zmeny se ulozi | |
| 3 | Smazani pozemku | Pozemek se odstrani ze seznamu | |

---

## TC-06: Typy pozemku

### TC-06.1: Zobrazeni typu pozemku
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Typy pozemku" | Seznam se zobrazi | |

### TC-06.2: Sprava typu pozemku
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Pridani noveho typu | Typ se prida | |
| 2 | Editace typu | Zmeny se ulozi | |

---

## TC-07: Sberna mista

### TC-07.1: Zobrazeni sbernych mist
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Sberna mista" | Seznam sbernych mist se zobrazi | |

### TC-07.2: CRUD operace
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Pridani mista | Misto se prida | |
| 2 | Editace mista | Zmeny se ulozi | |
| 3 | Smazani mista | Misto se odstrani | |

---

## TC-08: Sberne srazky

### TC-08.1: Zobrazeni sbernych srazek
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Sberne srazky" | Seznam se zobrazi | |

### TC-08.2: CRUD operace
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Pridani srazky | Srazka se prida | |
| 2 | Editace srazky | Zmeny se ulozi | |

---

## TC-09: Odpisy

### TC-09.1: Zobrazeni odpisu
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Odpisy" | Seznam odpisu se zobrazi | |

### TC-09.2: CRUD operace odpisu
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Pridani odpisu | Odpis se prida | |
| 2 | Editace odpisu | Zmeny se ulozi | |

---

## TC-10: Souhrn plodin

### TC-10.1: Zobrazeni souhrnu
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Souhrn plodin" | Zobrazi se souhrn plodin | |
| 2 | Overeni dat | Data jsou spravne agregovana | |

---

## TC-11: Roky

### TC-11.1: Sprava roku
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Roky" | Seznam roku se zobrazi | |
| 2 | Pridani roku | Rok se prida | |
| 3 | Editace roku | Zmeny se ulozi | |

---

## TC-12: Statistiky

### TC-12.1: Zobrazeni statistik
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Statistiky" | Stranka statistik se zobrazi | |
| 2 | Overeni grafu | Grafy se renderuji spravne | |
| 3 | Interakce s grafy | Hovery a tooltipy funguji | |

---

## TC-13: Sprava uzivatelu (pouze Admin)

### TC-13.1: Zobrazeni uzivatelu
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Prihlaste se jako Admin | - | |
| 2 | Kliknete na "Uzivatele" | Seznam uzivatelu se zobrazi | |

### TC-13.2: Pridani uzivatele
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na pridat uzivatele | Formular se zobrazi | |
| 2 | Vyplnte udaje (jmeno, email, role, heslo) | - | |
| 3 | Ulozte | Uzivatel se prida do seznamu | |

### TC-13.3: Editace uzivatele
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Vyberte uzivatele k editaci | - | |
| 2 | Zmente roli nebo udaje | - | |
| 3 | Ulozte | Zmeny se projevi | |

### TC-13.4: Pristup Editora k uzivatelum
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Prihlaste se jako Editor | - | |
| 2 | Overeni menu | Polozka "Uzivatele" neni v menu | |

---

## TC-14: Pristup k podnikum (pouze Admin)

### TC-14.1: Sprava pristupu
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Prihlaste se jako Admin | - | |
| 2 | Kliknete na "Pristup k podnikum" | Seznam se zobrazi | |
| 3 | Priradte uzivateli podnik | Prirazeni se ulozi | |

---

## TC-15: Podniky

### TC-15.1: Zobrazeni podniku
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Podniky" | Seznam podniku se zobrazi | |

### TC-15.2: CRUD operace
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Pridani podniku | Podnik se prida | |
| 2 | Editace podniku | Zmeny se ulozi | |

---

## TC-16: Plodiny

### TC-16.1: Zobrazeni plodin
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Plodiny" | Seznam plodin se zobrazi | |

### TC-16.2: CRUD operace
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Pridani plodiny | Plodina se prida | |
| 2 | Editace plodiny | Zmeny se ulozi | |

---

## TC-17: Odrudy osiva

### TC-17.1: Zobrazeni odrud osiva
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Kliknete na "Odrudy osiva" | Seznam se zobrazi | |

### TC-17.2: CRUD operace
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Pridani odrudy osiva | Odruda se prida | |
| 2 | Editace odrudy | Zmeny se ulozi | |

---

## TC-18: Obecne testy UI

### TC-18.1: Navigace
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Proklikejte vsechny polozky menu | Vsechny stranky se nactou bez chyb | |
| 2 | Prechod mezi strankami | Navigace je plynula | |

### TC-18.2: Responzivita
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Zmente velikost okna prohlizece | Layout se prizpusobi | |
| 2 | Otevrete na mobilnim zarizeni | Aplikace je pouzitelna | |

### TC-18.3: Zobrazeni chyb
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Sledujte konzoli prohlizece | Zadne JS errory | |
| 2 | Sledujte cervene hlasky ve Streamlit | Zadne Python exceptions | |

---

## TC-19: Datova integrita

### TC-19.1: Ulozeni dat
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Pridejte novy zaznam (napr. pole) | - | |
| 2 | Odhlaste se a znovu prihlaste | Zaznam je stale v systemu | |

### TC-19.2: Validace formularu
| Krok | Akce | Ocekavany vysledek | OK/NOK |
|------|------|-------------------|--------|
| 1 | Zkuste odeslat prazdny formular | Zobrazi se validacni hlaska | |
| 2 | Zadejte neplatne hodnoty | System upozorni na chybu | |

---

## Souhrn testu

| Cislo testu | Nazev | Tester | Datum | Vysledek |
|-------------|-------|--------|-------|----------|
| TC-01 | Prihlaseni a odhlaseni | | | |
| TC-02 | Dashboard | | | |
| TC-03 | Sprava Odrud | | | |
| TC-04 | Sprava Poli | | | |
| TC-05 | Sprava Pozemku | | | |
| TC-06 | Typy pozemku | | | |
| TC-07 | Sberna mista | | | |
| TC-08 | Sberne srazky | | | |
| TC-09 | Odpisy | | | |
| TC-10 | Souhrn plodin | | | |
| TC-11 | Roky | | | |
| TC-12 | Statistiky | | | |
| TC-13 | Sprava uzivatelu | | | |
| TC-14 | Pristup k podnikum | | | |
| TC-15 | Podniky | | | |
| TC-16 | Plodiny | | | |
| TC-17 | Odrudy osiva | | | |
| TC-18 | Obecne testy UI | | | |
| TC-19 | Datova integrita | | | |

---

## Poznamky testera

_Zde zapisujte veskere poznamky, nalezene bugy a pripominky:_

1.
2.
3.

---

**Pripravil:** Claude
**Verze dokumentu:** 1.0