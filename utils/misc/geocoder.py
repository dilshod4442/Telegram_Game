import logging
import aiohttp
from typing import Optional

logger = logging.getLogger(__name__)


async def reverse_geocode(lat: float, lon: float) -> str:
    """
    Преобразует координаты (широта, долгота) в понятный адрес или город
    с использованием бесплатного API OpenStreetMap Nominatim.
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "jsonv2",
        "lat": lat,
        "lon": lon,
        "accept-language": "ru",
        "zoom": 14,
    }
    headers = {
        "User-Agent": "TelegramRegistrationBot/1.0 (contact: info@example.com)"
    }

    try:
        timeout = aiohttp.ClientTimeout(total=4)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    address = data.get("address", {})
                    
                    # Пытаемся сформировать краткий и понятный адрес
                    city = (
                        address.get("city")
                        or address.get("town")
                        or address.get("village")
                        or address.get("suburb")
                        or address.get("county")
                    )
                    state = address.get("state")
                    country = address.get("country")
                    
                    parts = []
                    if city:
                        parts.append(city)
                    elif state:
                        parts.append(state)
                        
                    if country and country not in parts:
                        parts.append(country)
                        
                    if parts:
                        return ", ".join(parts)
                    
                    # Если отдельные части не распознаны, берем display_name
                    display_name = data.get("display_name")
                    if display_name:
                        return display_name.split(",")[0]
                        
    except Exception as exc:
        logger.warning(f"Ошибка геокодирования ({lat}, {lon}): {exc}")

    # Надежный запасной вариант при отсутствии связи
    return f"{lat:.4f}, {lon:.4f}"
