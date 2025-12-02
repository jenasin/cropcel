"""
Správce dat pro práci s CSV soubory
"""
import pandas as pd
import streamlit as st
from typing import Optional, List
from datetime import datetime
import os


class DataManager:
    """Správce dat z CSV souborů"""

    def __init__(self, base_path: str):
        """
        Args:
            base_path: Základní cesta k CSV souborům (lokální složka)
        """
        self.base_path = base_path
        self.cache = {}

    def load_csv(self, filename: str, force_reload: bool = False) -> pd.DataFrame:
        """
        Načte CSV soubor

        Args:
            filename: Název CSV souboru
            force_reload: Vynutit opětovné načtení

        Returns:
            DataFrame s daty
        """
        if filename in self.cache and not force_reload:
            return self.cache[filename].copy()

        try:
            filepath = os.path.join(self.base_path, filename)
            df = pd.read_csv(filepath)

            # Přidej nové záznamy ze session state
            if 'new_records' in st.session_state and filename in st.session_state.new_records:
                new_records = st.session_state.new_records[filename]
                if new_records:
                    new_df = pd.DataFrame(new_records)
                    df = pd.concat([df, new_df], ignore_index=True)

            self.cache[filename] = df
            return df.copy()
        except Exception as e:
            st.error(f"Chyba při načítání {filename}: {e}")
            return pd.DataFrame()

    def get_businesses(self) -> pd.DataFrame:
        """Načte seznam podniků"""
        return self.load_csv('businesses.csv')

    def get_crops(self) -> pd.DataFrame:
        """Načte seznam plodin"""
        return self.load_csv('crops.csv')

    def get_fields(self) -> pd.DataFrame:
        """Načte data o polích"""
        return self.load_csv('fields.csv')

    def get_users(self) -> pd.DataFrame:
        """Načte uživatele"""
        return self.load_csv('users.csv')

    def get_pozemky(self) -> pd.DataFrame:
        """Načte pozemky"""
        return self.load_csv('pozemky.csv')

    def get_sbernamista(self) -> pd.DataFrame:
        """Načte sběrná místa"""
        return self.load_csv('sbernamista.csv')

    def get_varieties_seed(self) -> pd.DataFrame:
        """Načte odrůdy osiva"""
        return self.load_csv('varieties_seed.csv')

    def get_roky(self) -> pd.DataFrame:
        """Načte roky"""
        return self.load_csv('roky.csv')

    def get_sbernasrazky(self) -> pd.DataFrame:
        """Načte sběrné srážky"""
        return self.load_csv('sbernasrazky.csv')

    def get_sumplodiny(self) -> pd.DataFrame:
        """Načte souhrn plodin"""
        return self.load_csv('sumplodiny.csv')

    def get_typpozemek(self) -> pd.DataFrame:
        """Načte typy pozemků"""
        return self.load_csv('typpozemek.csv')

    def get_userpodniky(self) -> pd.DataFrame:
        """Načte vztahy uživatel-podnik"""
        return self.load_csv('userpodniky.csv')

    def filter_by_business(self, df: pd.DataFrame, business_ids: List[int]) -> pd.DataFrame:
        """
        Filtruje data podle ID podniků

        Args:
            df: DataFrame k filtrování
            business_ids: Seznam ID podniků

        Returns:
            Filtrovaný DataFrame
        """
        if not business_ids or 'podnik_id' not in df.columns:
            return df

        return df[df['podnik_id'].isin(business_ids)]

    def add_record(self, filename: str, data: dict) -> bool:
        """
        Přidá nový záznam (simulace - pro produkci potřeba backend)

        Args:
            filename: Název CSV souboru
            data: Data k přidání

        Returns:
            True pokud úspěšné
        """
        try:
            df = self.load_csv(filename)

            # Generuj nové ID
            if 'id' in df.columns and len(df) > 0:
                new_id = df['id'].max() + 1
                data['id'] = new_id

            # Přidej časové razítko
            if 'datum_upravy' in df.columns:
                data['datum_upravy'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Pro demo - uložíme do session state
            if 'new_records' not in st.session_state:
                st.session_state.new_records = {}

            if filename not in st.session_state.new_records:
                st.session_state.new_records[filename] = []

            st.session_state.new_records[filename].append(data)

            # Invaliduj cache
            if filename in self.cache:
                del self.cache[filename]

            return True
        except Exception as e:
            st.error(f"Chyba při přidávání záznamu: {e}")
            return False

    def update_record(self, filename: str, record_id: int, data: dict) -> bool:
        """
        Aktualizuje záznam (simulace)

        Args:
            filename: Název CSV souboru
            record_id: ID záznamu
            data: Nová data

        Returns:
            True pokud úspěšné
        """
        try:
            # Pro demo - uložíme do session state
            if 'updated_records' not in st.session_state:
                st.session_state.updated_records = {}

            if filename not in st.session_state.updated_records:
                st.session_state.updated_records[filename] = {}

            data['datum_upravy'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            st.session_state.updated_records[filename][record_id] = data

            # Invaliduj cache
            if filename in self.cache:
                del self.cache[filename]

            return True
        except Exception as e:
            st.error(f"Chyba při aktualizaci záznamu: {e}")
            return False

    def delete_record(self, filename: str, record_id: int) -> bool:
        """
        Smaže záznam (simulace)

        Args:
            filename: Název CSV souboru
            record_id: ID záznamu

        Returns:
            True pokud úspěšné
        """
        try:
            # Pro demo - uložíme do session state
            if 'deleted_records' not in st.session_state:
                st.session_state.deleted_records = {}

            if filename not in st.session_state.deleted_records:
                st.session_state.deleted_records[filename] = []

            st.session_state.deleted_records[filename].append(record_id)

            # Invaliduj cache
            if filename in self.cache:
                del self.cache[filename]

            return True
        except Exception as e:
            st.error(f"Chyba při mazání záznamu: {e}")
            return False
