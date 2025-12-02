"""
Správa odpisů (prodejů ze skladu)
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime


def show(data_manager, user, auth_manager):
    """Zobrazí stránku správy odpisů"""
    st.title("📝 Odpisy (prodeje ze skladu)")
    st.markdown("---")

    # Načtení dat
    businesses = data_manager.get_businesses()
    fields = data_manager.get_fields()
    odpisy = data_manager.get_odpisy()

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
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"💵 Čeká na platbu: {nasmlouvano_kc:,.0f} Kč")
    with col2:
        st.caption(f"📊 Celkem tržby: {celkem_trzba:,.0f} Kč")
    with col3:
        procento = (celkem_prodano / cista_produkce * 100) if cista_produkce > 0 else 0
        st.caption(f"📈 Prodáno: {procento:.1f}% produkce")

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

    # === GRAF: Tržby ===
    if not odpisy_filtered.empty:
        st.subheader("💰 Přehled tržeb")

        col1, col2 = st.columns(2)

        with col1:
            # Graf tržeb podle prodejů
            fig_trzby = px.bar(
                odpisy_filtered.sort_values('datum_smlouvy'),
                x='datum_smlouvy',
                y='castka_kc',
                text='castka_kc',
                title='Tržby podle data',
                labels={'datum_smlouvy': 'Datum', 'castka_kc': 'Částka (Kč)'},
                color='castka_kc',
                color_continuous_scale='Greens'
            )
            fig_trzby.update_traces(texttemplate='%{text:,.0f} Kč', textposition='outside')
            fig_trzby.update_layout(showlegend=False, yaxis=dict(range=[0, odpisy_filtered['castka_kc'].max() * 1.2]))
            st.plotly_chart(fig_trzby, use_container_width=True)

        with col2:
            # Graf ceny za tunu
            odpisy_cena = odpisy_filtered.copy()
            odpisy_cena['cena_t'] = odpisy_cena['castka_kc'] / odpisy_cena['prodano_t']

            fig_cena = px.bar(
                odpisy_cena.sort_values('datum_smlouvy'),
                x='datum_smlouvy',
                y='cena_t',
                text='cena_t',
                title='Cena za tunu (Kč/t)',
                labels={'datum_smlouvy': 'Datum', 'cena_t': 'Cena (Kč/t)'},
                color='cena_t',
                color_continuous_scale='Blues'
            )
            fig_cena.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_cena.update_layout(showlegend=False, yaxis=dict(range=[0, odpisy_cena['cena_t'].max() * 1.2]))
            st.plotly_chart(fig_cena, use_container_width=True)

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
                castka_kc = st.number_input("Částka (Kč)*", min_value=0, step=1000, value=0)
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

    if not odpisy_filtered.empty:
        display_df = odpisy_filtered.copy()

        # Přeložit stav
        stav_map = {'prodano': '✅ Prodáno', 'nasmlouvano': '📝 Nasmlouváno'}
        if 'stav' in display_df.columns:
            display_df['stav'] = display_df['stav'].map(stav_map).fillna(display_df['stav'])

        # Vybrat a přejmenovat sloupce
        display_cols = ['datum_smlouvy', 'stav', 'prodano_t', 'castka_kc', 'poznamka']
        display_cols = [c for c in display_cols if c in display_df.columns]

        display_df = display_df[display_cols].copy()
        col_names = {'datum_smlouvy': 'Datum', 'stav': 'Stav', 'prodano_t': 'Množství (t)', 'castka_kc': 'Částka (Kč)', 'poznamka': 'Poznámka'}
        display_df.columns = [col_names.get(c, c) for c in display_cols]

        # Vypočítat cenu za tunu
        if 'Množství (t)' in display_df.columns and 'Částka (Kč)' in display_df.columns:
            display_df['Cena/t (Kč)'] = (display_df['Částka (Kč)'] / display_df['Množství (t)']).round(0)

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Množství (t)": st.column_config.NumberColumn(format="%.2f"),
                "Částka (Kč)": st.column_config.NumberColumn(format="%d"),
                "Cena/t (Kč)": st.column_config.NumberColumn(format="%d")
            }
        )

        # Souhrn
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
