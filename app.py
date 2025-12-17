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

        # Menu položky podle role
        menu_items = config.MENU_ITEMS.get(user['role'], [])

        # Vytvořit options pro radio button
        options = [f"{item['icon']} {item['name']}" for item in menu_items]
        names = [item['name'] for item in menu_items]

        # Inicializace vybrané stránky
        if 'selected_page' not in st.session_state:
            st.session_state.selected_page = 'Dashboard'

        # Najdi index aktuální stránky
        current_index = 0
        if st.session_state.selected_page in names:
            current_index = names.index(st.session_state.selected_page)

        # Radio button menu
        selected = st.radio(
            "Navigace",
            options=options,
            index=current_index,
            label_visibility="collapsed"
        )

        # Aktualizace vybrané stránky
        if selected:
            selected_name = names[options.index(selected)]
            if selected_name != st.session_state.selected_page:
                st.session_state.selected_page = selected_name
                st.rerun()

        st.markdown("---")

        # Tlačítko odhlášení
        if st.button("🚪 Odhlásit se", use_container_width=True):
            logout()


def show_main_content():
    """Zobrazí hlavní obsah podle vybrané stránky"""
    selected_page = st.session_state.get('selected_page', 'Dashboard')

    # Import a zobrazení příslušné stránky
    if selected_page == 'Dashboard':
        from page_modules import dashboard
        dashboard.show(get_data_manager(), st.session_state.user)
    elif selected_page == 'Podniky přehled':
        from page_modules import podniky_prehled
        podniky_prehled.show(get_data_manager(), st.session_state.user, get_auth_manager())
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


def main():
    """Hlavní funkce aplikace"""
    if not st.session_state.authenticated:
        show_login_page()
    else:
        show_sidebar()
        show_main_content()


if __name__ == "__main__":
    main()
