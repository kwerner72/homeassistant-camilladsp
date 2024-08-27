from __future__ import annotations

import logging

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityDescription,
    MediaPlayerEntityFeature,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NAME
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

    entities = []
    entities.append(CDSPMediaPlayer(coordinator, ENTITY_DESC))

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
        coordinator: CDSPDataUpdateCoordinator,
        description: MediaPlayerEntityDescription,
    ) -> None:
        super().__init__(coordinator)

        device_id = coordinator.cdsp.cdsp_id
        LOGGER.info(f"new device: {device_id}")

        self.entity_description = description

        self._attr_unique_id = f"{device_id}-{description.key}"
        self.has_entity_name = False
        self.name = NAME

        self.volume_step = 0.02

        self._data: CDSPData = self.coordinator.data
        self._set_attrs_from_data()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._data = self.coordinator.data
        self._set_attrs_from_data()
        super()._handle_coordinator_update()

    def _set_attrs_from_data(self):
        if self._data is not None:
            self._attr_state = self._data.state
            self._attr_volume_level = (self._data.volume + 50) / 50
            self._attr_is_volume_muted = self._data.mute
            self._attr_source = self._data.source
            self._attr_source_list = self._data.source_list

    @callback
    def _async_update_attrs_write_ha_state(self) -> None:
        self._set_attrs_from_data()
        self.async_write_ha_state()

    async def async_set_volume_level(self, volume: float) -> None:
        await self.coordinator.cdsp.async_set_volume_float(volume)
        self._data.volume = volume
        self._async_update_attrs_write_ha_state()

    async def async_mute_volume(self, mute: bool) -> None:
        await self.coordinator.cdsp.async_set_muted(mute)
        self._data.mute = mute
        self._async_update_attrs_write_ha_state()

    async def async_select_source(self, source: str) -> None:
        await self.coordinator.cdsp.async_select_source(source)
        self._data.source = source
        self._async_update_attrs_write_ha_state()
