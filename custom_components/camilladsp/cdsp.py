__version__ = "1.0.1"

import hashlib
import json
import logging
from typing import Any

from homeassistant.components.media_player import MediaPlayerState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from camilladsp import CamillaClient
from urllib.parse import urlparse

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

        parse_result = urlparse(self.url)
        host = parse_result.hostname
        port = 1234
        self.cdspClient = CamillaClient(host, port)

    def set_volume_fader(self, fader: str, volume: float) -> None:
        if not self.cdspClient.is_connected():
            self.cdspClient.connect()

        if fader == "Aux1":
            self.cdspClient.volume.set_volume(1, volume)
        elif fader == "Aux2":
            self.cdspClient.volume.set_volume(2, volume)
        elif fader == "Aux3":
            self.cdspClient.volume.set_volume(3, volume)
        elif fader == "Aux4":
            self.cdspClient.volume.set_volume(4, volume)

    def set_volume(self, volume: float):
        if not self.cdspClient.is_connected():
            self.cdspClient.connect()
        self.cdspClient.volume.set_main_volume(volume)
        self._volume = volume

    def set_fader_muted(self, fader: str, muted: bool) -> None:
        if not self.cdspClient.is_connected():
            self.cdspClient.connect()

        if fader == "Aux1":
            self.cdspClient.volume.set_mute(1, muted)
        elif fader == "Aux2":
            self.cdspClient.volume.set_mute(2, muted)
        elif fader == "Aux3":
            self.cdspClient.volume.set_mute(3, muted)
        elif fader == "Aux4":
            self.cdspClient.volume.set_mute(4, muted)
        else:
            self.cdspClient.volume.set_main_mute(muted)

    async def async_select_source(self, source: str):
        data = f"{{\"name\":\"{source!s}\"}}"
        await self.async_post_api(endpoint="setactiveconfigfile", data=data)
        configData = await self.async_get_api(endpoint="getactiveconfigfile")
        if json.loads(configData)["configFileName"] == source:
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
        volume_fader: dict[str, float] = {
            "Aux1": 0,
            "Aux2": 0,
            "Aux3": 0,
            "Aux4": 0,
        }
        mute: bool = False
        is_fader_muted: dict[str, bool] = {
            "Aux1": False,
            "Aux2": False,
            "Aux3": False,
            "Aux4": False,
        }
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
                if not self.cdspClient.is_connected():
                    self.cdspClient.connect()

                if statusData.get("capturerate") is not None:
                    capturerate = statusData["capturerate"]
                else:
                    capturerate = 0

                volume = self.cdspClient.volume.main_volume()
                volume_fader["Aux1"] = self.cdspClient.volume.volume(1)
                volume_fader["Aux2"] = self.cdspClient.volume.volume(2)
                volume_fader["Aux3"] = self.cdspClient.volume.volume(3)
                volume_fader["Aux4"] = self.cdspClient.volume.volume(4)
                mute = self.cdspClient.volume.main_mute()
                is_fader_muted["Aux1"] = self.cdspClient.volume.mute(1)
                is_fader_muted["Aux2"] = self.cdspClient.volume.mute(2)
                is_fader_muted["Aux3"] = self.cdspClient.volume.mute(3)
                is_fader_muted["Aux4"] = self.cdspClient.volume.mute(4)

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
                        volume_fader=volume_fader,               
                        mute=mute,
                        is_fader_muted=is_fader_muted,
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
