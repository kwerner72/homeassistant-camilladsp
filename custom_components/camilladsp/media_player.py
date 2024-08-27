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
    """Representation of a Sensor."""

    _attr_has_entity_name = True

    _attr_media_content_type = MediaType.MUSIC
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = (
        MediaPlayerEntityFeature.VOLUME_MUTE |
        MediaPlayerEntityFeature.VOLUME_SET |
        MediaPlayerEntityFeature.SELECT_SOURCE
    )
    _attr_source_list = []

    entity_description = MediaPlayerEntityDescription

    def __init__(
        self,
        coordinator: CDSPDataUpdateCoordinator,
        description: MediaPlayerEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        device_id = coordinator.cdsp.cdsp_id
        LOGGER.info(f"new device: {device_id}")

        self.entity_description = description

        self._attr_unique_id = f"{device_id}-{description.key}"
        self.has_entity_name = False
        self.name = NAME

        self.volume_step = 0.02

        if self.coordinator.data is not None:
            self._attr_state = self.coordinator.data.state
            self._attr_volume_level = self.coordinator.data.volume
            self._attr_is_volume_muted = self.coordinator.data.mute
            self._attr_source = self.coordinator.data.source
            self._attr_source_list = self.coordinator.data.source_list


    @property
    def available(self) -> bool:
        online = self.coordinator.data is not None
        LOGGER.info(f"Available: {online}")
        return online

    @property
    def volume_level(self) -> float | None:
        if self.coordinator.data is not None:
            return (self.coordinator.data.volume + 50) / 50
        return 0

    @property
    def volume_level_in_db(self) -> float | None:
        if self.coordinator.data is not None:
            return self.coordinator.data.volume
        return 0

    @property
    def is_volume_muted(self) -> bool | None:
        if self.coordinator.data is not None:
            return self.coordinator.data.mute
        return False

    @property
    def source(self) -> str | None:
        if self.coordinator.data is not None:
            return self.coordinator.data.source
        return None

    @property
    def source_list(self) -> list[str] | None:
        if self.coordinator.data is not None:
            return self.coordinator.data.source_list
        return None

    async def async_set_volume_level(self, volume: float) -> None:
        await self.coordinator.cdsp.async_set_volume_float(volume)
        await self.coordinator.async_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        await self.coordinator.cdsp.async_set_muted(mute)
        await self.coordinator.async_refresh()

    async def async_select_source(self, source: str) -> None:
        LOGGER.info(f"Select source: {source}")
        await self.coordinator.cdsp.async_select_source(source)
        await self.coordinator.async_refresh()
