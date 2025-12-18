"""
Modul pro zobrazení přehledu plodin po letech - Plodiny Tekro
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager=None):
    """Vstupní bod pro zobrazení stránky"""
    render(data_manager)


def render(data_manager):
    """Vykreslí stránku s přehledem plodin po letech"""
    st.header("Plodiny Tekro")

    # Načtení dat
    businesses = data_manager.get_businesses()
    fields = data_manager.get_fields()
    crops = data_manager.get_crops()

    if fields.empty:
        st.warning("Nejsou k dispozici žádná data.")
        return

    # Získat všechny roky
    all_years = sorted(fields['rok_sklizne'].dropna().unique())
    all_years = [int(y) for y in all_years]

    if not all_years:
        st.warning("Nejsou k dispozici žádné roky.")
        return

    # Sloučit s názvy plodin
    if not crops.empty:
        fields = fields.merge(
            crops[['id', 'nazev', 'poradi']].rename(columns={'nazev': 'plodina', 'poradi': 'plodina_poradi'}),
            left_on='plodina_id',
            right_on='id',
            how='left'
        )
    else:
        fields['plodina'] = 'Neznámá'
        fields['plodina_poradi'] = 999

    # Sloučit s názvy podniků
    if not businesses.empty:
        fields = fields.merge(
            businesses[['id', 'nazev']].rename(columns={'nazev': 'podnik'}),
            left_on='podnik_id',
            right_on='id',
            how='left',
            suffixes=('', '_podnik')
        )
    else:
        fields['podnik'] = 'Neznámý'

    # Získat všechny plodiny seřazené podle pořadí z tabulky Plodiny
    plodiny_order = fields[['plodina', 'plodina_poradi']].drop_duplicates()
    plodiny_order['plodina_poradi'] = plodiny_order['plodina_poradi'].fillna(999)
    plodiny_order = plodiny_order.sort_values('plodina_poradi')
    all_crops = plodiny_order['plodina'].dropna().tolist()

    # Pro každou plodinu vytvořit tabulku
    for plodina_name in all_crops:
        st.markdown("---")
        st.subheader(f"📋 {plodina_name}")

        # Filtrovat data pro tuto plodinu
        plodina_fields = fields[fields['plodina'] == plodina_name].copy()

        if plodina_fields.empty:
            st.info(f"Žádná data pro {plodina_name}")
            continue

        # Agregace dat pro všechny roky a podniky
        podniky_roky_data = []
        for year in all_years:
            year_fields = plodina_fields[plodina_fields['rok_sklizne'] == year].copy()
            if not year_fields.empty:
                # Agregace podle podniků
                podnik_agg = year_fields.groupby('podnik').agg({
                    'vymera': 'sum',
                    'cista_vaha': 'sum'
                }).reset_index()
                podnik_agg['cisty_vynos'] = podnik_agg.apply(
                    lambda row: round(row['cista_vaha'] / row['vymera'], 2) if row['vymera'] > 0 else 0,
                    axis=1
                )
                podnik_agg['rok'] = int(year)
                podniky_roky_data.append(podnik_agg)

        if not podniky_roky_data:
            st.info(f"Žádná data pro {plodina_name}")
            continue

        all_podniky_roky = pd.concat(podniky_roky_data, ignore_index=True)

        # Pivot tabulky pro každou metriku
        pivot_vymera = all_podniky_roky.pivot_table(
            index='podnik',
            columns='rok',
            values='vymera',
            fill_value=0
        )
        pivot_produkce = all_podniky_roky.pivot_table(
            index='podnik',
            columns='rok',
            values='cista_vaha',
            fill_value=0
        )
        pivot_vynos = all_podniky_roky.pivot_table(
            index='podnik',
            columns='rok',
            values='cisty_vynos',
            fill_value=0
        )

        # Seřadit roky
        sorted_years = sorted(pivot_vymera.columns)

        # Vytvořit jednu velkou tabulku s multi-level headers
        # Přejmenovat sloupce s prefixem pro každou metriku
        vynos_cols = {y: f"Čistý výnos (t/ha)|{int(y)}" for y in sorted_years}
        vymera_cols = {y: f"Výměra (ha)|{int(y)}" for y in sorted_years}
        produkce_cols = {y: f"Čistá produkce (t)|{int(y)}" for y in sorted_years}

        df_vynos = pivot_vynos[sorted_years].round(2).rename(columns=vynos_cols)
        df_vymera = pivot_vymera[sorted_years].round(2).rename(columns=vymera_cols)
        df_produkce = pivot_produkce[sorted_years].round(2).rename(columns=produkce_cols)

        # Spojit všechny tabulky - pořadí: Čistý výnos, Výměra, Čistá produkce
        combined_df = pd.concat([df_vynos, df_vymera, df_produkce], axis=1)

        # Vytvořit MultiIndex sloupce
        new_columns = []
        for col in combined_df.columns:
            parts = col.split('|')
            new_columns.append((parts[0], parts[1]))
        combined_df.columns = pd.MultiIndex.from_tuples(new_columns)

        st.dataframe(combined_df, use_container_width=True)
