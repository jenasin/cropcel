"""
Modul pro zobrazení přehledu podniků
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def show(data_manager, user, auth_manager=None):
    """Vstupní bod pro zobrazení stránky"""
    # Získání podniků uživatele
    user_businesses = []
    if user['role'] != 'admin':
        userpodniky = data_manager.get_userpodniky()
        user_businesses = userpodniky[userpodniky['user_id'] == user['id']]['podnik_id'].tolist()

    render(data_manager, user_businesses)


def render(data_manager, user_businesses):
    """Vykreslí stránku s přehledem podniku"""
    st.header("Přehled podniku")

    # Načtení dat
    businesses = data_manager.get_businesses()
    pozemky = data_manager.get_pozemky()
    typpozemek = data_manager.get_typpozemek()
    fields = data_manager.get_fields()
    crops = data_manager.get_crops()
    sbernasrazky = data_manager.get_sbernasrazky()
    sbernamista = data_manager.get_sbernamista()

    if businesses.empty:
        st.warning("Nejsou k dispozici žádné podniky.")
        return

    # Filtrování podniků podle oprávnění
    if user_businesses:
        businesses = businesses[businesses['id'].isin(user_businesses)]

    # Výběr podniku
    podnik_options = {row['id']: row['nazev'] for _, row in businesses.iterrows()}

    if not podnik_options:
        st.warning("Nemáte přístup k žádným podnikům.")
        return

    selected_podnik = st.selectbox(
        "Vyberte podnik",
        options=list(podnik_options.keys()),
        format_func=lambda x: podnik_options[x]
    )

    podnik_name = podnik_options[selected_podnik]
    st.subheader(f"Podnik: {podnik_name}")

    # Výběr roku - z pozemků a polí
    available_years = []
    if not pozemky.empty and 'Year' in pozemky.columns:
        pozemky_years = pozemky[pozemky['PodnikID'] == selected_podnik]['Year'].dropna().unique()
        available_years.extend(pozemky_years)
    if not fields.empty and 'rok_sklizne' in fields.columns:
        fields_years = fields[fields['podnik_id'] == selected_podnik]['rok_sklizne'].dropna().unique()
        available_years.extend(fields_years)

    available_years = sorted(set([int(y) for y in available_years if pd.notna(y)]))

    if not available_years:
        st.warning("Pro vybraný podnik nejsou k dispozici žádná data.")
        return

    selected_year = st.selectbox("Vyberte rok", available_years, index=len(available_years)-1)

    st.divider()

    # ==================== SEKCE 1: PŮDA ====================
    st.subheader(f"Půda - {selected_year}")

    # Filtrovat pozemky pro vybraný podnik a rok
    podnik_pozemky = pozemky[(pozemky['PodnikID'] == selected_podnik) & (pozemky['Year'] == selected_year)]

    if not podnik_pozemky.empty and not typpozemek.empty:
        # Sloučit s názvy typů pozemků
        podnik_pozemky = podnik_pozemky.merge(
            typpozemek[['id', 'Nazev']],
            left_on='NazevId',
            right_on='id',
            how='left',
            suffixes=('', '_typ')
        )
        podnik_pozemky['typ_nazev'] = podnik_pozemky['Nazev'].fillna('Neznámý')

        # Agregace podle typů půdy
        puda_stats = podnik_pozemky.groupby('typ_nazev').agg({
            'Velikost': 'sum'
        }).reset_index()
        puda_stats.columns = ['Typ půdy', 'Výměra (ha)']
        puda_stats = puda_stats.sort_values('Výměra (ha)', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Přehled půdy**")
            puda_stats_display = puda_stats.copy()
            puda_stats_display['Výměra (ha)'] = puda_stats_display['Výměra (ha)'].round(2)
            st.dataframe(puda_stats_display, use_container_width=True, hide_index=True)

            # Celková výměra
            total_area = puda_stats['Výměra (ha)'].sum()
            st.metric("Celková výměra", f"{total_area:.2f} ha")

        with col2:
            # Koláčový graf
            if not puda_stats.empty:
                fig = px.pie(
                    puda_stats,
                    values='Výměra (ha)',
                    names='Typ půdy',
                    title='Struktura půdy'
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pro tento podnik a rok nejsou k dispozici data o půdě.")

    st.divider()

    # ==================== SEKCE 2: SUMÁRNÍ LIST PLODIN ====================
    st.subheader(f"Sumární list plodin - {selected_year}")

    # Filtrovat pole pro vybraný podnik a rok
    podnik_fields = fields[(fields['podnik_id'] == selected_podnik) & (fields['rok_sklizne'] == selected_year)]

    if not podnik_fields.empty and not crops.empty:
        # Sloučit s názvy plodin
        podnik_fields = podnik_fields.merge(
            crops[['id', 'nazev']],
            left_on='plodina_id',
            right_on='id',
            how='left',
            suffixes=('', '_plodina')
        )
        podnik_fields['plodina_nazev'] = podnik_fields['nazev'].fillna('Neznámá')

        # Agregace podle plodin
        plodiny_stats = podnik_fields.groupby('plodina_nazev').agg({
            'cista_vaha': 'sum',
            'vymera': 'sum'
        }).reset_index()
        plodiny_stats.columns = ['Plodina', 'Čistá váha (t)', 'Výměra (ha)']
        plodiny_stats['Výnos (t/ha)'] = plodiny_stats['Čistá váha (t)'] / plodiny_stats['Výměra (ha)']
        plodiny_stats = plodiny_stats.sort_values('Čistá váha (t)', ascending=False)

        # Tabulka
        st.markdown("**Přehled plodin**")
        plodiny_stats_display = plodiny_stats.copy()
        plodiny_stats_display['Čistá váha (t)'] = plodiny_stats_display['Čistá váha (t)'].round(2)
        plodiny_stats_display['Výměra (ha)'] = plodiny_stats_display['Výměra (ha)'].round(2)
        plodiny_stats_display['Výnos (t/ha)'] = plodiny_stats_display['Výnos (t/ha)'].round(2)
        st.dataframe(plodiny_stats_display, use_container_width=True, hide_index=True)

        # Metriky
        col1, col2, col3 = st.columns(3)
        total_production = plodiny_stats['Čistá váha (t)'].sum()
        total_area = plodiny_stats['Výměra (ha)'].sum()
        avg_yield = total_production / total_area if total_area > 0 else 0

        with col1:
            st.metric("Celková produkce", f"{total_production:.2f} t")
        with col2:
            st.metric("Celková výměra", f"{total_area:.2f} ha")
        with col3:
            st.metric("Průměrný výnos", f"{avg_yield:.2f} t/ha")

        st.divider()

        # ==================== SEKCE 3: GRAF ČISTÉ PRODUKCE ====================
        st.subheader(f"Čistá produkce plodin - {selected_year}")

        # Sloupcový graf přes celou šířku
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=plodiny_stats['Plodina'],
            y=plodiny_stats['Čistá váha (t)'],
            marker_color='#2E86AB',
            text=plodiny_stats['Čistá váha (t)'].round(1),
            textposition='outside'
        ))
        max_val = plodiny_stats['Čistá váha (t)'].max() if not plodiny_stats.empty else 1
        fig.update_layout(
            title=f'Čistá produkce plodin - {podnik_name} ({selected_year})',
            xaxis_title='Plodina',
            yaxis_title='Čistá váha (t)',
            yaxis=dict(range=[0, max_val * 1.15]) if max_val > 0 else None,
            xaxis_tickangle=-45,
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Pro tento podnik a rok nejsou k dispozici data o plodinách.")

    st.divider()

    # ==================== SEKCE 4: SBĚRNÉ SRÁŽKY ====================
    st.subheader("Sběrné srážky - všechny podniky")

    # Načíst všechny podniky znovu (bez filtrování)
    all_businesses = data_manager.get_businesses()

    if not sbernasrazky.empty and not all_businesses.empty:
        # Sloučit srážky s podniky
        srazky_with_podnik = sbernasrazky.merge(
            all_businesses[['id', 'nazev']],
            left_on='PodnikID',
            right_on='id',
            how='left',
            suffixes=('', '_podnik')
        )
        srazky_with_podnik['podnik_nazev'] = srazky_with_podnik['nazev'].fillna('Neznámý')

        # Extrahovat rok z datumu
        srazky_with_podnik['Datum'] = pd.to_datetime(srazky_with_podnik['Datum'], errors='coerce')
        srazky_with_podnik['rok'] = srazky_with_podnik['Datum'].dt.year

        # Filtrovat podle vybraného roku
        srazky_rok = srazky_with_podnik[srazky_with_podnik['rok'] == selected_year]

        if not srazky_rok.empty:
            # Agregace podle podniků
            srazky_stats = srazky_rok.groupby('podnik_nazev').agg({
                'Objem': 'sum'
            }).reset_index()
            srazky_stats.columns = ['Podnik', 'Celkový objem srážek']
            srazky_stats = srazky_stats.sort_values('Celkový objem srážek', ascending=False)

            # Sloupcový graf přes celou šířku
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=srazky_stats['Podnik'],
                y=srazky_stats['Celkový objem srážek'],
                marker_color='#C73E1D',
                text=srazky_stats['Celkový objem srážek'].round(1),
                textposition='outside'
            ))
            max_val = srazky_stats['Celkový objem srážek'].max() if not srazky_stats.empty else 1
            fig.update_layout(
                title=f'Sběrné srážky podle podniků ({selected_year})',
                xaxis_title='Podnik',
                yaxis_title='Celkový objem srážek',
                yaxis=dict(range=[0, max_val * 1.15]) if max_val > 0 else None,
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)

            # Tabulka
            st.markdown("**Přehled srážek**")
            srazky_stats_display = srazky_stats.copy()
            srazky_stats_display['Celkový objem srážek'] = srazky_stats_display['Celkový objem srážek'].round(2)
            st.dataframe(srazky_stats_display, use_container_width=True, hide_index=True)
        else:
            st.info(f"Pro rok {selected_year} nejsou k dispozici žádné sběrné srážky.")
    else:
        st.info("Nejsou k dispozici data o sběrných srážkách.")
