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

# Menu položky podle rolí
MENU_ITEMS = {
    'admin': [
        {'name': 'Dashboard', 'icon': '📊'},
        {'name': 'Odrůdy', 'icon': '📉'},
        {'name': 'Pole', 'icon': '🚜'},
        {'name': 'Pozemky', 'icon': '🗺️'},
        {'name': 'Typy pozemků', 'icon': '🏞️'},
        {'name': 'Sběrná místa', 'icon': '📍'},
        {'name': 'Sběrné srážky', 'icon': '📦'},
        {'name': 'Souhrn plodin', 'icon': '📈'},
        {'name': 'Roky', 'icon': '📅'},
        {'name': 'Uživatelé', 'icon': '👥'},
        {'name': 'Přístup k podnikům', 'icon': '🔗'},
        {'name': 'Podniky', 'icon': '🏢'},
        {'name': 'Plodiny', 'icon': '🌾'},
        {'name': 'Odrůdy osiva', 'icon': '🌱'},
    ],
    'editor': [
        {'name': 'Dashboard', 'icon': '📊'},
        {'name': 'Odrůdy', 'icon': '📉'},
        {'name': 'Pole', 'icon': '🚜'},
        {'name': 'Pozemky', 'icon': '🗺️'},
        {'name': 'Typy pozemků', 'icon': '🏞️'},
        {'name': 'Sběrná místa', 'icon': '📍'},
        {'name': 'Sběrné srážky', 'icon': '📦'},
        {'name': 'Souhrn plodin', 'icon': '📈'},
        {'name': 'Roky', 'icon': '📅'},
        {'name': 'Podniky', 'icon': '🏢'},
        {'name': 'Plodiny', 'icon': '🌾'},
        {'name': 'Odrůdy osiva', 'icon': '🌱'},
    ],
    'watcher': [
        {'name': 'Dashboard', 'icon': '📊'},
        {'name': 'Odrůdy', 'icon': '📉'},
        {'name': 'Pole', 'icon': '🚜'},
        {'name': 'Souhrn plodin', 'icon': '📈'},
        {'name': 'Plodiny', 'icon': '🌾'},
    ]
}

# Mapování stránek na soubory
PAGE_FILES = {
    'Dashboard': 'dashboard',
    'Odrůdy': 'odrudy',
    'Podniky': 'businesses',
    'Plodiny': 'crops',
    'Pole': 'fields',
    'Pozemky': 'pozemky',
    'Typy pozemků': 'typpozemek',
    'Sběrná místa': 'sbernamista',
    'Sběrné srážky': 'sbernasrazky',
    'Souhrn plodin': 'sumplodiny',
    'Odrůdy osiva': 'varieties_seed',
    'Roky': 'roky',
    'Uživatelé': 'users',
    'Přístup k podnikům': 'userpodniky',
}
