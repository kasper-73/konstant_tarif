import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_INCLUDE_VAT, CONF_USE_DISCOUNTED


class KonstantTarifFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Konstant Tariffer", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_INCLUDE_VAT, default=True): bool,
            vol.Required(CONF_USE_DISCOUNTED, default=True): bool,
        })
        return self.async_show_form(step_id="user", data_schema=schema)
