"""
Modul pro zobrazení ročních statistik
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def show(data_manager, user, auth_manager=None):
    """Vstupní bod pro zobrazení stránky"""
    # Získání podniků uživatele
    user_businesses = []
    if user['role'] != 'admin':
        userpodniky = data_manager.get_userpodniky()
        user_businesses = userpodniky[userpodniky['user_id'] == user['id']]['podnik_id'].tolist()

    render(data_manager, user_businesses)


def render(data_manager, user_businesses):
    """Vykreslí stránku se statistikami"""
    st.header("Roční statistiky")

    # Načtení dat
    fields = data_manager.get_fields()
    crops = data_manager.get_crops()
    businesses = data_manager.get_businesses()
    varieties = data_manager.get_varieties_seed()
    odpisy = data_manager.get_odpisy()

    # Filtrování podle podniků uživatele
    if user_businesses:
        fields = data_manager.filter_by_business(fields, user_businesses)
        odpisy = data_manager.filter_by_business(odpisy, user_businesses)

    if fields.empty:
        st.warning("Nejsou k dispozici žádná data pro zobrazení statistik.")
        return

    # Kontrola struktury dat - rok_sklizne nebo roky jako sloupce
    if 'rok_sklizne' in fields.columns:
        # Nová struktura - rok_sklizne jako sloupec
        fields['rok_sklizne'] = pd.to_numeric(fields['rok_sklizne'], errors='coerce')
        available_years = sorted(fields['rok_sklizne'].dropna().unique().astype(int).tolist())
    else:
        # Stará struktura - roky jako sloupce
        year_cols = [col for col in fields.columns if col.isdigit()]
        available_years = sorted([int(y) for y in year_cols])

    if not available_years:
        st.warning("Nejsou k dispozici žádné roky pro statistiky.")
        return

    # Výběr roku pro detailní statistiky
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_year = st.selectbox("Vyberte rok", available_years, index=len(available_years)-1)

    # ==================== SEKCE 1: PŘEHLED PO LETECH ====================
    st.subheader("Vývoj v letech")

    # Připrav data pro roční přehled
    yearly_stats = []
    for year in available_years:
        if 'rok_sklizne' in fields.columns:
            year_data = fields[fields['rok_sklizne'] == year]
            total_area = year_data['vymera'].sum() if 'vymera' in year_data.columns else 0
            total_production = year_data['cista_vaha'].sum() if 'cista_vaha' in year_data.columns else 0
        else:
            year_str = str(year)
            year_data = fields[fields[year_str].notna() & (fields[year_str] > 0)]
            total_area = year_data['vymera'].sum() if 'vymera' in year_data.columns else 0
            total_production = year_data[year_str].sum()

        avg_yield = total_production / total_area if total_area > 0 else 0

        # Odpisy pro daný rok
        year_odpisy = odpisy[odpisy['rok'] == year] if not odpisy.empty else pd.DataFrame()
        total_sold = year_odpisy[year_odpisy['stav'] == 'prodano']['prodano_t'].sum() if not year_odpisy.empty else 0
        total_revenue = year_odpisy[year_odpisy['stav'] == 'prodano']['castka_kc'].sum() if not year_odpisy.empty else 0

        yearly_stats.append({
            'Rok': str(year),
            'Výměra (ha)': total_area,
            'Produkce (t)': total_production,
            'Průměrný výnos (t/ha)': avg_yield,
            'Prodáno (t)': total_sold,
            'Tržby (Kč)': total_revenue
        })

    if yearly_stats:
        yearly_df = pd.DataFrame(yearly_stats)

        # Graf vývoje produkce a výměry
        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=yearly_df['Rok'],
                y=yearly_df['Produkce (t)'],
                name='Produkce (t)',
                marker_color='#2E86AB',
                text=yearly_df['Produkce (t)'].round(1),
                textposition='outside'
            ))
            max_val = yearly_df['Produkce (t)'].max()
            fig.update_layout(
                title='Celková produkce v letech',
                xaxis_title='Rok',
                yaxis_title='Produkce (t)',
                yaxis=dict(range=[0, max_val * 1.15]) if max_val > 0 else None
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=yearly_df['Rok'],
                y=yearly_df['Výměra (ha)'],
                name='Výměra (ha)',
                marker_color='#A23B72',
                text=yearly_df['Výměra (ha)'].round(1),
                textposition='outside'
            ))
            max_val = yearly_df['Výměra (ha)'].max()
            fig.update_layout(
                title='Celková výměra v letech',
                xaxis_title='Rok',
                yaxis_title='Výměra (ha)',
                yaxis=dict(range=[0, max_val * 1.15]) if max_val > 0 else None
            )
            st.plotly_chart(fig, use_container_width=True)

        # Graf vývoje výnosu a tržeb
        col1, col2 = st.columns(2)

        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=yearly_df['Rok'],
                y=yearly_df['Průměrný výnos (t/ha)'],
                name='Průměrný výnos',
                marker_color='#F18F01',
                text=yearly_df['Průměrný výnos (t/ha)'].round(2),
                textposition='outside'
            ))
            max_val = yearly_df['Průměrný výnos (t/ha)'].max()
            fig.update_layout(
                title='Průměrný výnos v letech',
                xaxis_title='Rok',
                yaxis_title='Výnos (t/ha)',
                yaxis=dict(range=[0, max_val * 1.15]) if max_val > 0 else None
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=yearly_df['Rok'],
                y=yearly_df['Tržby (Kč)'] / 1000000,
                name='Tržby',
                marker_color='#C73E1D',
                text=(yearly_df['Tržby (Kč)'] / 1000000).round(2),
                textposition='outside'
            ))
            max_val = (yearly_df['Tržby (Kč)'] / 1000000).max() if yearly_df['Tržby (Kč)'].max() > 0 else 1
            fig.update_layout(
                title='Tržby v letech',
                xaxis_title='Rok',
                yaxis_title='Tržby (mil. Kč)',
                yaxis=dict(range=[0, max_val * 1.15]) if max_val > 0 else None
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ==================== SEKCE 2: STATISTIKY PLODIN ====================
    st.subheader(f"Statistiky plodin pro rok {selected_year}")

    # Data pro vybraný rok
    if 'rok_sklizne' in fields.columns:
        year_fields = fields[fields['rok_sklizne'] == selected_year].copy()
        production_col = 'cista_vaha'
    else:
        year_str = str(selected_year)
        year_fields = fields[fields[year_str].notna() & (fields[year_str] > 0)].copy()
        production_col = year_str

    if not year_fields.empty and 'plodina_id' in year_fields.columns:
        # Sloučení s názvy plodin
        if not crops.empty:
            year_fields = year_fields.merge(crops[['id', 'nazev']], left_on='plodina_id', right_on='id', how='left', suffixes=('', '_plodina'))
            year_fields['plodina_nazev'] = year_fields['nazev'].fillna('Neznámá')
        else:
            year_fields['plodina_nazev'] = 'Neznámá'

        # Agregace podle plodin
        crop_stats = year_fields.groupby('plodina_nazev').agg({
            'vymera': 'sum',
            production_col: 'sum'
        }).reset_index()
        crop_stats.columns = ['Plodina', 'Výměra (ha)', 'Produkce (t)']
        crop_stats['Výnos (t/ha)'] = crop_stats['Produkce (t)'] / crop_stats['Výměra (ha)']
        crop_stats = crop_stats.sort_values('Produkce (t)', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            # Graf produkce podle plodin
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=crop_stats['Plodina'],
                y=crop_stats['Produkce (t)'],
                marker_color='#2E86AB',
                text=crop_stats['Produkce (t)'].round(1),
                textposition='outside'
            ))
            max_val = crop_stats['Produkce (t)'].max()
            fig.update_layout(
                title='Produkce podle plodin',
                xaxis_title='Plodina',
                yaxis_title='Produkce (t)',
                yaxis=dict(range=[0, max_val * 1.15]) if max_val > 0 else None
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Koláčový graf podílu plodin
            fig = px.pie(
                crop_stats,
                values='Produkce (t)',
                names='Plodina',
                title='Podíl plodin na produkci'
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ==================== SEKCE 3: STATISTIKY ODRŮD ====================
    st.subheader(f"Statistiky odrůd pro rok {selected_year}")

    if not year_fields.empty and 'odruda_id' in year_fields.columns and not varieties.empty:
        # Sloučení s názvy odrůd
        year_fields_var = year_fields.merge(
            varieties[['id', 'nazev']],
            left_on='odruda_id',
            right_on='id',
            how='left',
            suffixes=('', '_odruda')
        )
        year_fields_var['odruda_nazev'] = year_fields_var['nazev_odruda'].fillna('Neznámá') if 'nazev_odruda' in year_fields_var.columns else 'Neznámá'

        # Agregace podle odrůd
        variety_stats = year_fields_var.groupby('odruda_nazev').agg({
            'vymera': 'sum',
            production_col: 'sum'
        }).reset_index()
        variety_stats.columns = ['Odrůda', 'Výměra (ha)', 'Produkce (t)']
        variety_stats['Výnos (t/ha)'] = variety_stats['Produkce (t)'] / variety_stats['Výměra (ha)']
        variety_stats = variety_stats.sort_values('Produkce (t)', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            # Všechny odrůdy podle produkce
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=variety_stats['Odrůda'],
                y=variety_stats['Produkce (t)'],
                marker_color='#A23B72',
                text=variety_stats['Produkce (t)'].round(1),
                textposition='outside'
            ))
            max_val = variety_stats['Produkce (t)'].max() if not variety_stats.empty else 1
            fig.update_layout(
                title='Odrůdy podle produkce',
                xaxis_title='Odrůda',
                yaxis_title='Produkce (t)',
                yaxis=dict(range=[0, max_val * 1.15]) if max_val > 0 else None,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Všechny odrůdy podle výnosu
            variety_stats_by_yield = variety_stats.sort_values('Výnos (t/ha)', ascending=False)
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=variety_stats_by_yield['Odrůda'],
                y=variety_stats_by_yield['Výnos (t/ha)'],
                marker_color='#F18F01',
                text=variety_stats_by_yield['Výnos (t/ha)'].round(2),
                textposition='outside'
            ))
            max_val = variety_stats_by_yield['Výnos (t/ha)'].max() if not variety_stats_by_yield.empty else 1
            fig.update_layout(
                title='Odrůdy podle výnosu',
                xaxis_title='Odrůda',
                yaxis_title='Výnos (t/ha)',
                yaxis=dict(range=[0, max_val * 1.15]) if max_val > 0 else None,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ==================== SEKCE 4: STATISTIKY PODNIKŮ ====================
    st.subheader(f"Statistiky podniků pro rok {selected_year}")

    if not year_fields.empty and 'podnik_id' in year_fields.columns and not businesses.empty:
        # Sloučení s názvy podniků
        year_fields_bus = year_fields.merge(
            businesses[['id', 'nazev']],
            left_on='podnik_id',
            right_on='id',
            how='left',
            suffixes=('', '_podnik')
        )
        year_fields_bus['podnik_nazev'] = year_fields_bus['nazev_podnik'].fillna('Neznámý') if 'nazev_podnik' in year_fields_bus.columns else 'Neznámý'

        # Agregace podle podniků
        business_stats = year_fields_bus.groupby('podnik_nazev').agg({
            'vymera': 'sum',
            production_col: 'sum'
        }).reset_index()
        business_stats.columns = ['Podnik', 'Výměra (ha)', 'Produkce (t)']
        business_stats['Výnos (t/ha)'] = business_stats['Produkce (t)'] / business_stats['Výměra (ha)']
        business_stats = business_stats.sort_values('Produkce (t)', ascending=False)

        col1, col2 = st.columns(2)

        with col1:
            # Graf produkce podle podniků
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=business_stats['Podnik'],
                y=business_stats['Produkce (t)'],
                marker_color='#2E86AB',
                text=business_stats['Produkce (t)'].round(1),
                textposition='outside'
            ))
            max_val = business_stats['Produkce (t)'].max() if not business_stats.empty else 1
            fig.update_layout(
                title='Produkce podle podniků',
                xaxis_title='Podnik',
                yaxis_title='Produkce (t)',
                yaxis=dict(range=[0, max_val * 1.15]) if max_val > 0 else None
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Koláčový graf podílu podniků
            fig = px.pie(
                business_stats,
                values='Produkce (t)',
                names='Podnik',
                title='Podíl podniků na produkci'
            )
            st.plotly_chart(fig, use_container_width=True)

        # Graf výnosů podle podniků
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=business_stats['Podnik'],
            y=business_stats['Výnos (t/ha)'],
            marker_color='#C73E1D',
            text=business_stats['Výnos (t/ha)'].round(2),
            textposition='outside'
        ))
        max_val = business_stats['Výnos (t/ha)'].max() if not business_stats.empty else 1
        fig.update_layout(
            title='Výnosy podle podniků',
            xaxis_title='Podnik',
            yaxis_title='Výnos (t/ha)',
            yaxis=dict(range=[0, max_val * 1.15]) if max_val > 0 else None
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ==================== SEKCE 5: ŽEBŘÍČKY ====================
    st.subheader(f"Žebříčky pro rok {selected_year}")

    col1, col2, col3 = st.columns(3)

    # Příprava názvu pole
    if 'nazev_honu' in year_fields.columns:
        year_fields['nazev_pole'] = year_fields['nazev_honu'].fillna('Pole ' + year_fields['id'].astype(str))
    elif 'nazev_pole' not in year_fields.columns:
        year_fields['nazev_pole'] = 'Pole ' + year_fields['id'].astype(str)

    with col1:
        st.markdown("**Pole podle produkce**")
        if not year_fields.empty:
            all_fields_prod = year_fields.sort_values(production_col, ascending=False)[['nazev_pole', 'vymera', production_col]]
            all_fields_prod.columns = ['Pole', 'Výměra (ha)', 'Produkce (t)']
            all_fields_prod['Produkce (t)'] = all_fields_prod['Produkce (t)'].round(1)
            st.dataframe(all_fields_prod, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**Pole podle výnosu**")
        if not year_fields.empty:
            year_fields['vynos_temp'] = year_fields[production_col] / year_fields['vymera']
            all_yield_fields = year_fields.sort_values('vynos_temp', ascending=False)[['nazev_pole', 'vymera', 'vynos_temp']]
            all_yield_fields.columns = ['Pole', 'Výměra (ha)', 'Výnos (t/ha)']
            all_yield_fields['Výnos (t/ha)'] = all_yield_fields['Výnos (t/ha)'].round(2)
            st.dataframe(all_yield_fields, use_container_width=True, hide_index=True)

    with col3:
        st.markdown("**Plodiny podle výnosu**")
        if 'crop_stats' in dir() and not crop_stats.empty:
            all_crop_yield = crop_stats.sort_values('Výnos (t/ha)', ascending=False)[['Plodina', 'Výnos (t/ha)']]
            all_crop_yield['Výnos (t/ha)'] = all_crop_yield['Výnos (t/ha)'].round(2)
            st.dataframe(all_crop_yield, use_container_width=True, hide_index=True)

    st.divider()

    # ==================== SEKCE 5.5: DOPORUČENÉ ODRŮDY PODLE PODNIKŮ ====================
    st.subheader(f"Doporučené odrůdy podle podniků pro rok {selected_year}")

    if not year_fields.empty and 'podnik_id' in year_fields.columns and 'odruda_id' in year_fields.columns and not varieties.empty and not businesses.empty:
        # Připrav kompletní data s názvy
        analysis_df = year_fields.copy()

        # Přidej názvy podniků
        analysis_df = analysis_df.merge(
            businesses[['id', 'nazev']],
            left_on='podnik_id',
            right_on='id',
            how='left',
            suffixes=('', '_podnik')
        )
        analysis_df['podnik_nazev'] = analysis_df['nazev'].fillna('Neznámý')

        # Přidej názvy odrůd
        analysis_df = analysis_df.merge(
            varieties[['id', 'nazev']],
            left_on='odruda_id',
            right_on='id',
            how='left',
            suffixes=('', '_odruda')
        )
        analysis_df['odruda_nazev'] = analysis_df['nazev_odruda'].fillna('Neznámá') if 'nazev_odruda' in analysis_df.columns else 'Neznámá'

        # Přidej názvy plodin (pokud ještě nejsou)
        if 'plodina_nazev' not in analysis_df.columns:
            analysis_df = analysis_df.merge(
                crops[['id', 'nazev']],
                left_on='plodina_id',
                right_on='id',
                how='left',
                suffixes=('', '_plodina')
            )
            analysis_df['plodina_nazev'] = analysis_df['nazev_plodina'].fillna('Neznámá') if 'nazev_plodina' in analysis_df.columns else 'Neznámá'

        # Vypočítej výnos
        analysis_df['vynos'] = analysis_df[production_col] / analysis_df['vymera']

        # Pro každý podnik zobraz nejlepší odrůdy
        unique_businesses = analysis_df['podnik_nazev'].unique()

        for podnik in unique_businesses:
            st.markdown(f"### {podnik}")

            podnik_data = analysis_df[analysis_df['podnik_nazev'] == podnik]

            # Agregace podle plodiny a odrůdy
            podnik_stats = podnik_data.groupby(['plodina_nazev', 'odruda_nazev']).agg({
                'vymera': 'sum',
                production_col: 'sum'
            }).reset_index()
            podnik_stats['Výnos (t/ha)'] = podnik_stats[production_col] / podnik_stats['vymera']
            podnik_stats = podnik_stats.sort_values('Výnos (t/ha)', ascending=False)

            # Všechny odrůdy pro každou plodinu
            unique_crops = podnik_stats['plodina_nazev'].unique()

            recommendations = []
            for plodina in unique_crops:
                plodina_data = podnik_stats[podnik_stats['plodina_nazev'] == plodina]
                for _, row in plodina_data.iterrows():
                    recommendations.append({
                        'Plodina': row['plodina_nazev'],
                        'Odrůda': row['odruda_nazev'],
                        'Výnos (t/ha)': round(row['Výnos (t/ha)'], 2),
                        'Výměra (ha)': round(row['vymera'], 1),
                        'Produkce (t)': round(row[production_col], 1)
                    })

            if recommendations:
                rec_df = pd.DataFrame(recommendations)
                st.dataframe(rec_df, use_container_width=True, hide_index=True)

                # Graf všech odrůd pro tento podnik
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=[f"{row['odruda_nazev']}<br>({row['plodina_nazev']})" for _, row in podnik_stats.iterrows()],
                    y=podnik_stats['Výnos (t/ha)'],
                    marker_color='#2E86AB',
                    text=podnik_stats['Výnos (t/ha)'].round(2),
                    textposition='outside'
                ))
                max_val = podnik_stats['Výnos (t/ha)'].max()
                fig.update_layout(
                    title=f'Nejvýnosnější odrůdy - {podnik}',
                    xaxis_title='Odrůda (Plodina)',
                    yaxis_title='Výnos (t/ha)',
                    yaxis=dict(range=[0, max_val * 1.15]) if max_val > 0 else None,
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")

    st.divider()

    # ==================== SEKCE 6: BILANCE V LETECH ====================
    st.subheader("Bilance v letech")

    if not odpisy.empty and yearly_stats:
        # Připrav data pro bilanci
        bilance_data = []
        for stat in yearly_stats:
            rok = stat['Rok']
            produkce = stat['Produkce (t)']
            prodano = stat['Prodáno (t)']
            zbyvajici = produkce - prodano
            bilance_data.append({
                'Rok': rok,
                'Produkce': produkce,
                'Prodáno': prodano,
                'Zbývá': max(0, zbyvajici)
            })

        bilance_df = pd.DataFrame(bilance_data)

        # Stacked bar chart pro bilanci
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=bilance_df['Rok'],
            y=bilance_df['Prodáno'],
            name='Prodáno',
            marker_color='#2E86AB',
            text=bilance_df['Prodáno'].round(1),
            textposition='inside'
        ))
        fig.add_trace(go.Bar(
            x=bilance_df['Rok'],
            y=bilance_df['Zbývá'],
            name='Zbývá',
            marker_color='#F18F01',
            text=bilance_df['Zbývá'].round(1),
            textposition='inside'
        ))
        fig.update_layout(
            title='Bilance produkce a prodejů v letech',
            xaxis_title='Rok',
            yaxis_title='Množství (t)',
            barmode='stack',
            legend=dict(orientation='h', yanchor='bottom', y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Tabulka bilance
        st.markdown("**Přehled bilance**")
        bilance_df['Produkce'] = bilance_df['Produkce'].round(1)
        bilance_df['Prodáno'] = bilance_df['Prodáno'].round(1)
        bilance_df['Zbývá'] = bilance_df['Zbývá'].round(1)
        st.dataframe(bilance_df, use_container_width=True, hide_index=True)
