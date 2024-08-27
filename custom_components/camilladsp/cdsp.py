__version__ = "0.1.0"

import hashlib
import json
import logging
from typing import Any, NamedTuple

import aiohttp

from homeassistant.components.media_player import MediaPlayerState

LOGGER = logging.getLogger(__name__)

class CDSPData(NamedTuple):

    state: str
    volume: float
    mute: bool
    source: str
    source_list: list[str]

class CDSPClient:
    """Set up CamillaDSP."""

    def __init__(self, url: str, timeout: int = 60) -> None:
        """Initialize CamillaDSP module."""
        self.url = url
        self.status: dict = {}
        self._timeout: int = timeout
        self._websession = None
        self.aio_timeout = aiohttp.ClientTimeout(total=self._timeout)


        md5 = hashlib.md5()
        md5.update(url.encode('utf-8'))
        self.cdsp_id = md5.hexdigest()[0:16]
        self.name = "camilla_dsp"

    async def async_set_volume_float(self, volume: float):
        await self.async_set_volume((volume * 50) - 50)

    async def async_set_volume(self, volume: float):

        await self.async_post_api(endpoint="setparam/volume", data=str(volume))
        self._volume = volume

    async def async_set_muted(self, muted: bool):
        await self.async_post_api(endpoint="setparam/mute", data=str(muted))
        self._mute = muted

    async def async_select_source(self, source: str):
        data = f"{{\"name\":\"{source!s}\"}}"
        LOGGER.info(f"source: {data}")
        await self.async_post_api(endpoint="setactiveconfigfile", data=data)
        self._source = source

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
        self._websession = aiohttp.ClientSession(timeout=self.aio_timeout)

        state: MediaPlayerState = MediaPlayerState.OFF
        volume: float = 0
        mute: bool = False
        source: str = None
        source_list: list[str] = None

        try:
            statusData = json.loads(await self.async_get_api(endpoint="status"))
            LOGGER.info(f"status: {statusData}")
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
                case _:
                    state = MediaPlayerState.OFF
            LOGGER.info(f"status: {state}")

            volume = float(await self.async_get_api(endpoint="getparam/volume"))
            LOGGER.info(f"volume: {volume}")

            mute = (await self.async_get_api(endpoint="getparam/mute")) == "True"
            LOGGER.info(f"mute: {mute}")

            source = (json.loads(await self.async_get_api(endpoint="getactiveconfigfile"))["configFileName"])
            LOGGER.info(f"source: {source}")

            source_list = (json.loads(await self.async_get_api(endpoint="storedconfigs")))[0]
            LOGGER.info(f"source_list: {source_list}")

        except Exception as e:
            self._state = None
            log = f"CamillaDSP error: api call failed: {e}"
            LOGGER.error(log)

        await self._websession.close()

        return CDSPData(state=state, volume=volume, mute=mute, source=source, source_list=source_list)

    async def async_get_api(self, endpoint: str) -> Any:
        """Retrieve data from the API."""
        url = f"{self.url}/api/{endpoint}"

        res = await self._websession.get(url)
        log = f"API call status: {res.status}"
        LOGGER.debug(log)
        ret = await res.text()
        log = f"API call returns: {ret}"
        LOGGER.debug(log)
        return ret


    async def async_post_api(self, endpoint: str, data: str) -> Any:
        self._websession = aiohttp.ClientSession(timeout=self.aio_timeout)

        """Retrieve data from the API."""
        url = f"{self.url}/api/{endpoint}"

        LOGGER.info(f"API call url: {url} / data: {data}")
        res = await self._websession.post(url, data=data, json=None)
        log = f"API call status: {res.status}"
        LOGGER.info(log)
        ret = await res.text()
        log = f"API call returns: {ret}"
        LOGGER.info(log)

        await self._websession.close()

        return ret

class ApiError(Exception):
    """Error to indicate something wrong with the API."""