"""
Agregační funkce pro výpočty podle Nette aplikace
"""
import pandas as pd
import numpy as np


class Aggregations:
    """Třída pro agregace dat podle business logiky z Nette"""

    def __init__(self, data_manager):
        self.data_manager = data_manager

    def get_pole_summary_by_year(self, year: int, enable_main: str = 'Y') -> pd.DataFrame:
        """
        Agregace polí podle roku a plodiny (show_in_table)

        Args:
            year: Rok sklizně
            enable_main: Y/N - zobrazit v hlavní tabulce

        Returns:
            DataFrame s agregovanými daty
        """
        fields = self.data_manager.get_fields()
        crops = self.data_manager.get_crops()

        # Filtr podle roku
        fields_year = fields[fields['rok_sklizne'] == year].copy() if 'rok_sklizne' in fields.columns else fields.copy()

        # Join s plodinami
        if not crops.empty:
            fields_year = fields_year.merge(
                crops[['id', 'nazev', 'enable_main_table', 'show_in_table', 'poradi']],
                left_on='plodina_id',
                right_on='id',
                how='left',
                suffixes=('', '_crop')
            )

            # Filtr podle enable_main_table
            if 'enable_main_table' in fields_year.columns:
                fields_year = fields_year[fields_year['enable_main_table'] == enable_main]

        # Agregace podle plodiny
        if not fields_year.empty:
            agg_dict = {
                'vymera': 'sum',
                'sklizeno': 'sum',
                'cista_vaha': 'sum',
                'hruba_vaha': 'sum'
            }

            # Agreguj podle plodiny
            summary = fields_year.groupby(['plodina_id', 'nazev', 'poradi']).agg({
                col: agg for col, agg in agg_dict.items() if col in fields_year.columns
            }).reset_index()

            # Výpočet výnosu
            if 'cista_vaha' in summary.columns and 'vymera' in summary.columns:
                summary['cisty_vynos'] = summary.apply(
                    lambda row: round(row['cista_vaha'] / row['vymera'], 2) if row['vymera'] > 0 else 0,
                    axis=1
                )

            # Seřadit podle pořadí
            if 'poradi' in summary.columns:
                summary = summary.sort_values('poradi')

            return summary

        return pd.DataFrame()

    def get_pole_podniky_summary_by_year(self, year: int, enable_main: str = 'Y') -> pd.DataFrame:
        """
        Agregace polí podle roku, podniku a plodiny

        Args:
            year: Rok sklizně
            enable_main: Y/N - zobrazit v hlavní tabulce

        Returns:
            DataFrame s agregovanými daty podle podniku
        """
        fields = self.data_manager.get_fields()
        crops = self.data_manager.get_crops()
        businesses = self.data_manager.get_businesses()

        # Filtr podle roku
        fields_year = fields[fields['rok_sklizne'] == year].copy() if 'rok_sklizne' in fields.columns else fields.copy()

        # Join s plodinami
        if not crops.empty:
            fields_year = fields_year.merge(
                crops[['id', 'nazev', 'enable_main_table', 'poradi']].rename(columns={'nazev': 'plodina', 'poradi': 'plodina_poradi'}),
                left_on='plodina_id',
                right_on='id',
                how='left',
                suffixes=('', '_crop')
            )

            # Filtr podle enable_main_table
            if 'enable_main_table' in fields_year.columns:
                fields_year = fields_year[fields_year['enable_main_table'] == enable_main]

        # Join s podniky
        if not businesses.empty:
            fields_year = fields_year.merge(
                businesses[['id', 'nazev', 'poradi']].rename(columns={'nazev': 'podnik', 'poradi': 'podnik_poradi'}),
                left_on='podnik_id',
                right_on='id',
                how='left',
                suffixes=('', '_business')
            )

        # Agregace podle podniku a plodiny
        if not fields_year.empty:
            agg_dict = {
                'vymera': 'sum',
                'sklizeno': 'sum',
                'cista_vaha': 'sum',
                'hruba_vaha': 'sum'
            }

            summary = fields_year.groupby(['podnik_id', 'podnik', 'podnik_poradi', 'plodina_id', 'plodina', 'plodina_poradi']).agg({
                col: agg for col, agg in agg_dict.items() if col in fields_year.columns
            }).reset_index()

            # Výpočet výnosu
            if 'cista_vaha' in summary.columns and 'vymera' in summary.columns:
                summary['cisty_vynos'] = summary.apply(
                    lambda row: round(row['cista_vaha'] / row['vymera'], 2) if row['vymera'] > 0 else 0,
                    axis=1
                )

            # Seřadit podle pořadí podniku a plodiny
            summary = summary.sort_values(['podnik_poradi', 'plodina_poradi'])

            return summary

        return pd.DataFrame()

    def get_sum_plodiny_for_missing(self, podnik_id: int, plodina_id: int, year: int) -> dict:
        """
        Získá čistou váhu z sumplodiny, pokud chybí v poli
        Podle logiky z PoleRepository::getSumPodnikByPlodina
        """
        sumplodiny = self.data_manager.get_sumplodiny()

        # Hledej v sumplodiny
        result = sumplodiny[
            (sumplodiny['podnik_id'] == podnik_id) &
            (sumplodiny['plodina_id'] == plodina_id) &
            (sumplodiny['year'] == year)
        ]

        if not result.empty:
            return {
                'cista_vaha': result.iloc[0]['cista_vaha'],
                'from_sumplodiny': True
            }

        return {'cista_vaha': 0, 'from_sumplodiny': False}

    def calculate_vynos(self, cista_vaha: float, vymera: float) -> float:
        """Výpočet výnosu (t/ha)"""
        if vymera > 0:
            return round(cista_vaha / vymera, 2)
        return 0.0

    def get_pozemky_summary_by_year(self, year: int) -> pd.DataFrame:
        """
        Souhrn pozemků podle typu a roku
        """
        pozemky = self.data_manager.get_pozemky()
        typpozemek = self.data_manager.get_typpozemek()

        # Normalize column names to lowercase
        if not pozemky.empty:
            pozemky.columns = pozemky.columns.str.lower()

        # Filtr podle roku
        pozemky_year = pozemky[pozemky['year'] == year].copy() if 'year' in pozemky.columns else pozemky.copy()

        # Join s typy pozemků
        if not typpozemek.empty and not pozemky_year.empty:
            # Normalize column names to lowercase
            typpozemek.columns = typpozemek.columns.str.lower()

            pozemky_year = pozemky_year.merge(
                typpozemek[['id', 'nazev', 'poradi']],
                left_on='nazevid',  # Was: typ_pozemek_id, but CSV has NazevId
                right_on='id',
                how='left',
                suffixes=('', '_typ')
            )

            # Agregace podle typu
            summary = pozemky_year.groupby(['nazev', 'poradi']).agg({
                'velikost': 'sum'  # Was: vymera, but CSV has Velikost
            }).reset_index()

            # Rename for display
            summary = summary.rename(columns={'velikost': 'vymera'})

            # Výpočet procent
            total = summary['vymera'].sum()
            if total > 0:
                summary['procento'] = summary['vymera'].apply(lambda x: round(x / total * 100, 2))
            else:
                summary['procento'] = 0

            summary = summary.sort_values('poradi')
            return summary

        return pd.DataFrame()
