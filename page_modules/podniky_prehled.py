"""
Modul pro zobrazení přehledu všech podniků - souhrnné tabulky plodin
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager=None):
    """Vstupní bod pro zobrazení stránky"""
    render(data_manager)


def render(data_manager):
    """Vykreslí stránku s přehledem podniků"""
    st.header("Podniky přehled")

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

    st.markdown("---")

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
            businesses[['id', 'nazev']],
            left_on='podnik_id',
            right_on='id',
            how='left',
            suffixes=('', '_podnik')
        )
        year_fields['podnik_nazev'] = year_fields['nazev_podnik'].fillna('Neznámý')
    else:
        year_fields['podnik_nazev'] = 'Neznámý'

    # Seřadit podniky podle pořadí
    if not businesses.empty and 'poradi' in businesses.columns:
        podnik_order = businesses.sort_values('poradi')['nazev'].tolist()
    else:
        podnik_order = sorted(year_fields['podnik_nazev'].unique())

    # Pro každý podnik vytvořit tabulku
    for podnik_nazev in podnik_order:
        podnik_data = year_fields[year_fields['podnik_nazev'] == podnik_nazev]

        if podnik_data.empty:
            continue

        st.subheader(podnik_nazev)

        # Agregace podle plodin
        plodiny_stats = podnik_data.groupby('plodina_nazev').agg({
            'vymera': 'sum',
            'sklizeno': 'sum',
            'hruba_vaha': 'sum',
            'cista_vaha': 'sum'
        }).reset_index()

        # Vypočítat metriky
        plodiny_stats['sklizeno_pct'] = (plodiny_stats['sklizeno'] / plodiny_stats['vymera'] * 100).fillna(0)
        plodiny_stats['hruby_vynos'] = (plodiny_stats['hruba_vaha'] / plodiny_stats['sklizeno']).fillna(0)
        plodiny_stats['cisty_vynos'] = (plodiny_stats['cista_vaha'] / plodiny_stats['sklizeno']).fillna(0)
        plodiny_stats['rozdil_pct'] = ((plodiny_stats['hruba_vaha'] - plodiny_stats['cista_vaha']) / plodiny_stats['hruba_vaha'] * 100).fillna(100)

        # Přejmenovat sloupce
        plodiny_stats.columns = [
            'Plodina',
            'Výměra [ha]',
            'Sklizeno [ha]',
            'Hrubá produkce [t]',
            'Čistá produkce [t]',
            'Sklizeno [%]',
            'Hrubý výnos [t/ha]',
            'Čistý výnos [t/ha]',
            'Rozdíl čistá/hrubá [%]'
        ]

        # Seřadit sloupce
        plodiny_stats = plodiny_stats[[
            'Plodina',
            'Výměra [ha]',
            'Sklizeno [ha]',
            'Sklizeno [%]',
            'Hrubý výnos [t/ha]',
            'Čistý výnos [t/ha]',
            'Hrubá produkce [t]',
            'Čistá produkce [t]',
            'Rozdíl čistá/hrubá [%]'
        ]]

        # Seřadit podle výměry
        plodiny_stats = plodiny_stats.sort_values('Výměra [ha]', ascending=False)

        # Přidat řádek Celkem
        celkem = pd.DataFrame([{
            'Plodina': 'Celkem',
            'Výměra [ha]': plodiny_stats['Výměra [ha]'].sum(),
            'Sklizeno [ha]': plodiny_stats['Sklizeno [ha]'].sum(),
            'Sklizeno [%]': (plodiny_stats['Sklizeno [ha]'].sum() / plodiny_stats['Výměra [ha]'].sum() * 100) if plodiny_stats['Výměra [ha]'].sum() > 0 else 0,
            'Hrubý výnos [t/ha]': (plodiny_stats['Hrubá produkce [t]'].sum() / plodiny_stats['Sklizeno [ha]'].sum()) if plodiny_stats['Sklizeno [ha]'].sum() > 0 else 0,
            'Čistý výnos [t/ha]': (plodiny_stats['Čistá produkce [t]'].sum() / plodiny_stats['Sklizeno [ha]'].sum()) if plodiny_stats['Sklizeno [ha]'].sum() > 0 else 0,
            'Hrubá produkce [t]': plodiny_stats['Hrubá produkce [t]'].sum(),
            'Čistá produkce [t]': plodiny_stats['Čistá produkce [t]'].sum(),
            'Rozdíl čistá/hrubá [%]': ((plodiny_stats['Hrubá produkce [t]'].sum() - plodiny_stats['Čistá produkce [t]'].sum()) / plodiny_stats['Hrubá produkce [t]'].sum() * 100) if plodiny_stats['Hrubá produkce [t]'].sum() > 0 else 0
        }])

        plodiny_stats = pd.concat([plodiny_stats, celkem], ignore_index=True)

        # Formátování
        display_df = plodiny_stats.copy()
        display_df['Výměra [ha]'] = display_df['Výměra [ha]'].apply(lambda x: f"{x:,.2f}".replace(',', ' '))
        display_df['Sklizeno [ha]'] = display_df['Sklizeno [ha]'].apply(lambda x: f"{x:,.2f}".replace(',', ' '))
        display_df['Sklizeno [%]'] = display_df['Sklizeno [%]'].apply(lambda x: f"{x:.2f}%")
        display_df['Hrubý výnos [t/ha]'] = display_df['Hrubý výnos [t/ha]'].apply(lambda x: f"{x:.2f}")
        display_df['Čistý výnos [t/ha]'] = display_df['Čistý výnos [t/ha]'].apply(lambda x: f"{x:.2f}")
        display_df['Hrubá produkce [t]'] = display_df['Hrubá produkce [t]'].apply(lambda x: f"{x:,.2f}".replace(',', ' '))
        display_df['Čistá produkce [t]'] = display_df['Čistá produkce [t]'].apply(lambda x: f"{x:,.2f}".replace(',', ' '))
        display_df['Rozdíl čistá/hrubá [%]'] = display_df['Rozdíl čistá/hrubá [%]'].apply(lambda x: f"{x:.2f}%")

        # Styling - modrý řádek Celkem, zelený první sloupec
        def highlight_rows(row):
            styles = []
            is_celkem = row['Plodina'] == 'Celkem'

            for i, col in enumerate(row.index):
                if is_celkem:
                    styles.append('background-color: #2E86AB; color: white; font-weight: bold')
                elif col == 'Plodina':
                    styles.append('background-color: #28a745; color: white; font-weight: bold')
                else:
                    styles.append('')
            return styles

        styled_df = display_df.style.apply(highlight_rows, axis=1).set_table_styles([
            {'selector': 'th', 'props': [('background-color', '#FFC107'), ('color', 'black'), ('font-weight', 'bold')]}
        ])

        # Zobrazit tabulku
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Plodina": st.column_config.TextColumn("Plodina", width="medium"),
            }
        )

        st.markdown("---")
