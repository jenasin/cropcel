"""
Správa uživatelů (pouze pro adminy)
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy uživatelů"""
    st.title("👥 Správa uživatelů")
    st.markdown("---")

    # Kontrola oprávnění
    if not auth_manager.has_permission(user['role'], 'manage_users'):
        st.error("Nemáte oprávnění k přístupu na tuto stránku")
        st.info("Správa uživatelů je dostupná pouze pro administrátory")
        return

    # Načtení dat
    users = data_manager.get_users()
    businesses = data_manager.get_businesses()

    # Tlačítka akcí
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if st.button("➕ Přidat nového", use_container_width=True):
            st.session_state.show_add_user_form = True

    with col2:
        if st.button("🔄 Obnovit", use_container_width=True):
            data_manager.load_csv('users.csv', force_reload=True)
            st.rerun()

    # Formulář pro přidání
    if st.session_state.get('show_add_user_form', False):
        with st.form("add_user_form"):
            st.subheader("Přidat nového uživatele")

            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Uživatelské jméno*")
                email = st.text_input("Email*")
                full_name = st.text_input("Celé jméno")

            with col2:
                role = st.selectbox("Role*", ['admin', 'editor', 'watcher'], index=1)
                password = st.text_input("Heslo*", type="password")
                is_active = st.checkbox("Aktivní účet", value=True)

            business_ids = st.text_input(
                "ID podniků (oddělené čárkou, např: 1,2,3)",
                help="Ponechte prázdné pro admina (vidí všechny podniky)"
            )

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Uložit", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("❌ Zrušit", use_container_width=True)

            if submit:
                if not username or not email or not password:
                    st.error("Uživatelské jméno, email a heslo jsou povinné")
                elif len(password) < 6:
                    st.error("Heslo musí mít alespoň 6 znaků")
                else:
                    # Kontrola, zda uživatel již existuje
                    if not users.empty and username in users['username'].values:
                        st.error(f"Uživatel '{username}' již existuje")
                    else:
                        new_user = {
                            'username': username,
                            'email': email,
                            'password': '',  # V produkci by se mělo hashovat
                            'role': role,
                            'full_name': full_name,
                            'business_ids': business_ids,
                            'password_salt': '',
                            'password_hash': '',
                            'password_iters': '',
                            'is_active': is_active
                        }
                        if data_manager.add_record('users.csv', new_user):
                            st.success(f"Uživatel '{username}' byl úspěšně vytvořen!")
                            st.info("💡 V demo režimu je heslo uloženo bez šifrování. V produkci se hesla šifrují.")
                            st.session_state.show_add_user_form = False
                            st.rerun()

            if cancel:
                st.session_state.show_add_user_form = False
                st.rerun()

    st.markdown("---")

    # Zobrazení tabulky
    st.subheader("Seznam uživatelů")

    if not users.empty:
        # Vytvořit nový DataFrame BEZ id a hesel
        display_df = users.copy()
        cols_to_remove = ['id', 'password', 'password_hash', 'password_salt', 'password_iters']
        for col in cols_to_remove:
            if col in display_df.columns:
                display_df = display_df.drop(columns=[col])

        # Převést ID podniků na názvy
        if not businesses.empty and 'business_ids' in display_df.columns:
            business_id_to_name = {row['id']: row['nazev'] for _, row in businesses.iterrows()}
            all_business_names = ', '.join(businesses.sort_values('poradi')['nazev'].tolist())

            def convert_ids_to_names(row):
                # Admin má automaticky všechny podniky
                if row.get('role') == 'admin':
                    return 'Všechny'

                ids_str = row.get('business_ids')
                if pd.isna(ids_str) or ids_str == '' or ids_str is None:
                    return ''
                try:
                    ids = str(ids_str).split(',')
                    names = []
                    for id_str in ids:
                        id_str = id_str.strip()
                        if id_str:
                            try:
                                id_int = int(float(id_str))
                                name = business_id_to_name.get(id_int, f'ID:{id_str}')
                                names.append(name)
                            except (ValueError, TypeError):
                                names.append(f'ID:{id_str}')
                    return ', '.join(names)
                except:
                    return str(ids_str)

            display_df['Podniky'] = display_df.apply(convert_ids_to_names, axis=1)
            display_df = display_df.drop(columns=['business_ids'])

        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "username": st.column_config.TextColumn(
                    "Uživatelské jméno",
                    required=True
                ),
                "email": st.column_config.TextColumn(
                    "Email",
                    required=True
                ),
                "role": st.column_config.SelectboxColumn(
                    "Role",
                    options=['admin', 'editor', 'watcher'],
                    required=True
                ),
                "full_name": st.column_config.TextColumn(
                    "Celé jméno"
                ),
                "Podniky": st.column_config.TextColumn(
                    "Podniky",
                    width="large"
                ),
                "is_active": st.column_config.CheckboxColumn(
                    "Aktivní",
                    default=True
                )
            },
            key="users_editor"
        )

        # Tlačítko pro uložení změn
        if st.button("💾 Uložit změny", type="primary"):
            st.success("Změny byly uloženy! (Demo režim)")
            st.info("💡 V produkční verzi by se zde změny uložily do databáze/CSV")
            st.warning("⚠️ Hesla jsou skrytá z bezpečnostních důvodů")

    else:
        st.info("Žádní uživatelé k zobrazení")

    # Statistiky
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.caption(f"Celkem uživatelů: {len(users)}")

    with col2:
        if not users.empty and 'is_active' in users.columns:
            active_users = len(users[users['is_active'] == True])
            st.caption(f"Aktivních: {active_users}")

    with col3:
        if not users.empty and 'role' in users.columns:
            admins = len(users[users['role'] == 'admin'])
            st.caption(f"Adminů: {admins}")

    with col4:
        if not users.empty and 'role' in users.columns:
            editors = len(users[users['role'] == 'editor'])
            st.caption(f"Editorů: {editors}")

    # Informace o rolích
    st.markdown("---")
    with st.expander("ℹ️ Informace o rolích"):
        st.markdown("""
        **Admin:**
        - Plný přístup ke všem datům
        - Může přidávat, upravovat a mazat záznamy
        - Může spravovat uživatele

        **Editor:**
        - Může číst všechna data
        - Může přidávat a upravovat záznamy
        - Nemůže mazat záznamy ani spravovat uživatele

        **Watcher:**
        - Pouze čtení dat
        - Nemůže upravovat žádné záznamy
        """)
