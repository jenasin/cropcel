"""
Správa odpisů (prodejů ze skladu)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy odpisů"""
    st.title("📝 Odpisy (prodeje ze skladu)")
    st.markdown("---")

    # Načtení dat (force reload pro aktuální data)
    businesses = data_manager.get_businesses()
    fields = data_manager.get_fields()
    odpisy = data_manager.load_csv('odpisy.csv', force_reload=True)

    # Zajistit správné datové typy
    if not odpisy.empty:
        for col in ['castka_kc', 'nabidka_kc', 'prodano_t']:
            if col in odpisy.columns:
                odpisy[col] = pd.to_numeric(odpisy[col], errors='coerce').fillna(0)

    # Filtrovat podniky podle přiřazení uživatele
    user_podniky = user.get('podniky', [])
    if user.get('role') != 'admin' and user_podniky:
        businesses_filtered = businesses[businesses['id'].isin(user_podniky)]
    else:
        businesses_filtered = businesses

    if businesses_filtered.empty:
        st.warning("Nemáte přiřazený žádný podnik.")
        return

    # Filtry
    col1, col2 = st.columns(2)

    with col1:
        podnik_options = {row['id']: row['nazev'] for _, row in businesses_filtered.iterrows()}
        selected_podnik = st.selectbox(
            "Podnik:",
            options=list(podnik_options.keys()),
            format_func=lambda x: podnik_options[x],
            key="odpisy_podnik"
        )

    with col2:
        if not fields.empty and 'rok_sklizne' in fields.columns:
            years = sorted(fields['rok_sklizne'].dropna().unique(), reverse=True)
            if years:
                current_year = datetime.now().year
                default_year = current_year if current_year in years else years[0]
                selected_year = st.selectbox(
                    "Rok:",
                    years,
                    index=years.index(default_year) if default_year in years else 0,
                    key="odpisy_rok"
                )
            else:
                selected_year = datetime.now().year
        else:
            selected_year = datetime.now().year

    st.markdown("---")

    # === VÝPOČET SKLADU ===
    # Čistá produkce z polí pro daný podnik a rok
    fields_filtered = fields[
        (fields['podnik_id'] == selected_podnik) &
        (fields['rok_sklizne'] == selected_year)
    ] if not fields.empty else pd.DataFrame()

    cista_produkce = fields_filtered['cista_vaha'].sum() if not fields_filtered.empty and 'cista_vaha' in fields_filtered.columns else 0

    # Odpisy (prodeje) pro daný podnik a rok
    odpisy_filtered = odpisy[
        (odpisy['podnik_id'] == selected_podnik) &
        (odpisy['rok'] == selected_year)
    ] if not odpisy.empty else pd.DataFrame()

    # Rozdělit podle stavu
    odpisy_prodano = odpisy_filtered[odpisy_filtered['stav'] == 'prodano'] if not odpisy_filtered.empty and 'stav' in odpisy_filtered.columns else pd.DataFrame()
    odpisy_nasmlouvano = odpisy_filtered[odpisy_filtered['stav'] == 'nasmlouvano'] if not odpisy_filtered.empty and 'stav' in odpisy_filtered.columns else pd.DataFrame()

    # Prodáno (vyděláno)
    prodano_t = odpisy_prodano['prodano_t'].sum() if not odpisy_prodano.empty else 0
    vydelano_kc = odpisy_prodano['castka_kc'].sum() if not odpisy_prodano.empty else 0

    # Nasmlouváno (čeká na platbu)
    nasmlouvano_t = odpisy_nasmlouvano['prodano_t'].sum() if not odpisy_nasmlouvano.empty else 0
    nasmlouvano_kc = odpisy_nasmlouvano['castka_kc'].sum() if not odpisy_nasmlouvano.empty else 0

    # Nabízeno celkem
    nabizeno_kc = odpisy_filtered['nabidka_kc'].sum() if not odpisy_filtered.empty and 'nabidka_kc' in odpisy_filtered.columns else 0

    # Celkem
    celkem_prodano = prodano_t + nasmlouvano_t
    celkem_trzba = vydelano_kc + nasmlouvano_kc

    # Zbytek na skladě
    zbytek_sklad = cista_produkce - celkem_prodano

    # === METRIKY ===
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("📦 Produkce", f"{cista_produkce:.2f} t")

    with col2:
        st.metric("✅ Prodáno", f"{prodano_t:.2f} t")

    with col3:
        st.metric("📝 Nasmlouváno", f"{nasmlouvano_t:.2f} t")

    with col4:
        st.metric("🏪 Zbývá", f"{zbytek_sklad:.2f} t")

    with col5:
        st.metric("💰 Vyděláno", f"{vydelano_kc:,.0f} Kč")

    # Druhý řádek metrik
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.caption(f"💵 Čeká na platbu: {nasmlouvano_kc:,.0f} Kč")
    with col2:
        st.caption(f"🏷️ Nabízeno: {nabizeno_kc:,.0f} Kč")
    with col3:
        rozdil = celkem_trzba - nabizeno_kc
        st.caption(f"📊 Vyjednáno navíc: {rozdil:+,.0f} Kč")
    with col4:
        procento = (celkem_prodano / cista_produkce * 100) if cista_produkce > 0 else 0
        st.caption(f"📈 Prodáno: {procento:.1f}% produkce")

    # === PŘEHLED PODLE TYPU OBILÍ ===
    if not odpisy_filtered.empty and 'poznamka' in odpisy_filtered.columns:
        st.markdown("---")
        st.subheader("🌾 Přehled podle typu obilí")

        # Extrahovat typ obilí z poznámky
        def extract_crop_type(poznamka):
            if pd.isna(poznamka) or poznamka == '':
                return 'Ostatní'
            poznamka_lower = str(poznamka).lower()
            if 'pšenic' in poznamka_lower:
                return 'Pšenice'
            elif 'ječmen' in poznamka_lower:
                return 'Ječmen'
            elif 'řepk' in poznamka_lower:
                return 'Řepka'
            elif 'kukuřic' in poznamka_lower:
                return 'Kukuřice'
            elif 'oves' in poznamka_lower:
                return 'Oves'
            elif 'žit' in poznamka_lower:
                return 'Žito'
            else:
                return 'Ostatní'

        odpisy_filtered_copy = odpisy_filtered.copy()
        odpisy_filtered_copy['typ_obili'] = odpisy_filtered_copy['poznamka'].apply(extract_crop_type)

        # Seskupit podle typu obilí
        grouped = odpisy_filtered_copy.groupby('typ_obili').agg({
            'prodano_t': 'sum',
            'nabidka_kc': 'sum',
            'castka_kc': 'sum'
        }).reset_index()

        if not grouped.empty:
            grouped['rozdil'] = grouped['castka_kc'] - grouped['nabidka_kc']
            grouped['cena_t_nabidka'] = (grouped['nabidka_kc'] / grouped['prodano_t']).round(0)
            grouped['cena_t_prodej'] = (grouped['castka_kc'] / grouped['prodano_t']).round(0)

            # Zobrazit jako přehlednou tabulku
            table_df = grouped[['typ_obili', 'prodano_t', 'nabidka_kc', 'castka_kc', 'rozdil', 'cena_t_nabidka', 'cena_t_prodej']].copy()
            table_df.columns = ['Plodina', 'Prodáno (t)', 'Nabízeno (Kč)', 'Prodáno za (Kč)', 'Rozdíl (Kč)', 'Cena/t nabídka', 'Cena/t prodej']

            st.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Plodina": st.column_config.TextColumn("🌾 Plodina", width="medium"),
                    "Prodáno (t)": st.column_config.NumberColumn("Prodáno (t)", format="%.1f"),
                    "Nabízeno (Kč)": st.column_config.NumberColumn("Nabízeno (Kč)", format="%,.0f"),
                    "Prodáno za (Kč)": st.column_config.NumberColumn("Prodáno za (Kč)", format="%,.0f"),
                    "Rozdíl (Kč)": st.column_config.NumberColumn("Rozdíl (Kč)", format="%+,.0f"),
                    "Cena/t nabídka": st.column_config.NumberColumn("Cena/t nabídka", format="%,.0f"),
                    "Cena/t prodej": st.column_config.NumberColumn("Cena/t prodej", format="%,.0f"),
                }
            )

            # Celkový souhrn
            st.markdown("**Celkem:**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Prodáno", f"{grouped['prodano_t'].sum():.1f} t")
            with col2:
                st.metric("Nabízeno", f"{grouped['nabidka_kc'].sum():,.0f} Kč")
            with col3:
                st.metric("Prodáno za", f"{grouped['castka_kc'].sum():,.0f} Kč")
            with col4:
                total_rozdil = grouped['rozdil'].sum()
                st.metric("Vyjednáno navíc", f"{total_rozdil:+,.0f} Kč")

    st.markdown("---")

    # === GRAF: Stav skladu ===
    st.subheader("📊 Stav skladu")

    col1, col2 = st.columns(2)

    with col1:
        # Sloupcový graf - 3 stavy
        fig_bar = go.Figure(data=[
            go.Bar(name='✅ Prodáno', x=['Sklad'], y=[prodano_t], marker_color='#2ECC71',
                   text=[f'{prodano_t:.1f} t'], textposition='outside'),
            go.Bar(name='📝 Nasmlouváno', x=['Sklad'], y=[nasmlouvano_t], marker_color='#F39C12',
                   text=[f'{nasmlouvano_t:.1f} t'], textposition='outside'),
            go.Bar(name='🏪 Zbývá', x=['Sklad'], y=[zbytek_sklad], marker_color='#3498DB',
                   text=[f'{zbytek_sklad:.1f} t'], textposition='outside')
        ])
        fig_bar.update_layout(
            barmode='group',
            title=f'Stav skladu - {podnik_options[selected_podnik]} ({selected_year})',
            yaxis_title='Tuny (t)',
            showlegend=True,
            yaxis=dict(range=[0, max(cista_produkce * 1.2, 1)])
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        # Koláčový graf
        if cista_produkce > 0:
            fig_pie = px.pie(
                values=[prodano_t, nasmlouvano_t, max(zbytek_sklad, 0)],
                names=['Prodáno', 'Nasmlouváno', 'Zbývá'],
                title='Rozdělení produkce',
                color_discrete_sequence=['#2ECC71', '#F39C12', '#3498DB'],
                hole=0.4
            )
            fig_pie.update_traces(textinfo='percent+value', texttemplate='%{label}<br>%{value:.1f} t<br>(%{percent})')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Žádná produkce pro tento rok")

    # === GRAF: Vývoj v čase ===
    if not odpisy_filtered.empty:
        st.subheader("📈 Vývoj prodejů v čase")

        # Připravit data - seřadit podle data a spočítat kumulativní součty
        odpisy_sorted = odpisy_filtered.sort_values('datum_smlouvy').copy()
        odpisy_sorted['datum_smlouvy'] = pd.to_datetime(odpisy_sorted['datum_smlouvy'])
        odpisy_sorted['kumulativni_t'] = odpisy_sorted['prodano_t'].cumsum()
        odpisy_sorted['kumulativni_kc'] = odpisy_sorted['castka_kc'].cumsum()
        odpisy_sorted['cena_t'] = odpisy_sorted['castka_kc'] / odpisy_sorted['prodano_t']

        # Graf kumulativního prodeje v tunách
        fig_timeline = go.Figure()

        # Čára - kumulativní prodej
        fig_timeline.add_trace(go.Scatter(
            x=odpisy_sorted['datum_smlouvy'],
            y=odpisy_sorted['kumulativni_t'],
            mode='lines+markers+text',
            name='Kumulativní prodej (t)',
            line=dict(color='#2ECC71', width=3),
            marker=dict(size=10),
            text=odpisy_sorted['kumulativni_t'].round(1),
            textposition='top center',
            fill='tozeroy',
            fillcolor='rgba(46, 204, 113, 0.2)'
        ))

        # Horizontální čára - cílová produkce
        fig_timeline.add_hline(
            y=cista_produkce,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Produkce: {cista_produkce:.0f} t",
            annotation_position="top right"
        )

        fig_timeline.update_layout(
            title=f'Kumulativní prodej v čase - {podnik_options[selected_podnik]} ({selected_year})',
            xaxis_title='Datum',
            yaxis_title='Prodáno (t)',
            hovermode='x unified',
            yaxis=dict(range=[0, max(cista_produkce, odpisy_sorted['kumulativni_t'].max()) * 1.15])
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

        # Druhý řádek grafů
        st.subheader("💰 Přehled tržeb")
        col1, col2 = st.columns(2)

        with col1:
            # Graf kumulativních tržeb
            fig_trzby_kum = go.Figure()

            fig_trzby_kum.add_trace(go.Scatter(
                x=odpisy_sorted['datum_smlouvy'],
                y=odpisy_sorted['kumulativni_kc'],
                mode='lines+markers',
                name='Kumulativní tržby (Kč)',
                line=dict(color='#F39C12', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(243, 156, 18, 0.2)'
            ))

            fig_trzby_kum.update_layout(
                title='Kumulativní tržby v čase',
                xaxis_title='Datum',
                yaxis_title='Tržby (Kč)',
                yaxis=dict(tickformat=',d')
            )
            st.plotly_chart(fig_trzby_kum, use_container_width=True)

        with col2:
            # Graf ceny za tunu v čase
            fig_cena = go.Figure()

            fig_cena.add_trace(go.Scatter(
                x=odpisy_sorted['datum_smlouvy'],
                y=odpisy_sorted['cena_t'],
                mode='lines+markers+text',
                name='Cena za tunu',
                line=dict(color='#3498DB', width=2),
                marker=dict(size=8),
                text=odpisy_sorted['cena_t'].round(0).astype(int),
                textposition='top center'
            ))

            # Průměrná cena
            avg_cena = celkem_trzba / celkem_prodano if celkem_prodano > 0 else 0
            fig_cena.add_hline(
                y=avg_cena,
                line_dash="dash",
                line_color="gray",
                annotation_text=f"Průměr: {avg_cena:,.0f} Kč/t",
                annotation_position="top right"
            )

            fig_cena.update_layout(
                title='Vývoj ceny za tunu (Kč/t)',
                xaxis_title='Datum',
                yaxis_title='Cena (Kč/t)',
                yaxis=dict(range=[0, odpisy_sorted['cena_t'].max() * 1.2])
            )
            st.plotly_chart(fig_cena, use_container_width=True)

        # Třetí řádek - sloupcové grafy jednotlivých prodejů
        col1, col2 = st.columns(2)

        with col1:
            # Sloupcový graf jednotlivých prodejů
            fig_bar = px.bar(
                odpisy_sorted,
                x='datum_smlouvy',
                y='prodano_t',
                text='prodano_t',
                title='Jednotlivé prodeje (t)',
                labels={'datum_smlouvy': 'Datum', 'prodano_t': 'Množství (t)'},
                color='stav' if 'stav' in odpisy_sorted.columns else None,
                color_discrete_map={'prodano': '#2ECC71', 'nasmlouvano': '#F39C12'}
            )
            fig_bar.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig_bar.update_layout(yaxis=dict(range=[0, odpisy_sorted['prodano_t'].max() * 1.3]))
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            # Sloupcový graf tržeb
            fig_trzby_bar = px.bar(
                odpisy_sorted,
                x='datum_smlouvy',
                y='castka_kc',
                text='castka_kc',
                title='Jednotlivé tržby (Kč)',
                labels={'datum_smlouvy': 'Datum', 'castka_kc': 'Částka (Kč)'},
                color='stav' if 'stav' in odpisy_sorted.columns else None,
                color_discrete_map={'prodano': '#2ECC71', 'nasmlouvano': '#F39C12'}
            )
            fig_trzby_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_trzby_bar.update_layout(yaxis=dict(range=[0, odpisy_sorted['castka_kc'].max() * 1.3]))
            st.plotly_chart(fig_trzby_bar, use_container_width=True)

    st.markdown("---")

    # === TLAČÍTKA AKCÍ ===
    col1, col2, col3 = st.columns([1, 1, 4])

    with col1:
        if auth_manager.has_permission(user['role'], 'write'):
            if st.button("➕ Přidat prodej", use_container_width=True):
                st.session_state.show_add_odpis_form = True

    with col2:
        if st.button("🔄 Obnovit", use_container_width=True):
            data_manager.load_csv('odpisy.csv', force_reload=True)
            st.rerun()

    # === FORMULÁŘ PRO PŘIDÁNÍ ===
    if st.session_state.get('show_add_odpis_form', False):
        with st.form("add_odpis_form"):
            st.subheader("Přidat nový prodej")

            col1, col2 = st.columns(2)

            with col1:
                datum_smlouvy = st.date_input("Datum smlouvy*", value=datetime.now())
                prodano_t = st.number_input("Prodané množství (t)*", min_value=0.0, step=0.1, value=0.0)
                stav = st.selectbox("Stav*", options=['nasmlouvano', 'prodano'],
                                   format_func=lambda x: '📝 Nasmlouváno' if x == 'nasmlouvano' else '✅ Prodáno')

            with col2:
                nabidka_kc = st.number_input("Nabízená cena (Kč)", min_value=0, step=1000, value=0, help="Cena, za kterou bylo nabízeno")
                castka_kc = st.number_input("Prodejní cena (Kč)*", min_value=0, step=1000, value=0)
                poznamka = st.text_area("Poznámka")
                faktura = st.file_uploader("Faktura (volitelné)", type=['pdf', 'jpg', 'png'])

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Uložit", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("❌ Zrušit", use_container_width=True)

            if submit:
                if prodano_t <= 0:
                    st.error("Množství musí být větší než 0")
                elif castka_kc <= 0:
                    st.error("Částka musí být větší než 0")
                elif prodano_t > zbytek_sklad:
                    st.error(f"Nelze prodat více než je na skladě ({zbytek_sklad:.2f} t)")
                else:
                    new_odpis = {
                        'podnik_id': selected_podnik,
                        'rok': selected_year,
                        'datum_smlouvy': datum_smlouvy.strftime('%Y-%m-%d'),
                        'castka_kc': castka_kc,
                        'nabidka_kc': nabidka_kc,
                        'prodano_t': prodano_t,
                        'faktura': faktura.name if faktura else '',
                        'poznamka': poznamka,
                        'stav': stav
                    }
                    if data_manager.add_record('odpisy.csv', new_odpis):
                        st.success("Prodej byl přidán!")
                        st.session_state.show_add_odpis_form = False
                        st.rerun()

            if cancel:
                st.session_state.show_add_odpis_form = False
                st.rerun()

    st.markdown("---")

    # === SEZNAM PRODEJŮ ===
    st.subheader(f"📋 Seznam prodejů - {podnik_options[selected_podnik]} ({selected_year})")

    # Oprávnění k editaci
    can_edit = auth_manager.has_permission(user['role'], 'write')

    if not odpisy_filtered.empty:
        display_df = odpisy_filtered.copy()

        # Uložit originální ID pro editaci
        original_ids = display_df['id'].tolist() if 'id' in display_df.columns else []

        # Pro editaci - stav jako selectbox hodnota
        stav_options = ['nasmlouvano', 'prodano']
        stav_labels = {'nasmlouvano': 'Nasmlouváno', 'prodano': 'Prodáno'}

        # Přeložit stav pro export
        stav_map_export = {'prodano': 'Prodáno', 'nasmlouvano': 'Nasmlouváno'}
        if 'stav' in display_df.columns:
            display_df['stav_export'] = display_df['stav'].map(stav_map_export).fillna(display_df['stav'])

        # Vypočítat rozdíl (vyjednáno navíc)
        if 'nabidka_kc' in display_df.columns and 'castka_kc' in display_df.columns:
            display_df['rozdil_kc'] = display_df['castka_kc'] - display_df['nabidka_kc']

        # Vybrat sloupce pro editaci
        edit_cols = ['datum_smlouvy', 'stav', 'prodano_t', 'nabidka_kc', 'castka_kc', 'rozdil_kc', 'faktura', 'poznamka']
        edit_cols = [c for c in edit_cols if c in display_df.columns]

        display_df_edit = display_df[edit_cols].copy().reset_index(drop=True)

        # Převést datum_smlouvy na datetime pro DateColumn
        if 'datum_smlouvy' in display_df_edit.columns:
            display_df_edit['datum_smlouvy'] = pd.to_datetime(display_df_edit['datum_smlouvy'], errors='coerce')

        # Editovatelná tabulka
        edited_df = st.data_editor(
            display_df_edit,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic" if can_edit else "fixed",
            disabled=not can_edit,
            column_config={
                "datum_smlouvy": st.column_config.DateColumn(
                    "Datum",
                    format="YYYY-MM-DD",
                    required=True
                ),
                "stav": st.column_config.SelectboxColumn(
                    "Stav",
                    options=stav_options,
                    required=True
                ),
                "prodano_t": st.column_config.NumberColumn(
                    "Množství (t)",
                    format="%.2f",
                    min_value=0.0,
                    required=True
                ),
                "nabidka_kc": st.column_config.NumberColumn(
                    "Nabízeno (Kč)",
                    format="%d",
                    min_value=0
                ),
                "castka_kc": st.column_config.NumberColumn(
                    "Prodáno za (Kč)",
                    format="%d",
                    min_value=0,
                    required=True
                ),
                "rozdil_kc": st.column_config.NumberColumn(
                    "Rozdíl (Kč)",
                    format="%+d",
                    disabled=True,
                    help="Rozdíl mezi prodejní cenou a nabídkou"
                ),
                "faktura": st.column_config.TextColumn(
                    "Faktura",
                    width="medium"
                ),
                "poznamka": st.column_config.TextColumn(
                    "Poznámka"
                )
            },
            key="odpisy_editor"
        )

        # Tlačítko pro uložení změn
        if can_edit:
            if st.button("💾 Uložit změny v tabulce", type="primary"):
                try:
                    # Načíst všechny odpisy
                    all_odpisy = data_manager.get_odpisy()

                    # Smazat staré záznamy pro tento podnik a rok
                    all_odpisy = all_odpisy[~((all_odpisy['podnik_id'] == selected_podnik) & (all_odpisy['rok'] == selected_year))]

                    # Přidat upravené záznamy
                    for idx, row in edited_df.iterrows():
                        if pd.notna(row.get('prodano_t')) and row.get('prodano_t', 0) > 0:
                            new_record = {
                                'id': original_ids[idx] if idx < len(original_ids) else int(all_odpisy['id'].max() + 1) if not all_odpisy.empty else 1,
                                'podnik_id': selected_podnik,
                                'rok': selected_year,
                                'datum_smlouvy': str(row.get('datum_smlouvy', ''))[:10],
                                'stav': row.get('stav', 'nasmlouvano'),
                                'prodano_t': row.get('prodano_t', 0),
                                'nabidka_kc': row.get('nabidka_kc', 0),
                                'castka_kc': row.get('castka_kc', 0),
                                'poznamka': row.get('poznamka', ''),
                                'faktura': row.get('faktura', '')
                            }
                            all_odpisy = pd.concat([all_odpisy, pd.DataFrame([new_record])], ignore_index=True)

                    # Uložit
                    all_odpisy.to_csv(f'{data_manager.data_dir}/odpisy.csv', index=False)
                    data_manager.load_csv('odpisy.csv', force_reload=True)
                    st.success("Změny byly uloženy!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Chyba při ukládání: {e}")

        # === STAŽENÍ PDF FAKTUR ===
        import os
        faktury_dir = os.path.join(data_manager.base_path, 'faktury')
        faktury_list = []
        if 'faktura' in display_df.columns:
            for idx, row in display_df.iterrows():
                faktura_name = row.get('faktura', '')
                if faktura_name and pd.notna(faktura_name) and faktura_name != '':
                    faktura_path = os.path.join(faktury_dir, faktura_name)
                    if os.path.exists(faktura_path):
                        faktury_list.append({
                            'name': faktura_name,
                            'path': faktura_path,
                            'datum': str(row.get('datum_smlouvy', ''))[:10],
                            'poznamka': row.get('poznamka', ''),
                            'castka': row.get('castka_kc', 0)
                        })

        if faktury_list:
            st.markdown("### 📎 Faktury ke stažení")
            for i, f in enumerate(faktury_list):
                col1, col2, col3, col4 = st.columns([2, 3, 2, 2])
                with col1:
                    st.text(f['datum'])
                with col2:
                    st.text(f['poznamka'][:30] + '...' if len(str(f['poznamka'])) > 30 else f['poznamka'])
                with col3:
                    st.text(f"{f['castka']:,.0f} Kč")
                with col4:
                    with open(f['path'], 'rb') as file:
                        st.download_button(
                            label=f"📥 {f['name']}",
                            data=file.read(),
                            file_name=f['name'],
                            mime="application/pdf",
                            key=f"dl_{f['name']}_{i}",
                            use_container_width=True
                        )

        # === TABULKA NABÍDEK PRO ROK ===
        st.markdown("---")
        st.subheader(f"🏷️ Nabídky pro rok {selected_year}")

        # Načíst nabídky
        nabidky_all = data_manager.load_csv('nabidky.csv', force_reload=True)

        if not nabidky_all.empty and 'id' in display_df.columns:
            # Filtrovat nabídky pro aktuální odpisy
            odpis_ids = display_df['id'].tolist()
            nabidky_rok = nabidky_all[nabidky_all['odpis_id'].isin(odpis_ids)].copy()

            if not nabidky_rok.empty:
                # Zajistit správné datové typy
                nabidky_rok['nabidka_kc'] = pd.to_numeric(nabidky_rok['nabidka_kc'], errors='coerce').fillna(0)

                # Přidat info o odpisu (poznámka a finální cena)
                odpis_info = display_df[['id', 'poznamka', 'castka_kc', 'datum_smlouvy']].copy()
                odpis_info.columns = ['odpis_id', 'plodina', 'finalni_cena', 'datum_prodeje']
                nabidky_rok = nabidky_rok.merge(odpis_info, on='odpis_id', how='left')

                # Seřadit podle data
                nabidky_rok = nabidky_rok.sort_values('datum_nabidky', ascending=False)

                # Vybrat sloupce pro zobrazení
                display_nabidky = nabidky_rok[['datum_nabidky', 'plodina', 'odberatel', 'nabidka_kc', 'finalni_cena', 'poznamka']].copy()

                st.dataframe(
                    display_nabidky,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "datum_nabidky": st.column_config.DateColumn("Datum nabídky", format="YYYY-MM-DD"),
                        "plodina": st.column_config.TextColumn("Plodina"),
                        "odberatel": st.column_config.TextColumn("Odběratel"),
                        "nabidka_kc": st.column_config.NumberColumn("Nabídka (Kč)", format="%,.0f"),
                        "finalni_cena": st.column_config.NumberColumn("Finální cena (Kč)", format="%,.0f"),
                        "poznamka": st.column_config.TextColumn("Poznámka"),
                    }
                )

                # Souhrn nabídek
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"Počet nabídek: {len(nabidky_rok)}")
                with col2:
                    st.caption(f"Průměrná nabídka: {nabidky_rok['nabidka_kc'].mean():,.0f} Kč")
                with col3:
                    st.caption(f"Počet odběratelů: {nabidky_rok['odberatel'].nunique()}")
            else:
                st.info("Žádné nabídky pro tento rok")
        else:
            st.info("Žádné nabídky k zobrazení")

        # === HISTORIE NABÍDEK ===
        st.markdown("---")
        st.subheader("📋 Historie nabídek")

        # Načíst nabídky
        nabidky = data_manager.load_csv('nabidky.csv', force_reload=True)

        if not nabidky.empty and 'id' in display_df.columns:
            # Filtrovat nabídky pro aktuální odpisy
            odpis_ids = display_df['id'].tolist()
            nabidky_filtered = nabidky[nabidky['odpis_id'].isin(odpis_ids)]

            if not nabidky_filtered.empty:
                # Zajistit správné datové typy
                nabidky_filtered['nabidka_kc'] = pd.to_numeric(nabidky_filtered['nabidka_kc'], errors='coerce').fillna(0)

                # Zobrazit pro každý odpis
                for _, odpis_row in display_df.iterrows():
                    odpis_id = odpis_row.get('id')
                    odpis_nabidky = nabidky_filtered[nabidky_filtered['odpis_id'] == odpis_id]

                    if not odpis_nabidky.empty:
                        poznamka = odpis_row.get('poznamka', '')
                        datum = str(odpis_row.get('datum_smlouvy', ''))[:10]
                        final_cena = odpis_row.get('castka_kc', 0)

                        with st.expander(f"📊 {poznamka} ({datum}) - Finální cena: {final_cena:,.0f} Kč"):
                            # Seřadit podle data
                            odpis_nabidky_sorted = odpis_nabidky.sort_values('datum_nabidky')

                            for idx, (_, nab) in enumerate(odpis_nabidky_sorted.iterrows()):
                                col1, col2, col3, col4 = st.columns([2, 2, 3, 3])
                                with col1:
                                    st.text(f"{idx + 1}. nabídka")
                                with col2:
                                    st.text(str(nab['datum_nabidky'])[:10])
                                with col3:
                                    st.text(f"{nab['nabidka_kc']:,.0f} Kč")
                                with col4:
                                    st.text(f"{nab['odberatel']} - {nab['poznamka']}")

                            # Zobrazit zlepšení
                            first_offer = odpis_nabidky_sorted.iloc[0]['nabidka_kc']
                            improvement = final_cena - first_offer
                            st.success(f"✅ Vyjednáno navíc: {improvement:+,.0f} Kč (z {first_offer:,.0f} na {final_cena:,.0f} Kč)")
            else:
                st.info("Pro tyto prodeje nejsou zaznamenány žádné nabídky")
        else:
            st.info("Žádné nabídky k zobrazení")

        # Pro export - zobrazit s českými názvy
        display_df_show = display_df[edit_cols].copy()
        col_names = {'datum_smlouvy': 'Datum', 'stav': 'Stav', 'prodano_t': 'Množství (t)', 'nabidka_kc': 'Nabídka (Kč)', 'castka_kc': 'Prodejní cena (Kč)', 'poznamka': 'Poznámka'}
        display_df_show.columns = [col_names.get(c, c) for c in edit_cols]

        # Vypočítat cenu za tunu pro export
        if 'Množství (t)' in display_df_show.columns and 'Prodejní cena (Kč)' in display_df_show.columns:
            display_df_show['Cena/t (Kč)'] = (display_df_show['Prodejní cena (Kč)'] / display_df_show['Množství (t)']).round(0)

        # === TLAČÍTKA PRO EXPORT ===
        st.markdown("---")
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

        # Připravit data pro export
        export_cols = ['datum_smlouvy', 'stav_export', 'prodano_t', 'nabidka_kc', 'castka_kc', 'poznamka']
        export_cols = [c for c in export_cols if c in display_df.columns]
        export_df = display_df[export_cols].copy()
        export_col_names = {'datum_smlouvy': 'Datum', 'stav_export': 'Stav', 'prodano_t': 'Množství (t)', 'nabidka_kc': 'Nabídka (Kč)', 'castka_kc': 'Prodejní cena (Kč)', 'poznamka': 'Poznámka'}
        export_df.columns = [export_col_names.get(c, c) for c in export_cols]
        if 'Prodejní cena (Kč)' in export_df.columns and 'Množství (t)' in export_df.columns:
            export_df['Cena/t (Kč)'] = (export_df['Prodejní cena (Kč)'] / export_df['Množství (t)']).round(0)

        # Přidat souhrn na konec
        souhrn_data = {
            'Datum': 'CELKEM',
            'Stav': '',
            'Množství (t)': export_df['Množství (t)'].sum() if 'Množství (t)' in export_df.columns else 0,
            'Poznámka': ''
        }
        if 'Nabídka (Kč)' in export_df.columns:
            souhrn_data['Nabídka (Kč)'] = export_df['Nabídka (Kč)'].sum()
        if 'Prodejní cena (Kč)' in export_df.columns:
            souhrn_data['Prodejní cena (Kč)'] = export_df['Prodejní cena (Kč)'].sum()
            souhrn_data['Cena/t (Kč)'] = souhrn_data['Prodejní cena (Kč)'] / souhrn_data['Množství (t)'] if souhrn_data['Množství (t)'] > 0 else 0
        souhrn_row = pd.DataFrame([souhrn_data])
        export_df_with_sum = pd.concat([export_df, souhrn_row], ignore_index=True)

        with col1:
            # Export do CSV
            csv_data = export_df_with_sum.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Stáhnout CSV",
                data=csv_data,
                file_name=f"odpisy_{podnik_options[selected_podnik]}_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col2:
            # Export do Excel
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                # Hlavní data
                export_df_with_sum.to_excel(writer, sheet_name='Prodeje', index=False)

                # Souhrn
                souhrn_data = pd.DataFrame([
                    ['Podnik', podnik_options[selected_podnik]],
                    ['Rok', selected_year],
                    ['Produkce (t)', cista_produkce],
                    ['Prodáno (t)', prodano_t],
                    ['Nasmlouváno (t)', nasmlouvano_t],
                    ['Zbývá (t)', zbytek_sklad],
                    ['Vyděláno (Kč)', vydelano_kc],
                    ['Čeká na platbu (Kč)', nasmlouvano_kc],
                    ['Celkem tržby (Kč)', celkem_trzba],
                ], columns=['Ukazatel', 'Hodnota'])
                souhrn_data.to_excel(writer, sheet_name='Souhrn', index=False)

            excel_data = excel_buffer.getvalue()
            st.download_button(
                label="📥 Stáhnout Excel",
                data=excel_data,
                file_name=f"odpisy_{podnik_options[selected_podnik]}_{selected_year}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with col3:
            # Tisk / PDF info
            st.download_button(
                label="🖨️ Tisk (CSV)",
                data=csv_data,
                file_name=f"odpisy_tisk_{podnik_options[selected_podnik]}_{selected_year}.csv",
                mime="text/csv",
                use_container_width=True
            )

        # Souhrn pod tlačítky
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"Počet prodejů: {len(odpisy_filtered)}")
        with col2:
            avg_cena = celkem_trzba / celkem_prodano if celkem_prodano > 0 else 0
            st.caption(f"Průměrná cena: {avg_cena:,.0f} Kč/t")
        with col3:
            procento_prodano = (celkem_prodano / cista_produkce * 100) if cista_produkce > 0 else 0
            st.caption(f"Prodáno: {procento_prodano:.1f}% produkce")

    else:
        st.info(f"Žádné prodeje pro podnik {podnik_options[selected_podnik]} v roce {selected_year}")

    # === PŘENOS Z MINULÉHO ROKU ===
    st.markdown("---")
    with st.expander("📅 Přenos z minulých let"):
        st.markdown("**Zůstatky na skladě z předchozích let:**")

        # Spočítat zůstatky pro všechny roky
        if not fields.empty and 'rok_sklizne' in fields.columns:
            all_years = sorted(fields[fields['podnik_id'] == selected_podnik]['rok_sklizne'].dropna().unique())

            zustatky_data = []
            for year in all_years:
                year_fields = fields[(fields['podnik_id'] == selected_podnik) & (fields['rok_sklizne'] == year)]
                year_produkce = year_fields['cista_vaha'].sum() if 'cista_vaha' in year_fields.columns else 0

                year_odpisy = odpisy[(odpisy['podnik_id'] == selected_podnik) & (odpisy['rok'] == year)] if not odpisy.empty else pd.DataFrame()
                year_prodano = year_odpisy['prodano_t'].sum() if not year_odpisy.empty and 'prodano_t' in year_odpisy.columns else 0

                zustatky_data.append({
                    'Rok': int(year),
                    'Produkce (t)': year_produkce,
                    'Prodáno (t)': year_prodano,
                    'Zůstatek (t)': year_produkce - year_prodano
                })

            if zustatky_data:
                zustatky_df = pd.DataFrame(zustatky_data)
                st.dataframe(
                    zustatky_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Produkce (t)": st.column_config.NumberColumn(format="%.2f"),
                        "Prodáno (t)": st.column_config.NumberColumn(format="%.2f"),
                        "Zůstatek (t)": st.column_config.NumberColumn(format="%.2f")
                    }
                )

                # Celkový zůstatek ze všech let
                celkovy_zustatek = zustatky_df['Zůstatek (t)'].sum()
                st.metric("Celkový zůstatek ze všech let", f"{celkovy_zustatek:.2f} t")
