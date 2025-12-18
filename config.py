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
        {'name': 'Přehled Tekro', 'icon': '📋'},
        {'name': 'Plodiny Tekro', 'icon': '🌱'},
        {'name': 'Osevní plány Tekro', 'icon': '📅'},
        {'name': 'Podniky Tekro', 'icon': '🏢'},
        {'name': 'Pozemky Tekro', 'icon': '🌍'},
        {'name': 'Srážky Tekro', 'icon': '🌧️'},
        {'name': 'Přehled podniku', 'icon': '🏭'},
        {'name': 'Statistiky', 'icon': '📈'},
        {'name': 'Odrůdy', 'icon': '📉'},
        {'name': 'Pole', 'icon': '🚜'},
        {'name': 'Pozemky', 'icon': '🗺️'},
        {'name': 'Typy pozemků', 'icon': '🏞️'},
        {'name': 'Sběrná místa', 'icon': '📍'},
        {'name': 'Sběrné srážky', 'icon': '📦'},
        {'name': 'Odpisy', 'icon': '📝'},
        {'name': 'Souhrn plodin', 'icon': '🌾'},
        {'name': 'Roky', 'icon': '📅'},
        {'name': 'Uživatelé', 'icon': '👥'},
        {'name': 'Přístup k podnikům', 'icon': '🔗'},
        {'name': 'Podniky', 'icon': '🏢'},
        {'name': 'Plodiny', 'icon': '🌾'},
        {'name': 'Odrůdy osiva', 'icon': '🌱'},
        {'name': 'Nástěnka', 'icon': '📊'},
    ],
    'editor': [
        {'name': 'Přehled Tekro', 'icon': '📋'},
        {'name': 'Plodiny Tekro', 'icon': '🌱'},
        {'name': 'Osevní plány Tekro', 'icon': '📅'},
        {'name': 'Podniky Tekro', 'icon': '🏢'},
        {'name': 'Pozemky Tekro', 'icon': '🌍'},
        {'name': 'Srážky Tekro', 'icon': '🌧️'},
        {'name': 'Zadávání dat', 'icon': '📝'},
        {'name': 'Přehled podniku', 'icon': '🏭'},
        {'name': 'Statistiky', 'icon': '📈'},
        {'name': 'Odrůdy', 'icon': '📉'},
        {'name': 'Pole', 'icon': '🚜'},
        {'name': 'Pozemky', 'icon': '🗺️'},
        {'name': 'Typy pozemků', 'icon': '🏞️'},
        {'name': 'Sběrná místa', 'icon': '📍'},
        {'name': 'Sběrné srážky', 'icon': '📦'},
        {'name': 'Odpisy', 'icon': '📝'},
        {'name': 'Souhrn plodin', 'icon': '🌾'},
        {'name': 'Roky', 'icon': '📅'},
        {'name': 'Podniky', 'icon': '🏢'},
        {'name': 'Plodiny', 'icon': '🌾'},
        {'name': 'Odrůdy osiva', 'icon': '🌱'},
        {'name': 'Nástěnka', 'icon': '📊'},
    ],
    'watcher': [
        {'name': 'Přehled Tekro', 'icon': '📋'},
        {'name': 'Plodiny Tekro', 'icon': '🌱'},
        {'name': 'Osevní plány Tekro', 'icon': '📅'},
        {'name': 'Podniky Tekro', 'icon': '🏢'},
        {'name': 'Pozemky Tekro', 'icon': '🌍'},
        {'name': 'Přehled podniku', 'icon': '🏭'},
        {'name': 'Odrůdy', 'icon': '📉'},
        {'name': 'Pole', 'icon': '🚜'},
        {'name': 'Souhrn plodin', 'icon': '📈'},
        {'name': 'Plodiny', 'icon': '🌾'},
        {'name': 'Nástěnka', 'icon': '📊'},
    ]
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
}
