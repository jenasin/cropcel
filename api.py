"""
API endpoint pro veřejný přístup k datům
Spuštění: uvicorn api:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
from typing import Optional

# Cesta k datům
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

app = FastAPI(
    title="Tekro Sklizeň API",
    description="Veřejné API pro přístup k zemědělským datům",
    version="1.0.0"
)

# CORS - povolení přístupu ze všech domén
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_csv_as_dict(filename: str) -> list:
    """Načte CSV soubor a vrátí jako seznam slovníků"""
    try:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            # Nahradit NaN a Inf hodnotami None pro JSON kompatibilitu
            df = df.replace([float('inf'), float('-inf')], None)
            # Konverze na Python typy (nahradí numpy NaN za None)
            records = df.to_dict(orient='records')
            # Nahradit NaN v záznamech
            clean_records = []
            for record in records:
                clean_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        clean_record[key] = None
                    else:
                        clean_record[key] = value
                clean_records.append(clean_record)
            return clean_records
        return []
    except Exception as e:
        return [{"error": str(e)}]


@app.get("/")
def root():
    """Hlavní endpoint s informacemi o API"""
    return {
        "name": "Tekro Sklizeň API",
        "version": "1.0.0",
        "endpoints": {
            "/data": "Všechna data v jednom JSON objektu",
            "/data/businesses": "Seznam podniků",
            "/data/crops": "Seznam plodin",
            "/data/fields": "Data o polích a sklizni",
            "/data/pozemky": "Pozemky",
            "/data/varieties_seed": "Odrůdy osiva",
            "/data/sbernamista": "Sběrná místa",
            "/data/sbernasrazky": "Sběrné srážky",
            "/data/typpozemek": "Typy pozemků",
            "/data/roky": "Roky",
            "/data/sumplodiny": "Souhrn plodin",
            "/data/odpisy": "Odpisy (prodeje)"
        }
    }


@app.get("/data")
def get_all_data():
    """Vrátí všechna data jako jeden JSON objekt - pole záznamů"""
    all_records = []

    # Načtení všech datových zdrojů
    datasets = {
        "businesses": "businesses.csv",
        "crops": "crops.csv",
        "fields": "fields.csv",
        "pozemky": "pozemky.csv",
        "varieties_seed": "varieties_seed.csv",
        "sbernamista": "sbernamista.csv",
        "sbernasrazky": "sbernasrazky.csv",
        "typpozemek": "typpozemek.csv",
        "roky": "roky.csv",
        "sumplodiny": "sumplodiny.csv",
        "userpodniky": "userpodniky.csv",
        "odpisy": "odpisy.csv"
    }

    for data_type, filename in datasets.items():
        records = load_csv_as_dict(filename)
        for record in records:
            record["_type"] = data_type
            all_records.append(record)

    return all_records


@app.get("/data/businesses")
def get_businesses():
    """Vrátí seznam podniků"""
    return load_csv_as_dict("businesses.csv")


@app.get("/data/crops")
def get_crops():
    """Vrátí seznam plodin"""
    return load_csv_as_dict("crops.csv")


@app.get("/data/fields")
def get_fields(
    year: Optional[int] = None,
    business_id: Optional[int] = None,
    crop_id: Optional[int] = None
):
    """
    Vrátí data o polích s možností filtrování

    Args:
        year: Filtr podle roku sklizně
        business_id: Filtr podle ID podniku
        crop_id: Filtr podle ID plodiny
    """
    filepath = os.path.join(DATA_DIR, "fields.csv")
    if not os.path.exists(filepath):
        return []

    df = pd.read_csv(filepath)

    if year is not None and 'rok_sklizne' in df.columns:
        df = df[df['rok_sklizne'] == year]

    if business_id is not None and 'podnik_id' in df.columns:
        df = df[df['podnik_id'] == business_id]

    if crop_id is not None and 'plodina_id' in df.columns:
        df = df[df['plodina_id'] == crop_id]

    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient='records')


@app.get("/data/pozemky")
def get_pozemky():
    """Vrátí pozemky"""
    return load_csv_as_dict("pozemky.csv")


@app.get("/data/varieties_seed")
def get_varieties_seed():
    """Vrátí odrůdy osiva"""
    return load_csv_as_dict("varieties_seed.csv")


@app.get("/data/sbernamista")
def get_sbernamista():
    """Vrátí sběrná místa"""
    return load_csv_as_dict("sbernamista.csv")


@app.get("/data/sbernasrazky")
def get_sbernasrazky():
    """Vrátí sběrné srážky"""
    return load_csv_as_dict("sbernasrazky.csv")


@app.get("/data/typpozemek")
def get_typpozemek():
    """Vrátí typy pozemků"""
    return load_csv_as_dict("typpozemek.csv")


@app.get("/data/roky")
def get_roky():
    """Vrátí roky"""
    return load_csv_as_dict("roky.csv")


@app.get("/data/sumplodiny")
def get_sumplodiny():
    """Vrátí souhrn plodin"""
    return load_csv_as_dict("sumplodiny.csv")


@app.get("/data/odpisy")
def get_odpisy(year: Optional[int] = None):
    """
    Vrátí odpisy (prodeje)

    Args:
        year: Filtr podle roku
    """
    filepath = os.path.join(DATA_DIR, "odpisy.csv")
    if not os.path.exists(filepath):
        return []

    df = pd.read_csv(filepath)

    if year is not None and 'rok' in df.columns:
        df = df[df['rok'] == year]

    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient='records')


@app.get("/stats/summary")
def get_summary_stats():
    """Vrátí souhrnné statistiky"""
    fields = load_csv_as_dict("fields.csv")

    if not fields or isinstance(fields, dict):
        return {"error": "No data available"}

    df = pd.DataFrame(fields)

    stats = {
        "total_records": len(df),
        "years": [],
        "total_area_ha": 0,
        "total_production_t": 0
    }

    if 'rok_sklizne' in df.columns:
        stats["years"] = sorted(df['rok_sklizne'].dropna().unique().tolist())

    if 'vymera' in df.columns:
        stats["total_area_ha"] = float(df['vymera'].sum())

    if 'cista_vaha' in df.columns:
        stats["total_production_t"] = float(df['cista_vaha'].sum())

    if stats["total_area_ha"] > 0:
        stats["avg_yield_t_ha"] = round(stats["total_production_t"] / stats["total_area_ha"], 2)
    else:
        stats["avg_yield_t_ha"] = 0

    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
