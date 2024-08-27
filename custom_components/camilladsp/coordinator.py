import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .cdsp import CDSPClient
from .const import DOMAIN
from .model import CDSPData

LOGGER = logging.getLogger(__name__)


class CDSPDataUpdateCoordinator(DataUpdateCoordinator[CDSPData]):  # type: ignore[misc]
    """Class to manage fetching CamillaDSP data from single endpoint."""

    def __init__(self, hass: HomeAssistant, cdsp: CDSPClient, interval: float) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, LOGGER, name=DOMAIN, update_interval=interval)
        self.cdsp = cdsp

    async def _async_update_data(self) -> CDSPData:
        if self.hass.is_stopping:
            return None

        try:
            return await self.cdsp.update()

        except ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise ConfigEntryAuthFailed from err

class ApiError(Exception):
    """Error to indicate something wrong with the API."""
