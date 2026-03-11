[![Security](https://img.shields.io/badge/security-hardened-darkgreen)](#)  [![Python](https://img.shields.io/badge/python-3.x-blue?logo=python)](#)  [![Platform](https://img.shields.io/badge/platform-python--cli-lightgrey)](#) [![Telemetry](https://img.shields.io/badge/telemetry-disabled-darkgreen)](#) [![Privacy](https://img.shields.io/badge/privacy-local--first-darkgreen)](#)

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
8. [Privacy & Support](#privacy--support)

## Why You'll Love It
- 🔍 **Direct Tesla API connection**: Get the latest order information without any detours.
- 🧾 **Display of important details**: Vehicle options, production and delivery progress.
- 🕒 **History at a glance**: Every change (e.g. VIN allocation) is documented locally.
- 📋 **Share mode output**: Anonymized output for forums and social media, with optional clipboard copy in `--share` mode.
- 🔁 **Multi-order ready**: Handles multiple Tesla orders at once, with `--order <reference>` to focus on a single one.
- 🧩 **Modular & expandable**: Option codes, languages and features can be flexibly expanded.
- 🔐 **Security-hardened by default**: Tokens and settings remain local, telemetry is disabled, and non-essential third-party traffic is blocked.
- 🛡️ **Strict outbound allowlist**: Only Tesla API endpoints and GitHub release traffic required for update checks or explicit update downloads are permitted.
- 📦 **Offline option catalog**: Option-code decoding is bundled locally instead of fetched from external services.
- 🔒 **Safer updates**: Startup checks are notification-only, and release archives are checksum-verified before extraction whether supplied locally or downloaded explicitly from GitHub.

The goal is to give users more transparency and control over the ordering process without adding extra third-party services beyond Tesla itself and optional GitHub release checks.

## Security Hardening
- Outbound network access is restricted to Tesla API traffic and optional GitHub release checks or explicit release downloads.
- TLS certificate verification is enabled on all HTTP requests, and requests use bounded retry/backoff logic instead of uncontrolled retries.
- Tesla login uses OAuth PKCE with `S256`, and the returned OAuth `state` is validated before exchanging the code.
- No third-party telemetry, remote banners, or remote option-code lookups exist in the runtime anymore.
- Startup update checks are notification-only. Explicit updates remain manual and require a SHA-256-verified ZIP archive with zip-slip and symlink checks during extraction.
- Tesla OAuth tokens are stored locally in `data/private/tesla_tokens.json` with restrictive file permissions.
- Tokens are not hashed at rest, because they must be presented back to Tesla for authenticated API calls. This repository does not use separate API keys.
- A complete offline option-code catalog ships in the repository so decoding does not depend on external servers.
- Common legacy local layouts are migrated locally on startup when they can be upgraded safely without external data.

## 🚀 Quick Links
- 📦 Direct download as ZIP: https://github.com/enoch85/tesla-order-status/archive/refs/heads/main.zip

## Get Started
Download the complete project to your machine. If you are unsure how, you can grab the ZIP archive directly from GitHub: https://github.com/enoch85/tesla-order-status/archive/refs/heads/main.zip
> ⚠️ Do not run single scripts without the rest of the repository. Everything is meant to work together.

## Installation
1. Install [Python 3](https://www.python.org/downloads/) for your operating system.
2. Tested environment: Ubuntu 24.04 with `python3`.
3. In the tested Ubuntu 24.04 environment, no additional install step was required. Other environments may need `requests`; clipboard support via `pyperclip` is optional.
4. Extract the repository and run the script directly with `python3`.

If you are coming from an older fork layout, the tool performs a limited local compatibility migration on startup for common legacy file locations and history formats.

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
- `--all` displays every available key in your history (verbose output)
- `--details` show additional information such as financing details.
- `--share` hides personal data like order ID and VIN for sharing and limits output to dates and status changes.
- `--status` only reports whether the order information has changed since the last run. No interactive login happens, so `tesla_tokens.json` must already exist. The token is refreshed if necessary.
  - 0 => no changes
  - 1 => changes detected
  - 2 => pending updates
  - -1 => error. Run the script once without flags to verify the local setup. The token may be invalid or `tesla_orders.json` may not exist yet.
    
> 💡 When `pyperclip` is installed, a share-friendly summary is copied to your clipboard only in `--share` mode.

#### Work Modes
Work modes can be combined with any output mode:
- `--cached` – reuse locally cached order data without calling the API (perfect with `--share`)
- Automatic caching activates when you run the script again within one minute of a successful API request, keeping Tesla happy with fewer calls.

#### Update Mode
- `--update` opens the interactive update flow from the main CLI.
- `--update path/to/release.zip --sha256 <expected-sha256>` applies a local verified archive directly.
- The interactive update flow can check for releases and download the latest release archive from GitHub before optional local application.

#### Order Filters
- `--order <referenceNumber>` – refresh every order in the background but only print the selected one (e.g. `--order RN123456`).

## Configuration
### General Settings
The script stores the configuration in `data/private/settings.json`. Feel free to tweak it—if something breaks, the script falls back to default values.

On the first run the script detects your system language and stores it as `language` in the settings file. Edit this entry to override the language manually. If no translation is available yet, the setting is simply ignored until one becomes available.

### Updates
The main entry point now owns updates as well. Use `python3 tesla_order_status.py --update` to enter the update flow from the primary CLI instead of switching to a separate tool.

`python3 tesla_order_status.py --update` starts the interactive check/download/apply flow. You can also pass a local ZIP directly with `python3 tesla_order_status.py --update path/to/release.zip --sha256 <expected-sha256>`. Applying an archive still requires SHA-256 verification before extraction.

### Local Data Compatibility
This fork now performs a limited local compatibility migration on startup for common older fork layouts. Legacy root-level files such as `tesla_tokens.json`, `tesla_orders.json`, `tesla_order_history.json`, and `settings.json` are moved into `data/private`, older conflicts are backed up under `data/private/backup`, and list-based history data is upgraded to the current reference-based format when it can be resolved locally.

### Option Codes
Known Tesla option codes are bundled locally in `data/public/option-codes/`,
including the complete offline catalog shipped with this repository. Option decoding
no longer depends on third-party lookups. You can still drop custom JSON files into
`data/public/option-codes` to override or extend the bundled data; local entries win
if multiple files define the same option code.

## History & Preview
The script stores the latest order information in `data/private/tesla_orders.json` and keeps a change log in `data/private/tesla_order_history.json`. Every detected difference—like a VIN assignment or delivery-window change—is appended to the history file and displayed after the current status. The "Order Information" section always shows live data first, followed by historical changes.

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
- 2025-08-19: ≠ Delivery Window: 6 September - 30 September -> 10 September - 30 September
- 2025-08-19: + VIN: 131232
```

#### Share Mode Example
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

## Privacy & Support
- The tool runs locally on your machine, but it still needs Tesla API access to authenticate and load order data.
- Optional GitHub traffic is limited to release metadata checks and explicit release downloads triggered through the update flow.
- No telemetry, remote banners, or third-party option-code lookups exist in the runtime path anymore.
- Tesla tokens can be stored locally for future runs only if you choose to save them.
- If you hit a problem, report it in [GitHub Issues](https://github.com/enoch85/tesla-order-status/issues).
