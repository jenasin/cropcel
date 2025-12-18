"""
Modul pro zobrazení celkového přehledu Tekro - podniky a plodiny
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager=None):
    """Vstupní bod pro zobrazení stránky"""
    render(data_manager)


def render(data_manager):
    """Vykreslí stránku s přehledem Tekro"""

    # Načtení dat
    businesses = data_manager.get_businesses()
    fields = data_manager.get_fields()
    crops = data_manager.get_crops()

    if fields.empty:
        st.warning("Nejsou k dispozici žádná data.")
        return

    # Výběr roku
    if 'rok_sklizne' in fields.columns:
        available_years = sorted(fields['rok_sklizne'].dropna().unique(), reverse=True)
        available_years = [int(y) for y in available_years]
    else:
        st.warning("Data neobsahují informace o rocích.")
        return

    if not available_years:
        st.warning("Nejsou k dispozici žádné roky.")
        return

    selected_year = st.selectbox("Rok:", available_years, index=0)

    st.header(f"Přehled Tekro {selected_year}")

    # Filtrovat data pro vybraný rok
    year_fields = fields[fields['rok_sklizne'] == selected_year].copy()

    if year_fields.empty:
        st.info(f"Pro rok {selected_year} nejsou k dispozici žádná data.")
        return

    # Sloučit s názvy plodin
    if not crops.empty:
        year_fields = year_fields.merge(
            crops[['id', 'nazev']],
            left_on='plodina_id',
            right_on='id',
            how='left',
            suffixes=('', '_plodina')
        )
        year_fields['plodina_nazev'] = year_fields['nazev'].fillna('Neznámá')
    else:
        year_fields['plodina_nazev'] = 'Neznámá'

    # Sloučit s názvy podniků
    if not businesses.empty:
        year_fields = year_fields.merge(
            businesses[['id', 'nazev', 'poradi']],
            left_on='podnik_id',
            right_on='id',
            how='left',
            suffixes=('', '_podnik')
        )
        year_fields['podnik_nazev'] = year_fields['nazev_podnik'].fillna('Neznámý')
    else:
        year_fields['podnik_nazev'] = 'Neznámý'
        year_fields['poradi'] = 0

    # Definice speciálních plodin (cukrová řepa, brambory, apod.)
    specialni_plodiny = ['Cukrová řepa', 'brambory', 'Brambory', 'cukrová řepa']

    # ==================== TABULKA 1: PODNIKY ====================
    st.subheader("Podniky")

    # Filtrovat bez speciálních plodin
    normal_fields = year_fields[~year_fields['plodina_nazev'].isin(specialni_plodiny)]

    podniky_stats = create_podnik_stats(normal_fields, businesses)
    display_table(podniky_stats, 'Podnik')

    # ==================== TABULKA 2: PODNIKY (Cukrová řepa, apod.) ====================
    st.subheader("Podniky (Cukrová řepa, apod.)")

    # Filtrovat pouze speciální plodiny
    special_fields = year_fields[year_fields['plodina_nazev'].isin(specialni_plodiny)]

    if not special_fields.empty:
        special_stats = create_podnik_plodina_stats(special_fields, businesses)
        display_table(special_stats, 'Podnik', include_plodina=True)
    else:
        st.info("Žádné speciální plodiny (cukrová řepa, brambory) pro tento rok.")

    # ==================== TABULKA 3: PLODINY ====================
    st.subheader("Plodiny")

    plodiny_stats = create_plodina_stats(year_fields)
    display_table(plodiny_stats, 'Plodina')


def create_podnik_stats(fields_df, businesses):
    """Vytvoří statistiky podle podniků"""
    if fields_df.empty:
        return pd.DataFrame()

    # Seřadit podniky podle pořadí
    if not businesses.empty and 'poradi' in businesses.columns:
        podnik_order = businesses.sort_values('poradi')['nazev'].tolist()
    else:
        podnik_order = sorted(fields_df['podnik_nazev'].unique())

    # Agregace podle podniků
    stats = fields_df.groupby('podnik_nazev').agg({
        'vymera': 'sum',
        'sklizeno': 'sum',
        'hruba_vaha': 'sum',
        'cista_vaha': 'sum'
    }).reset_index()

    # Vypočítat metriky
    stats['sklizeno_pct'] = (stats['sklizeno'] / stats['vymera'] * 100).fillna(0)
    stats['hruby_vynos'] = (stats['hruba_vaha'] / stats['sklizeno']).fillna(0)
    stats['cisty_vynos'] = (stats['cista_vaha'] / stats['sklizeno']).fillna(0)
    stats['rozdil_pct'] = ((stats['hruba_vaha'] - stats['cista_vaha']) / stats['hruba_vaha'] * 100).fillna(100)

    # Přejmenovat sloupce
    stats.columns = [
        'Podnik', 'Výměra [ha]', 'Sklizeno [ha]', 'Hrubá produkce [t]', 'Čistá produkce [t]',
        'Sklizeno [%]', 'Hrubý výnos [t/ha]', 'Čistý výnos [t/ha]', 'Rozdíl čistá/hrubá [%]'
    ]

    # Seřadit sloupce
    stats = stats[[
        'Podnik', 'Výměra [ha]', 'Sklizeno [ha]', 'Sklizeno [%]',
        'Hrubý výnos [t/ha]', 'Čistý výnos [t/ha]',
        'Hrubá produkce [t]', 'Čistá produkce [t]', 'Rozdíl čistá/hrubá [%]'
    ]]

    # Seřadit podle pořadí podniků
    stats['sort_order'] = stats['Podnik'].apply(lambda x: podnik_order.index(x) if x in podnik_order else 999)
    stats = stats.sort_values('sort_order').drop('sort_order', axis=1)

    # Přidat řádek Celkem
    celkem = create_celkem_row(stats, 'Podnik')
    stats = pd.concat([stats, celkem], ignore_index=True)

    return stats


def create_podnik_plodina_stats(fields_df, businesses):
    """Vytvoří statistiky podle podniků a plodin"""
    if fields_df.empty:
        return pd.DataFrame()

    # Seřadit podniky podle pořadí
    if not businesses.empty and 'poradi' in businesses.columns:
        podnik_order = businesses.sort_values('poradi')['nazev'].tolist()
    else:
        podnik_order = sorted(fields_df['podnik_nazev'].unique())

    # Agregace podle podniků a plodin
    stats = fields_df.groupby(['podnik_nazev', 'plodina_nazev']).agg({
        'vymera': 'sum',
        'sklizeno': 'sum',
        'hruba_vaha': 'sum',
        'cista_vaha': 'sum'
    }).reset_index()

    # Vypočítat metriky
    stats['sklizeno_pct'] = (stats['sklizeno'] / stats['vymera'] * 100).fillna(0)
    stats['hruby_vynos'] = (stats['hruba_vaha'] / stats['sklizeno']).fillna(0)
    stats['cisty_vynos'] = (stats['cista_vaha'] / stats['sklizeno']).fillna(0)
    stats['rozdil_pct'] = ((stats['hruba_vaha'] - stats['cista_vaha']) / stats['hruba_vaha'] * 100).fillna(100)

    # Přejmenovat sloupce
    stats.columns = [
        'Podnik', 'Plodina', 'Výměra [ha]', 'Sklizeno [ha]', 'Hrubá produkce [t]', 'Čistá produkce [t]',
        'Sklizeno [%]', 'Hrubý výnos [t/ha]', 'Čistý výnos [t/ha]', 'Rozdíl čistá/hrubá [%]'
    ]

    # Seřadit sloupce
    stats = stats[[
        'Podnik', 'Plodina', 'Výměra [ha]', 'Sklizeno [ha]', 'Sklizeno [%]',
        'Hrubý výnos [t/ha]', 'Čistý výnos [t/ha]',
        'Hrubá produkce [t]', 'Čistá produkce [t]', 'Rozdíl čistá/hrubá [%]'
    ]]

    # Seřadit podle pořadí podniků
    stats['sort_order'] = stats['Podnik'].apply(lambda x: podnik_order.index(x) if x in podnik_order else 999)
    stats = stats.sort_values('sort_order').drop('sort_order', axis=1)

    # Přidat řádek Celkem
    celkem = create_celkem_row(stats, 'Podnik', include_plodina=True)
    stats = pd.concat([stats, celkem], ignore_index=True)

    return stats


def create_plodina_stats(fields_df):
    """Vytvoří statistiky podle plodin"""
    if fields_df.empty:
        return pd.DataFrame()

    # Agregace podle plodin
    stats = fields_df.groupby('plodina_nazev').agg({
        'vymera': 'sum',
        'sklizeno': 'sum',
        'hruba_vaha': 'sum',
        'cista_vaha': 'sum'
    }).reset_index()

    # Vypočítat metriky
    stats['sklizeno_pct'] = (stats['sklizeno'] / stats['vymera'] * 100).fillna(0)
    stats['hruby_vynos'] = (stats['hruba_vaha'] / stats['sklizeno']).fillna(0)
    stats['cisty_vynos'] = (stats['cista_vaha'] / stats['sklizeno']).fillna(0)
    stats['rozdil_pct'] = ((stats['hruba_vaha'] - stats['cista_vaha']) / stats['hruba_vaha'] * 100).fillna(100)

    # Přejmenovat sloupce
    stats.columns = [
        'Plodina', 'Výměra [ha]', 'Sklizeno [ha]', 'Hrubá produkce [t]', 'Čistá produkce [t]',
        'Sklizeno [%]', 'Hrubý výnos [t/ha]', 'Čistý výnos [t/ha]', 'Rozdíl čistá/hrubá [%]'
    ]

    # Seřadit sloupce
    stats = stats[[
        'Plodina', 'Výměra [ha]', 'Sklizeno [ha]', 'Sklizeno [%]',
        'Hrubý výnos [t/ha]', 'Čistý výnos [t/ha]',
        'Hrubá produkce [t]', 'Čistá produkce [t]', 'Rozdíl čistá/hrubá [%]'
    ]]

    # Seřadit podle výměry
    stats = stats.sort_values('Výměra [ha]', ascending=False)

    # Přidat řádek Celkem
    celkem = create_celkem_row(stats, 'Plodina')
    stats = pd.concat([stats, celkem], ignore_index=True)

    return stats


def create_celkem_row(stats, first_col, include_plodina=False):
    """Vytvoří řádek Celkem"""
    row = {first_col: 'Celkem'}

    if include_plodina:
        row['Plodina'] = ''

    row['Výměra [ha]'] = stats['Výměra [ha]'].sum()
    row['Sklizeno [ha]'] = stats['Sklizeno [ha]'].sum()
    row['Sklizeno [%]'] = (row['Sklizeno [ha]'] / row['Výměra [ha]'] * 100) if row['Výměra [ha]'] > 0 else 0
    row['Hrubá produkce [t]'] = stats['Hrubá produkce [t]'].sum()
    row['Čistá produkce [t]'] = stats['Čistá produkce [t]'].sum()
    row['Hrubý výnos [t/ha]'] = (row['Hrubá produkce [t]'] / row['Sklizeno [ha]']) if row['Sklizeno [ha]'] > 0 else 0
    row['Čistý výnos [t/ha]'] = (row['Čistá produkce [t]'] / row['Sklizeno [ha]']) if row['Sklizeno [ha]'] > 0 else 0
    row['Rozdíl čistá/hrubá [%]'] = ((row['Hrubá produkce [t]'] - row['Čistá produkce [t]']) / row['Hrubá produkce [t]'] * 100) if row['Hrubá produkce [t]'] > 0 else 0

    return pd.DataFrame([row])


def display_table(df, first_col, include_plodina=False):
    """Zobrazí formátovanou tabulku"""
    if df.empty:
        st.info("Žádná data pro zobrazení.")
        return

    display_df = df.copy()

    # Formátování
    display_df['Výměra [ha]'] = display_df['Výměra [ha]'].apply(lambda x: f"{x:,.2f}".replace(',', ' '))
    display_df['Sklizeno [ha]'] = display_df['Sklizeno [ha]'].apply(lambda x: f"{x:,.2f}".replace(',', ' '))
    display_df['Sklizeno [%]'] = display_df['Sklizeno [%]'].apply(lambda x: f"{x:.2f}%")
    display_df['Hrubý výnos [t/ha]'] = display_df['Hrubý výnos [t/ha]'].apply(lambda x: f"{x:.2f}")
    display_df['Čistý výnos [t/ha]'] = display_df['Čistý výnos [t/ha]'].apply(lambda x: f"{x:.2f}")
    display_df['Hrubá produkce [t]'] = display_df['Hrubá produkce [t]'].apply(lambda x: f"{x:,.2f}".replace(',', ' '))
    display_df['Čistá produkce [t]'] = display_df['Čistá produkce [t]'].apply(lambda x: f"{x:,.2f}".replace(',', ' '))
    display_df['Rozdíl čistá/hrubá [%]'] = display_df['Rozdíl čistá/hrubá [%]'].apply(lambda x: f"{x:.2f}%")

    # Styling
    def highlight_rows(row):
        styles = []
        is_celkem = row[first_col] == 'Celkem'

        for col in row.index:
            if is_celkem:
                styles.append('background-color: #2E86AB; color: white; font-weight: bold')
            elif col == first_col:
                styles.append('background-color: #28a745; color: white; font-weight: bold')
            else:
                styles.append('')
        return styles

    styled_df = display_df.style.apply(highlight_rows, axis=1)

    # Výška podle počtu řádků
    table_height = len(display_df) * 35 + 38

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        height=table_height
    )
