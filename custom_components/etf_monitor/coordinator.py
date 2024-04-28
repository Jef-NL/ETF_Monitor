"""API Polling coordinator."""

from datetime import timedelta
import logging

import async_timeout  # noqa: TID251
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .EtfMonitor import ETFList, ETFTransaction

UPDATE_ITEMS_SCHEMA = vol.Schema(
    {
        vol.Required("entity_id"): str,
        vol.Required("amount"): int,
        vol.Required("price"): vol.Coerce(float),
        vol.Optional("date"): str,
    },
    # extra=vol.ALLOW_EXTRA,
)


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

        hass.services.async_register(
            DOMAIN, "update_etf", self._service_callback, schema=UPDATE_ITEMS_SCHEMA
        )

    async def _async_update_data(self):
        self.logger.info("Polling JustETF API for assets")
        data_frame = {}
        for entry in self._entries.etfs:
            try:
                with async_timeout.timeout(10):
                    data_frame[entry.name] = await entry.get_current_value(self.hass)
            except ValueError:
                self.logger.error(
                    "ETF API call for %s returned an error. Check the ISIN of '%s' in the configuration.",
                    entry.name,
                    entry.name,
                )
                self._entries.etfs.remove(entry)  # Kick entry from list
        return data_frame

    async def _service_callback(self, call: ServiceCall):
        found_macth = False
        amount = call.data.get("amount")
        price = call.data.get("price")
        date = call.data.get("date")
        for entry in self._entries.etfs:
            if entry.entity_id == call.data.get("entity_id"):
                found_macth = True
                entry.transactions.append(
                    ETFTransaction(
                        amount=amount, purchase_price=price, purchase_date=date
                    )
                )

        if not found_macth:
            raise ValueError(
                f"Failed to purchase for Entity '{call.data.get('entity_id')}'"
            )

        # ToDo: write new data to file
        self.async_update_listeners()
