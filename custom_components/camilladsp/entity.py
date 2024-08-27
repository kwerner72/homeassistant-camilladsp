from __future__ import annotations

from typing import Any

from homeassistant.const import ATTR_NAME, ATTR_VIA_DEVICE
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, VERSION
from .coordinator import CDSPData, CDSPDataUpdateCoordinator


class CDSPEntity(CoordinatorEntity[CDSPData]):  # type:ignore [misc]
    """Represent a CDSP Entity."""

    coordinator: CDSPDataUpdateCoordinator

    def __init__(
        self,
        coordinator: CDSPDataUpdateCoordinator,
    ) -> None:
        """Initialise the gateway."""
        super().__init__(coordinator)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            manufacturer=NAME,
            name=NAME,
            model=VERSION,
        )