from datetime import datetime, timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.util import dt as dt_util
from homeassistant.helpers.event import async_track_time_interval
from .scraper import async_fetch_konstant_tariffs
from .const import CONF_INCLUDE_VAT, CONF_USE_DISCOUNTED


class KonstantTarifSensor(SensorEntity):
    _attr_name = "Konstant Tarif"
    _attr_unit_of_measurement = "kr/kWh"

    def __init__(self, hass, entry, tariffs):
        self.hass = hass
        self.entry = entry
        self._tariffs = tariffs
        self._include_vat = entry.data.get(CONF_INCLUDE_VAT, True)
        self._use_discounted = entry.data.get(CONF_USE_DISCOUNTED, True)
        self._attr_native_value = None
        self._raw_today = []
        self._raw_tomorrow = []

    async def async_update(self):
        now = dt_util.now()
        self._attr_native_value = round(self._get_tariff(now), 4)
        self._raw_today = self._generate_tariff_series(now.date())
        self._raw_tomorrow = self._generate_tariff_series((now + timedelta(days=1)).date())

    def _get_tariff(self, dt: datetime) -> float:
        m = dt.month
        h = dt.hour
        season = "winter" if m in (10, 11, 12, 1, 2, 3) else "summer"
        if 0 <= h < 6:
            zone = "lav"
        elif 6 <= h < 17:
            zone = "høj"
        elif 17 <= h < 21:
            zone = "spids"
        else:
            zone = "høj"
        key_vat = "med_moms" if self._include_vat else "uden_moms"
        val = self._tariffs.get(season, {}).get(zone, {}).get(key_vat, 0)
        return val / 100.0

    def _generate_tariff_series(self, date):
        out = []
        base = datetime.combine(date, datetime.min.time()).astimezone(dt_util.DEFAULT_TIME_ZONE)
        for i in range(96):  # 96 * 15 min = 24h
            start = base + timedelta(minutes=15 * i)
            end = start + timedelta(minutes=15)
            val = round(self._get_tariff(start), 5)
            out.append({"start": start.isoformat(), "end": end.isoformat(), "value": val})
        return out

    @property
    def extra_state_attributes(self):
        return {
            "raw_today": self._raw_today,
            "raw_tomorrow": self._raw_tomorrow,
            "tariffs": self._tariffs,
        }


async def async_setup_entry(hass, entry, async_add_entities):
    tariffs = await async_fetch_konstant_tariffs()
    sensor = KonstantTarifSensor(hass, entry, tariffs)
    async_add_entities([sensor], True)

    async def update_tariffs(_):
        new_tariffs = await async_fetch_konstant_tariffs()
        sensor._tariffs = new_tariffs
        await sensor.async_update_ha_state(True)

    async_track_time_interval(hass, update_tariffs, timedelta(hours=24))
