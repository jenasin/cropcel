"""
Správa vztahů uživatel-podnik
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy vztahů uživatel-podnik"""
    st.title("🔗 Přístup k podnikům")
    st.markdown("---")

    # Kontrola oprávnění
    if not auth_manager.has_permission(user['role'], 'manage_users'):
        st.error("Nemáte oprávnění k přístupu na tuto stránku")
        st.info("Správa vztahů uživatel-podnik je dostupná pouze pro administrátory")
        return

    # Načtení dat
    userpodniky = data_manager.get_userpodniky()
    users = data_manager.get_users()
    businesses = data_manager.get_businesses()

    # Tlačítka akcí
    col1, col2 = st.columns([1, 5])

    with col1:
        if st.button("🔄 Obnovit", use_container_width=True):
            data_manager.load_csv('userpodniky.csv', force_reload=True)
            st.rerun()

    st.markdown("---")

    # Zobrazení tabulky
    st.subheader("Přiřazení podniků uživatelům")

    if not users.empty and not businesses.empty:
        # Seřadit podniky
        biz_sorted = businesses.sort_values('nazev')
        biz_names = biz_sorted['nazev'].tolist()

        # Vytvořit matici - řádky = uživatelé, sloupce = podniky (checkboxy)
        matrix_data = []
        for _, user_row in users.iterrows():
            user_id = user_row['id']
            username = user_row['username']
            role = user_row.get('role', '-')

            row = {
                'Uživatel': username,
                'Role': role
            }

            # Pro každý podnik zjistit, jestli má uživatel přístup
            for _, biz_row in biz_sorted.iterrows():
                has_access = False
                if not userpodniky.empty and 'userId' in userpodniky.columns and 'podnikId' in userpodniky.columns:
                    has_access = bool(((userpodniky['userId'] == user_id) &
                                      (userpodniky['podnikId'] == biz_row['id'])).any())
                row[biz_row['nazev']] = has_access

            matrix_data.append(row)

        matrix_df = pd.DataFrame(matrix_data)
        matrix_df = matrix_df.sort_values('Uživatel').reset_index(drop=True)

        # Konfigurace sloupců
        column_config = {
            "Uživatel": st.column_config.TextColumn(width="small", disabled=True),
            "Role": st.column_config.TextColumn(width="small", disabled=True)
        }
        for biz_name in biz_names:
            column_config[biz_name] = st.column_config.CheckboxColumn(width="small")

        # Editovatelná tabulka
        edited_df = st.data_editor(
            matrix_df,
            use_container_width=True,
            hide_index=True,
            key="userpodniky_editor",
            column_config=column_config
        )

        if st.button("💾 Uložit změny", type="primary"):
            st.success("Změny byly uloženy! (Demo režim)")

    else:
        st.info("Žádní uživatelé nebo podniky k zobrazení")

    # Statistiky
    st.markdown("---")
    st.caption(f"Celkem vztahů: {len(userpodniky)}")

    # Informace
    with st.expander("ℹ️ Co jsou vztahy uživatel-podnik?"):
        st.markdown("""
        Tato tabulka definuje, ke kterým podnikům má každý uživatel přístup.

        - Jeden uživatel může mít přístup k více podnikům
        - Jeden podnik může mít více uživatelů
        - Tyto vztahy určují filtrování dat podle přístupu uživatele
        """)
