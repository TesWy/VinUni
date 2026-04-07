import unicodedata
from datetime import datetime
from typing import Any

import requests

from langchain_core.tools import tool

from observability import get_logger, write_trace


FLIGHTS_DB = {
    ("Ha Noi", "Da Nang"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "07:20", "price": 1450000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "14:00", "arrival": "15:20", "price": 2800000, "class": "business"},
        {"airline": "VietJet Air", "departure": "08:30", "arrival": "09:50", "price": 890000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "11:00", "arrival": "12:20", "price": 1200000, "class": "economy"},
    ],
    ("Ha Noi", "Phu Quoc"): [
        {"airline": "Vietnam Airlines", "departure": "07:00", "arrival": "09:15", "price": 2100000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "10:00", "arrival": "12:15", "price": 1350000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "16:00", "arrival": "18:15", "price": 1100000, "class": "economy"},
    ],
    ("Ha Noi", "Ho Chi Minh"): [
        {"airline": "Vietnam Airlines", "departure": "06:00", "arrival": "08:10", "price": 1600000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "07:30", "arrival": "09:40", "price": 950000, "class": "economy"},
        {"airline": "Bamboo Airways", "departure": "12:00", "arrival": "14:10", "price": 1300000, "class": "economy"},
        {"airline": "Vietnam Airlines", "departure": "18:00", "arrival": "20:10", "price": 3200000, "class": "business"},
    ],
    ("Ho Chi Minh", "Da Nang"): [
        {"airline": "Vietnam Airlines", "departure": "09:00", "arrival": "10:20", "price": 1300000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "13:00", "arrival": "14:20", "price": 780000, "class": "economy"},
    ],
    ("Ho Chi Minh", "Phu Quoc"): [
        {"airline": "Vietnam Airlines", "departure": "08:00", "arrival": "09:00", "price": 1100000, "class": "economy"},
        {"airline": "VietJet Air", "departure": "15:00", "arrival": "16:00", "price": 650000, "class": "economy"},
    ],
}

HOTELS_DB = {
    "Da Nang": [
        {"name": "Muong Thanh Luxury", "stars": 5, "price_per_night": 1800000, "area": "My Khe", "rating": 4.5},
        {"name": "Sala Danang Beach", "stars": 4, "price_per_night": 1200000, "area": "My Khe", "rating": 4.3},
        {"name": "Fivitel Danang", "stars": 3, "price_per_night": 650000, "area": "Son Tra", "rating": 4.1},
        {"name": "Memory Hostel", "stars": 2, "price_per_night": 250000, "area": "Hai Chau", "rating": 4.6},
        {"name": "Christina's Homestay", "stars": 2, "price_per_night": 350000, "area": "An Thuong", "rating": 4.7},
    ],
    "Phu Quoc": [
        {"name": "Vinpearl Resort", "stars": 5, "price_per_night": 3500000, "area": "Bai Dai", "rating": 4.4},
        {"name": "Sol by Melia", "stars": 4, "price_per_night": 1500000, "area": "Bai Truong", "rating": 4.2},
        {"name": "Lahana Resort", "stars": 3, "price_per_night": 800000, "area": "Duong Dong", "rating": 4.0},
        {"name": "9Station Hostel", "stars": 2, "price_per_night": 200000, "area": "Duong Dong", "rating": 4.5},
    ],
    "Ho Chi Minh": [
        {"name": "Rex Hotel", "stars": 5, "price_per_night": 2800000, "area": "Quan 1", "rating": 4.3},
        {"name": "Liberty Central", "stars": 4, "price_per_night": 1400000, "area": "Quan 1", "rating": 4.1},
        {"name": "Cochin Zen Hotel", "stars": 3, "price_per_night": 550000, "area": "Quan 3", "rating": 4.4},
        {"name": "The Common Room", "stars": 2, "price_per_night": 180000, "area": "Quan 1", "rating": 4.6},
    ],
}

LOGGER = get_logger("travelbuddy.tools")
CITY_ALIASES = {
    "ha noi": "Ha Noi",
    "hanoi": "Ha Noi",
    "da nang": "Da Nang",
    "danang": "Da Nang",
    "phu quoc": "Phu Quoc",
    "phuquoc": "Phu Quoc",
    "ho chi minh": "Ho Chi Minh",
    "hcm": "Ho Chi Minh",
    "hcmc": "Ho Chi Minh",
    "tp hcm": "Ho Chi Minh",
    "sai gon": "Ho Chi Minh",
    "saigon": "Ho Chi Minh",
}
FRANKFURTER_V2_URL = "https://api.frankfurter.dev/v2/rates"
FRANKFURTER_V1_URL = "https://api.frankfurter.dev/v1/latest"
WEATHER_CODE_MAP = {
    0: "Troi quang",
    1: "Chu yeu quang",
    2: "Co may",
    3: "Am u",
    45: "Suong mu",
    48: "Suong mu dong bang",
    51: "Mua phun nhe",
    53: "Mua phun vua",
    55: "Mua phun nang",
    61: "Mua nhe",
    63: "Mua vua",
    65: "Mua to",
    71: "Tuyet nhe",
    73: "Tuyet vua",
    75: "Tuyet day",
    80: "Mua rao nhe",
    81: "Mua rao vua",
    82: "Mua rao to",
    95: "Dong set",
    96: "Dong set co mua da",
    99: "Dong set, mua da manh",
}


def _fmt_vnd(value: int) -> str:
    return f"{value:,}".replace(",", ".") + "d"


def _strip_accents(text: str) -> str:
    text = text.replace("Ä", "D").replace("Ä‘", "d")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _normalize_key(text: str) -> str:
    compact = " ".join(_strip_accents(text).lower().strip().split())
    return compact


def _canonical_city(text: str) -> str:
    key = _normalize_key(text)
    if key in CITY_ALIASES:
        return CITY_ALIASES[key]
    return " ".join(word.capitalize() for word in key.split())


def _normalize_flight_key(origin: str, destination: str) -> tuple[str, str]:
    return (_canonical_city(origin), _canonical_city(destination))


def _parse_vnd_number(text: str) -> int:
    cleaned = text.lower().strip()
    for token in ("vnđ", "vnd", "đ", "d"):
        cleaned = cleaned.replace(token, "")
    cleaned = cleaned.replace(".", "").replace("_", "").replace(" ", "")
    if not cleaned.isdigit():
        raise ValueError
    return int(cleaned)


def _response_error(response: requests.Response) -> str:
    try:
        body = response.text.strip()
    except Exception:
        body = "<no body>"
    return f"status={response.status_code}, body={body[:200]}"


def _round_rate(rate: float) -> float:
    if abs(rate) < 0.001:
        return round(rate, 10)
    return round(rate, 6)


def _fetch_frankfurter_v2_row(from_currency: str, to_currency: str) -> dict[str, Any]:
    response = requests.get(
        FRANKFURTER_V2_URL,
        params={"base": from_currency, "quotes": to_currency},
        timeout=8,
    )
    if not response.ok:
        return {}
    payload = response.json()
    if isinstance(payload, list) and payload:
        return payload[0]
    return {}


@tool
def search_flights(origin: str, destination: str) -> str:
    """
    Dung khi can lay danh sach chuyen bay hien co giua hai thanh pho.

    Args:
        origin: Thanh pho khoi hanh, co the nhap co dau hoac khong dau.
        destination: Thanh pho diem den, co the nhap co dau hoac khong dau.

    Returns:
        Danh sach chuyen bay theo tung hang bay, gio bay, hang ghe va gia.
        Neu khong co chieu di truc tiep nhung co chieu nguoc lai, tool se bao ro.

    Cach dung:
    - Neu user chi muon xem cac chuyen bay hien co, goi tool nay va liet ke day du.
    - Neu user muon goi y chuyen bay phu hop, van goi tool nay roi tu so sanh
      trong phan tra loi cuoi cung: ve re nhat, ve bay som, ve cao cap, ve hop budget.
    - Neu user co nhac den budget hoac hang ghe, agent tu suy luan tren danh sach
      tra ve thay vi can tool khac.
    """
    origin_norm, destination_norm = _normalize_flight_key(origin, destination)
    LOGGER.info(
        "search_flights called | origin=%s | destination=%s | normalized_origin=%s | normalized_destination=%s",
        origin,
        destination,
        origin_norm,
        destination_norm,
    )

    direct_key = (origin_norm, destination_norm)
    reverse_key = (destination_norm, origin_norm)

    flights = FLIGHTS_DB.get(direct_key)
    if flights:
        LOGGER.info("search_flights direct hit | key=%s | count=%s", direct_key, len(flights))
        lines = [f"Cac chuyen bay tu {origin_norm} den {destination_norm}:"]
        for idx, flight in enumerate(flights, start=1):
            lines.append(
                f"{idx}. {flight['airline']} | {flight['departure']} - {flight['arrival']} | "
                f"{flight['class']} | {_fmt_vnd(flight['price'])}"
            )
        result = "\n".join(lines)
        write_trace(
            "tool.search_flights",
            {
                "origin": origin,
                "destination": destination,
                "normalized_origin": origin_norm,
                "normalized_destination": destination_norm,
                "mode": "direct",
                "result_count": len(flights),
            },
        )
        return result

    reverse_flights = FLIGHTS_DB.get(reverse_key)
    if reverse_flights:
        LOGGER.info("search_flights reverse hit | key=%s | count=%s", reverse_key, len(reverse_flights))
        lines = [f"Khong tim thay chuyen bay truc tiep tu {origin_norm} den {destination_norm}."]
        lines.append(f"Tuy nhien co chuyen nguoc lai tu {destination_norm} den {origin_norm}:")
        for idx, flight in enumerate(reverse_flights, start=1):
            lines.append(
                f"{idx}. {flight['airline']} | {flight['departure']} - {flight['arrival']} | "
                f"{flight['class']} | {_fmt_vnd(flight['price'])}"
            )
        result = "\n".join(lines)
        write_trace(
            "tool.search_flights",
            {
                "origin": origin,
                "destination": destination,
                "normalized_origin": origin_norm,
                "normalized_destination": destination_norm,
                "mode": "reverse",
                "result_count": len(reverse_flights),
            },
        )
        return result

    LOGGER.warning("search_flights not found | direct_key=%s | reverse_key=%s", direct_key, reverse_key)
    write_trace(
        "tool.search_flights",
        {
            "origin": origin,
            "destination": destination,
            "normalized_origin": origin_norm,
            "normalized_destination": destination_norm,
            "mode": "not_found",
            "result_count": 0,
        },
    )
    return f"Khong tim thay chuyen bay tu {origin_norm} den {destination_norm}."


def search_hotels(city: str, max_price_per_night: int = 99999999) -> str:
    """
    Dung khi can tim khach san tai mot thanh pho va loc theo ngan sach moi dem.

    Args:
        city: Thanh pho can tim khach san.
        max_price_per_night: Gia toi da cho moi dem. De mac dinh neu user chua dua budget.

    Returns:
        Danh sach khach san phu hop, da sap xep theo rating giam dan, gom ten,
        so sao, gia moi dem, khu vuc va rating.
    """
    city_norm = _canonical_city(city)
    LOGGER.info(
        "search_hotels called | city=%s | normalized_city=%s | max_price=%s",
        city,
        city_norm,
        max_price_per_night,
    )
    hotels = HOTELS_DB.get(city_norm)
    if not hotels:
        LOGGER.warning("search_hotels city not found | city=%s", city_norm)
        write_trace(
            "tool.search_hotels",
            {"city": city, "normalized_city": city_norm, "max_price_per_night": max_price_per_night, "result_count": 0},
        )
        return f"Khong tim thay du lieu khach san tai {city_norm}."

    filtered = [hotel for hotel in hotels if hotel["price_per_night"] <= max_price_per_night]
    if not filtered:
        LOGGER.info("search_hotels no hotels in budget | city=%s | max_price=%s", city_norm, max_price_per_night)
        write_trace(
            "tool.search_hotels",
            {"city": city, "normalized_city": city_norm, "max_price_per_night": max_price_per_night, "result_count": 0},
        )
        return f"Khong tim thay khach san tai {city_norm} voi gia duoi {_fmt_vnd(max_price_per_night)}/dem."

    filtered.sort(key=lambda item: item["rating"], reverse=True)
    LOGGER.info("search_hotels success | city=%s | result_count=%s", city_norm, len(filtered))
    lines = [f"Danh sach khach san tai {city_norm} (gia <= {_fmt_vnd(max_price_per_night)}/dem):"]
    for idx, hotel in enumerate(filtered, start=1):
        lines.append(
            f"{idx}. {hotel['name']} | {hotel['stars']} sao | {_fmt_vnd(hotel['price_per_night'])}/dem | "
            f"{hotel['area']} | rating {hotel['rating']}"
        )
    write_trace(
        "tool.search_hotels",
        {
            "city": city,
            "normalized_city": city_norm,
            "max_price_per_night": max_price_per_night,
            "result_count": len(filtered),
        },
    )
    return "\n".join(lines)


@tool
def calculate_budget(total_budget: int, expenses: str) -> str:
    """
    Dung khi can tinh tong chi phi va ngan sach con lai cho chuyen di.

    Args:
        total_budget: Tong budget cua user theo VND.
        expenses: Chuoi cac khoan chi phi theo dang
            've_may_bay:890000,khach_san:650000,an_uong:500000'

    Returns:
        Bang chi tiet tung khoan, tong chi, ngan sach va phan con lai
        hoac canh bao vuot budget.

    Chi goi tool nay khi da co so tien cu the. Khong goi neu chi moi co mo ta
    chung chung ma chua co gia tu cac tool khac hoac tu user.
    """
    LOGGER.info("calculate_budget called | total_budget=%s | expenses_raw=%s", total_budget, expenses)
    if total_budget < 0:
        LOGGER.warning("calculate_budget invalid total_budget | total_budget=%s", total_budget)
        return "Tong ngan sach phai la so duong."

    if not expenses or not expenses.strip():
        return (
            "Bang chi tiet:\n"
            "---\n"
            f"Tong chi: {_fmt_vnd(0)}\n"
            f"Ngan sach: {_fmt_vnd(total_budget)}\n"
            f"Con lai: {_fmt_vnd(total_budget)}"
        )

    parsed = []
    for raw_item in expenses.split(","):
        item = raw_item.strip()
        if not item:
            continue
        if ":" not in item:
            LOGGER.warning("calculate_budget invalid format | item=%s", item)
            return f"Dinh dang khong hop le: '{item}'. Dung mau 'ten_khoan:so_tien'."
        name, value_text = item.split(":", 1)
        name = name.strip()
        value_text = value_text.strip()
        if not name or not value_text:
            LOGGER.warning("calculate_budget invalid pair | item=%s", item)
            return f"Dinh dang khong hop le: '{item}'. Dung mau 'ten_khoan:so_tien'."
        try:
            amount = _parse_vnd_number(value_text)
        except ValueError:
            LOGGER.warning("calculate_budget invalid amount | item=%s", item)
            return f"So tien khong hop le trong khoan '{item}'."
        parsed.append((name, amount))

    total_expenses = sum(amount for _, amount in parsed)
    remaining = total_budget - total_expenses

    lines = ["Bang chi tiet:"]
    for name, amount in parsed:
        lines.append(f"- {name}: {_fmt_vnd(amount)}")
    lines.append("---")
    lines.append(f"Tong chi: {_fmt_vnd(total_expenses)}")
    lines.append(f"Ngan sach: {_fmt_vnd(total_budget)}")
    if remaining >= 0:
        lines.append(f"Con lai: {_fmt_vnd(remaining)}")
    else:
        lines.append(f"Vuot ngan sach {_fmt_vnd(abs(remaining))}! Can dieu chinh.")
    LOGGER.info(
        "calculate_budget computed | total_expenses=%s | remaining=%s | item_count=%s",
        total_expenses,
        remaining,
        len(parsed),
    )
    write_trace(
        "tool.calculate_budget",
        {
            "total_budget": total_budget,
            "total_expenses": total_expenses,
            "remaining": remaining,
            "item_count": len(parsed),
        },
    )
    return "\n".join(lines)


@tool
def get_weather(city: str) -> str:
    """
    Dung khi user hoi thoi tiet hien tai tai mot thanh pho hoac diem den.

    Args:
        city: Ten thanh pho can kiem tra thoi tiet.

    Returns:
        Nhiet do, toc do gio, tinh trang thoi tiet va thoi diem cap nhat.

    Khong dung tool nay cho du bao nhieu ngay toi neu user khong chi can
    thoi tiet hien tai.
    """
    city_query = city.strip()
    if not city_query:
        return "Vui long nhap ten thanh pho de kiem tra thoi tiet."

    LOGGER.info("get_weather called | city=%s", city_query)
    try:
        geo_response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city_query, "count": 1, "language": "en", "format": "json"},
            timeout=8,
        )
        if not geo_response.ok:
            err = _response_error(geo_response)
            LOGGER.warning("get_weather geocode failed | city=%s | error=%s", city_query, err)
            write_trace(
                "tool.get_weather.error",
                {"city": city_query, "stage": "geocoding", "error": err},
            )
            return f"Khong the lay thoi tiet luc nay (loi geocoding: {err})."

        geo_payload = geo_response.json()
        results = geo_payload.get("results") or []
        if not results:
            LOGGER.warning("get_weather no geocode result | city=%s", city_query)
            write_trace(
                "tool.get_weather.error",
                {"city": city_query, "stage": "geocoding", "error": "no_results"},
            )
            return f"Khong tim thay thanh pho '{city_query}'."

        location = results[0]
        lat = location["latitude"]
        lon = location["longitude"]
        resolved_name = location.get("name", city_query)
        country = location.get("country", "")

        weather_response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "timezone": "auto",
            },
            timeout=8,
        )
        if not weather_response.ok:
            err = _response_error(weather_response)
            LOGGER.warning("get_weather forecast failed | city=%s | error=%s", city_query, err)
            write_trace(
                "tool.get_weather.error",
                {"city": city_query, "stage": "forecast", "error": err},
            )
            return f"Khong the lay thoi tiet luc nay (loi forecast: {err})."

        weather_payload = weather_response.json()
        current = weather_payload.get("current_weather")
        if not current:
            LOGGER.warning("get_weather empty current_weather | city=%s", city_query)
            write_trace(
                "tool.get_weather.error",
                {"city": city_query, "stage": "forecast", "error": "empty_current_weather"},
            )
            return "Khong nhan duoc du lieu thoi tiet hien tai."

        temp = current.get("temperature")
        wind = current.get("windspeed")
        weather_code = current.get("weathercode")
        weather_desc = WEATHER_CODE_MAP.get(weather_code, f"Ma thoi tiet {weather_code}")
        observed_time = current.get("time")

        result = (
            f"Thoi tiet hien tai tai {resolved_name}"
            f"{', ' + country if country else ''}:\n"
            f"- Nhiet do: {temp}Â°C\n"
            f"- Gio: {wind} km/h\n"
            f"- Tinh trang: {weather_desc}\n"
            f"- Thoi diem cap nhat: {observed_time}"
        )
        write_trace(
            "tool.get_weather",
            {
                "city": city_query,
                "resolved_name": resolved_name,
                "country": country,
                "temperature_c": temp,
                "windspeed_kmh": wind,
                "weathercode": weather_code,
            },
        )
        return result
    except requests.RequestException as exc:
        LOGGER.warning("get_weather request exception | city=%s | error=%s", city_query, exc)
        write_trace(
            "tool.get_weather.error",
            {"city": city_query, "stage": "network", "error": str(exc)},
        )
        return f"Khong the lay thoi tiet luc nay (network error: {exc})."
    except Exception as exc:
        LOGGER.exception("get_weather unexpected error | city=%s", city_query)
        write_trace(
            "tool.get_weather.error",
            {"city": city_query, "stage": "unexpected", "error": str(exc)},
        )
        return f"Khong the lay thoi tiet luc nay (error: {exc})."


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Dung khi can quy doi tien te giua hai don vi, vi du VND sang USD.

    Args:
        amount: So tien can doi.
        from_currency: Ma tien te nguon, vi du VND, USD, EUR.
        to_currency: Ma tien te dich.

    Returns:
        So tien sau quy doi, ty gia, nguon ty gia va thoi diem lay du lieu.

    Khong dung tool nay de tinh budget tong chuyen di neu tat ca chi phi da
    o cung mot don vi; khi do dung calculate_budget.
    """
    try:
        amount_val = float(amount)
    except (TypeError, ValueError):
        return "amount phai la so."

    source = str(from_currency or "").upper().strip()
    target = str(to_currency or "").upper().strip()
    if not source or not target:
        write_trace(
            "tool.convert_currency.error",
            {"amount": amount, "from": from_currency, "to": to_currency, "error": "missing_currency"},
        )
        return "Can nhap day du from_currency va to_currency."
    if amount_val < 0:
        write_trace(
            "tool.convert_currency.error",
            {"amount": amount_val, "from": source, "to": target, "error": "negative_amount"},
        )
        return "amount phai >= 0."
    if source == target:
        return (
            f"{amount_val:.2f} {source} = {amount_val:.2f} {target}\n"
            f"Ty gia: 1.0\n"
            f"Nguon: identity\n"
            f"Thoi diem: {datetime.utcnow().isoformat()}"
        )

    LOGGER.info(
        "convert_currency called | amount=%s | from=%s | to=%s",
        amount_val,
        source,
        target,
    )
    try:
        v2_row = _fetch_frankfurter_v2_row(source, target)
        if v2_row:
            direct_rate = float(v2_row["rate"])
            timestamp = v2_row.get("date", datetime.utcnow().date().isoformat())
            source_name = "frankfurter_v2"

            if direct_rate < 0.001:
                reverse_row = _fetch_frankfurter_v2_row(target, source)
                if reverse_row and float(reverse_row["rate"]) > 1:
                    direct_rate = 1 / float(reverse_row["rate"])
                    timestamp = reverse_row.get("date", timestamp)
                    source_name = "frankfurter_v2_inverse"

            converted = round(amount_val * direct_rate, 2)
            rounded_rate = _round_rate(direct_rate)
            result = (
                f"{amount_val:.2f} {source} = {converted:.2f} {target}\n"
                f"Ty gia: {rounded_rate}\n"
                f"Nguon: {source_name}\n"
                f"Thoi diem: {timestamp}"
            )
            write_trace(
                "tool.convert_currency",
                {
                    "amount": amount_val,
                    "from": source,
                    "to": target,
                    "rate": rounded_rate,
                    "converted": converted,
                    "source": source_name,
                    "timestamp": timestamp,
                },
            )
            return result

        v2_response = requests.get(
            FRANKFURTER_V2_URL,
            params={"base": source, "quotes": target},
            timeout=8,
        )
        v2_error = _response_error(v2_response)

        v1_response = requests.get(
            FRANKFURTER_V1_URL,
            params={"base": source, "symbols": target},
            timeout=8,
        )
        if v1_response.ok:
            v1_payload = v1_response.json()
            rates = v1_payload.get("rates", {})
            if target in rates:
                rate = float(rates[target])
                converted = round(amount_val * rate, 2)
                rounded_rate = _round_rate(rate)
                timestamp = v1_payload.get("date", datetime.utcnow().date().isoformat())
                result = (
                    f"{amount_val:.2f} {source} = {converted:.2f} {target}\n"
                    f"Ty gia: {rounded_rate}\n"
                    f"Nguon: frankfurter_v1\n"
                    f"Thoi diem: {timestamp}"
                )
                write_trace(
                    "tool.convert_currency",
                    {
                        "amount": amount_val,
                        "from": source,
                        "to": target,
                        "rate": rounded_rate,
                        "converted": converted,
                        "source": "frankfurter_v1",
                        "timestamp": timestamp,
                    },
                )
                return result

        v1_error = _response_error(v1_response)
        LOGGER.warning(
            "convert_currency api failed | amount=%s | from=%s | to=%s | v2=%s | v1=%s",
            amount_val,
            source,
            target,
            v2_error,
            v1_error,
        )
        write_trace(
            "tool.convert_currency.error",
            {
                "amount": amount_val,
                "from": source,
                "to": target,
                "stage": "api",
                "v2_error": v2_error,
                "v1_error": v1_error,
            },
        )
        return f"Khong the chuyen doi tien te luc nay. v2={v2_error}; v1={v1_error}"
    except requests.RequestException as exc:
        LOGGER.warning("convert_currency network exception | from=%s | to=%s | error=%s", source, target, exc)
        write_trace(
            "tool.convert_currency.error",
            {"amount": amount_val, "from": source, "to": target, "stage": "network", "error": str(exc)},
        )
        return f"Khong the chuyen doi tien te luc nay (network error: {exc})."
    except Exception as exc:
        LOGGER.exception("convert_currency unexpected error | from=%s | to=%s", source, target)
        write_trace(
            "tool.convert_currency.error",
            {"amount": amount_val, "from": source, "to": target, "stage": "unexpected", "error": str(exc)},
        )
        return f"Khong the chuyen doi tien te luc nay (error: {exc})."


