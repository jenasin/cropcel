"""
Správa souhrnu plodin
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager):
    """Zobrazí stránku souhrnu plodin"""
    st.title("📈 Souhrn plodin")
    st.markdown("---")

    # Načtení dat
    souhrn = data_manager.get_sumplodiny()
    crops = data_manager.get_crops()
    businesses = data_manager.get_businesses()

    # Tlačítka akcí
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("➕ Přidat nový", use_container_width=True):
            st.session_state.show_add_sumplodiny_form = True

    with col2:
        if st.button("🔄 Obnovit", use_container_width=True):
            data_manager.load_csv('sumplodiny.csv', force_reload=True)
            st.rerun()

    # Formulář pro přidání
    if st.session_state.get('show_add_sumplodiny_form', False):
        with st.form("add_sumplodiny_form"):
            st.subheader("Přidat nový souhrn plodiny")

            col1, col2 = st.columns(2)
            with col1:
                year = st.number_input("Rok*", min_value=2000, max_value=2100, step=1, value=2025)

                if not crops.empty:
                    crop_options = {row['nazev']: row['id'] for _, row in crops.iterrows()}
                    selected_crop = st.selectbox("Plodina*", list(crop_options.keys()))
                else:
                    st.error("Nejsou k dispozici žádné plodiny")
                    selected_crop = None

            with col2:
                vaha = st.number_input("Čistá váha (t)*", min_value=0.0, step=0.01, value=0.0)

                if not businesses.empty:
                    business_options = {row['nazev']: row['id'] for _, row in businesses.iterrows()}
                    selected_business = st.selectbox("Podnik*", list(business_options.keys()))
                else:
                    st.error("Nejsou k dispozici žádné podniky")
                    selected_business = None

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Uložit", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("❌ Zrušit", use_container_width=True)

            if submit:
                if not selected_crop or not selected_business:
                    st.error("Všechna pole jsou povinná")
                elif vaha <= 0:
                    st.error("Váha musí být větší než 0")
                elif auth_manager.has_permission(user['role'], 'write'):
                    new_record = {
                        'Year': int(year),
                        'PlodinaID': crop_options[selected_crop],
                        'CistaVaha': vaha,
                        'PodnikID': business_options[selected_business]
                    }
                    if data_manager.add_record('sumplodiny.csv', new_record):
                        st.success("Záznam byl úspěšně přidán!")
                        st.session_state.show_add_sumplodiny_form = False
                        st.rerun()
                else:
                    st.error("Nemáte oprávnění k přidávání záznamů")

            if cancel:
                st.session_state.show_add_sumplodiny_form = False
                st.rerun()

    st.markdown("---")

    # Filtry
    col1, col2 = st.columns(2)
    with col1:
        if not souhrn.empty and 'Year' in souhrn.columns:
            years = sorted(souhrn['Year'].unique(), reverse=True)
            # Výchozí je poslední rok (index=1 protože první je 'Vše')
            year_options = ['Vše'] + list(years)
            selected_year = st.selectbox("Filtr - Rok", year_options, index=1)
        else:
            selected_year = 'Vše'

    with col2:
        if not businesses.empty:
            business_names = sorted(businesses['nazev'].unique())
            selected_business = st.selectbox("Filtr - Podnik", ['Vše'] + list(business_names))
        else:
            selected_business = 'Vše'

    selected_crop_filter = 'Vše'

    # Zobrazení tabulky
    st.subheader("Seznam souhrnu plodin")

    if not souhrn.empty:
        # Join s plodinami a podniky
        display_df = souhrn.copy()

        # Join s plodinami
        if not crops.empty and 'PlodinaID' in display_df.columns:
            display_df = display_df.merge(
                crops[['id', 'nazev']].rename(columns={'nazev': 'Plodina'}),
                left_on='PlodinaID',
                right_on='id',
                how='left',
                suffixes=('', '_crop')
            )

        # Join s podniky
        if not businesses.empty and 'PodnikID' in display_df.columns:
            display_df = display_df.merge(
                businesses[['id', 'nazev']].rename(columns={'nazev': 'Podnik'}),
                left_on='PodnikID',
                right_on='id',
                how='left',
                suffixes=('', '_business')
            )

        # Aplikovat filtry
        if selected_year != 'Vše' and 'Year' in display_df.columns:
            display_df = display_df[display_df['Year'] == selected_year]

        if selected_crop_filter != 'Vše' and 'Plodina' in display_df.columns:
            display_df = display_df[display_df['Plodina'] == selected_crop_filter]

        if selected_business != 'Vše' and 'Podnik' in display_df.columns:
            display_df = display_df[display_df['Podnik'] == selected_business]

        # Seřadit podle roku sestupně
        if 'Year' in display_df.columns:
            display_df = display_df.sort_values('Year', ascending=False)

        # Vybrat a seřadit sloupce: Rok, Plodina, Podnik, Čistá váha
        final_df = pd.DataFrame()
        if 'Year' in display_df.columns:
            final_df['Rok'] = display_df['Year'].values
        if 'Plodina' in display_df.columns:
            final_df['Plodina'] = display_df['Plodina'].values
        if 'Podnik' in display_df.columns:
            final_df['Podnik'] = display_df['Podnik'].values
        if 'CistaVaha' in display_df.columns:
            final_df['Čistá váha (t)'] = display_df['CistaVaha'].values

        can_edit = auth_manager.has_permission(user['role'], 'write')

        edited_df = st.data_editor(
            final_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic" if can_edit else "fixed",
            key="sumplodiny_editor",
            column_config={
                "Rok": st.column_config.NumberColumn(format="%d", width="small"),
                "Plodina": st.column_config.TextColumn(width="medium"),
                "Podnik": st.column_config.TextColumn(width="medium"),
                "Čistá váha (t)": st.column_config.NumberColumn(format="%.2f", width="small")
            }
        )

        # Tlačítko pro uložení změn
        if auth_manager.has_permission(user['role'], 'write'):
            if st.button("💾 Uložit změny", type="primary"):
                st.success("Změny byly uloženy! (Demo režim)")
                st.info("💡 V produkční verzi by se zde změny uložily do databáze/CSV")

    else:
        st.info("Žádný souhrn plodin k zobrazení")

    # Statistiky
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Celkem záznamů: {len(souhrn)}")
    with col2:
        if not souhrn.empty and 'CistaVaha' in souhrn.columns:
            total_weight = souhrn['CistaVaha'].sum()
            st.caption(f"Celková váha: {total_weight:.2f} t")

    # Graf podle roku
    if not souhrn.empty and 'Year' in souhrn.columns and 'CistaVaha' in souhrn.columns:
        st.markdown("---")
        st.subheader("Vývoj produkce podle roku")

        yearly_sum = souhrn.groupby('Year')['CistaVaha'].sum().reset_index()

        import plotly.express as px
        fig = px.bar(
            yearly_sum,
            x='Year',
            y='CistaVaha',
            title='Celková produkce podle roku',
            labels={'Year': 'Rok', 'CistaVaha': 'Čistá váha (t)'}
        )
        st.plotly_chart(fig, use_container_width=True)
