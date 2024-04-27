"""ETF data structure definition."""

from dataclasses import dataclass
import json

import requests

from homeassistant.core import HomeAssistant

from .const import (
    ASSET_HISTORY_FIELD,
    ASSET_ID_FIELD,
    ASSET_LIST_TOP_FIELD,
    ASSET_NAME_FIELD,
    HISTORY_ENTRY_AMOUNT_FIELD,
    HISTORY_ENTRY_DATE_FIELD,
    HISTORY_ENTRY_PRICE_FIELD,
)

API_BASE_URL = "https://www.justetf.com/api/etfs/"
API_CHART_SETTINGS = "/performance-chart?locale=en&currency=EUR&valuesType=MARKET_VALUE&reduceData=true&includeDividends=true&period=D1"


@dataclass
class ETFTransaction:
    """ETF Transaction history object."""

    amount: float
    purchase_price: float
    purchase_date: str

    @classmethod
    async def entries_from_dict(cls, data: dict):
        """Parse entries from the dictionairy."""
        return cls(
            amount=data.get(HISTORY_ENTRY_AMOUNT_FIELD),
            purchase_price=data.get(HISTORY_ENTRY_PRICE_FIELD),
            purchase_date=data.get(HISTORY_ENTRY_DATE_FIELD),
        )


@dataclass
class ETFEntry:
    """Single ETF entry."""

    name: str
    isn: str
    transactions: list[ETFTransaction]
    current_price: float = 0

    async def calculate_purchase_sum(self):
        """Calculate the total purchase value of the ETF history."""
        total: float = 0.0
        for transaction in self.transactions:
            total += transaction.purchase_price * transaction.amount
        return total

    async def calulate_gain(self, price: float = 0.0):
        """Calculate the total asset gain from purchase."""
        price = price if price != 0.0 else self.current_price
        gain = 0.0
        for transaction in self.transactions:
            gain += (float(price) - transaction.purchase_price) * transaction.amount
        return gain

    async def get_current_value(self, hass: HomeAssistant) -> float:
        """Pull the current value of the ETF from the API."""
        response = await hass.async_add_executor_job(
            requests.get, API_BASE_URL + self.isn + API_CHART_SETTINGS
        )

        if response.ok:
            data = json.loads(response.text)
            self.current_price = float(data["series"][-1]["value"]["localized"])
            return self.current_price

        raise ValueError("Bad ETF Update Request.")

    async def get_shares_amount(self) -> float:
        """Get the total owned shares."""
        shares = 0.0
        for transaction in self.transactions:
            shares += transaction.amount
        return shares

    async def get_shares_value(self, shares: float = 0.0) -> float:
        """Get the current portfolio value."""
        shares = self.get_shares_amount() if shares == 0.0 else shares
        return shares * self.current_price

    @classmethod
    async def entry_from_dict(cls, data: dict):
        """Parse entries from the dictionairy."""
        name = data.get(ASSET_NAME_FIELD)
        isn = data.get(ASSET_ID_FIELD)
        entries = data.get(ASSET_HISTORY_FIELD)
        if entries is None:
            return cls

        transaction_list = []
        for entry in entries:
            etf_transaction = await ETFTransaction.entries_from_dict(entry)
            transaction_list.append(etf_transaction)
        return cls(name=name, isn=isn, transactions=transaction_list)


@dataclass
class ETFList:
    """Top of ETF data structure."""

    etfs: list[ETFEntry]

    @classmethod
    async def entries_from_dict(cls, data: dict):
        """Parse entries from the dictionairy."""
        entries = data.get(ASSET_LIST_TOP_FIELD)
        if entries is None:
            return cls

        entry_list = []
        for entry in entries:
            etf_entry = await ETFEntry.entry_from_dict(entry)
            entry_list.append(etf_entry)
        return cls(etfs=entry_list)
