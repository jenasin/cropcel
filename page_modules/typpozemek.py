"""
Správa typů pozemků
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy typů pozemků"""
    st.title("🏞️ Správa typů pozemků")
    st.markdown("---")

    # Načtení dat
    typy = data_manager.get_typpozemek()

    # Tlačítka akcí
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("➕ Přidat nový", use_container_width=True):
            st.session_state.show_add_typ_form = True

    with col2:
        if st.button("🔄 Obnovit", use_container_width=True):
            data_manager.load_csv('typpozemek.csv', force_reload=True)
            st.rerun()

    # Formulář pro přidání
    if st.session_state.get('show_add_typ_form', False):
        st.subheader("Přidat nový typ pozemku")

        nazev = st.text_input("Název typu*", key="add_typ_nazev")

        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("➕ Přidat", type="primary", use_container_width=True):
                if not nazev:
                    st.error("Název je povinný")
                elif auth_manager.has_permission(user['role'], 'write'):
                    # Najít nejvyšší pořadí
                    max_poradi = typy['Poradi'].max() if not typy.empty and 'Poradi' in typy.columns else 0
                    new_typ = {
                        'Nazev': nazev,
                        'Poradi': int(max_poradi) + 1 if pd.notna(max_poradi) else 1
                    }
                    if data_manager.add_record('typpozemek.csv', new_typ):
                        st.success("Typ pozemku byl úspěšně přidán!")
                        st.session_state.show_add_typ_form = False
                        st.rerun()
                else:
                    st.error("Nemáte oprávnění k přidávání záznamů")

        with col2:
            if st.button("❌ Zrušit", use_container_width=True):
                st.session_state.show_add_typ_form = False
                st.rerun()

    st.markdown("---")

    # Zobrazení tabulky
    st.subheader("Seznam typů pozemků")

    if not typy.empty:
        can_edit = auth_manager.has_permission(user['role'], 'write')

        # Uložit seznam ID v pořadí do session state
        if 'typy_id_order' not in st.session_state:
            sorted_typy = typy.sort_values('Poradi', na_position='last')
            st.session_state.typy_id_order = sorted_typy['id'].tolist()

        # Seřadit podle uloženého pořadí
        id_order = st.session_state.typy_id_order
        for typ_id in typy['id'].tolist():
            if typ_id not in id_order:
                id_order.append(typ_id)
        id_order = [i for i in id_order if i in typy['id'].values]
        st.session_state.typy_id_order = id_order

        # Seřadit DataFrame podle id_order
        typy['_order'] = typy['id'].apply(lambda x: id_order.index(x) if x in id_order else 999)
        typy = typy.sort_values('_order').drop(columns=['_order']).reset_index(drop=True)

        # Ovládání pořadí
        if can_edit and len(typy) > 1:
            st.markdown("**Změna pořadí:**")
            col1, col2, col3 = st.columns([4, 1, 1])

            typ_names = typy['Nazev'].tolist()
            typ_ids = typy['id'].tolist()

            if 'selected_typ_idx' not in st.session_state:
                st.session_state.selected_typ_idx = 0

            with col1:
                selected_idx = st.selectbox(
                    "Vyberte typ",
                    options=range(len(typ_names)),
                    format_func=lambda x: typ_names[x],
                    index=st.session_state.selected_typ_idx,
                    key="typ_select",
                    label_visibility="collapsed"
                )
                st.session_state.selected_typ_idx = selected_idx

            with col2:
                if st.button("⬆️ Nahoru", disabled=(selected_idx == 0), key="typ_up"):
                    id_list = st.session_state.typy_id_order.copy()
                    typ_id = typ_ids[selected_idx]
                    pos = id_list.index(typ_id)
                    if pos > 0:
                        id_list[pos], id_list[pos-1] = id_list[pos-1], id_list[pos]
                        st.session_state.typy_id_order = id_list
                        st.session_state.selected_typ_idx = selected_idx - 1
                        st.rerun()

            with col3:
                if st.button("⬇️ Dolů", disabled=(selected_idx >= len(typy) - 1), key="typ_down"):
                    id_list = st.session_state.typy_id_order.copy()
                    typ_id = typ_ids[selected_idx]
                    pos = id_list.index(typ_id)
                    if pos < len(id_list) - 1:
                        id_list[pos], id_list[pos+1] = id_list[pos+1], id_list[pos]
                        st.session_state.typy_id_order = id_list
                        st.session_state.selected_typ_idx = selected_idx + 1
                        st.rerun()

        # Vybrat jen název
        final_df = pd.DataFrame()
        final_df['Název typu'] = typy['Nazev'].values

        st.data_editor(
            final_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic" if can_edit else "fixed",
            key="typpozemek_editor",
            column_config={
                "Název typu": st.column_config.TextColumn(width="large")
            }
        )

        # Tlačítko pro uložení změn
        if can_edit:
            if st.button("💾 Uložit změny", type="primary"):
                if 'typy_id_order' in st.session_state:
                    del st.session_state.typy_id_order
                st.success("Změny byly uloženy! (Demo režim)")

    else:
        st.info("Žádné typy pozemků k zobrazení")

    # Statistiky
    st.markdown("---")
    st.caption(f"Celkem typů: {len(typy)}")
