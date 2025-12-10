"""
Modul pro zadávání dat - Pole, Srážky, Pozemky, Odpisy
S implementací RBAC (Role-Based Access Control)
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date


def show(data_manager, user, auth_manager):
    """Vstupní bod pro zobrazení stránky zadávání dat"""
    st.title("📝 Zadávání dat")

    # Načtení dat
    businesses = data_manager.get_businesses()
    fields = data_manager.get_fields()
    crops = data_manager.get_crops()
    varieties = data_manager.get_varieties_seed()
    pozemky = data_manager.get_pozemky()
    typpozemek = data_manager.get_typpozemek()
    sbernasrazky = data_manager.get_sbernasrazky()
    sbernamista = data_manager.get_sbernamista()
    odpisy = data_manager.get_odpisy()
    roky = data_manager.get_roky()

    # Filtrovat podniky podle oprávnění uživatele
    allowed_businesses = auth_manager.get_allowed_podniky(user, businesses)

    if allowed_businesses.empty:
        st.warning("Nemáte přiřazený žádný podnik. Kontaktujte administrátora.")
        return

    # === VÝBĚR PODNIKU ===
    st.markdown("---")
    col1, col2 = st.columns([2, 4])

    with col1:
        podnik_options = {row['id']: row['nazev'] for _, row in allowed_businesses.iterrows()}
        selected_podnik = st.selectbox(
            "**Vyberte podnik:**",
            options=list(podnik_options.keys()),
            format_func=lambda x: podnik_options[x],
            key="zadavani_podnik"
        )

    podnik_name = podnik_options[selected_podnik]

    # Kontrola práv k editaci
    can_edit = auth_manager.can_edit_podnik(user, selected_podnik)

    with col2:
        role_info = {
            'admin': ('🔴 ADMIN', 'Máte plný přístup ke všem funkcím'),
            'editor': ('🟡 EDITOR', f'Můžete editovat podnik {podnik_name}' if can_edit else f'Nemáte oprávnění editovat {podnik_name}'),
            'watcher': ('🟢 VIEWER', 'Máte pouze právo náhledu')
        }
        role_badge, role_desc = role_info.get(user['role'], ('⚪ UNKNOWN', ''))
        st.markdown(f"**Role:** {role_badge}")
        st.caption(role_desc)

    st.markdown("---")

    # === TOOLBAR - POUZE PRO OPRÁVNĚNÉ ===
    if can_edit:
        st.markdown(f"### 🛠️ Akce pro podnik: {podnik_name}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("➕ Přidat pole", use_container_width=True, type="primary"):
                st.session_state.show_form = 'pole'

        with col2:
            if st.button("➕ Přidat pozemek", use_container_width=True):
                st.session_state.show_form = 'pozemek'

        with col3:
            if st.button("➕ Přidat srážky", use_container_width=True):
                st.session_state.show_form = 'srazky'

        with col4:
            if st.button("➕ Přidat odpis", use_container_width=True):
                st.session_state.show_form = 'odpis'

        st.markdown("---")

        # === FORMULÁŘE ===
        if st.session_state.get('show_form') == 'pole':
            show_pole_form(data_manager, selected_podnik, podnik_name, crops, varieties, fields)

        elif st.session_state.get('show_form') == 'pozemek':
            show_pozemek_form(data_manager, selected_podnik, podnik_name, typpozemek, pozemky)

        elif st.session_state.get('show_form') == 'srazky':
            show_srazky_form(data_manager, selected_podnik, podnik_name, sbernamista, sbernasrazky)

        elif st.session_state.get('show_form') == 'odpis':
            show_odpis_form(data_manager, selected_podnik, podnik_name, odpisy)

    else:
        st.info("🔒 Nemáte práva upravovat tento podnik. Kontaktujte administrátora pro přidělení oprávnění.")

    st.markdown("---")

    # === TABULKA DAT ===
    show_data_table(data_manager, selected_podnik, podnik_name, can_edit, fields, crops, varieties, pozemky, typpozemek, sbernasrazky, sbernamista)


def show_pole_form(data_manager, podnik_id, podnik_name, crops, varieties, fields):
    """Formulář pro přidání pole"""
    st.subheader("📋 Nové pole")

    with st.form("add_pole_form"):
        col1, col2 = st.columns(2)

        with col1:
            nazev_honu = st.text_input("Název honu *")
            cislo_honu = st.text_input("Číslo honu")
            vymera = st.number_input("Výměra (ha) *", min_value=0.0, step=0.01)

        with col2:
            rok_sklizne = st.number_input("Rok sklizně *", min_value=2000, max_value=2100, value=datetime.now().year)

            # Plodina
            crop_options = {0: "-- Nevybráno --"}
            if not crops.empty:
                crop_options.update({row['id']: row['nazev'] for _, row in crops.iterrows()})
            selected_crop = st.selectbox("Plodina", options=list(crop_options.keys()), format_func=lambda x: crop_options[x])

            # Odrůda
            variety_options = {0: "-- Nevybráno --"}
            if not varieties.empty:
                variety_options.update({row['id']: row['nazev'] for _, row in varieties.iterrows()})
            selected_variety = st.selectbox("Odrůda", options=list(variety_options.keys()), format_func=lambda x: variety_options[x])

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Uložit pole", use_container_width=True, type="primary")
        with col2:
            cancel = st.form_submit_button("❌ Zrušit", use_container_width=True)

        if submit:
            if not nazev_honu:
                st.error("Vyplňte název honu")
            elif vymera <= 0:
                st.error("Výměra musí být větší než 0")
            else:
                new_field = {
                    'nazev_honu': nazev_honu,
                    'cislo_honu': cislo_honu,
                    'vymera': vymera,
                    'rok_sklizne': int(rok_sklizne),
                    'plodina_id': selected_crop if selected_crop > 0 else None,
                    'odruda_id': selected_variety if selected_variety > 0 else None,
                    'podnik_id': podnik_id,
                    'sklizeno': 0,
                    'cista_vaha': 0,
                    'hruba_vaha': 0,
                    'stmn': '',
                    'datum_seti': '',
                    'datum_vznik': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'operation': 'insert'
                }
                if data_manager.add_record('fields.csv', new_field):
                    st.success(f"Pole '{nazev_honu}' bylo přidáno!")
                    st.session_state.show_form = None
                    st.rerun()
                else:
                    st.error("Chyba při ukládání")

        if cancel:
            st.session_state.show_form = None
            st.rerun()


def show_pozemek_form(data_manager, podnik_id, podnik_name, typpozemek, pozemky):
    """Formulář pro přidání pozemku"""
    st.subheader("🗺️ Nový pozemek")

    with st.form("add_pozemek_form"):
        col1, col2 = st.columns(2)

        with col1:
            rok = st.number_input("Rok *", min_value=2000, max_value=2100, value=datetime.now().year)
            velikost = st.number_input("Velikost (ha) *", min_value=0.0, step=0.01)

        with col2:
            # Typ pozemku
            typ_options = {}
            if not typpozemek.empty:
                typ_options = {row['id']: row['Nazev'] for _, row in typpozemek.iterrows()}
            selected_typ = st.selectbox("Typ pozemku *", options=list(typ_options.keys()), format_func=lambda x: typ_options[x])

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Uložit pozemek", use_container_width=True, type="primary")
        with col2:
            cancel = st.form_submit_button("❌ Zrušit", use_container_width=True)

        if submit:
            if velikost <= 0:
                st.error("Velikost musí být větší než 0")
            else:
                # Najít max ID
                max_id = pozemky['id'].max() if not pozemky.empty else 0
                new_id = int(max_id) + 1

                new_pozemek = {
                    'id': new_id,
                    'PodnikID': podnik_id,
                    'Year': int(rok),
                    'Velikost': velikost,
                    'NazevId': selected_typ
                }
                if data_manager.add_record('pozemky.csv', new_pozemek):
                    st.success(f"Pozemek byl přidán!")
                    st.session_state.show_form = None
                    st.rerun()
                else:
                    st.error("Chyba při ukládání")

        if cancel:
            st.session_state.show_form = None
            st.rerun()


def show_srazky_form(data_manager, podnik_id, podnik_name, sbernamista, sbernasrazky):
    """Formulář pro přidání sběrných srážek"""
    st.subheader("📦 Nové sběrné srážky")

    with st.form("add_srazky_form"):
        col1, col2 = st.columns(2)

        with col1:
            datum = st.date_input("Datum *", value=date.today())
            objem = st.number_input("Objem *", min_value=0.0, step=0.1)

        with col2:
            # Sběrné místo
            misto_options = {}
            if not sbernamista.empty:
                misto_options = {row['id']: row['nazev'] for _, row in sbernamista.iterrows()}
            selected_misto = st.selectbox("Sběrné místo *", options=list(misto_options.keys()), format_func=lambda x: misto_options[x]) if misto_options else None

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Uložit srážky", use_container_width=True, type="primary")
        with col2:
            cancel = st.form_submit_button("❌ Zrušit", use_container_width=True)

        if submit:
            if objem < 0:
                st.error("Objem nemůže být záporný")
            elif not selected_misto:
                st.error("Vyberte sběrné místo")
            else:
                # Najít max ID
                max_id = sbernasrazky['id'].max() if not sbernasrazky.empty else 0
                new_id = int(max_id) + 1

                new_srazka = {
                    'id': new_id,
                    'MistoID': selected_misto,
                    'PodnikID': podnik_id,
                    'Objem': objem,
                    'Datum': datetime.combine(datum, datetime.min.time()).strftime('%Y-%m-%d %H:%M:%S')
                }
                if data_manager.add_record('sbernasrazky.csv', new_srazka):
                    st.success(f"Srážky byly přidány!")
                    st.session_state.show_form = None
                    st.rerun()
                else:
                    st.error("Chyba při ukládání")

        if cancel:
            st.session_state.show_form = None
            st.rerun()


def show_odpis_form(data_manager, podnik_id, podnik_name, odpisy):
    """Formulář pro přidání odpisu (prodeje)"""
    st.subheader("📝 Nový odpis (prodej)")

    with st.form("add_odpis_form"):
        col1, col2 = st.columns(2)

        with col1:
            datum_smlouvy = st.date_input("Datum smlouvy *", value=date.today())
            rok = st.number_input("Rok *", min_value=2000, max_value=2100, value=datetime.now().year)
            prodano_t = st.number_input("Prodané množství (t) *", min_value=0.0, step=0.01)

        with col2:
            castka_kc = st.number_input("Částka (Kč) *", min_value=0, step=1000)
            stav = st.selectbox("Stav *", options=['nasmlouvano', 'prodano'], format_func=lambda x: 'Nasmlouváno' if x == 'nasmlouvano' else 'Prodáno')
            poznamka = st.text_area("Poznámka")

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Uložit odpis", use_container_width=True, type="primary")
        with col2:
            cancel = st.form_submit_button("❌ Zrušit", use_container_width=True)

        if submit:
            if prodano_t <= 0:
                st.error("Množství musí být větší než 0")
            elif castka_kc <= 0:
                st.error("Částka musí být větší než 0")
            else:
                new_odpis = {
                    'podnik_id': podnik_id,
                    'rok': int(rok),
                    'datum_smlouvy': datum_smlouvy.strftime('%Y-%m-%d'),
                    'castka_kc': castka_kc,
                    'prodano_t': prodano_t,
                    'faktura': '',
                    'poznamka': poznamka,
                    'stav': stav
                }
                if data_manager.add_record('odpisy.csv', new_odpis):
                    st.success(f"Odpis byl přidán!")
                    st.session_state.show_form = None
                    st.rerun()
                else:
                    st.error("Chyba při ukládání")

        if cancel:
            st.session_state.show_form = None
            st.rerun()


def show_data_table(data_manager, podnik_id, podnik_name, can_edit, fields, crops, varieties, pozemky, typpozemek, sbernasrazky, sbernamista):
    """Zobrazí tabulku dat s akcemi"""
    st.subheader(f"📊 Data podniku: {podnik_name}")

    # Tabs pro různé typy dat
    tab1, tab2, tab3, tab4 = st.tabs(["🚜 Pole", "🗺️ Pozemky", "📦 Srážky", "📝 Odpisy"])

    with tab1:
        show_fields_table(data_manager, podnik_id, can_edit, fields, crops, varieties)

    with tab2:
        show_pozemky_table(data_manager, podnik_id, can_edit, pozemky, typpozemek)

    with tab3:
        show_srazky_table(data_manager, podnik_id, can_edit, sbernasrazky, sbernamista)

    with tab4:
        show_odpisy_table(data_manager, podnik_id, can_edit)


def show_fields_table(data_manager, podnik_id, can_edit, fields, crops, varieties):
    """Zobrazí tabulku polí"""
    # Filtrovat podle podniku
    podnik_fields = fields[fields['podnik_id'] == podnik_id] if not fields.empty and 'podnik_id' in fields.columns else pd.DataFrame()

    if podnik_fields.empty:
        st.info("Žádná pole pro tento podnik")
        return

    # Výběr roku
    if 'rok_sklizne' in podnik_fields.columns:
        years = sorted(podnik_fields['rok_sklizne'].dropna().unique(), reverse=True)
        if years:
            selected_year = st.selectbox("Rok:", years, key="fields_year")
            podnik_fields = podnik_fields[podnik_fields['rok_sklizne'] == selected_year]

    # Sloučit s názvy plodin a odrůd
    if not crops.empty and 'plodina_id' in podnik_fields.columns:
        podnik_fields = podnik_fields.merge(crops[['id', 'nazev']], left_on='plodina_id', right_on='id', how='left', suffixes=('', '_plodina'))
        podnik_fields['plodina'] = podnik_fields['nazev'].fillna('-')
    else:
        podnik_fields['plodina'] = '-'

    if not varieties.empty and 'odruda_id' in podnik_fields.columns:
        podnik_fields = podnik_fields.merge(varieties[['id', 'nazev']], left_on='odruda_id', right_on='id', how='left', suffixes=('', '_odruda'))
        podnik_fields['odruda'] = podnik_fields['nazev_odruda'].fillna('-') if 'nazev_odruda' in podnik_fields.columns else '-'
    else:
        podnik_fields['odruda'] = '-'

    # Zobrazit tabulku
    for idx, row in podnik_fields.iterrows():
        col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 2])

        with col1:
            st.write(f"**{row.get('nazev_honu', 'Bez názvu')}**")
            st.caption(f"Číslo: {row.get('cislo_honu', '-')}")

        with col2:
            st.write(f"Plodina: {row.get('plodina', '-')}")
            st.write(f"Odrůda: {row.get('odruda', '-')}")

        with col3:
            st.metric("Výměra", f"{row.get('vymera', 0):.2f} ha")

        with col4:
            vynos = row.get('cista_vaha', 0) / row.get('vymera', 1) if row.get('vymera', 0) > 0 else 0
            st.metric("Výnos", f"{vynos:.2f} t/ha")

        with col5:
            if can_edit:
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("📋", key=f"dup_field_{row['id']}", help="Duplikovat"):
                        st.info("Funkce duplikace")
                with c2:
                    if st.button("✏️", key=f"edit_field_{row['id']}", help="Editovat"):
                        st.info("Funkce editace")
                with c3:
                    if st.button("🗑️", key=f"del_field_{row['id']}", help="Smazat"):
                        st.warning("Funkce smazání")
            else:
                st.caption("Jen čtení")

        st.markdown("---")


def show_pozemky_table(data_manager, podnik_id, can_edit, pozemky, typpozemek):
    """Zobrazí tabulku pozemků"""
    podnik_pozemky = pozemky[pozemky['PodnikID'] == podnik_id] if not pozemky.empty else pd.DataFrame()

    if podnik_pozemky.empty:
        st.info("Žádné pozemky pro tento podnik")
        return

    # Výběr roku
    if 'Year' in podnik_pozemky.columns:
        years = sorted(podnik_pozemky['Year'].dropna().unique(), reverse=True)
        if years:
            selected_year = st.selectbox("Rok:", years, key="pozemky_year")
            podnik_pozemky = podnik_pozemky[podnik_pozemky['Year'] == selected_year]

    # Sloučit s názvy typů
    if not typpozemek.empty:
        podnik_pozemky = podnik_pozemky.merge(typpozemek[['id', 'Nazev']], left_on='NazevId', right_on='id', how='left', suffixes=('', '_typ'))
        podnik_pozemky['typ'] = podnik_pozemky['Nazev'].fillna('-')
    else:
        podnik_pozemky['typ'] = '-'

    # Zobrazit tabulku
    for idx, row in podnik_pozemky.iterrows():
        col1, col2, col3 = st.columns([2, 2, 2])

        with col1:
            st.write(f"**{row.get('typ', 'Neznámý typ')}**")

        with col2:
            st.metric("Velikost", f"{row.get('Velikost', 0):.2f} ha")

        with col3:
            if can_edit:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✏️", key=f"edit_poz_{row['id']}", help="Editovat"):
                        st.info("Funkce editace")
                with c2:
                    if st.button("🗑️", key=f"del_poz_{row['id']}", help="Smazat"):
                        st.warning("Funkce smazání")
            else:
                st.caption("Jen čtení")

        st.markdown("---")


def show_srazky_table(data_manager, podnik_id, can_edit, sbernasrazky, sbernamista):
    """Zobrazí tabulku srážek"""
    podnik_srazky = sbernasrazky[sbernasrazky['PodnikID'] == podnik_id] if not sbernasrazky.empty else pd.DataFrame()

    if podnik_srazky.empty:
        st.info("Žádné srážky pro tento podnik")
        return

    # Sloučit s názvy míst
    if not sbernamista.empty:
        podnik_srazky = podnik_srazky.merge(sbernamista[['id', 'nazev']], left_on='MistoID', right_on='id', how='left', suffixes=('', '_misto'))
        podnik_srazky['misto'] = podnik_srazky['nazev'].fillna('-')
    else:
        podnik_srazky['misto'] = '-'

    # Seřadit podle data
    if 'Datum' in podnik_srazky.columns:
        podnik_srazky = podnik_srazky.sort_values('Datum', ascending=False)

    # Zobrazit posledních 20
    for idx, row in podnik_srazky.head(20).iterrows():
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

        with col1:
            datum = pd.to_datetime(row.get('Datum', ''), errors='coerce')
            st.write(f"**{datum.strftime('%Y-%m-%d') if pd.notna(datum) else '-'}**")

        with col2:
            st.write(f"Místo: {row.get('misto', '-')}")

        with col3:
            st.metric("Objem", f"{row.get('Objem', 0):.1f}")

        with col4:
            if can_edit:
                if st.button("🗑️", key=f"del_sraz_{row['id']}", help="Smazat"):
                    st.warning("Funkce smazání")
            else:
                st.caption("-")

        st.markdown("---")


def show_odpisy_table(data_manager, podnik_id, can_edit):
    """Zobrazí tabulku odpisů"""
    odpisy = data_manager.get_odpisy()
    podnik_odpisy = odpisy[odpisy['podnik_id'] == podnik_id] if not odpisy.empty and 'podnik_id' in odpisy.columns else pd.DataFrame()

    if podnik_odpisy.empty:
        st.info("Žádné odpisy pro tento podnik")
        return

    # Seřadit podle data
    if 'datum_smlouvy' in podnik_odpisy.columns:
        podnik_odpisy = podnik_odpisy.sort_values('datum_smlouvy', ascending=False)

    stav_map = {'prodano': 'Prodáno', 'nasmlouvano': 'Nasmlouváno'}

    for idx, row in podnik_odpisy.iterrows():
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

        with col1:
            st.write(f"**{row.get('datum_smlouvy', '-')}**")
            st.caption(f"Rok: {row.get('rok', '-')}")

        with col2:
            st.write(f"{stav_map.get(row.get('stav', ''), row.get('stav', '-'))}")

        with col3:
            st.metric("Množství", f"{row.get('prodano_t', 0):.2f} t")

        with col4:
            st.metric("Částka", f"{row.get('castka_kc', 0):,.0f} Kč")

        with col5:
            if can_edit:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✏️", key=f"edit_odp_{row.get('id', idx)}", help="Editovat"):
                        st.info("Funkce editace")
                with c2:
                    if st.button("🗑️", key=f"del_odp_{row.get('id', idx)}", help="Smazat"):
                        st.warning("Funkce smazání")
            else:
                st.caption("-")

        st.markdown("---")
