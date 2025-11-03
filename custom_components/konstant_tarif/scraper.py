import aiohttp
from bs4 import BeautifulSoup
import logging

_LOGGER = logging.getLogger(__name__)

URL = "https://konstant.dk/priser-og-vilkaar/nettarif-abonnement-gebyr-og-tilslutningsbidrag"


async def async_fetch_konstant_tariffs():
    """Scraper aktuelle Konstant-tariffer for kundegruppe C (lavspænding)."""
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as resp:
            html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")
    table_div = soup.find("div", {"data-customergroup": "C"})
    tariffs = {"summer": {}, "winter": {}}

    if not table_div:
        _LOGGER.warning("Kunne ikke finde tarif-tabel på konstant.dk")
        return tariffs

    rows = table_div.find_all("tr")
    season = None

    for row in rows:
        season_cell = row.find("p", class_="seasonP")
        if season_cell:
            s_text = season_cell.get_text(strip=True).lower()
            if "sommer" in s_text:
                season = "summer"
            elif "vinter" in s_text:
                season = "winter"
            continue

        cols = row.find_all("td")
        if len(cols) < 6 or not season:
            continue

        name = cols[0].get_text(strip=True).lower()
        if not any(k in name for k in ["lav", "høj", "spids"]):
            continue

        # "Beløb efter rabat" = sidste kolonne
        amount_td = cols[-1]
        spans = amount_td.find_all("span", class_="tdTarif_price")
        if len(spans) >= 2:
            no_vat = spans[0].get_text(strip=True).replace(",", ".")
            with_vat = spans[1].get_text(strip=True).replace(",", ".")
        else:
            no_vat = with_vat = amount_td.get_text(strip=True).replace(",", ".")

        try:
            tariffs[season][name] = {
                "uden_moms": float(no_vat),
                "med_moms": float(with_vat),
            }
        except ValueError:
            continue

    return tariffs
