[![Security](https://img.shields.io/badge/security-hardened-darkgreen)](#)  [![Python](https://img.shields.io/badge/python-3.x-blue?logo=python)](#)  [![Platform](https://img.shields.io/badge/platform-python--cli-lightgrey)](#) [![Telemetry](https://img.shields.io/badge/telemetry-disabled-darkgreen)](#) [![Privacy](https://img.shields.io/badge/privacy-100%25_local-darkgreen)](#)

[![Stars](https://img.shields.io/github/stars/enoch85/tesla-order-status?style=social)](https://github.com/enoch85/tesla-order-status/stargazers) [![Forks](https://img.shields.io/github/forks/enoch85/tesla-order-status?style=social)](https://github.com/enoch85/tesla-order-status/network/members) [![Issues](https://img.shields.io/github/issues/enoch85/tesla-order-status?style=social)](https://github.com/enoch85/tesla-order-status/issues)

> Prefer reading in German?<br>
> [Hier geht’s zur deutschen Version des README](README_DE.md)

# Tesla Order Status Tracker Security-Hardened 🚗📦
Stay in control of your Tesla order from the moment you place it until delivery. This security-hardened open-source Python CLI tool gives you direct access to the Tesla API while keeping the runtime local-first, minimizing external communication, and removing third-party telemetry.

## Table of Contents
1. [Why You'll Love It](#why-youll-love-it)
2. [Security Hardening](#security-hardening)
3. [Get Started](#get-started)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Configuration](#configuration)
7. [History & Preview](#history--preview)
8. [Telemetry](#telemetry)
9. [Disclaimer](#disclaimer)
10. [Support & Contact](#support--contact)

## Why You'll Love It
- 🔍 **Direct Tesla API connection**: Get the latest order information without any detours.
- 🧾 **Display of important details**: Vehicle options, production and delivery progress.
- 🕒 **History at a glance**: Every change (e.g. VIN allocation) is documented locally.
- 📋 **Share mode output**: Anonymized output for forums and social media, with optional clipboard copy in `--share` mode.
- 🔁 **Multi-order ready**: Handles multiple Tesla orders at once, with `--order <reference>` to focus on a single one.
- 🧩 **Modular & expandable**: Option codes, languages and features can be flexibly expanded.
- 🔐 **Security-hardened by default**: Tokens and settings remain local, telemetry is disabled, and third-party traffic is blocked.
- 🛡️ **Strict outbound allowlist**: Only Tesla API endpoints and GitHub release metadata checks are permitted.
- 📦 **Offline option catalog**: Option-code decoding is bundled locally instead of fetched from external services.
- 🔒 **Safer updates and migrations**: Updates are manual, local hotfix archives are checksum-verified, and migrations are pinned to a trusted allowlist.

The goal is to give users more transparency and control over the ordering process – without depending on external services.

## Security Hardening
- Outbound network access is restricted to Tesla API traffic and optional GitHub release metadata checks.
- TLS certificate verification is enabled on all HTTP requests, and requests use bounded retry/backoff logic instead of uncontrolled retries.
- Tesla login uses OAuth PKCE with `S256`, and the returned OAuth `state` is validated before exchanging the code.
- No third-party telemetry, remote banners, or remote option-code lookups exist in the runtime anymore.
- Updates are notification-only; applying a hotfix requires a locally supplied ZIP archive that is SHA-256 verified and extracted with zip-slip and symlink checks.
- Migration execution is limited to trusted files with pinned SHA-256 hashes.
- Tesla OAuth tokens are stored locally in `data/private/tesla_tokens.json` with restrictive file permissions.
- Tokens are not hashed at rest, because they must be presented back to Tesla for authenticated API calls. This repository does not use separate API keys.
- A complete offline option-code catalog ships in the repository so decoding does not depend on external servers.

## 🚀 Quick Links
- 📦 Direct download as ZIP: https://github.com/enoch85/tesla-order-status/archive/refs/heads/main.zip

## Get Started
Download the complete project to your machine. If you are unsure how, you can grab the ZIP archive directly from GitHub: https://github.com/enoch85/tesla-order-status/archive/refs/heads/main.zip
> ⚠️ Do not run single scripts without the rest of the repository. Everything is meant to work together.

## Installation
1. Install [Python 3](https://www.python.org/downloads/) for your operating system.
2. Tested environment: Ubuntu 24.04 with `python3`.
3. In the tested Ubuntu 24.04 environment, no additional Python packages were required.
4. Extract the repository and run the script directly with `python3`.

### Runtime Notes
- This project is distributed as a Python script, not as a packaged Windows or Linux binary.
- Ubuntu 24.04 is the primary tested environment.
- The code includes Windows-specific locale and terminal color handling, so Windows may work as well, but it should be treated as best-effort unless you verify it in your environment.

## Usage
Run the main script to fetch and display your order details:
```sh
python3 tesla_order_status.py
```
### Optional flags:
Get an overview of all command-line options:
```sh
python3 tesla_order_status.py --help
```
#### Output Modes
Only one of the options can be used at a time.
- `--all` display every available key in your history (verbose output)
- `--details` show additional information such as financing details.
- `--share` hide personal data like order ID and VIN for sharing. limits output to dates and status changes.
- `--status` only report whether the order information has changed since the last run. no login happens, so tesla_tokens.json have to be present already. token will get refreshed if necessary.
  - 0 => no changes
  - 1 => changes detected
  - 2 => pending updates
  - -1 => error ... you better run the script once without any params to make sure, it is working. Possibly the api token is invalid or there is no tesla_orders.json already
    
> 💡 When `pyperclip` is installed, a share-friendly summary is copied to your clipboard only in `--share` mode.

#### Work Modes
Work modes can be combined with any output mode:
- `--cached` – reuse locally cached order data without calling the API (perfect with `--share`)
- Automatic caching activates when you run the script again within one minute of a successful API request, keeping Tesla happy with fewer calls.

#### Order Filters
- `--order <referenceNumber>` – refresh every order in the background but only print the selected one (e.g. `--order RN123456`).

## Configuration
### General Settings
The script stores the configuration in `data/private/settings.json`. Feel free to tweak it—if something breaks, the script falls back to default values.

On the first run the script detects your system language and stores it as `language` in the settings file. Edit this entry to override the language manually. If no translation is available yet, the setting is simply ignored until one becomes available.

### Updates
The built-in updater only checks whether a newer version exists. Installing updates is now a manual step: download a verified release from GitHub and replace your local copy. The `hotfix.py` helper only applies a locally downloaded ZIP archive and no longer fetches code from the network.

### Option Codes
Known Tesla option codes are bundled locally in `data/public/option-codes/`,
including the complete offline catalog shipped with this repository. Option decoding
no longer depends on third-party lookups. You can still drop custom JSON files into
`data/public/option-codes` to override or extend the bundled data; local entries win
if multiple files define the same option code.

## History & Preview
The script stores the latest order information in `tesla_orders.json` and keeps a change log in `tesla_order_history.json`. Every detected difference—like a VIN assignment—is appended to the history file and displayed after the current status. The "Order Information" section always shows live data first, followed by historical changes.

### Order Information
```
---------------------------------------------
              ORDER INFORMATION
---------------------------------------------
Order Details:
- Order ID: RN100000000
- Status: BOOKED
- Model: my
- VIN: N/A

Configuration Options:
- APBS: Autopilot base features
- APPB: Enhanced Autopilot
- CPF0: Standard Connectivity
- IPW8: Interior: Black and White
- MDLY: Model Y
- MTY47: Model Y Long Range Dual Motor
- PPSB: Paint: Deep Blue Metallic
- SC04: Pay-per-use Supercharging
- STY5S: Seating: 5 Seat Interior
- WY19P: 19" Crossflow wheels (Model Y Juniper)

Delivery Information:
- Routing Location: None (N/A)
- Delivery Center: Tesla Delivery & Used Car Center Hanau Holzpark
- Delivery Window: 6 September - 30 September
- ETA to Delivery Center: None
- Delivery Appointment: None

Financing Information:
- Finance Product: OPERATIONAL_LEASE
- Finance Partner: Santander Consumer Leasing GmbH
- Monthly Payment: 683.35
- Term (months): 48
- Interest Rate: 6.95 %
- Range per Year: 10000
- Financed Amount: 60270
- Approved Amount: 60270
---------------------------------------------
```

### Timeline
```
Order Timeline:
- 2025-08-07: Reservation
- 2025-08-07: Order Booked
- 2025-08-07: Delivery Window: 6 September - 30 September
- 2025-08-23: new Delivery Window: 10 September - 30 September
```

### Change History
```
Change History:
2025-08-19: ≠ 0.details.tasks.deliveryDetails.regData.regDetails.company.address.careOf: Maximilian Mustermann -> Max Mustermann
2025-08-19: ≠ 0.details.tasks.deliveryDetails.regData.orderDetails.vin: None -> 131232
2025-08-19: + 0.details.tasks.deliveryDetails.regData.orderDetails.userId: 10000000
2025-08-19: - 0.details.tasks.deliveryDetails.regData.orderDetails.ritzbitz
```

#### SHARED MODE example:
```
---
Order Details:
- Model Y - AWD LR / Deep Blue / White
- Tesla Delivery & Used Car Center Hanau Holzpark

Order Timeline:
- 2025-08-07: Reservation
- 2025-08-07: Order Booked
- 2025-08-07: Delivery Window: 6 September - 30 September
- 2025-08-23: new Delivery Window: 10 September - 30 September
```

## Telemetry
Telemetry has been removed from this repository configuration.

No anonymous usage statistics, option codes, banners, or other third-party telemetry
data are sent anywhere because those code paths no longer exist.

### Network policy

- Tesla API traffic is allowed because the tool needs it to authenticate and load order data.
- GitHub release metadata checks are allowed for update notifications.
- Third-party telemetry, remote banner fetches, and remote option-code lookups are disabled.
- Installing updates is always a manual action using a locally downloaded archive.

## Issues
If you have any issues, running the script or getting error messages, please use the [issues](https://github.com/enoch85/tesla-order-status/issues) section.


## Disclaimer
- The script runs locally on your machine.
- No third-party data sharing is performed. Outbound traffic is limited to Tesla API calls and optional GitHub release metadata checks.
- You need to log in via browser and return the resulting URL to the script to extract the login token used for the API.
- The script only uses the token to work with for the current session.
- With your permission the script stores the token on your hard disk.

## Support & Contact
This repository is based on earlier upstream work from the original project lineage.

Original upstream repository: https://github.com/chrisi51/tesla-order-status
