"""
Konfigurační soubor aplikace
"""
import os

# Cesta k lokálním CSV souborům
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Nastavení aplikace
APP_TITLE = "Tekro sklizeň"
APP_ICON = "🌾"

# Menu položky podle rolí - rozděleno do skupin
MENU_GROUPS = {
    'admin': {
        'Přehledy': [
            'Přehled Tekro',
            'Plodiny Tekro',
            'Osevní plány Tekro',
            'Podniky Tekro',
            'Pozemky Tekro',
            'Srážky Tekro',
            'Přehled nabídek',
            'Přehled podniku',
            'Statistiky',
            'Odrůdy',
        ],
        'Správa': [
            'Pole',
            'Pozemky',
            'Typy pozemků',
            'Sběrná místa',
            'Sběrné srážky',
            'Odpisy',
            'Souhrn plodin',
            'Roky',
            'Uživatelé',
            'Přístup k podnikům',
            'Podniky',
            'Plodiny',
            'Odrůdy osiva',
            'Nástěnka',
        ]
    },
    'editor': {
        'Přehledy': [
            'Přehled Tekro',
            'Plodiny Tekro',
            'Osevní plány Tekro',
            'Podniky Tekro',
            'Pozemky Tekro',
            'Srážky Tekro',
            'Přehled nabídek',
            'Přehled podniku',
            'Statistiky',
            'Odrůdy',
        ],
        'Správa': [
            'Zadávání dat',
            'Pole',
            'Pozemky',
            'Typy pozemků',
            'Sběrná místa',
            'Sběrné srážky',
            'Odpisy',
            'Souhrn plodin',
            'Roky',
            'Podniky',
            'Plodiny',
            'Odrůdy osiva',
            'Nástěnka',
        ]
    },
    'watcher': {
        'Přehledy': [
            'Přehled Tekro',
            'Plodiny Tekro',
            'Osevní plány Tekro',
            'Podniky Tekro',
            'Pozemky Tekro',
            'Přehled podniku',
            'Odrůdy',
        ],
        'Správa': [
            'Pole',
            'Souhrn plodin',
            'Plodiny',
            'Nástěnka',
        ]
    }
}

# Pro zpětnou kompatibilitu - flat list všech položek
MENU_ITEMS = {
    role: [{'name': item, 'icon': ''} for group in groups.values() for item in group]
    for role, groups in MENU_GROUPS.items()
}

# Mapování stránek na soubory
PAGE_FILES = {
    'Nástěnka': 'dashboard',
    'Podniky Tekro': 'podniky_prehled',
    'Pozemky Tekro': 'pozemky_tekro',
    'Zadávání dat': 'zadavani',
    'Přehled podniku': 'prehled_podniku',
    'Odrůdy': 'odrudy',
    'Podniky': 'businesses',
    'Plodiny': 'crops',
    'Pole': 'fields',
    'Pozemky': 'pozemky',
    'Typy pozemků': 'typpozemek',
    'Sběrná místa': 'sbernamista',
    'Sběrné srážky': 'sbernasrazky',
    'Odpisy': 'odpisy',
    'Souhrn plodin': 'sumplodiny',
    'Odrůdy osiva': 'varieties_seed',
    'Roky': 'roky',
    'Uživatelé': 'users',
    'Přístup k podnikům': 'userpodniky',
    'Statistiky': 'statistiky',
    'Srážky Tekro': 'srazky_tekro',
    'Přehled Tekro': 'prehled_tekro',
    'Plodiny Tekro': 'plodiny_tekro',
    'Osevní plány Tekro': 'osevni_plany',
    'Přehled nabídek': 'prehled_nabidek',
}
