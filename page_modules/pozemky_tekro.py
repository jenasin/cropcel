"""
Modul pro zobrazení přehledu pozemků všech podniků po letech
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager=None):
    """Vstupní bod pro zobrazení stránky"""
    render(data_manager)


def render(data_manager):
    """Vykreslí stránku s přehledem pozemků"""
    st.header("Pozemky Tekro")

    # Načtení dat
    businesses = data_manager.get_businesses()
    pozemky = data_manager.get_pozemky()
    typpozemek = data_manager.get_typpozemek()

    if pozemky.empty:
        st.warning("Nejsou k dispozici žádná data o pozemcích.")
        return

    if typpozemek.empty:
        st.warning("Nejsou k dispozici žádné typy pozemků.")
        return

    # Získat všechny roky
    all_years = sorted(pozemky['Year'].dropna().unique())
    all_years = [int(y) for y in all_years]

    if not all_years:
        st.warning("Nejsou k dispozici žádné roky.")
        return

    # Seřadit typy pozemků podle pořadí
    if 'Poradi' in typpozemek.columns:
        typpozemek_sorted = typpozemek.sort_values('Poradi')
    else:
        typpozemek_sorted = typpozemek.sort_values('Nazev')

    typ_names = typpozemek_sorted['Nazev'].tolist()
    typ_ids = typpozemek_sorted['id'].tolist()

    # Seřadit podniky podle pořadí
    if not businesses.empty and 'poradi' in businesses.columns:
        businesses_sorted = businesses.sort_values('poradi')
    else:
        businesses_sorted = businesses.sort_values('nazev')

    st.markdown("---")

    # Pro každý podnik vytvořit tabulku
    for _, podnik in businesses_sorted.iterrows():
        podnik_id = podnik['id']
        podnik_nazev = podnik['nazev']

        st.subheader(podnik_nazev)

        # Filtrovat pozemky pro tento podnik
        podnik_pozemky = pozemky[pozemky['PodnikID'] == podnik_id]

        if podnik_pozemky.empty:
            st.info(f"Žádné pozemky pro podnik {podnik_nazev}")
            st.markdown("---")
            continue

        # Vytvořit pivot tabulku
        data_rows = []

        for typ_id, typ_nazev in zip(typ_ids, typ_names):
            row = {'Typ pozemku': typ_nazev}

            for year in all_years:
                # Najít velikost pro daný typ a rok
                filtered = podnik_pozemky[(podnik_pozemky['NazevId'] == typ_id) & (podnik_pozemky['Year'] == year)]
                velikost = filtered['Velikost'].sum() if not filtered.empty else 0
                row[f'{year}[ha]'] = velikost

            data_rows.append(row)

        # Přidat řádek Celkem
        celkem_row = {'Typ pozemku': 'Celkem'}
        for year in all_years:
            filtered = podnik_pozemky[podnik_pozemky['Year'] == year]
            celkem = filtered['Velikost'].sum() if not filtered.empty else 0
            celkem_row[f'{year}[ha]'] = celkem
        data_rows.append(celkem_row)

        # Vytvořit DataFrame
        df = pd.DataFrame(data_rows)

        # Formátování - zaokrouhlit na 2 desetinná místa
        year_cols = [col for col in df.columns if col != 'Typ pozemku']
        for col in year_cols:
            df[col] = df[col].apply(lambda x: f"{x:,.2f}".replace(',', ' ') if x > 0 else "0")

        # Styling - modrý řádek Celkem, zelený první sloupec
        def highlight_rows(row):
            styles = []
            is_celkem = row['Typ pozemku'] == 'Celkem'

            for i, col in enumerate(row.index):
                if is_celkem:
                    styles.append('background-color: #2E86AB; color: white; font-weight: bold')
                elif col == 'Typ pozemku':
                    styles.append('background-color: #28a745; color: white; font-weight: bold')
                else:
                    styles.append('')
            return styles

        styled_df = df.style.apply(highlight_rows, axis=1).set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#FFC107'), ('color', 'black'), ('font-weight', 'bold')]}
        ])

        # Zobrazit tabulku
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Typ pozemku": st.column_config.TextColumn("Typ pozemku", width="medium"),
            }
        )

        st.markdown("---")
