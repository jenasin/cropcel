"""
Správa polí - podle logiky z Nette (PozemkyPresenter, Plodiny etc.)
"""
import streamlit as st
import pandas as pd
from datetime import datetime


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy polí s filtrováním podle podniku a roku"""
    st.title("🚜 Správa polí")

    # Načtení dat
    fields = data_manager.get_fields()
    crops = data_manager.get_crops()
    businesses = data_manager.get_businesses()
    roky = data_manager.get_roky()

    # Filtrovat podniky podle přiřazení uživatele
    user_podniky = user.get('podniky', [])
    if user.get('role') != 'admin' and user_podniky:
        businesses_filtered = businesses[businesses['id'].isin(user_podniky)]
    else:
        businesses_filtered = businesses

    if businesses_filtered.empty:
        st.warning("Nemáte přiřazený žádný podnik. Kontaktujte administrátora.")
        return

    st.markdown("---")

    # Filtry - Podnik a Rok
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        # Výběr podniku
        if not businesses_filtered.empty:
            podnik_options = {row['id']: row['nazev'] for _, row in businesses_filtered.iterrows()}
            selected_podnik = st.selectbox(
                "Podnik:",
                options=list(podnik_options.keys()),
                format_func=lambda x: podnik_options[x],
                key="podnik_filter"
            )
        else:
            st.error("Žádné podniky k dispozici")
            return

    with col2:
        # Výběr roku
        if not fields.empty and 'rok_sklizne' in fields.columns:
            years = sorted(fields['rok_sklizne'].dropna().unique(), reverse=True)
            if years:
                current_year = datetime.now().year
                default_year = current_year if current_year in years else years[0]
                selected_year = st.selectbox(
                    "Rok sklizně:",
                    years,
                    index=years.index(default_year) if default_year in years else 0
                )
            else:
                selected_year = datetime.now().year
        else:
            selected_year = datetime.now().year

    with col3:
        # Kontrola práv pro rok
        year_perms = roky[roky['year'] == selected_year] if not roky.empty else pd.DataFrame()
        can_create = year_perms.iloc[0]['creatable'] == 'Y' if not year_perms.empty else True
        can_update = year_perms.iloc[0]['updatable'] == 'Y' if not year_perms.empty else True
        can_delete = year_perms.iloc[0]['deletable'] == 'Y' if not year_perms.empty else True

        # Zobrazení práv
        if not year_perms.empty:
            st.caption("**Práva k roku:**")
            st.caption(f"✓ Vytvořit: {'Ano' if can_create else 'Ne'}")
            st.caption(f"✓ Upravit: {'Ano' if can_update else 'Ne'}")

    st.markdown("---")

    # Filtrování polí podle podniku a roku
    fields_filtered = fields.copy()
    if not fields_filtered.empty:
        if 'podnik_id' in fields_filtered.columns:
            fields_filtered = fields_filtered[fields_filtered['podnik_id'] == selected_podnik]
        if 'rok_sklizne' in fields_filtered.columns:
            fields_filtered = fields_filtered[fields_filtered['rok_sklizne'] == selected_year]

    # Tlačítka akcí
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        # Přidání nového pole - pouze pokud má práva
        if can_create and auth_manager.has_permission(user['role'], 'write'):
            if st.button("➕ Přidat pole", use_container_width=True):
                st.session_state.show_add_field_form = True
                st.session_state.duplicate_field_data = None
        elif not can_create:
            st.button("➕ Přidat pole", use_container_width=True, disabled=True, help="Rok nemá právo k vytváření")

    with col2:
        # Duplikování pole
        if can_create and auth_manager.has_permission(user['role'], 'write') and not fields_filtered.empty:
            if st.button("📋 Duplikovat", use_container_width=True):
                st.session_state.show_duplicate_select = True
        elif not can_create:
            st.button("📋 Duplikovat", use_container_width=True, disabled=True, help="Rok nemá právo k vytváření")

    # Výběr pole k duplikování
    if st.session_state.get('show_duplicate_select', False) and not fields_filtered.empty:
        st.subheader("Vyberte pole k duplikování")

        # Připravit seznam polí pro výběr
        fields_for_select = fields_filtered.copy()
        if not crops.empty and 'plodina_id' in fields_for_select.columns:
            fields_for_select = fields_for_select.merge(
                crops[['id', 'nazev']].rename(columns={'nazev': 'plodina_nazev'}),
                left_on='plodina_id',
                right_on='id',
                how='left',
                suffixes=('', '_crop')
            )

        # Vytvořit popisky pro selectbox
        field_options = {}
        for _, row in fields_for_select.iterrows():
            plodina = row.get('plodina_nazev', 'Neznámá')
            vymera = row.get('vymera', 0)
            nazev_honu = row.get('nazev_honu', '')
            label = f"{plodina} - {vymera:.2f} ha"
            if nazev_honu:
                label += f" ({nazev_honu})"
            field_options[row['id']] = label

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            selected_field_id = st.selectbox(
                "Pole:",
                options=list(field_options.keys()),
                format_func=lambda x: field_options[x],
                key="duplicate_field_select"
            )
        with col2:
            if st.button("✅ Potvrdit", use_container_width=True):
                # Najít vybrané pole a uložit jeho data
                selected_row = fields_filtered[fields_filtered['id'] == selected_field_id].iloc[0]
                st.session_state.duplicate_field_data = selected_row.to_dict()
                st.session_state.show_duplicate_select = False
                st.session_state.show_add_field_form = True
                st.rerun()
        with col3:
            if st.button("❌ Zrušit", use_container_width=True, key="cancel_duplicate"):
                st.session_state.show_duplicate_select = False
                st.rerun()

    # Formulář pro přidání
    if st.session_state.get('show_add_field_form', False):
        # Získat data pro předvyplnění (z duplikování nebo prázdné)
        dup_data = st.session_state.get('duplicate_field_data', {})
        is_duplicate = bool(dup_data)

        with st.form("add_field_form"):
            st.subheader("Duplikovat pole" if is_duplicate else "Přidat nové pole")

            col1, col2 = st.columns(2)

            with col1:
                # Výběr plodiny
                if not crops.empty:
                    crop_options = {row['id']: row['nazev'] for _, row in crops.iterrows()}
                    crop_ids = list(crop_options.keys())
                    default_plodina_idx = 0
                    if is_duplicate and dup_data.get('plodina_id'):
                        try:
                            default_plodina_idx = crop_ids.index(int(dup_data['plodina_id']))
                        except (ValueError, TypeError):
                            pass
                    plodina_id = st.selectbox("Plodina*", options=crop_ids,
                                             index=default_plodina_idx,
                                             format_func=lambda x: crop_options[x])
                else:
                    plodina_id = st.number_input("ID plodiny*", min_value=1, step=1)

                default_vymera = float(dup_data.get('vymera', 0)) if is_duplicate else 0.0
                default_sklizeno = float(dup_data.get('sklizeno', 0)) if is_duplicate else 0.0
                default_cislo_honu = str(dup_data.get('cislo_honu', '')) if is_duplicate else ''

                vymera = st.number_input("Výměra (ha)*", min_value=0.0, step=0.01, value=default_vymera)
                sklizeno = st.number_input("Sklizeno (ha)", min_value=0.0, step=0.01, value=default_sklizeno)
                cislo_honu = st.text_input("Číslo honu", value=default_cislo_honu)

            with col2:
                default_cista = float(dup_data.get('cista_vaha', 0)) if is_duplicate else 0.0
                default_hruba = float(dup_data.get('hruba_vaha', 0)) if is_duplicate else 0.0
                default_nazev_honu = str(dup_data.get('nazev_honu', '')) if is_duplicate else ''

                cista_vaha = st.number_input("Čistá váha (t)", min_value=0.0, step=0.1, value=default_cista)
                hruba_vaha = st.number_input("Hrubá váha (t)", min_value=0.0, step=0.1, value=default_hruba)
                nazev_honu = st.text_input("Název honu", value=default_nazev_honu)
                datum_seti = st.date_input("Datum setí")

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Uložit", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("❌ Zrušit", use_container_width=True)

            if submit:
                if vymera <= 0:
                    st.error("Výměra musí být větší než 0")
                else:
                    new_field = {
                        'vymera': vymera,
                        'sklizeno': sklizeno,
                        'cista_vaha': cista_vaha,
                        'hruba_vaha': hruba_vaha,
                        'plodina_id': plodina_id,
                        'podnik_id': selected_podnik,
                        'cislo_honu': cislo_honu,
                        'nazev_honu': nazev_honu,
                        'datum_seti': datum_seti.strftime('%Y-%m-%d') if datum_seti else '',
                        'datum_vznik': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'rok_sklizne': selected_year,
                        'operation': 'insert'
                    }
                    if data_manager.add_record('fields.csv', new_field):
                        st.success("Pole bylo úspěšně přidáno!")
                        st.session_state.show_add_field_form = False
                        st.session_state.duplicate_field_data = None
                        st.rerun()

            if cancel:
                st.session_state.show_add_field_form = False
                st.session_state.duplicate_field_data = None
                st.rerun()

    st.markdown("---")

    # Zobrazení tabulky polí
    st.subheader(f"Seznam polí - {podnik_options[selected_podnik]} ({selected_year})")

    if not fields_filtered.empty:
        # Join s plodinami pro zobrazení názvů
        display_df = fields_filtered.copy()

        if not crops.empty and 'plodina_id' in display_df.columns:
            display_df = display_df.merge(
                crops[['id', 'nazev']].rename(columns={'nazev': 'Plodina'}),
                left_on='plodina_id',
                right_on='id',
                how='left',
                suffixes=('', '_crop')
            )

        # Odstranit ID sloupce
        id_cols = ['id', 'podnik_id', 'plodina_id', 'id_crop']
        for col in id_cols:
            if col in display_df.columns:
                display_df = display_df.drop(columns=[col])

        # Výběr sloupců k zobrazení
        display_cols = ['Plodina', 'vymera', 'sklizeno', 'cista_vaha', 'hruba_vaha',
                       'cislo_honu', 'nazev_honu', 'datum_seti']
        display_cols = [col for col in display_cols if col in display_df.columns]

        # Editovatelná tabulka
        can_edit = can_update and auth_manager.has_permission(user['role'], 'write')

        edited_df = st.data_editor(
            display_df[display_cols],
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            disabled=['Plodina'] if not can_edit else ['Plodina'],
            key="fields_editor",
            column_config={
                "Plodina": "Plodina",
                "vymera": st.column_config.NumberColumn("Výměra (ha)", format="%.2f"),
                "sklizeno": st.column_config.NumberColumn("Sklizeno (ha)", format="%.2f"),
                "cista_vaha": st.column_config.NumberColumn("Čistá váha (t)", format="%.2f"),
                "hruba_vaha": st.column_config.NumberColumn("Hrubá váha (t)", format="%.2f"),
                "cislo_honu": "Číslo honu",
                "nazev_honu": "Název honu",
                "datum_seti": "Datum setí"
            }
        )

        # Tlačítko pro uložení změn
        if can_edit:
            if st.button("💾 Uložit změny", type="primary"):
                st.success("Změny byly uloženy! (Demo režim)")
                st.info("💡 V produkční verzi by se zde změny uložily do CSV")

    else:
        st.info(f"Žádná pole pro podnik {podnik_options[selected_podnik]} v roce {selected_year}")

    # Statistiky
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    if not fields_filtered.empty:
        with col1:
            total_vymera = fields_filtered['vymera'].sum() if 'vymera' in fields_filtered.columns else 0
            st.caption(f"Výměra: {total_vymera:.2f} ha")

        with col2:
            total_sklizeno = fields_filtered['sklizeno'].sum() if 'sklizeno' in fields_filtered.columns else 0
            st.caption(f"Sklizeno: {total_sklizeno:.2f} ha")

        with col3:
            total_cista_vaha = fields_filtered['cista_vaha'].sum() if 'cista_vaha' in fields_filtered.columns else 0
            st.caption(f"Čistá váha: {total_cista_vaha:.2f} t")

        with col4:
            avg_vynos = total_cista_vaha / total_vymera if total_vymera > 0 else 0
            st.caption(f"Průměrný výnos: {avg_vynos:.2f} t/ha")
