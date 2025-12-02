# Rychlý start

## Spuštění aplikace

### 1. Instalace závislostí

```bash
pip install -r requirements.txt
```

### 2. Spuštění aplikace

```bash
streamlit run app.py
```

Aplikace se otevře na adrese: `http://localhost:8501`

## Přihlášení

Použijte některý z těchto demo účtů:

### Administrátor
- **Username:** `adminpetr`
- **Heslo:** jakékoliv (demo režim)
- **Oprávnění:** Plný přístup, včetně správy uživatelů

### Editor
- **Username:** `agronom`
- **Heslo:** jakékoliv (demo režim)
- **Oprávnění:** Čtení a zápis dat (bez správy uživatelů)

### Watcher
- **Username:** `zemedelec`
- **Heslo:** jakékoliv (demo režim)
- **Oprávnění:** Pouze čtení dat

## Funkce aplikace

Po přihlášení máte k dispozici:

1. **Dashboard** - Přehled statistik a grafů
2. **Podniky** - Správa podniků
3. **Plodiny** - Správa plodin s filtry
4. **Pole** - Správa polí a sklizně
5. **Pozemky** - Evidence pozemků
6. **Sběrná místa** - Správa sběrných míst
7. **Odrůdy osiva** - Katalog odrůd
8. **Uživatelé** - Správa uživatelů (pouze admin)

## Poznámky

- Aplikace běží v **demo režimu**
- Změny nejsou **perzistentní** (uloženy pouze v session)
- Data se načítají z GitHub repozitáře (read-only)
- Pro produkční použití je potřeba backend API

## Nasazení do cloudu

### Streamlit Cloud (zdarma)

1. Pushněte kód do GitHub repozitáře
2. Jděte na [share.streamlit.io](https://share.streamlit.io)
3. Přihlaste se GitHub účtem
4. Klikněte "New app"
5. Vyberte repozitář a nastavte `app.py` jako main file
6. Klikněte "Deploy"

Aplikace bude dostupná na veřejné URL do několika minut!

## Podpora

Pro reportování chyb nebo dotazy:
- Vytvořte issue v GitHub repozitáři
- Email: [váš email]
