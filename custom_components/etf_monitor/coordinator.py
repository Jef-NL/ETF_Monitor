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
        self._startup = True

    async def _async_update_data(self):
        # Do not poll outside of market hours
        if await self._entries.in_trading_hours() is False and not self._startup:
            self.logger.info("Outside of trading hours")
            return None
        self._startup = False

        self.logger.info("Polling JustETF API for assets")
        data_frame = {}
        for entry in self._entries.etfs:
            try:
                with async_timeout.timeout(10):
                    data_frame[entry.name] = await entry.get_current_value(self.hass)
            except ValueError as err:
                self.logger.error(
                    "ETF API call for %s returned an error. Check the ISIN of '%s' in the configuration. Err: %s",
                    entry.name,
                    entry.name,
                    err
                )
                self._entries.etfs.remove(entry)  # Kick entry from list
            except ConnectionAbortedError as err:
                self.logger.error(
                    "ETF API call for %s returned no correct response. Ignored for now.  Err: %s",
                    entry.name,
                    err
                )
        return data_frame
