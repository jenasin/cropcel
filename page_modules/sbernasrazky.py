"""
Správa sběrných srážek
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy sběrných srážek"""
    st.title("📦 Správa sběrných srážek")
    st.markdown("---")

    # Načtení dat
    srazky = data_manager.get_sbernasrazky()
    sbernamista = data_manager.get_sbernamista()
    businesses = data_manager.get_businesses()

    # Tlačítka akcí
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("➕ Přidat novou", use_container_width=True):
            st.session_state.show_add_srazka_form = True

    with col2:
        if st.button("🔄 Obnovit", use_container_width=True):
            data_manager.load_csv('sbernasrazky.csv', force_reload=True)
            st.rerun()

    # Formulář pro přidání
    if st.session_state.get('show_add_srazka_form', False):
        st.subheader("Přidat novou sběrnou srážku")

        # Připravit options
        business_options = {}
        misto_options = {}

        if not businesses.empty:
            business_options = {row['nazev']: row['id'] for _, row in businesses.iterrows()}
        if not sbernamista.empty:
            misto_options = {row['Nazev']: row['id'] for _, row in sbernamista.iterrows()}

        col1, col2 = st.columns(2)
        with col1:
            selected_business = st.selectbox("Podnik*", list(business_options.keys()), key="add_podnik")
            datum = st.date_input("Datum*", value=date.today(), key="add_datum")

        with col2:
            selected_misto = st.selectbox("Sběrné místo*", list(misto_options.keys()), key="add_misto")
            objem = st.number_input("Objem (t)*", min_value=0.0, step=0.01, value=0.0, key="add_objem")

        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("➕ Přidat", type="primary", use_container_width=True):
                if not selected_business or not selected_misto:
                    st.error("Všechna pole jsou povinná")
                elif objem < 0:
                    st.error("Objem nemůže být záporný")
                elif auth_manager.has_permission(user['role'], 'write'):
                    new_record = {
                        'Datum': datum.strftime('%Y-%m-%d'),
                        'PodnikID': business_options[selected_business],
                        'MistoID': misto_options[selected_misto],
                        'Objem': objem
                    }
                    if data_manager.add_record('sbernasrazky.csv', new_record):
                        st.success("Srážka byla úspěšně přidána!")
                        st.session_state.show_add_srazka_form = False
                        st.rerun()
                else:
                    st.error("Nemáte oprávnění k přidávání záznamů")

        with col2:
            if st.button("❌ Zrušit", use_container_width=True):
                st.session_state.show_add_srazka_form = False
                st.rerun()

    st.markdown("---")

    # Filtr podniku
    if not businesses.empty:
        business_names = sorted(businesses['nazev'].unique())
        selected_filter_business = st.selectbox("Filtr - Podnik", ['Vše'] + list(business_names))
    else:
        selected_filter_business = 'Vše'

    # Zobrazení tabulky
    st.subheader("Seznam sběrných srážek")

    if not srazky.empty:
        # Join s místy a podniky
        display_df = srazky.copy()

        # Join se sběrnými místy
        if not sbernamista.empty and 'MistoID' in display_df.columns:
            display_df = display_df.merge(
                sbernamista[['id', 'Nazev']].rename(columns={'Nazev': 'Místo'}),
                left_on='MistoID',
                right_on='id',
                how='left',
                suffixes=('', '_misto')
            )

        # Join s podniky
        if not businesses.empty and 'PodnikID' in display_df.columns:
            display_df = display_df.merge(
                businesses[['id', 'nazev']].rename(columns={'nazev': 'Podnik'}),
                left_on='PodnikID',
                right_on='id',
                how='left',
                suffixes=('', '_podnik')
            )

        # Filtrovat podle podniku
        if selected_filter_business != 'Vše' and 'Podnik' in display_df.columns:
            display_df = display_df[display_df['Podnik'] == selected_filter_business]

        # Seřadit podle data sestupně
        if 'Datum' in display_df.columns:
            display_df = display_df.sort_values('Datum', ascending=False)

        # Vybrat a seřadit sloupce: Datum, Podnik, Místo, Objem
        final_df = pd.DataFrame()
        if 'Datum' in display_df.columns:
            final_df['Datum'] = display_df['Datum'].values
        if 'Podnik' in display_df.columns:
            final_df['Podnik'] = display_df['Podnik'].values
        if 'Místo' in display_df.columns:
            final_df['Místo'] = display_df['Místo'].values
        if 'Objem' in display_df.columns:
            final_df['Objem (t)'] = display_df['Objem'].values

        can_edit = auth_manager.has_permission(user['role'], 'write')

        edited_df = st.data_editor(
            final_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic" if can_edit else "fixed",
            key="sbernasrazky_editor",
            column_config={
                "Datum": st.column_config.TextColumn(width="small"),
                "Podnik": st.column_config.TextColumn(width="medium"),
                "Místo": st.column_config.TextColumn(width="medium"),
                "Objem (t)": st.column_config.NumberColumn(format="%.2f", width="small")
            }
        )

        # Tlačítko pro uložení změn
        if auth_manager.has_permission(user['role'], 'write'):
            if st.button("💾 Uložit změny", type="primary"):
                st.success("Změny byly uloženy! (Demo režim)")
                st.info("💡 V produkční verzi by se zde změny uložily do databáze/CSV")

    else:
        st.info("Žádné sběrné srážky k zobrazení")

    # Statistiky
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Celkem záznamů: {len(srazky)}")
    with col2:
        if not srazky.empty and 'Objem' in srazky.columns:
            total_volume = srazky['Objem'].sum()
            st.caption(f"Celkový objem: {total_volume:.2f} t")
