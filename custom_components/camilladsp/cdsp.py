__version__ = "1.0.0"

import hashlib
import json
import logging
from typing import Any

from homeassistant.components.media_player import MediaPlayerState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .model import CDSPData

LOGGER = logging.getLogger(__name__)


class CDSPClient:
    """Set up CamillaDSP."""

    def __init__(self, hass: HomeAssistant, url: str) -> None:
        """Initialize CamillaDSP module."""
        self.hass = hass
        self.url = url
        self.status: dict = {}

        md5 = hashlib.md5()
        md5.update(url.encode('utf-8'))
        self.cdsp_id = md5.hexdigest()[0:16]
        self.name = DOMAIN

        self._volume: float = 0
        self._mute: bool = False
        self._source: str = ""

    async def async_set_volume(self, volume: float):
        await self.async_post_api(endpoint="setparam/volume", data=str(volume))
        self._volume = volume

    async def async_set_muted(self, muted: bool):
        await self.async_post_api(endpoint="setparam/mute", data=str(muted))
        self._mute = muted

    async def async_select_source(self, source: str):
        data = f"{{\"name\":\"{source!s}\"}}"
        await self.async_post_api(endpoint="setactiveconfigfile", data=data)
        configData = json.loads(await self.async_get_api(endpoint="getactiveconfigfile"))
        if configData["configFileName"] == source:
            await self.async_post_api(endpoint="setconfig", data=configData)
            self._source = source
        else:
            LOGGER.warning("Error setting active config file")

    async def connect(self) -> None:
        """Connect to CamillaDSP API."""

        try:
            await self.update()
        except Exception as e:
            log = f"CamillaDSP unable to update: {e}"
            LOGGER.error(log)

        LOGGER.debug("CamillaDSP connected!")


    async def update(self) -> CDSPData:
        """Update CamillaDSP data through API."""
        state: MediaPlayerState = MediaPlayerState.OFF
        volume: float = 0
        mute: bool = False
        source: str = ""
        source_list: list[str] = []
        capturerate: int = 0

        try:
            statusData = json.loads(await self.async_get_api(endpoint="status"))
            match statusData["cdsp_status"]:
                case 'INACTIVE':
                    state = MediaPlayerState.STANDBY
                case 'PAUSED':
                    state = MediaPlayerState.PAUSED
                case 'RUNNING':
                    state = MediaPlayerState.PLAYING
                case 'STALLED':
                    state = MediaPlayerState.IDLE
                case 'STARTING':
                    state = MediaPlayerState.ON

            if state != MediaPlayerState.OFF:
                if statusData.get("capturerate") is not None:
                    capturerate = statusData["capturerate"]
                else:
                    capturerate = 0

                volume = float(await self.async_get_api(endpoint="getparam/volume"))
                mute = (await self.async_get_api(endpoint="getparam/mute")) == "True"
                source = (json.loads(await self.async_get_api(endpoint="getactiveconfigfile"))["configFileName"])

                storedconfigs = json.loads(await self.async_get_api(endpoint="storedconfigs"))
                source_list = []
                for config in storedconfigs:
                    if config.get("name") is not None:
                        source_list.append(config.get("name"))

        except Exception as e:
            log = f"CamillaDSP error: api call failed: {e}"
            LOGGER.debug(log)

        #await self._websession.close()

        return CDSPData(state=state,
                        volume=volume,
                        mute=mute,
                        source=source,
                        source_list=source_list,
                        capturerate=capturerate)

    async def async_get_api(self, endpoint: str) -> Any:
        url = f"{self.url}/api/{endpoint}"

        session = async_get_clientsession(self.hass)
        res = await session.get(url)
        return await res.text()


    async def async_post_api(self, endpoint: str, data: str) -> Any:
        url = f"{self.url}/api/{endpoint}"

        session = async_get_clientsession(self.hass)
        res = await session.post(url, data=data, json=None)
        return await res.text()
