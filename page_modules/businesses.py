"""
Správa podniků
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy podniků"""
    st.title("🏢 Správa podniků")
    st.markdown("---")

    # Načtení dat
    businesses = data_manager.get_businesses()

    # Tlačítka akcí
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("➕ Přidat nový", use_container_width=True):
            st.session_state.show_add_form = True

    with col2:
        if st.button("🔄 Obnovit", use_container_width=True):
            data_manager.load_csv('businesses.csv', force_reload=True)
            st.rerun()

    # Formulář pro přidání
    if st.session_state.get('show_add_form', False):
        with st.form("add_business_form"):
            st.subheader("Přidat nový podnik")

            nazev = st.text_input("Název podniku*")
            poradi = st.number_input("Pořadí", min_value=1.0, step=1.0, value=1.0)

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Uložit", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("❌ Zrušit", use_container_width=True)

            if submit:
                if not nazev:
                    st.error("Název je povinný")
                elif auth_manager.has_permission(user['role'], 'write'):
                    new_business = {
                        'nazev': nazev,
                        'poradi': poradi
                    }
                    if data_manager.add_record('businesses.csv', new_business):
                        st.success("Podnik byl úspěšně přidán!")
                        st.session_state.show_add_form = False
                        st.rerun()
                else:
                    st.error("Nemáte oprávnění k přidávání záznamů")

            if cancel:
                st.session_state.show_add_form = False
                st.rerun()

    st.markdown("---")

    # Zobrazení tabulky
    st.subheader("Seznam podniků")

    if not businesses.empty:
        # Seřadit podle pořadí
        if 'poradi' in businesses.columns:
            businesses = businesses.sort_values('poradi', na_position='last')

        can_edit = auth_manager.has_permission(user['role'], 'write')

        # Uložit seznam ID v pořadí do session state
        if 'businesses_id_order' not in st.session_state:
            st.session_state.businesses_id_order = businesses['id'].tolist()

        # Seřadit podle uloženého pořadí
        id_order = st.session_state.businesses_id_order
        for biz_id in businesses['id'].tolist():
            if biz_id not in id_order:
                id_order.append(biz_id)
        id_order = [i for i in id_order if i in businesses['id'].values]
        st.session_state.businesses_id_order = id_order

        # Seřadit DataFrame podle id_order
        businesses['_order'] = businesses['id'].apply(lambda x: id_order.index(x) if x in id_order else 999)
        businesses = businesses.sort_values('_order').drop(columns=['_order']).reset_index(drop=True)
        businesses['poradi'] = range(1, len(businesses) + 1)

        # Ovládání pořadí nad tabulkou
        if can_edit and len(businesses) > 1:
            st.markdown("**Změna pořadí:**")
            col1, col2, col3 = st.columns([4, 1, 1])

            biz_names = businesses['nazev'].tolist()
            biz_ids = businesses['id'].tolist()

            if 'selected_biz_idx' not in st.session_state:
                st.session_state.selected_biz_idx = 0

            with col1:
                selected_idx = st.selectbox(
                    "Vyberte podnik",
                    options=range(len(biz_names)),
                    format_func=lambda x: biz_names[x],
                    index=st.session_state.selected_biz_idx,
                    key="biz_select",
                    label_visibility="collapsed"
                )
                st.session_state.selected_biz_idx = selected_idx

            with col2:
                if st.button("⬆️ Nahoru", disabled=(selected_idx == 0), key="biz_up"):
                    id_list = st.session_state.businesses_id_order.copy()
                    biz_id = biz_ids[selected_idx]
                    pos = id_list.index(biz_id)
                    if pos > 0:
                        id_list[pos], id_list[pos-1] = id_list[pos-1], id_list[pos]
                        st.session_state.businesses_id_order = id_list
                        st.session_state.selected_biz_idx = selected_idx - 1
                        st.rerun()

            with col3:
                if st.button("⬇️ Dolů", disabled=(selected_idx >= len(businesses) - 1), key="biz_down"):
                    id_list = st.session_state.businesses_id_order.copy()
                    biz_id = biz_ids[selected_idx]
                    pos = id_list.index(biz_id)
                    if pos < len(id_list) - 1:
                        id_list[pos], id_list[pos+1] = id_list[pos+1], id_list[pos]
                        st.session_state.businesses_id_order = id_list
                        st.session_state.selected_biz_idx = selected_idx + 1
                        st.rerun()

        # Vytvořit DataFrame pro zobrazení
        display_df = businesses[['nazev', 'poradi']].copy()
        display_df.columns = ['Název podniku', 'Pořadí']

        # Editovatelná tabulka
        if can_edit:
            edited_df = st.data_editor(
                display_df,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="businesses_editor",
                column_config={
                    "Název podniku": st.column_config.TextColumn(width="large"),
                    "Pořadí": st.column_config.NumberColumn(min_value=1, step=1, width="small")
                }
            )

            if st.button("💾 Uložit změny", type="primary"):
                if 'businesses_id_order' in st.session_state:
                    del st.session_state.businesses_id_order
                st.success("Změny byly uloženy! (Demo režim)")
        else:
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    else:
        st.info("Žádné podniky k zobrazení")

    # Statistiky
    st.markdown("---")
    st.caption(f"Celkem podniků: {len(businesses)}")
