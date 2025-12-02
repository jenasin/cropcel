# Crop Management System

Webová aplikace pro správu zemědělských dat postavená na Streamlit frameworku.

## Funkce

- **Přihlašování podle rolí** (Admin, Editor, Watcher)
- **Dashboard** s přehledem statistik a grafů
- **Správa podniků** - přidávání a editace podniků
- **Správa plodin** - správa seznamu plodin s filtry
- **Správa polí** - detailní správa polí včetně výměry, sklizně a vah
- **Správa pozemků** - evidence pozemků
- **Sběrná místa** - správa sběrných míst
- **Odrůdy osiva** - katalog odrůd osiva
- **Správa uživatelů** - pouze pro administrátory

## Role a oprávnění

### Admin
- Plný přístup ke všem datům
- Může přidávat, upravovat a mazat záznamy
- Může spravovat uživatele

### Editor
- Může číst všechna data
- Může přidávat a upravovat záznamy
- Nemůže mazat záznamy ani spravovat uživatele

### Watcher
- Pouze čtení dat
- Nemůže upravovat žádné záznamy

## Instalace a spuštění

### Lokálně

1. Naklonujte repozitář:
```bash
git clone <repository-url>
cd croptekro
```

2. Nainstalujte závislosti:
```bash
pip install -r requirements.txt
```

3. Spusťte aplikaci:
```bash
streamlit run app.py
```

4. Otevřete prohlížeč na adrese `http://localhost:8501`

### Demo přístupy

- **Admin:** username: `adminpetr`, heslo: jakékoliv (demo režim)
- **Editor:** username: `agronom`, heslo: jakékoliv (demo režim)
- **Watcher:** username: `zemedelec`, heslo: jakékoliv (demo režim)

## Nasazení do Streamlit Cloud

1. Pushněte kód do GitHub repozitáře
2. Přihlaste se na [share.streamlit.io](https://share.streamlit.io)
3. Klikněte na "New app"
4. Vyberte váš repozitář a branch
5. Nastavte main file path: `app.py`
6. Klikněte "Deploy"

## Struktura projektu

```
croptekro/
├── app.py                 # Hlavní aplikační soubor
├── config.py             # Konfigurace aplikace
├── requirements.txt      # Python závislosti
├── README.md            # Dokumentace
├── .streamlit/
│   └── config.toml      # Streamlit konfigurace
├── utils/
│   ├── __init__.py
│   ├── auth.py          # Autentizace a autorizace
│   └── data_manager.py  # Správa dat z CSV
└── pages/
    ├── __init__.py
    ├── dashboard.py     # Dashboard
    ├── businesses.py    # Správa podniků
    ├── crops.py         # Správa plodin
    ├── fields.py        # Správa polí
    ├── pozemky.py       # Správa pozemků
    ├── sbernamista.py   # Sběrná místa
    ├── varieties_seed.py # Odrůdy osiva
    └── users.py         # Správa uživatelů
```

## Datový model

Aplikace pracuje s CSV soubory z GitHub repozitáře:
- `users.csv` - Uživatelé a autentizace
- `businesses.csv` - Podniky
- `crops.csv` - Plodiny
- `fields.csv` - Pole a sklizeň
- `pozemky.csv` - Pozemky
- `sbernamista.csv` - Sběrná místa
- `varieties_seed.csv` - Odrůdy osiva

## Poznámky k demo verzi

Tato verze je demo a funguje v read-only módu. Změny v datech nejsou perzistentní a jsou uloženy pouze v session state. Pro produkční použití je potřeba:

1. Implementovat backend API pro zápis dat
2. Použít databázi místo CSV souborů
3. Implementovat správné hashování hesel (bcrypt/pbkdf2)
4. Přidat validaci a bezpečnostní kontroly
5. Implementovat auditní log změn

## Technologie

- **Streamlit** - Web framework
- **Pandas** - Práce s daty
- **Plotly** - Interaktivní grafy

## Licence

MIT
