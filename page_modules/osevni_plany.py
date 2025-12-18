"""
Modul pro zobrazení osevních plánů - Osevní plány Tekro
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager=None):
    """Vstupní bod pro zobrazení stránky"""
    render(data_manager)


def render(data_manager):
    """Vykreslí stránku s osevními plány"""

    # Načtení dat
    businesses = data_manager.get_businesses()
    fields = data_manager.get_fields()
    crops = data_manager.get_crops()
    varieties = data_manager.get_varieties_seed()

    if fields.empty:
        st.warning("Nejsou k dispozici žádná data.")
        return

    # Získat všechny roky
    if 'rok_sklizne' in fields.columns:
        available_years = sorted(fields['rok_sklizne'].dropna().unique(), reverse=True)
        available_years = [int(y) for y in available_years]
    else:
        st.warning("Data neobsahují informace o rocích.")
        return

    if not available_years:
        st.warning("Nejsou k dispozici žádné roky.")
        return

    # Seřadit podniky podle pořadí
    if not businesses.empty and 'poradi' in businesses.columns:
        businesses_sorted = businesses.sort_values('poradi')
    else:
        businesses_sorted = businesses.sort_values('nazev')

    # Výběr roku a podniku
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("Rok:", available_years, index=0)
    with col2:
        podnik_options = {row['id']: row['nazev'] for _, row in businesses_sorted.iterrows()}
        selected_podnik = st.selectbox(
            "Podnik:",
            options=list(podnik_options.keys()),
            format_func=lambda x: podnik_options[x]
        )

    podnik_name = podnik_options[selected_podnik]
    st.header(f"Osevní plány {selected_year} {podnik_name}")

    # Filtrovat data
    year_fields = fields[(fields['rok_sklizne'] == selected_year) & (fields['podnik_id'] == selected_podnik)].copy()

    if year_fields.empty:
        st.info(f"Pro rok {selected_year} a podnik {podnik_name} nejsou k dispozici žádná data.")
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

    # Sloučit s názvy odrůd
    if not varieties.empty:
        year_fields = year_fields.merge(
            varieties[['id', 'nazev']],
            left_on='odruda_id',
            right_on='id',
            how='left',
            suffixes=('', '_odruda')
        )
        year_fields['odruda_nazev'] = year_fields['nazev_odruda'].fillna('')
    else:
        year_fields['odruda_nazev'] = ''

    # Formátovat datum setí
    year_fields['datum_seti'] = pd.to_datetime(year_fields['datum_seti'], errors='coerce')
    year_fields['datum_seti_str'] = year_fields['datum_seti'].dt.strftime('%d.%m.%Y').fillna('')

    # Pro každou plodinu vytvořit tabulku
    plodiny = year_fields['plodina_nazev'].unique()

    for plodina in sorted(plodiny):
        st.subheader(plodina)

        plodina_data = year_fields[year_fields['plodina_nazev'] == plodina].copy()

        if plodina_data.empty:
            continue

        # Vytvořit tabulku
        display_data = []
        for _, row in plodina_data.iterrows():
            display_data.append({
                'Název honu': row.get('nazev_honu', '') if pd.notna(row.get('nazev_honu', '')) else '',
                'Číslo honu': row.get('cislo_honu', '') if pd.notna(row.get('cislo_honu', '')) else '',
                'Výměra [ha]': round(row['vymera'], 2) if pd.notna(row['vymera']) else 0,
                'Odrůda': row['odruda_nazev'],
                'St.mn.': row.get('stmn', '') if pd.notna(row.get('stmn', '')) else '',
                'Datum Setí': row['datum_seti_str']
            })

        # Přidat řádek Celkem
        celkem_vymera = plodina_data['vymera'].sum()
        display_data.append({
            'Název honu': 'Celkem',
            'Číslo honu': '',
            'Výměra [ha]': round(celkem_vymera, 2),
            'Odrůda': '',
            'St.mn.': '',
            'Datum Setí': ''
        })

        df = pd.DataFrame(display_data)

        # Styling - modrý řádek Celkem, zelený první sloupec
        def highlight_rows(row):
            styles = []
            is_celkem = row['Název honu'] == 'Celkem'

            for col in row.index:
                if is_celkem:
                    styles.append('background-color: #2E86AB; color: white; font-weight: bold')
                elif col == 'Název honu':
                    styles.append('background-color: #28a745; color: white; font-weight: bold')
                else:
                    styles.append('')
            return styles

        styled_df = df.style.apply(highlight_rows, axis=1)

        # Výška podle počtu řádků
        table_height = len(df) * 35 + 38

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=table_height
        )
