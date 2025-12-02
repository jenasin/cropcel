"""
Správa plodin
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy plodin"""
    st.title("🌾 Správa plodin")
    st.markdown("---")

    # Načtení dat
    crops = data_manager.get_crops()

    # Tlačítka akcí
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("➕ Přidat novou", use_container_width=True):
            st.session_state.show_add_crop_form = True

    with col2:
        if st.button("🔄 Obnovit", use_container_width=True):
            data_manager.load_csv('crops.csv', force_reload=True)
            st.rerun()

    # Formulář pro přidání
    if st.session_state.get('show_add_crop_form', False):
        with st.form("add_crop_form"):
            st.subheader("Přidat novou plodinu")

            nazev = st.text_input("Název plodiny*")
            enable_main_table = st.selectbox("Povolit v hlavní tabulce", ['Y', 'N'], index=0)
            show_in_table = st.selectbox("Zobrazit v tabulce", ['Y', 'N'], index=0)
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
                    new_crop = {
                        'nazev': nazev,
                        'enable_main_table': enable_main_table,
                        'show_in_table': show_in_table,
                        'poradi': poradi
                    }
                    if data_manager.add_record('crops.csv', new_crop):
                        st.success("Plodina byla úspěšně přidána!")
                        st.session_state.show_add_crop_form = False
                        st.rerun()
                else:
                    st.error("Nemáte oprávnění k přidávání záznamů")

            if cancel:
                st.session_state.show_add_crop_form = False
                st.rerun()

    st.markdown("---")

    # Filtry
    col1, col2 = st.columns(2)
    with col1:
        filter_enabled = st.selectbox(
            "Filtr - Povolit v hlavní tabulce",
            ['Vše', 'Ano', 'Ne'],
            index=0
        )
    with col2:
        filter_show = st.selectbox(
            "Filtr - Zobrazit v tabulce",
            ['Vše', 'Ano', 'Ne'],
            index=0
        )

    # Aplikace filtrů
    if not crops.empty:
        filtered_crops = crops.copy()

        if filter_enabled == 'Ano':
            filtered_crops = filtered_crops[filtered_crops['enable_main_table'] == 'Y']
        elif filter_enabled == 'Ne':
            filtered_crops = filtered_crops[filtered_crops['enable_main_table'] == 'N']

        if filter_show == 'Ano':
            filtered_crops = filtered_crops[filtered_crops['show_in_table'] == 'Y']
        elif filter_show == 'Ne':
            filtered_crops = filtered_crops[filtered_crops['show_in_table'] == 'N']

        # Seřadit podle pořadí
        if 'poradi' in filtered_crops.columns:
            filtered_crops = filtered_crops.sort_values('poradi', na_position='last')

        # Zobrazení tabulky
        st.subheader(f"Seznam plodin ({len(filtered_crops)})")

        can_edit = auth_manager.has_permission(user['role'], 'write')

        # Uložit seznam ID v pořadí do session state
        if 'crops_id_order' not in st.session_state:
            st.session_state.crops_id_order = filtered_crops['id'].tolist()

        # Seřadit podle uloženého pořadí
        id_order = st.session_state.crops_id_order
        # Přidat nové ID které nejsou v seznamu
        for crop_id in filtered_crops['id'].tolist():
            if crop_id not in id_order:
                id_order.append(crop_id)
        # Filtrovat pouze existující ID
        id_order = [i for i in id_order if i in filtered_crops['id'].values]
        st.session_state.crops_id_order = id_order

        # Seřadit DataFrame podle id_order
        filtered_crops['_order'] = filtered_crops['id'].apply(lambda x: id_order.index(x) if x in id_order else 999)
        filtered_crops = filtered_crops.sort_values('_order').drop(columns=['_order']).reset_index(drop=True)
        # Přečíslovat pořadí
        filtered_crops['poradi'] = range(1, len(filtered_crops) + 1)

        # Ovládání pořadí nad tabulkou
        if can_edit and len(filtered_crops) > 1:
            st.markdown("**Změna pořadí:**")
            col1, col2, col3 = st.columns([4, 1, 1])

            crop_names = filtered_crops['nazev'].tolist()
            crop_ids = filtered_crops['id'].tolist()

            # Uložit vybraný index
            if 'selected_crop_idx' not in st.session_state:
                st.session_state.selected_crop_idx = 0

            with col1:
                selected_idx = st.selectbox(
                    "Vyberte plodinu",
                    options=range(len(crop_names)),
                    format_func=lambda x: crop_names[x],
                    index=st.session_state.selected_crop_idx,
                    key="crop_select",
                    label_visibility="collapsed"
                )
                st.session_state.selected_crop_idx = selected_idx

            with col2:
                if st.button("⬆️ Nahoru", disabled=(selected_idx == 0)):
                    id_list = st.session_state.crops_id_order.copy()
                    crop_id = crop_ids[selected_idx]
                    pos = id_list.index(crop_id)
                    if pos > 0:
                        id_list[pos], id_list[pos-1] = id_list[pos-1], id_list[pos]
                        st.session_state.crops_id_order = id_list
                        st.session_state.selected_crop_idx = selected_idx - 1
                        st.rerun()

            with col3:
                if st.button("⬇️ Dolů", disabled=(selected_idx >= len(filtered_crops) - 1)):
                    id_list = st.session_state.crops_id_order.copy()
                    crop_id = crop_ids[selected_idx]
                    pos = id_list.index(crop_id)
                    if pos < len(id_list) - 1:
                        id_list[pos], id_list[pos+1] = id_list[pos+1], id_list[pos]
                        st.session_state.crops_id_order = id_list
                        st.session_state.selected_crop_idx = selected_idx + 1
                        st.rerun()

        # Připravit data pro zobrazení
        display_df = filtered_crops[['nazev', 'enable_main_table', 'show_in_table', 'poradi']].copy()
        display_df['enable_main_table'] = display_df['enable_main_table'].map({'Y': 'Ano', 'N': 'Ne'})
        display_df['show_in_table'] = display_df['show_in_table'].map({'Y': 'Ano', 'N': 'Ne'})
        display_df.columns = ['Název plodiny', 'Povolit v tabulce', 'Zobrazit', 'Pořadí']

        if can_edit:
            edited_df = st.data_editor(
                display_df,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="crops_editor",
                column_config={
                    "Název plodiny": st.column_config.TextColumn(width="large"),
                    "Povolit v tabulce": st.column_config.SelectboxColumn(options=['Ano', 'Ne'], width="small"),
                    "Zobrazit": st.column_config.SelectboxColumn(options=['Ano', 'Ne'], width="small"),
                    "Pořadí": st.column_config.NumberColumn(min_value=1, step=1, width="small")
                }
            )

            if st.button("💾 Uložit změny", type="primary"):
                if 'crops_id_order' in st.session_state:
                    del st.session_state.crops_id_order
                st.success("Změny byly uloženy! (Demo režim)")
        else:
            st.dataframe(display_df, use_container_width=True, hide_index=True)

    else:
        st.info("Žádné plodiny k zobrazení")

    # Statistiky
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"Celkem plodin: {len(crops)}")
    with col2:
        if not crops.empty:
            enabled = len(crops[crops['enable_main_table'] == 'Y'])
            st.caption(f"Povoleno v tabulce: {enabled}")
    with col3:
        if not crops.empty:
            shown = len(crops[crops['show_in_table'] == 'Y'])
            st.caption(f"Zobrazeno: {shown}")
