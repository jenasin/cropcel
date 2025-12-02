"""
Správa pozemků - podle logiky PozemkyPresenter z Nette
"""
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.aggregations import Aggregations


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy pozemků s souhrny podle typu"""
    st.title("🗺️ Správa pozemků")

    # Načtení dat
    pozemky = data_manager.get_pozemky()
    typy = data_manager.get_typpozemek()
    businesses = data_manager.get_businesses()

    # Inicializace agregací
    agg = Aggregations(data_manager)

    # Tlačítka akcí
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("➕ Přidat nový", use_container_width=True):
            st.session_state.show_add_pozemek_form = True

    with col2:
        if st.button("🔄 Obnovit", use_container_width=True):
            data_manager.load_csv('pozemky.csv', force_reload=True)
            st.rerun()

    # Formulář pro přidání
    if st.session_state.get('show_add_pozemek_form', False):
        st.subheader("Přidat nový pozemek")

        col1, col2 = st.columns(2)
        with col1:
            if not businesses.empty:
                business_names = sorted(businesses['nazev'].tolist())
                business_map = {row['nazev']: row['id'] for _, row in businesses.iterrows()}
                selected_podnik = st.selectbox("Podnik*", business_names, key="add_poz_podnik")
            else:
                selected_podnik = None

            rok = st.number_input("Rok*", min_value=2000, max_value=2100, value=datetime.now().year, key="add_poz_rok")

        with col2:
            if not typy.empty:
                typ_names = typy['Nazev'].tolist()
                typ_map = {row['Nazev']: row['id'] for _, row in typy.iterrows()}
                selected_typ = st.selectbox("Typ pozemku*", typ_names, key="add_poz_typ")
            else:
                selected_typ = None

            velikost = st.number_input("Výměra (ha)*", min_value=0.0, step=0.01, value=0.0, key="add_poz_velikost")

        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("➕ Přidat", type="primary", use_container_width=True):
                if not selected_podnik or not selected_typ:
                    st.error("Všechna pole jsou povinná")
                elif velikost < 0:
                    st.error("Výměra nemůže být záporná")
                elif auth_manager.has_permission(user['role'], 'write'):
                    new_pozemek = {
                        'PodnikID': business_map[selected_podnik],
                        'NazevId': typ_map[selected_typ],
                        'Year': rok,
                        'Velikost': velikost
                    }
                    if data_manager.add_record('pozemky.csv', new_pozemek):
                        st.success("Pozemek byl úspěšně přidán!")
                        st.session_state.show_add_pozemek_form = False
                        st.rerun()
                else:
                    st.error("Nemáte oprávnění k přidávání záznamů")

        with col2:
            if st.button("❌ Zrušit", use_container_width=True):
                st.session_state.show_add_pozemek_form = False
                st.rerun()

    st.markdown("---")

    # === TABULKA: Typy půdy vs Roky ===
    st.subheader("📊 Výměra podle typu půdy a roku")

    if not pozemky.empty and not typy.empty:
        # Join s typy
        pozemky_joined = pozemky.merge(
            typy[['id', 'Nazev']].rename(columns={'Nazev': 'TypPozemku'}),
            left_on='NazevId',
            right_on='id',
            how='left'
        )

        # Pivot tabulka: řádky = typ půdy, sloupce = roky
        pivot_df = pozemky_joined.pivot_table(
            values='Velikost',
            index='TypPozemku',
            columns='Year',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        # Seřadit sloupce (roky) sestupně
        year_cols = [col for col in pivot_df.columns if col != 'TypPozemku']
        year_cols_sorted = sorted(year_cols)
        pivot_df = pivot_df[['TypPozemku'] + year_cols_sorted]

        # Přejmenovat sloupce
        pivot_df = pivot_df.rename(columns={'TypPozemku': 'Typ půdy'})

        st.dataframe(
            pivot_df,
            use_container_width=True,
            hide_index=True,
            column_config={col: st.column_config.NumberColumn(format="%.2f") for col in year_cols_sorted}
        )

        # Graf vývoje typů pozemků
        st.subheader("📈 Vývoj výměry podle typu půdy")

        # Připravit data pro graf - long format
        chart_df = pozemky_joined.groupby(['Year', 'TypPozemku'])['Velikost'].sum().reset_index()
        chart_df = chart_df.sort_values('Year')

        import plotly.express as px
        fig = px.line(
            chart_df,
            x='Year',
            y='Velikost',
            color='TypPozemku',
            markers=True,
            title='Vývoj výměry pozemků podle typu',
            labels={'Year': 'Rok', 'Velikost': 'Výměra (ha)', 'TypPozemku': 'Typ půdy'}
        )
        fig.update_layout(
            xaxis_title="Rok",
            yaxis_title="Výměra (ha)",
            legend_title="Typ půdy"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Výběr roku pro detail
    if not pozemky.empty and 'Year' in pozemky.columns:
        years = sorted(pozemky['Year'].dropna().unique(), reverse=True)
        if years:
            current_year = datetime.now().year
            default_year = current_year if current_year in years else years[0]
            selected_year = st.selectbox(
                "Rok pro detail:",
                years,
                index=years.index(default_year) if default_year in years else 0
            )
        else:
            selected_year = datetime.now().year
    else:
        selected_year = datetime.now().year

    # Souhrn pozemků podle typu
    st.subheader(f"📊 Souhrn pozemků podle typu ({selected_year})")

    summary = agg.get_pozemky_summary_by_year(selected_year)

    if not summary.empty:
        # Zobrazení souhrnu
        display_df = summary[['nazev', 'vymera', 'procento']].copy()
        display_df.columns = ['Typ pozemku', 'Výměra (ha)', 'Procento (%)']

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Výměra (ha)": st.column_config.NumberColumn(format="%.2f"),
                "Procento (%)": st.column_config.NumberColumn(format="%.2f")
            }
        )

        # Graf
        import plotly.express as px
        fig = px.pie(
            summary,
            values='vymera',
            names='nazev',
            title='Rozdělení pozemků podle typu'
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info(f"Žádná data o pozemcích pro rok {selected_year}")

    st.markdown("---")

    # Detailní tabulka pozemků - rozdělené podle podniků
    st.subheader("📋 Detailní seznam pozemků podle podniků")

    # Filtrování pozemků podle roku
    pozemky_filtered = pozemky[pozemky['Year'] == selected_year].copy() if not pozemky.empty and 'Year' in pozemky.columns else pd.DataFrame()

    if not pozemky_filtered.empty:
        # Join s typy pozemků
        if not typy.empty and 'NazevId' in pozemky_filtered.columns:
            pozemky_filtered = pozemky_filtered.merge(
                typy[['id', 'Nazev']].rename(columns={'Nazev': 'TypPozemku'}),
                left_on='NazevId',
                right_on='id',
                how='left',
                suffixes=('', '_typ')
            )

        # Join s podniky
        if not businesses.empty and 'PodnikID' in pozemky_filtered.columns:
            pozemky_filtered = pozemky_filtered.merge(
                businesses[['id', 'nazev']].rename(columns={'nazev': 'Podnik'}),
                left_on='PodnikID',
                right_on='id',
                how='left',
                suffixes=('', '_podnik')
            )

        # Agregace podle podniku a typu pozemku
        if 'Podnik' in pozemky_filtered.columns and 'TypPozemku' in pozemky_filtered.columns:
            agg_df = pozemky_filtered.groupby(['Podnik', 'TypPozemku'])['Velikost'].sum().reset_index()

            # Pro každý podnik zobrazit tabulku
            podniky_list = sorted(agg_df['Podnik'].unique())

            for podnik in podniky_list:
                st.markdown(f"**🏢 {podnik}**")

                podnik_data = agg_df[agg_df['Podnik'] == podnik][['TypPozemku', 'Velikost']].copy()
                podnik_data.columns = ['Typ pozemku', 'Výměra (ha)']

                # Přidat součet
                total = podnik_data['Výměra (ha)'].sum()

                st.dataframe(
                    podnik_data,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Výměra (ha)": st.column_config.NumberColumn(format="%.2f")
                    }
                )
                st.caption(f"Celkem: {total:.2f} ha")
                st.markdown("")

    else:
        st.info(f"Žádné pozemky pro rok {selected_year}")

    # Statistiky
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.caption(f"Celkem záznamů: {len(pozemky_filtered)}")

    with col2:
        if not summary.empty:
            total_vymera = summary['vymera'].sum()
            st.caption(f"Celková výměra: {total_vymera:.2f} ha")

    # Nápověda
    with st.expander("ℹ️ O pozemcích"):
        st.markdown("""
        ### Typy pozemků:
        - **Orná půda** - Půda určená pro pěstování plodin
        - **Louky** - Trvalé travní porosty používané k sečení
        - **Pastviny** - Trvalé travní porosty pro pastvu dobytka
        - **Ostatní půda** - Ostatní druhy pozemků

        Součet výměr podle typů by měl odpovídat celkové výměře hospodářství.
        """)
