"""
Správa odrůd osiva
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy odrůd osiva"""
    st.title("🌱 Správa odrůd osiva")
    st.markdown("---")

    # Načtení dat
    varieties = data_manager.get_varieties_seed()

    # Tlačítka akcí
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("➕ Přidat novou", use_container_width=True):
            st.session_state.show_add_variety_form = True

    with col2:
        if st.button("🔄 Obnovit", use_container_width=True):
            data_manager.load_csv('varieties_seed.csv', force_reload=True)
            st.rerun()

    # Formulář pro přidání
    if st.session_state.get('show_add_variety_form', False):
        with st.form("add_variety_form"):
            st.subheader("Přidat novou odrůdu osiva")

            nazev = st.text_input("Název odrůdy*")

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Uložit", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("❌ Zrušit", use_container_width=True)

            if submit:
                if not nazev:
                    st.error("Název je povinný")
                elif auth_manager.has_permission(user['role'], 'write'):
                    new_variety = {
                        'nazev': nazev
                    }
                    if data_manager.add_record('varieties_seed.csv', new_variety):
                        st.success("Odrůda osiva byla úspěšně přidána!")
                        st.session_state.show_add_variety_form = False
                        st.rerun()
                else:
                    st.error("Nemáte oprávnění k přidávání záznamů")

            if cancel:
                st.session_state.show_add_variety_form = False
                st.rerun()

    st.markdown("---")

    # Zobrazení tabulky
    st.subheader("Seznam odrůd osiva")

    if not varieties.empty:
        # Vytvořit nový DataFrame BEZ id sloupce
        display_df = varieties.copy()
        if 'id' in display_df.columns:
            display_df = display_df.drop(columns=['id'])

        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic" if auth_manager.has_permission(user['role'], 'write') else "fixed",
            key="varieties_editor",
            column_config={
                "nazev": st.column_config.TextColumn(
                    "Název odrůdy",
                    help="Název odrůdy osiva",
                    max_chars=200,
                    required=True
                )
            }
        )

        # Tlačítko pro uložení změn
        if auth_manager.has_permission(user['role'], 'write'):
            if st.button("💾 Uložit změny", type="primary"):
                st.success("Změny byly uloženy! (Demo režim)")
                st.info("💡 V produkční verzi by se zde změny uložily do databáze/CSV")

    else:
        st.info("Žádné odrůdy osiva k zobrazení")

    # Statistiky
    st.markdown("---")
    st.caption(f"Celkem odrůd: {len(varieties)}")
