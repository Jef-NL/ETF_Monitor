"""Constants for the ETF motitoring integration."""

DOMAIN = "etf_monitor"

# Integration config options
CONF_FILE_OPTION_FIELD = "config"
POLL_RATE_FIELD = "update_rate"
ASSET_LIST_TOP_FIELD = "etfs"
ASSET_NAME_FIELD = "name"
ASSET_ID_FIELD = "isin"
ASSET_HISTORY_FIELD = "transactions"
HISTORY_ENTRY_AMOUNT_FIELD = "amount"
HISTORY_ENTRY_PRICE_FIELD = "purchase_price"
HISTORY_ENTRY_DATE_FIELD = "purchase_date"

DEFAULT_CONFIG_NAME = "etf_tracker.yaml"
DEFAULT_POLLING_RATE_S = 300
MIN_POLLING_RATE_S = 60
