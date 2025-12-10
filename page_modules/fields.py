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
    varieties = data_manager.get_varieties_seed()

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
    has_write_perm = auth_manager.has_permission(user['role'], 'write')

    # Získat dostupné roky pro kopírování
    all_years = sorted(fields['rok_sklizne'].dropna().unique(), reverse=True) if not fields.empty and 'rok_sklizne' in fields.columns else []

    if has_write_perm and all_years:
        st.markdown("### 📅 Kopírovat osevní plán")

        col1, col2, col3, col4 = st.columns([1.5, 1.5, 1, 2])

        with col1:
            # Zdrojový rok
            source_year = st.selectbox(
                "Z roku:",
                all_years,
                key="copy_source_year"
            )

        with col2:
            # Cílový rok
            next_year = int(max(all_years)) + 1 if all_years else datetime.now().year + 1
            target_year = st.number_input(
                "Do roku:",
                min_value=2000,
                max_value=2100,
                value=next_year,
                key="copy_target_year"
            )

        # Počet polí ke kopírování
        source_fields = fields[(fields['podnik_id'] == selected_podnik) & (fields['rok_sklizne'] == source_year)]

        with col3:
            st.metric("Polí", len(source_fields))

        with col4:
            if st.button(f"📋 Kopírovat {len(source_fields)} polí z {int(source_year)} → {int(target_year)}", use_container_width=True, type="primary"):
                if len(source_fields) == 0:
                    st.error("Žádná pole ke kopírování")
                else:
                    # Kopírování polí
                    copied_count = 0
                    for _, row in source_fields.iterrows():
                        new_field = {
                            'vymera': row.get('vymera', 0),
                            'sklizeno': 0,  # Vynulovat
                            'cista_vaha': 0,  # Vynulovat
                            'hruba_vaha': 0,  # Vynulovat
                            'plodina_id': None,  # Nevyplnit
                            'odruda_id': None,  # Nevyplnit
                            'podnik_id': selected_podnik,
                            'cislo_honu': row.get('cislo_honu', ''),
                            'nazev_honu': row.get('nazev_honu', ''),
                            'stmn': row.get('stmn', ''),
                            'datum_seti': '',
                            'datum_vznik': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'rok_sklizne': int(target_year),
                            'operation': 'insert'
                        }
                        if data_manager.add_record('fields.csv', new_field):
                            copied_count += 1

                    st.success(f"Úspěšně zkopírováno {copied_count} polí do roku {target_year}")
                    st.rerun()

        st.caption("ℹ️ Zkopíruje výměry a názvy honů. Plodiny, odrůdy a sklizeň zůstanou prázdné.")

    st.markdown("---")

    # Zobrazení tabulky polí
    st.subheader(f"Seznam polí - {podnik_options[selected_podnik]} ({selected_year})")

    # Příprava dat pro editovatelnou tabulku
    can_edit = can_update and has_write_perm

    # Vytvoření seznamu plodin a odrůd pro selectbox
    crop_options_list = [""] + [row['nazev'] for _, row in crops.iterrows()] if not crops.empty else [""]
    crop_name_to_id = {row['nazev']: row['id'] for _, row in crops.iterrows()} if not crops.empty else {}

    variety_name_col = 'nazev' if not varieties.empty and 'nazev' in varieties.columns else 'name'
    variety_options_list = [""] + [row.get(variety_name_col, str(row['id'])) for _, row in varieties.iterrows()] if not varieties.empty else [""]
    variety_name_to_id = {row.get(variety_name_col, str(row['id'])): row['id'] for _, row in varieties.iterrows()} if not varieties.empty else {}

    if not fields_filtered.empty or (can_create and has_write_perm):
        # Příprava dat pro zobrazení
        if not fields_filtered.empty:
            display_df = fields_filtered.copy()

            # Přidání názvů plodin
            if not crops.empty and 'plodina_id' in display_df.columns:
                crop_id_to_name = {row['id']: row['nazev'] for _, row in crops.iterrows()}
                display_df['Plodina'] = display_df['plodina_id'].map(crop_id_to_name).fillna("")

            # Přidání názvů odrůd
            if not varieties.empty and 'odruda_id' in display_df.columns:
                variety_id_to_name = {row['id']: row.get(variety_name_col, str(row['id'])) for _, row in varieties.iterrows()}
                display_df['Odrůda'] = display_df['odruda_id'].map(variety_id_to_name).fillna("")
        else:
            # Prázdný dataframe pro přidání prvního záznamu
            display_df = pd.DataFrame(columns=['id', 'Plodina', 'Odrůda', 'vymera', 'sklizeno', 'cista_vaha',
                                               'hruba_vaha', 'cislo_honu', 'nazev_honu', 'stmn', 'datum_seti'])

        # Výběr sloupců k zobrazení (s id pro existující záznamy)
        display_cols = ['Plodina', 'Odrůda', 'vymera', 'sklizeno', 'cista_vaha', 'hruba_vaha',
                       'cislo_honu', 'nazev_honu', 'stmn', 'datum_seti']
        display_cols = [col for col in display_cols if col in display_df.columns or col in ['Plodina', 'Odrůda']]

        # Zajistit že sloupce existují
        for col in display_cols:
            if col not in display_df.columns:
                display_df[col] = ""

        # Resetovat index aby se nezobrazoval
        display_df_view = display_df[display_cols].reset_index(drop=True)

        # Editovatelná tabulka - povolení přidávání řádků
        edited_df = st.data_editor(
            display_df_view,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic" if can_edit and can_create else "fixed",
            disabled=not can_edit,
            key="fields_editor",
            column_config={
                "Plodina": st.column_config.SelectboxColumn(
                    "Plodina",
                    options=crop_options_list,
                    width="medium",
                    required=False
                ),
                "Odrůda": st.column_config.SelectboxColumn(
                    "Odrůda",
                    options=variety_options_list,
                    width="medium",
                    required=False
                ),
                "vymera": st.column_config.NumberColumn("Výměra (ha)", format="%.2f", min_value=0),
                "sklizeno": st.column_config.NumberColumn("Sklizeno (ha)", format="%.2f", min_value=0),
                "cista_vaha": st.column_config.NumberColumn("Čistá váha (t)", format="%.2f", min_value=0),
                "hruba_vaha": st.column_config.NumberColumn("Hrubá váha (t)", format="%.2f", min_value=0),
                "cislo_honu": st.column_config.TextColumn("Číslo honu"),
                "nazev_honu": st.column_config.TextColumn("Název honu"),
                "stmn": st.column_config.TextColumn("STMN"),
                "datum_seti": st.column_config.TextColumn("Datum setí")
            }
        )

        # Tlačítko pro uložení změn
        if can_edit:
            col1, col2 = st.columns([1, 5])
            with col1:
                if st.button("💾 Uložit změny", use_container_width=True, type="primary"):
                    # Zjištění nových, upravených a smazaných řádků
                    original_len = len(display_df)
                    edited_len = len(edited_df)

                    changes_made = False

                    # Nové řádky (přidané na konec)
                    if edited_len > original_len:
                        for i in range(original_len, edited_len):
                            new_row = edited_df.iloc[i]
                            vymera = new_row.get('vymera', 0) or 0

                            if vymera > 0:
                                plodina_name = new_row.get('Plodina', '')
                                odruda_name = new_row.get('Odrůda', '')

                                new_field = {
                                    'vymera': vymera,
                                    'sklizeno': new_row.get('sklizeno', 0) or 0,
                                    'cista_vaha': new_row.get('cista_vaha', 0) or 0,
                                    'hruba_vaha': new_row.get('hruba_vaha', 0) or 0,
                                    'plodina_id': crop_name_to_id.get(plodina_name) if plodina_name else None,
                                    'odruda_id': variety_name_to_id.get(odruda_name) if odruda_name else None,
                                    'podnik_id': selected_podnik,
                                    'cislo_honu': new_row.get('cislo_honu', '') or '',
                                    'nazev_honu': new_row.get('nazev_honu', '') or '',
                                    'stmn': new_row.get('stmn', '') or '',
                                    'datum_seti': new_row.get('datum_seti', '') or '',
                                    'datum_vznik': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'rok_sklizne': selected_year,
                                    'operation': 'insert'
                                }
                                data_manager.add_record('fields.csv', new_field)
                                changes_made = True

                    # Upravené řádky
                    for i in range(min(original_len, edited_len)):
                        original_row = display_df.iloc[i]
                        edited_row = edited_df.iloc[i]

                        # Porovnání hodnot
                        row_changed = False
                        for col in display_cols:
                            orig_val = original_row.get(col, '')
                            edit_val = edited_row.get(col, '')
                            if pd.isna(orig_val):
                                orig_val = ''
                            if pd.isna(edit_val):
                                edit_val = ''
                            if str(orig_val) != str(edit_val):
                                row_changed = True
                                break

                        if row_changed:
                            field_id = original_row['id']
                            plodina_name = edited_row.get('Plodina', '')
                            odruda_name = edited_row.get('Odrůda', '')

                            update_data = {
                                'vymera': edited_row.get('vymera', 0) or 0,
                                'sklizeno': edited_row.get('sklizeno', 0) or 0,
                                'cista_vaha': edited_row.get('cista_vaha', 0) or 0,
                                'hruba_vaha': edited_row.get('hruba_vaha', 0) or 0,
                                'plodina_id': crop_name_to_id.get(plodina_name) if plodina_name else None,
                                'odruda_id': variety_name_to_id.get(odruda_name) if odruda_name else None,
                                'cislo_honu': edited_row.get('cislo_honu', '') or '',
                                'nazev_honu': edited_row.get('nazev_honu', '') or '',
                                'stmn': edited_row.get('stmn', '') or '',
                                'datum_seti': edited_row.get('datum_seti', '') or '',
                                'operation': 'update'
                            }
                            data_manager.update_record('fields.csv', field_id, update_data)
                            changes_made = True

                    # Smazané řádky
                    if edited_len < original_len:
                        # Zjistit které řádky byly smazány
                        for i in range(edited_len, original_len):
                            field_id = display_df.iloc[i]['id']
                            data_manager.delete_record('fields.csv', field_id)
                            changes_made = True

                    if changes_made:
                        st.success("Změny byly uloženy!")
                        st.rerun()
                    else:
                        st.info("Žádné změny k uložení")

    else:
        st.info(f"Žádná pole pro podnik {podnik_options[selected_podnik]} v roce {selected_year}")

    # Statistiky
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    if not fields_filtered.empty:
        with col1:
            total_vymera = fields_filtered['vymera'].sum() if 'vymera' in fields_filtered.columns else 0
            st.metric("Výměra", f"{total_vymera:.2f} ha")

        with col2:
            total_sklizeno = fields_filtered['sklizeno'].sum() if 'sklizeno' in fields_filtered.columns else 0
            st.metric("Sklizeno", f"{total_sklizeno:.2f} ha")

        with col3:
            total_cista_vaha = fields_filtered['cista_vaha'].sum() if 'cista_vaha' in fields_filtered.columns else 0
            st.metric("Čistá váha", f"{total_cista_vaha:.2f} t")

        with col4:
            avg_vynos = total_cista_vaha / total_vymera if total_vymera > 0 else 0
            st.metric("Průměrný výnos", f"{avg_vynos:.2f} t/ha")


def _prepare_fields_for_display(fields_df, crops_df):
    """Připraví pole pro zobrazení s názvy plodin"""
    result = fields_df.copy()
    if not crops_df.empty and 'plodina_id' in result.columns:
        result = result.merge(
            crops_df[['id', 'nazev']].rename(columns={'nazev': 'plodina_nazev'}),
            left_on='plodina_id',
            right_on='id',
            how='left',
            suffixes=('', '_crop')
        )
    return result


def _create_field_options(fields_df):
    """Vytvoří options pro selectbox polí"""
    field_options = {}
    for _, row in fields_df.iterrows():
        plodina = row.get('plodina_nazev', 'Neznámá')
        if pd.isna(plodina):
            plodina = 'Neznámá'
        vymera = row.get('vymera', 0)
        nazev_honu = row.get('nazev_honu', '')
        label = f"{plodina} - {vymera:.2f} ha"
        if nazev_honu and not pd.isna(nazev_honu):
            label += f" ({nazev_honu})"
        field_options[row['id']] = label
    return field_options
