HASS integration to track your ETF values and profits based of the [JustETF](https://www.justetf.com/en/) API[*](#important-notice).

# ETF Monitor
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

## Installation
1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `etf_monitor`.
1. Download _all_ the files from the `custom_components/etf_monitor/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Add the `etf_monitor` as a new sensor to your `configuration.yaml` [See Configuration](#configuration)
1. Create your ETF configuration file and add your ETFs. [See ETF Config](#etf-config)
1. Restart Home Assistant

## Configuration
For an example configuration see the [./config](./config/) folder. This folder contains an example for the sensor creation in the `configuration.yaml` and an example of an etf configuration file.

Ready to stay informed about your ETF investments? Head over to [JustETF](https://www.justetf.com/en/) to find your desired ETF(s). Once located, simply copy the ISIN of the ETF and seamlessly integrate it into your [ETF configuration](#etf-config). After adding your purchases and restarting Home Assistant, your ETFs will be represented by two sensor entries: one displaying the current price per share, and the other showcasing the Gain/Loss of your investments. Stay ahead of the curve with effortless ETF monitoring!

#### Integration Config
Configuration of the integration in the `configuration.yaml`.
```yaml
sensor:
  - platform: etf_monitor       # Platform of this integration
    name: "ETF Sens"            # (Optional) Name for the integration (Default: None)
    config: "etf_tracker.yaml"  # (Optional) Name of the configuration file relative to the config folder (Default: "etf_tracker.yaml")
    update_rate: 300            # (Optional) API polling rate in seconds (Default: 300)
```
#### ETF Config
Configuration of ETFs to track and purchase history.
```yaml etf_tracker.yaml
etfs:                   # ETF collection
  - name: MSCI Europe   # ETF Name and sensor entity name
    isin: LU0274209237  # ETF ISIN for API requests
    transactions:       # List of transactions to track
      - amount: 8                       # Amount of shares
        purchase_price: 80.64           # Price per share
        purchase_date: 18-01-2024       # (optional) Date of purchase
      - amount: 15                      # ...
        purchase_price: 80.97
        purchase_date: 12-12-2023
```


## Important Notice:
Please be advised that the API utilized in this project is not officially documented by [JustETF](https://www.justetf.com/en/). Consequently, it may be subject to alterations, limitations, or discontinuation without prior notice. As such, we cannot guarantee its continued availability or functionality.