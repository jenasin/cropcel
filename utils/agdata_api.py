"""
Utilita pro stahování dat z API agdata.cz (meteostanice)
"""
import os
import datetime as dt
import requests

BASE_URL = "https://api.agdata.cz"


def get_api_token():
    """Získá API token z environment variable nebo config souboru"""
    # Nejprve zkusit environment variable
    token = os.environ.get("AGDATA_API_TOKEN")
    if token:
        return token

    # Zkusit načíst z config souboru
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "agdata_token.txt")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return f.read().strip()

    return None


def api_get(path: str, params: dict) -> dict:
    """Provede GET request na API"""
    token = get_api_token()
    if not token:
        raise ValueError("AGDATA_API_TOKEN není nastaven")

    url = f"{BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_daily(sensor_addr: str, date_range: str = "today") -> dict:
    """Stáhne denní agregaci pro zadané období (today/yesterday)"""
    return api_get("/sensors/daily", {"sensorAddr": sensor_addr, "dateRange": date_range})


def fetch_today_daily(sensor_addr: str) -> dict:
    """Stáhne denní agregaci pro dnešek, nebo včerejšek pokud dnešní data nejsou"""
    # Zkusit dnešní data
    payload = api_get("/sensors/daily", {"sensorAddr": sensor_addr, "dateRange": "today"})

    # Pokud dnešní data nejsou k dispozici, zkusit včerejší
    if not payload.get("data"):
        payload = api_get("/sensors/daily", {"sensorAddr": sensor_addr, "dateRange": "yesterday"})

    return payload


def pick_first_day_record(payload: dict) -> dict:
    """Extrahuje první záznam z odpovědi API"""
    data = payload.get("data")
    if isinstance(data, list) and data:
        rec = data[0]
        if isinstance(rec, dict) and "data" in rec and isinstance(rec["data"], dict):
            return rec["data"]
        if isinstance(rec, dict):
            return rec
    return {}


def get_today_rain(sensor_addr: str) -> float | None:
    """Získá dnešní srážky v mm pro danou meteostanici"""
    try:
        payload = fetch_today_daily(sensor_addr)
        metrics = pick_first_day_record(payload)

        # Různé možné názvy pro srážky
        rain = (
            metrics.get("rainVolume")
            or metrics.get("precipitation")
            or metrics.get("precip")
            or metrics.get("rain")
        )

        if rain is not None:
            return float(rain)
        return None
    except Exception as e:
        print(f"Chyba při stahování srážek: {e}")
        return None


def get_today_weather(sensor_addr: str, fallback_yesterday: bool = True) -> dict:
    """Získá kompletní počasí pro danou meteostanici

    Args:
        sensor_addr: Adresa senzoru
        fallback_yesterday: Pokud True, použije včerejší data když dnešní nejsou k dispozici
    """
    try:
        if fallback_yesterday:
            payload = fetch_today_daily(sensor_addr)
        else:
            # Pouze dnešní data bez fallbacku
            payload = fetch_daily(sensor_addr, "today")

        metrics = pick_first_day_record(payload)

        # Extrahovat datum z API response
        data_list = payload.get("data", [])
        api_date = None
        if data_list and isinstance(data_list[0], dict):
            date_str = data_list[0].get("date", "")
            if date_str:
                api_date = date_str[:10]  # "2026-01-05T00:00:00.000Z" -> "2026-01-05"

        # Pokud nejsou data a nechceme fallback, vrátit dnešní datum
        if not api_date and not fallback_yesterday:
            api_date = dt.date.today().isoformat()

        # Různé možné názvy pro srážky
        rain = metrics.get("rainVolume")
        if rain is None:
            rain = metrics.get("precipitation") or metrics.get("precip") or metrics.get("rain")

        # Teplota - API používá temp1
        temp = metrics.get("temp1")
        if temp is None:
            temp = metrics.get("temperature") or metrics.get("temp")

        # Vlhkost - API používá hum1
        hum = metrics.get("hum1")
        if hum is None:
            hum = metrics.get("humidity") or metrics.get("hum")

        return {
            "date": api_date or dt.date.today().isoformat(),
            "rain_mm": float(rain) if rain is not None else None,
            "temp_c": float(temp) if temp is not None else None,
            "humidity_pct": float(hum) if hum is not None else None,
            "raw_metrics": metrics
        }
    except Exception as e:
        return {"error": str(e)}


def get_yesterday_weather(sensor_addr: str) -> dict:
    """Získá včerejší počasí pro danou meteostanici (pro automatické stahování v 5:00)"""
    try:
        payload = fetch_daily(sensor_addr, "yesterday")
        metrics = pick_first_day_record(payload)

        # Extrahovat datum z API response
        data_list = payload.get("data", [])
        api_date = None
        if data_list and isinstance(data_list[0], dict):
            date_str = data_list[0].get("date", "")
            if date_str:
                api_date = date_str[:10]

        # Různé možné názvy pro srážky
        rain = metrics.get("rainVolume")
        if rain is None:
            rain = metrics.get("precipitation") or metrics.get("precip") or metrics.get("rain")

        # Teplota - API používá temp1
        temp = metrics.get("temp1")
        if temp is None:
            temp = metrics.get("temperature") or metrics.get("temp")

        # Vlhkost - API používá hum1
        hum = metrics.get("hum1")
        if hum is None:
            hum = metrics.get("humidity") or metrics.get("hum")

        return {
            "date": api_date,
            "rain_mm": float(rain) if rain is not None else None,
            "temp_c": float(temp) if temp is not None else None,
            "humidity_pct": float(hum) if hum is not None else None,
            "raw_metrics": metrics
        }
    except Exception as e:
        return {"error": str(e)}
