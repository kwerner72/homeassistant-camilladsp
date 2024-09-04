from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant, callback

from .cdsp import CDSPClient
from .const import (
    CONFIG_URL,
    CONFIG_VOLUME_MAX,
    CONFIG_VOLUME_MIN,
    CONFIG_VOLUME_STEP,
    DOMAIN,
    NAME,
)

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONFIG_URL): str
    }
)

def get_options_schema(init_values: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
    {
        vol.Optional(CONFIG_VOLUME_MIN,
                     default=init_values[CONFIG_VOLUME_MIN]): vol.All(vol.Coerce(float),
                                                                      vol.Range(min=-100, max=0)),
        vol.Optional(CONFIG_VOLUME_MAX,
                     default=init_values[CONFIG_VOLUME_MAX]): vol.All(vol.Coerce(float),
                                                                      vol.Range(min=-100, max=0)),
        vol.Optional(CONFIG_VOLUME_STEP,
                     default=init_values[CONFIG_VOLUME_STEP]): vol.All(vol.Coerce(float),
                                                                       vol.Range(min=0, max=100))
    }
)

async def validate_data_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:

    url = data[CONFIG_URL]
    cdsp = CDSPClient(hass, url)
    if not await cdsp.update():
        raise CannotConnect

async def validate_options_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:

    if data[CONFIG_VOLUME_MAX] > 0 or data[CONFIG_VOLUME_MIN] > data[CONFIG_VOLUME_MAX]:
        raise InvalidValue
    if data[CONFIG_VOLUME_STEP] < 0:
        raise InvalidValue


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=DATA_SCHEMA, errors=errors
            )

        try:
            await validate_data_input(self.hass, user_input)

            return self.async_create_entry(title=NAME,
                                           data=user_input,
                                           options={
                                               CONFIG_VOLUME_MIN: -50,
                                               CONFIG_VOLUME_MAX: 0,
                                               CONFIG_VOLUME_STEP: 1
                                           })
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidHost:
            errors[CONFIG_URL] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors = {}

        if user_input is None:
            return self.async_show_form(
                step_id="init", data_schema=get_options_schema(self.config_entry.options), errors=errors
            )

        try:
            await validate_options_input(self.hass, user_input)

            return self.async_create_entry(title="VolumeOptions",
                                           data=user_input)
        except InvalidValue:
            errors["base"] = "invalid_value"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="init", data_schema=get_options_schema(self.config_entry.options), errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""

class InvalidValue(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
