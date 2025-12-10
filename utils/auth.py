"""
Autentizační modul pro správu uživatelů a rolí
"""
import streamlit as st
import pandas as pd
import hashlib
import hmac
from typing import Optional, Dict


class AuthManager:
    """Správce autentizace a autorizace"""

    ROLES = {
        'admin': ['read', 'write', 'delete', 'manage_users'],
        'editor': ['read', 'write'],
        'watcher': ['read']
    }

    def __init__(self, users_csv_path: str):
        self.users_csv_path = users_csv_path
        self._load_users()

    def _load_users(self):
        """Načte uživatele z CSV"""
        try:
            self.users_df = pd.read_csv(self.users_csv_path)
        except Exception as e:
            st.error(f"Chyba při načítání uživatelů: {e}")
            self.users_df = pd.DataFrame()

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        Autentizuje uživatele

        Args:
            username: Uživatelské jméno
            password: Heslo

        Returns:
            Dict s informacemi o uživateli nebo None
        """
        user = self.users_df[self.users_df['username'] == username]

        if user.empty:
            return None

        user = user.iloc[0]

        # Kontrola aktivity
        if not user.get('is_active', True):
            return None

        # Ověření hesla (zjednodušená verze - v produkci použít bcrypt)
        if self._verify_password(password, user):
            # Získat přiřazené podniky podle userpodniky
            podniky = self.get_user_podniky(user['id'])

            return {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'full_name': user['full_name'],
                'business_ids': user.get('business_ids', ''),
                'podniky': podniky  # Seznam ID podniků uživatele
            }

        return None

    def _verify_password(self, password: str, user: pd.Series) -> bool:
        """Ověří heslo (zjednodušená verze)"""
        # DEMO REŽIM - akceptuje jakékoliv heslo
        # V produkci implementovat správné ověření s bcrypt/pbkdf2
        return True

    def has_permission(self, role: str, permission: str) -> bool:
        """
        Kontroluje, zda role má dané oprávnění

        Args:
            role: Role uživatele
            permission: Požadované oprávnění

        Returns:
            True pokud má oprávnění
        """
        return permission in self.ROLES.get(role, [])

    def get_user_businesses(self, business_ids: str) -> list:
        """Vrátí seznam ID podniků pro uživatele"""
        if pd.isna(business_ids) or business_ids == '':
            return []

        # Business IDs mohou být oddělené čárkou
        return [int(x.strip()) for x in str(business_ids).split(',') if x.strip()]

    def get_user_podniky(self, user_id: int) -> list:
        """
        Vrátí seznam ID podniků přiřazených uživateli
        Admin vidí všechny podniky
        """
        import os
        import config

        # Načti userpodniky
        userpodniky_path = os.path.join(config.DATA_DIR, 'userpodniky.csv')
        try:
            userpodniky_df = pd.read_csv(userpodniky_path)
        except:
            return []

        # Načti podniky
        businesses_path = os.path.join(config.DATA_DIR, 'businesses.csv')
        try:
            businesses_df = pd.read_csv(businesses_path)
        except:
            return []

        # Zkontroluj, zda je admin
        user = self.users_df[self.users_df['id'] == user_id]
        if not user.empty and user.iloc[0]['role'] == 'admin':
            # Admin vidí všechny podniky
            return businesses_df['id'].tolist()

        # Ostatní vidí jen své přiřazené podniky
        user_businesses = userpodniky_df[userpodniky_df['userId'] == user_id]
        return user_businesses['podnikId'].tolist()

    def authorize_podnik(self, user: Dict, podnik_id: int) -> bool:
        """
        Kontroluje, zda má uživatel přístup k danému podniku

        Args:
            user: Dict s informacemi o uživateli
            podnik_id: ID podniku

        Returns:
            True pokud má přístup
        """
        # Admin má přístup ke všemu
        if user.get('role') == 'admin':
            return True

        # Kontrola, zda podnik je v seznamu povolených podniků
        podniky = user.get('podniky', [])
        return podnik_id in podniky

    def can_edit_podnik(self, user: Dict, podnik_id: int) -> bool:
        """
        Kontroluje, zda může uživatel editovat daný podnik

        Args:
            user: Dict s informacemi o uživateli
            podnik_id: ID podniku

        Returns:
            True pokud má právo editovat
        """
        role = user.get('role', 'watcher')

        # Watcher nemůže editovat nic
        if role == 'watcher':
            return False

        # Admin může editovat vše
        if role == 'admin':
            return True

        # Editor může editovat jen přiřazené podniky
        if role == 'editor':
            podniky = user.get('podniky', [])
            return podnik_id in podniky

        return False

    def get_allowed_podniky(self, user: Dict, businesses_df: pd.DataFrame) -> pd.DataFrame:
        """
        Vrátí DataFrame podniků, ke kterým má uživatel přístup

        Args:
            user: Dict s informacemi o uživateli
            businesses_df: DataFrame všech podniků

        Returns:
            Filtrovaný DataFrame podniků
        """
        if user.get('role') == 'admin':
            return businesses_df

        podniky = user.get('podniky', [])
        if podniky:
            return businesses_df[businesses_df['id'].isin(podniky)]

        return pd.DataFrame()


def init_session_state():
    """Inicializuje session state pro autentizaci"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None


def require_auth(auth_manager: AuthManager):
    """Dekorátor pro stránky vyžadující autentizaci"""
    if not st.session_state.get('authenticated', False):
        st.warning("Prosím přihlaste se pro pokračování")
        st.stop()


def logout():
    """Odhlásí uživatele"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()
