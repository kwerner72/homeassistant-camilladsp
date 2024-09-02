from __future__ import annotations

import logging

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityDescription,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    ATTR_CAPTURE_RATE,
    ATTR_VOLUME_DB,
    CONFIG_VOLUME_MAX,
    CONFIG_VOLUME_MIN,
    DOMAIN,
    NAME,
)
from .coordinator import CDSPDataUpdateCoordinator
from .entity import CDSPEntity
from .model import CDSPData

LOGGER = logging.getLogger(__name__)

ENTITY_DESC = MediaPlayerEntityDescription(
    key="mediaplayer",
    translation_key="mediaplayer",
)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    volume_min = config_entry.options.get(CONFIG_VOLUME_MIN)
    volume_max = config_entry.options.get(CONFIG_VOLUME_MAX)

    entities = []
    entities.append(CDSPMediaPlayer(config_entry.entry_id, coordinator, ENTITY_DESC, volume_min, volume_max))

    async_add_entities(entities, update_before_add=False)


class CDSPMediaPlayer(CDSPEntity, MediaPlayerEntity):  # type: ignore[misc]

    _attr_has_entity_name = True

    _attr_media_content_type = MediaType.MUSIC
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_MUTE |
        MediaPlayerEntityFeature.VOLUME_SET |
        MediaPlayerEntityFeature.VOLUME_STEP |
        MediaPlayerEntityFeature.SELECT_SOURCE
    )
    _attr_source_list = []

    entity_description = MediaPlayerEntityDescription

    def __init__(
        self,
        unique_id: str,
        coordinator: CDSPDataUpdateCoordinator,
        description: MediaPlayerEntityDescription,
        volume_min: float,
        volume_max: float
    ) -> None:
        super().__init__(coordinator)

        self.entity_description = description

        self.has_entity_name = False
        self.name = NAME

        self._attr_unique_id = f"{unique_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self.unique_id))},
            name=NAME,
            manufacturer="HEnquist",
            model="",
        )

        self.volume_step = 0.02

        self._volume_min = volume_min
        self._volume_max = volume_max

        self._extra_state_attributes = {}

        self._data: CDSPData = self.coordinator.data
        self._set_attrs_from_data()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._data = self.coordinator.data
        self._set_attrs_from_data()
        super()._handle_coordinator_update()

    def _set_attrs_from_data(self):
        if self._data is not None:
            self._attr_available = self._data.state != MediaPlayerState.OFF
            self._attr_state = self._data.state
            self._attr_volume_level = self._convertFromDb(self._data.volume)
            self._attr_is_volume_muted = self._data.mute
            self._attr_source = self._data.source
            self._attr_source_list = self._data.source_list
            self._extra_state_attributes[ATTR_VOLUME_DB] = self._data.volume
            self._extra_state_attributes[ATTR_CAPTURE_RATE] = self._data.capturerate
        else:
            self._attr_available = False


    @callback
    def _async_update_attrs_write_ha_state(self) -> None:
        self._set_attrs_from_data()
        self.async_write_ha_state()

    def available(self) -> bool:
        """Return True if entity is available."""
        return self._attr_available

    @property
    def extra_state_attributes(self):
        return self._extra_state_attributes

    async def async_set_volume_level(self, volume: float) -> None:
        await self.coordinator.cdsp.async_set_volume(self._convertToDb(volume))
        self._data.volume = self._convertToDb(volume)
        self._async_update_attrs_write_ha_state()

    async def async_mute_volume(self, mute: bool) -> None:
        await self.coordinator.cdsp.async_set_muted(mute)
        self._data.mute = mute
        self._async_update_attrs_write_ha_state()

    async def async_select_source(self, source: str) -> None:
        await self.coordinator.cdsp.async_select_source(source)
        self._data.source = source
        self._async_update_attrs_write_ha_state()

    def _convertToDb(self, volume: float) -> float:
        if self._isValidVolume():
            return self._volume_min + (volume * abs(self._volume_max - self._volume_min))
        return 0

    def _convertFromDb(self, volume: float) -> float:
        if self._isValidVolume():
            return abs(self._volume_min - volume) / abs(self._volume_max - self._volume_min)
        return 0

    def _isValidVolume(self) -> bool:
        return isinstance(self._volume_min, float) and isinstance(self._volume_max, float)
