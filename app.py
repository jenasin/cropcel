"""
Hlavní soubor Streamlit aplikace pro správu zemědělských dat
"""
import streamlit as st
import pandas as pd
from utils.auth import AuthManager, init_session_state, logout
from utils.data_manager import DataManager
import config

# Konfigurace stránky
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializace
init_session_state()

# Globální instance managerů
@st.cache_resource
def get_auth_manager():
    """Vrátí instanci AuthManager"""
    import os
    users_path = os.path.join(config.DATA_DIR, 'users.csv')
    return AuthManager(users_path)

@st.cache_resource
def get_data_manager():
    """Vrátí instanci DataManager"""
    return DataManager(config.DATA_DIR)


def show_login_page():
    """Zobrazí přihlašovací stránku"""
    st.title(f"{config.APP_ICON} {config.APP_TITLE}")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("Přihlášení")

        with st.form("login_form"):
            username = st.text_input("Uživatelské jméno")
            password = st.text_input("Heslo", type="password")
            submit = st.form_submit_button("Přihlásit se", use_container_width=True)

            if submit:
                auth_manager = get_auth_manager()
                user = auth_manager.authenticate(username, password)

                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.success(f"Vítejte, {user['full_name']}!")
                    st.rerun()
                else:
                    st.error("Nesprávné uživatelské jméno nebo heslo")

        st.info("💡 Demo přístupy:\n- Admin: adminpetr\n- Editor: agronom\n- Watcher: zemedelec")


def fetch_and_save_rain(biz_id: int, sensor_addr: str, dm, use_yesterday: bool = False) -> tuple[bool, str, float | None]:
    """Stáhne a uloží srážky pro podnik. Vrací (success, message, rain_mm)

    Args:
        use_yesterday: Pokud True, stáhne včerejší data (pro automatické stahování v 5:00)
    """
    from utils.agdata_api import get_today_weather, get_yesterday_weather

    if use_yesterday:
        weather = get_yesterday_weather(sensor_addr)
    else:
        weather = get_today_weather(sensor_addr, fallback_yesterday=False)

    if 'error' in weather:
        return False, f"Chyba: {weather['error']}", None

    rain = weather.get('rain_mm')
    if rain is None:
        rain = 0.0  # Žádné srážky = 0 mm

    # Použít datum z API (může být včerejší pokud dnešní data nejsou k dispozici)
    api_date = weather.get('date')

    # Zkontrolovat, zda už existuje záznam pro toto datum
    srazky_df = dm.get_sbernasrazky()
    today_str = api_date

    existing = srazky_df[
        (srazky_df['PodnikID'] == biz_id) &
        (srazky_df['Datum'].astype(str) == today_str)
    ]

    if not existing.empty:
        # Aktualizovat existující záznam
        idx = existing.index[0]
        srazky_df.loc[idx, 'Objem'] = rain
        dm.save_sbernasrazky(srazky_df)
        return True, f"{api_date}: {rain:.1f} mm (aktualizováno)", rain

    # Přidat nový záznam
    misto_mapping = {1: 30, 2: 29, 3: 28, 4: 27, 5: 26, 6: 25, 8: 42, 9: 43}
    misto_id = misto_mapping.get(int(biz_id), 30)

    new_id = srazky_df['id'].max() + 1 if not srazky_df.empty else 1
    new_row = {
        'id': new_id,
        'MistoID': misto_id,
        'PodnikID': biz_id,
        'Datum': today_str,
        'Objem': rain
    }
    srazky_df = pd.concat([srazky_df, pd.DataFrame([new_row])], ignore_index=True)
    dm.save_sbernasrazky(srazky_df)

    return True, f"{api_date}: {rain:.1f} mm", rain


def check_auto_fetch():
    """Zkontroluje a provede automatické stažení v 5:00 (data z předchozího dne)"""
    from datetime import datetime, date
    import os

    dm = get_data_manager()
    businesses = dm.get_businesses()

    if 'sensor_addr' not in businesses.columns:
        return

    businesses_with_sensor = businesses[
        businesses['sensor_addr'].notna() &
        (businesses['sensor_addr'] != '')
    ]

    if businesses_with_sensor.empty:
        return

    # Flag soubor pro sledování denního stažení
    flag_file = os.path.join(os.path.dirname(__file__), "config", "last_fetch.txt")
    today_str = date.today().strftime('%Y-%m-%d')
    now = datetime.now()

    # Zkontrolovat, zda už bylo dnes staženo
    last_fetch_date = None
    if os.path.exists(flag_file):
        with open(flag_file, 'r') as f:
            last_fetch_date = f.read().strip()

    already_fetched_today = (last_fetch_date == today_str)

    # Podmínky pro automatické stažení:
    # Je 5:00 nebo později a ještě nebylo dnes staženo
    # (stahuje data z předchozího dne, která jsou v 5:00 již kompletní)
    should_fetch = False

    if not already_fetched_today:
        if now.hour >= 5:
            should_fetch = True
            st.toast("Automatické stahování srážek z předchozího dne...", icon="🌧️")

    if should_fetch:
        for _, biz in businesses_with_sensor.iterrows():
            fetch_and_save_rain(int(biz['id']), biz['sensor_addr'], dm, use_yesterday=True)

        # Zapsat flag
        os.makedirs(os.path.dirname(flag_file), exist_ok=True)
        with open(flag_file, 'w') as f:
            f.write(today_str)


def show_weather_widget():
    """Widget pro stahování srážek z meteostanic v sidebaru"""
    from datetime import date
    from utils.agdata_api import get_api_token

    # Zkontrolovat, zda je API token nastaven
    if not get_api_token():
        return

    dm = get_data_manager()
    businesses = dm.get_businesses()

    # Najít podniky s nastaveným sensor_addr
    if 'sensor_addr' not in businesses.columns:
        return

    businesses_with_sensor = businesses[
        businesses['sensor_addr'].notna() &
        (businesses['sensor_addr'] != '')
    ]

    if businesses_with_sensor.empty:
        return

    # Automatické stažení (16:00 nebo catch-up)
    check_auto_fetch()

    st.markdown("**Meteostanice**")

    # Získat dnešní data pro zobrazení
    srazky_df = dm.get_sbernasrazky()
    today_str = date.today().strftime('%Y-%m-%d')

    for _, biz in businesses_with_sensor.iterrows():
        sensor_addr = biz['sensor_addr']
        biz_name = biz['nazev']
        biz_id = int(biz['id'])

        # Zjistit, zda existuje dnešní záznam
        today_record = srazky_df[
            (srazky_df['PodnikID'] == biz_id) &
            (srazky_df['Datum'].astype(str) == today_str)
        ]

        with st.expander(f"{biz_name}", expanded=False):
            # Zobrazit dnešní hodnotu, pokud existuje
            if not today_record.empty:
                rain_val = today_record.iloc[0]['Objem']
                st.metric("Dnešní srážky", f"{rain_val:.1f} mm")

            # Tlačítko pro manuální stažení a uložení
            if st.button(f"Stáhnout a uložit", key=f"fetch_save_{biz_id}"):
                with st.spinner("Stahuji..."):
                    success, msg, rain = fetch_and_save_rain(biz_id, sensor_addr, dm)

                if success:
                    st.toast(msg, icon="✅")
                else:
                    st.toast(msg, icon="❌")

                # Refresh po 2 sekundách
                import time
                time.sleep(2)
                st.rerun()


def show_sidebar():
    """Zobrazí boční menu"""
    with st.sidebar:
        user = st.session_state.user

        # Logo a název aplikace
        st.markdown(f"## {config.APP_ICON} {config.APP_TITLE}")
        st.markdown("---")

        # Informace o uživateli
        display_name = user.get('full_name') or user.get('username', 'Uživatel')
        if pd.isna(display_name) or display_name == '':
            display_name = user.get('username', 'Uživatel')
        st.markdown(f"**👤 {display_name}**")
        role_colors = {'admin': '🔴', 'editor': '🟡', 'watcher': '🟢'}
        role_color = role_colors.get(user['role'], '⚪')
        st.caption(f"{role_color} {user['role'].upper()}")
        st.markdown("---")

        # Inicializace vybrané stránky
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = 'Přehled Tekro'

        # Menu rozdělené do skupin - ale jeden radio button
        menu_groups = config.MENU_GROUPS.get(user['role'], {})

        # Vytvořit seznam všech položek s nadpisy skupin
        all_options = []
        for group_name, items in menu_groups.items():
            all_options.append(f"**{group_name}**")  # Nadpis skupiny
            all_options.extend(items)

        # Najdi index aktuální stránky
        current_index = 0
        if st.session_state.selected_page in all_options:
            current_index = all_options.index(st.session_state.selected_page)
        else:
            # Najít první položku, která není nadpis
            for i, opt in enumerate(all_options):
                if not opt.startswith("**"):
                    current_index = i
                    break

        # Jeden radio button pro celé menu
        selected = st.radio(
            "Navigace",
            options=all_options,
            index=current_index,
            key="main_menu",
            label_visibility="collapsed",
            format_func=lambda x: x.replace("**", "") if x.startswith("**") else f"  {x}"
        )

        # Aktualizace vybrané stránky (ignorovat nadpisy skupin)
        if selected and not selected.startswith("**"):
            if selected != st.session_state.selected_page:
                st.session_state.selected_page = selected
                st.rerun()

        st.markdown("---")

        # Widget pro stahování srážek z meteostanic
        show_weather_widget()

        st.markdown("---")

        # Tlačítko odhlášení
        if st.button("🚪 Odhlásit se", use_container_width=True):
            logout()


def show_main_content():
    """Zobrazí hlavní obsah podle vybrané stránky"""
    selected_page = st.session_state.get('selected_page', 'Přehled Tekro')

    # Import a zobrazení příslušné stránky
    if selected_page == 'Nástěnka':
        from page_modules import dashboard
        dashboard.show(get_data_manager(), st.session_state.user)
    elif selected_page == 'Podniky Tekro':
        from page_modules import podniky_prehled
        podniky_prehled.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Pozemky Tekro':
        from page_modules import pozemky_tekro
        pozemky_tekro.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Zadávání dat':
        from page_modules import zadavani
        zadavani.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Přehled podniku':
        from page_modules import prehled_podniku
        prehled_podniku.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Odrůdy':
        from page_modules import odrudy
        odrudy.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Podniky':
        from page_modules import businesses
        businesses.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Plodiny':
        from page_modules import crops
        crops.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Pole':
        from page_modules import fields
        fields.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Pozemky':
        from page_modules import pozemky
        pozemky.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Sběrná místa':
        from page_modules import sbernamista
        sbernamista.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Odrůdy osiva':
        from page_modules import varieties_seed
        varieties_seed.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Uživatelé':
        from page_modules import users
        users.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Roky':
        from page_modules import roky
        roky.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Sběrné srážky':
        from page_modules import sbernasrazky
        sbernasrazky.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Odpisy':
        from page_modules import odpisy
        odpisy.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Souhrn plodin':
        from page_modules import sumplodiny
        sumplodiny.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Typy pozemků':
        from page_modules import typpozemek
        typpozemek.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Přístup k podnikům':
        from page_modules import userpodniky
        userpodniky.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Statistiky':
        from page_modules import statistiky
        statistiky.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Srážky Tekro':
        from page_modules import srazky_tekro
        srazky_tekro.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Přehled Tekro':
        from page_modules import prehled_tekro
        prehled_tekro.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Plodiny Tekro':
        from page_modules import plodiny_tekro
        plodiny_tekro.show(get_data_manager(), st.session_state.user, get_auth_manager())
    elif selected_page == 'Osevní plány Tekro':
        from page_modules import osevni_plany
        osevni_plany.show(get_data_manager(), st.session_state.user, get_auth_manager())


def main():
    """Hlavní funkce aplikace"""
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_sidebar()
        show_main_content()


if __name__ == "__main__":
    main()
