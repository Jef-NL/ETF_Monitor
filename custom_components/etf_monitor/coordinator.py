"""API Polling coordinator."""

from datetime import timedelta
import logging

import async_timeout  # noqa: TID251

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .EtfMonitor import ETFList


class ETFUpdateCoordinator(DataUpdateCoordinator):
    """Shared API polling coordinator."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        entries: ETFList,
        poll_interval: int = 300,
    ) -> None:
        """Init the coordinator and assign the entries."""
        super().__init__(
            hass,
            logger,
            name="ETF Monitor",
            update_interval=timedelta(seconds=poll_interval),
        )
        self._entries = entries

    async def _async_update_data(self):
        self.logger.info("Polling JustETF API for assets")
        data_frame = {}
        for entry in self._entries.etfs:
            try:
                with async_timeout.timeout(10):
                    data_frame[entry.name] = await entry.get_current_value(self.hass)
            except ValueError:
                self.logger.error(
                    "ETF API call for %s returned an error. Check the ISN of '%s' in the configuration.",
                    entry.name,
                    entry.name,
                )
                self._entries.etfs.remove(entry)  # Kick entry from list
        return data_frame
