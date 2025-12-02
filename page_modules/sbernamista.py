"""
Správa sběrných míst
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy sběrných míst"""
    st.title("📍 Správa sběrných míst")
    st.markdown("---")

    # Načtení dat
    sbernamista = data_manager.get_sbernamista()
    businesses = data_manager.get_businesses()

    # Tlačítka akcí
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("➕ Přidat nové", use_container_width=True):
            st.session_state.show_add_sbernamisto_form = True

    with col2:
        if st.button("🔄 Obnovit", use_container_width=True):
            data_manager.load_csv('sbernamista.csv', force_reload=True)
            st.rerun()

    # Formulář pro přidání
    if st.session_state.get('show_add_sbernamisto_form', False):
        st.subheader("Přidat nové sběrné místo")

        col1, col2 = st.columns(2)
        with col1:
            nazev = st.text_input("Název místa*", key="add_nazev_mista")

        with col2:
            if not businesses.empty:
                business_names = sorted(businesses['nazev'].tolist())
                business_map = {row['nazev']: row['id'] for _, row in businesses.iterrows()}
                selected_podnik = st.selectbox("Podnik*", business_names, key="add_podnik_mista")
            else:
                selected_podnik = None

        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("➕ Přidat", type="primary", use_container_width=True):
                if not nazev:
                    st.error("Název je povinný")
                elif not selected_podnik:
                    st.error("Vyberte podnik")
                elif auth_manager.has_permission(user['role'], 'write'):
                    new_misto = {
                        'PodnikID': business_map[selected_podnik],
                        'Nazev': nazev
                    }
                    if data_manager.add_record('sbernamista.csv', new_misto):
                        st.success("Sběrné místo bylo úspěšně přidáno!")
                        st.session_state.show_add_sbernamisto_form = False
                        st.rerun()
                else:
                    st.error("Nemáte oprávnění k přidávání záznamů")

        with col2:
            if st.button("❌ Zrušit", use_container_width=True):
                st.session_state.show_add_sbernamisto_form = False
                st.rerun()

    st.markdown("---")

    # Zobrazení tabulky
    st.subheader("Seznam sběrných míst")

    if not sbernamista.empty:
        # Join s podniky pro zobrazení názvů
        display_df = sbernamista.copy()

        if not businesses.empty and 'PodnikID' in display_df.columns:
            display_df = display_df.merge(
                businesses[['id', 'nazev']].rename(columns={'nazev': 'Podnik'}),
                left_on='PodnikID',
                right_on='id',
                how='left',
                suffixes=('', '_biz')
            )

        # Vybrat jen potřebné sloupce: Název, Podnik
        final_df = pd.DataFrame()
        if 'Nazev' in display_df.columns:
            final_df['Název místa'] = display_df['Nazev'].values
        if 'Podnik' in display_df.columns:
            final_df['Podnik'] = display_df['Podnik'].values

        can_edit = auth_manager.has_permission(user['role'], 'write')

        # Seznam podniků pro selectbox
        podnik_options = sorted(businesses['nazev'].unique().tolist()) if not businesses.empty else []

        st.data_editor(
            final_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic" if can_edit else "fixed",
            key="sbernamista_editor",
            column_config={
                "Název místa": st.column_config.TextColumn(width="medium"),
                "Podnik": st.column_config.SelectboxColumn(width="medium", options=podnik_options)
            }
        )

        # Tlačítko pro uložení změn
        if auth_manager.has_permission(user['role'], 'write'):
            if st.button("💾 Uložit změny", type="primary"):
                st.success("Změny byly uloženy! (Demo režim)")
                st.info("💡 V produkční verzi by se zde změny uložily do databáze/CSV")

    else:
        st.info("Žádná sběrná místa k zobrazení")

    # Statistiky
    st.markdown("---")
    st.caption(f"Celkem sběrných míst: {len(sbernamista)}")
