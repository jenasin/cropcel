"""
Správa roků s právy - podle logiky AdminRokPresenter z Nette
"""
import streamlit as st
import pandas as pd


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy roků podle logiky AdminRokPresenter"""
    st.title("📅 Správa roků a přístupových práv")

    # Pouze admin může spravovat roky
    if user.get('role') != 'admin':
        st.error("Nemáte oprávnění k přístupu na tuto stránku")
        st.info("Správa roků je dostupná pouze pro administrátory")
        return

    st.markdown("---")

    # Načtení dat
    roky = data_manager.get_roky()

    # Informační box
    st.info("""
    **Práva k rokům:**
    - **Creatable (Lze vytvořit)** - Povolit vytváření nových záznamů pro daný rok
    - **Updatable (Lze upravit)** - Povolit úpravy existujících záznamů pro daný rok
    - **Deletable (Lze smazat)** - Povolit mazání záznamů pro daný rok
    """)

    st.markdown("---")

    # Zobrazení tabulky
    st.subheader("Seznam roků a jejich práv")

    if not roky.empty:
        # Seřadit podle roku sestupně
        display_df = roky.sort_values('year', ascending=False).reset_index(drop=True)

        # Převod Y/N na True/False pro checkboxy
        display_df['creatable'] = display_df['creatable'] == 'Y'
        display_df['updatable'] = display_df['updatable'] == 'Y'
        display_df['deletable'] = display_df['deletable'] == 'Y'

        # Vybrat jen potřebné sloupce (bez id)
        display_df = display_df[['year', 'creatable', 'updatable', 'deletable']]

        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="roky_editor",
            column_config={
                "year": st.column_config.NumberColumn(
                    "Rok",
                    min_value=2000,
                    max_value=2100,
                    step=1,
                    required=True,
                    help="Rok sklizně"
                ),
                "creatable": st.column_config.CheckboxColumn(
                    "Lze vytvořit",
                    help="Povolit vytváření nových záznamů"
                ),
                "updatable": st.column_config.CheckboxColumn(
                    "Lze upravit",
                    help="Povolit úpravy existujících záznamů"
                ),
                "deletable": st.column_config.CheckboxColumn(
                    "Lze smazat",
                    help="Povolit mazání záznamů"
                )
            }
        )

        # Tlačítko pro uložení změn
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("💾 Uložit změny", type="primary", use_container_width=True):
                # TODO: Implementovat ukládání změn do CSV
                st.success("Změny byly uloženy! (Demo režim)")
                st.info("💡 V produkční verzi by se zde změny uložily do CSV souboru")

    else:
        st.info("Žádné roky k zobrazení")
        st.warning("⚠️ Doporučujeme přidat alespoň jeden rok pro správné fungování aplikace")

    # Statistiky a přehled
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.caption(f"Celkem roků: {len(roky)}")

    if not roky.empty:
        with col2:
            creatable_count = len(roky[roky['creatable'] == 'Y'])
            st.caption(f"Lze vytvářet: {creatable_count}")

        with col3:
            updatable_count = len(roky[roky['updatable'] == 'Y'])
            st.caption(f"Lze upravovat: {updatable_count}")

        with col4:
            deletable_count = len(roky[roky['deletable'] == 'Y'])
            st.caption(f"Lze mazat: {deletable_count}")

    # Poznámky
    st.markdown("---")
    with st.expander("ℹ️ Jak práva fungují"):
        st.markdown("""
        ### Použití práv v aplikaci

        1. **Vytváření záznamů** - Pokud je rok nastaven jako "creatable=N", uživatelé nemohou vytvářet nová pole pro daný rok
        2. **Úpravy záznamů** - Pokud je rok nastaven jako "updatable=N", uživatelé nemohou upravovat existující pole
        3. **Mazání záznamů** - Pokud je rok nastaven jako "deletable=N", uživatelé nemohou mazat pole

        **Doporučení:**
        - Pro uzavřené roky nastavte všechna práva na "N"
        - Pro aktuální rok nastavte všechna práva na "Y"
        - Pro budoucí roky můžete povolit pouze vytváření
        """)
