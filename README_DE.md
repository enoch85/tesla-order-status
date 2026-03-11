[![Security](https://img.shields.io/badge/security-hardened-darkgreen)](#)  [![Python](https://img.shields.io/badge/python-3.x-blue?logo=python)](#)  [![Platform](https://img.shields.io/badge/platform-python--cli-lightgrey)](#) [![Telemetry](https://img.shields.io/badge/telemetry-disabled-darkgreen)](#) [![Privacy](https://img.shields.io/badge/privacy-local--first-darkgreen)](#)

[![Stars](https://img.shields.io/github/stars/enoch85/tesla-order-status?style=social)](https://github.com/enoch85/tesla-order-status/stargazers) [![Forks](https://img.shields.io/github/forks/enoch85/tesla-order-status?style=social)](https://github.com/enoch85/tesla-order-status/network/members) [![Issues](https://img.shields.io/github/issues/enoch85/tesla-order-status?style=social)](https://github.com/enoch85/tesla-order-status/issues)

> Prefer reading in English?<br>
> [Click here for the English version of the README](README.md)
> 
# Tesla Order Status Tracker Security-Hardened 🚗📦

Behalte deine Tesla-Bestellung von der Auftragsbestätigung bis zur Auslieferung im Blick. Dieses sicherheitsgehärtete Open‑Source‑Python‑CLI‑Tool gibt dir direkten Zugriff auf die Tesla‑API und hält den Laufzeitbetrieb gleichzeitig lokal, reduziert externe Kommunikation auf das Nötigste und entfernt Drittanbieter-Telemetry.

## Inhaltsverzeichnis

1. [Warum du es lieben wirst](#warum-du-es-lieben-wirst)
2. [Sicherheits-Härtung](#sicherheits-hartung)
3. [Schnellstart](#schnellstart)
4. [Installation](#installation)
5. [Benutzung](#benutzung)
6. [Konfiguration](#konfiguration)
7. [Historie & Vorschau](#historie--vorschau)
8. [Datenschutz & Support](#datenschutz--support)

## Warum du es lieben wirst

* 🔍 **Direkte Tesla‑API‑Anbindung**: Hol dir die neuesten Bestellinfos ohne Umwege.
* 🧾 **Wichtige Details im Blick**: Fahrzeugoptionen, Produktions‑ und Lieferfortschritt.
* 🕒 **Historie auf einen Blick**: Jede Änderung (z. B. VIN‑Zuteilung) wird lokal protokolliert.
* 📋 **One‑Click‑Share‑Modus**: Anonymisierte Zwischenablage für Foren & Social Media.
* 🔁 **Mehrfach-Bestellungen**: Unterstützt mehrere Tesla-Aufträge parallel, `--order <Referenz>` filtert eine einzelne Bestellung.
* 🧩 **Modular & erweiterbar**: Option‑Codes, Sprachen und Features flexibel ausbaubar.
* 🔐 **Sicherheitsgehärtet ab Werk**: Tokens und Einstellungen bleiben lokal, Telemetry ist deaktiviert und nicht notwendiger Drittanbieter-Traffic ist blockiert.
* 🛡️ **Strikte Outbound-Allowlist**: Erlaubt sind nur Tesla-API-Endpunkte und GitHub-Release-Verbindungen für Update-Prüfungen oder explizite Update-Downloads.
* 📦 **Offline-Option-Katalog**: Die Auflösung der Option-Codes erfolgt lokal statt über externe Dienste.
* 🔒 **Sicherere Updates**: Startseitige Update-Prüfungen bleiben hinweisbasiert, und Release-Archive werden vor dem Entpacken per Prüfsumme verifiziert, egal ob lokal bereitgestellt oder explizit von GitHub geladen.

Ziel ist, dir mehr Transparenz und Kontrolle über den Bestellprozess zu geben, ohne zusätzliche Drittdienste jenseits von Tesla selbst und optionalen GitHub-Release-Prüfungen einzubinden.

## Sicherheits-Härtung

* Ausgehender Netzwerkverkehr ist auf Tesla-API-Traffic und optionale GitHub-Release-Prüfungen oder explizite Release-Downloads beschränkt.
* Für alle HTTP-Anfragen ist TLS-Zertifikatsprüfung aktiviert, und Requests nutzen begrenzte Retry-/Backoff-Logik statt unkontrollierter Wiederholungen.
* Der Tesla-Login nutzt OAuth PKCE mit `S256`, und der zurückkommende OAuth-`state` wird vor dem Token-Tausch geprüft.
* Drittanbieter-Telemetry, Remote-Banner und externe Option‑Code-Lookups sind nicht Teil des Laufzeitpfads.
* Startseitige Update-Prüfungen sind nur Hinweis-basiert. Explizite Updates bleiben manuell und verlangen immer ein per SHA-256 geprüftes ZIP-Archiv mit Zip-Slip-/Symlink-Schutz beim Entpacken.
* Tesla-OAuth-Tokens werden lokal in `data/private/tesla_tokens.json` mit restriktiven Dateirechten gespeichert.
* Wenn `TESLA_ORDER_STATUS_TOKEN_PASSPHRASE` gesetzt ist und `cryptography` installiert wurde, wird die Token-Datei lokal verschlüsselt auf die Platte geschrieben.
* Tesla-Tokens lassen sich für den Laufzeitgebrauch nicht sinnvoll hashen, weil sie für authentifizierte Tesla-API-Aufrufe wieder im Klartext an Tesla gesendet werden müssen. Separate API-Keys verwendet dieses Repository nicht.
* Ein vollständiger Offline-Option-Katalog liegt im Repository, damit die Dekodierung nicht von externen Servern abhängt.
* Gängige ältere lokale Layouts werden beim Start lokal migriert, wenn sie sich sicher ohne externe Daten aktualisieren lassen.

## 🚀 Quick Links

* 📦 Direktdownload als ZIP: [https://github.com/enoch85/tesla-order-status/archive/refs/heads/main.zip](https://github.com/enoch85/tesla-order-status/archive/refs/heads/main.zip)

## Schnellstart

Lade das komplette Projekt auf deinen Rechner. Wenn du unsicher bist, nutze einfach das ZIP‑Archiv von GitHub: [https://github.com/enoch85/tesla-order-status/archive/refs/heads/main.zip](https://github.com/enoch85/tesla-order-status/archive/refs/heads/main.zip)

> ⚠️ Bitte keine einzelnen Skripte isoliert ausführen – alles ist als Gesamtprojekt gedacht.

## Installation

1. Installiere [Python 3](https://www.python.org/downloads/) für dein Betriebssystem.
2. Getestete Umgebung: Ubuntu 24.04 mit `python3`.
3. In der getesteten Ubuntu-24.04-Umgebung war kein zusätzlicher Installationsschritt nötig. In anderen Umgebungen kann `requests` erforderlich sein; Zwischenablagen-Support über `pyperclip` ist optional.
4. Repository entpacken und das Skript direkt mit `python3` ausführen.

Wenn du von einem älteren Fork oder einer älteren Ordnerstruktur kommst, führt das Tool beim Start eine begrenzte lokale Kompatibilitätsmigration für typische Alt-Dateien und History-Formate aus.

### Laufzeit-Hinweise

* Dieses Projekt wird als Python-Skript ausgeliefert, nicht als gepackte Windows- oder Linux-Binärdatei.
* Ubuntu 24.04 ist die primär getestete Umgebung.
* Der Code enthält Windows-spezifische Behandlung für Locale und Terminalfarben. Windows kann also ebenfalls funktionieren, sollte aber als Best-Effort gelten, solange du es nicht selbst verifiziert hast.

## Benutzung

Starte das Hauptskript, um Bestelldaten abzurufen und anzuzeigen:

```sh
python3 tesla_order_status.py
```

### Optionale Flags

Übersicht aller Optionen:

```sh
python3 tesla_order_status.py --help
```

#### Output‑Modi

(Es kann jeweils nur ein Output‑Modus genutzt werden.)

* `--all` zeigt sämtliche verfügbaren Schlüssel in deiner Historie (sehr ausführlich)
* `--details` zeigt zusätzliche Infos wie Finanzierungsdetails
* `--share` anonymisiert persönliche Daten (Order‑ID, VIN) und reduziert die Ausgabe auf Datum/Statusänderungen
* `--status` meldet nur, ob sich seit dem letzten Lauf etwas geändert hat. Es findet **kein** Login statt, daher müssen `tesla_tokens.json` bereits vorhanden sein; ein Refresh des Tokens erfolgt bei Bedarf.

  * **0** → keine Änderungen
  * **1** → Änderungen erkannt
  * **2** → Updates ausstehend
  * **-1** → Fehler (führe das Skript einmal ohne Parameter aus, um die Basis einzurichten; ggf. ist das API‑Token ungültig oder `tesla_orders.json` fehlt)

> 💡 Wenn `pyperclip` installiert ist, wird eine share‑freundliche Zusammenfassung nur im `--share`-Modus in die Zwischenablage kopiert.

#### Arbeits‑Modi

(Diese können mit jedem Output‑Modus kombiniert werden.)

* `--cached` – nutzt lokal gecachte Bestelldaten ohne neue API‑Anfragen (ideal zusammen mit `--share`)
* Automatisches Caching: Startest du das Skript innerhalb einer Minute nach einem erfolgreichen API‑Request erneut, wird automatisch der Cache genutzt (schont die Tesla‑API).

#### Optionale Token-Verschlüsselung

* Installiere `cryptography` mit `python3 -m pip install cryptography`.
* Setze vor dem Start lokal eine Passphrase, zum Beispiel `export TESLA_ORDER_STATUS_TOKEN_PASSPHRASE='waehle-eine-lange-passphrase'`, wenn nicht-interaktive Läufe wie Cronjobs oder `--status` weiter funktionieren sollen.
* Wenn bereits eine verschlüsselte Token-Datei existiert und keine Passphrase in der Umgebung konfiguriert ist, fragt die CLI sie bei interaktiven Läufen sicher ab.
* Bereits vorhandene Klartext-Token-Dateien werden beim nächsten Schreibvorgang automatisch verschlüsselt neu gespeichert, solange eine Passphrase konfiguriert ist.

#### Update-Modus

* `--update` öffnet den interaktiven Update-Ablauf direkt in der Haupt-CLI.
* `--update pfad/zum/release.zip --sha256 <erwartete-sha256>` wendet ein lokales verifiziertes Archiv direkt an.
* Der interaktive Update-Ablauf kann Releases prüfen und das neueste Release-Archiv von GitHub herunterladen, bevor es optional lokal angewendet wird.

#### Filter

* `--order <Referenznummer>` – aktualisiert weiterhin alle Bestellungen, zeigt aber nur die angegebene Referenz (z. B. `--order RN123456`) an.

## Konfiguration

### Allgemeine Einstellungen

Die Konfiguration liegt unter `data/private/settings.json`. Du kannst sie anpassen – bei ungültigen Werten fällt das Tool automatisch auf Defaults zurück.

Beim ersten Start wird die Systemsprache erkannt und als `language` gespeichert. Du kannst den Wert manuell ändern. Ist für deine Sprache noch keine Übersetzung vorhanden, wird die Einstellung ignoriert, bis eine Übersetzung verfügbar ist.

### Option Codes

Bekannte Tesla‑Option‑Codes werden lokal in `data/public/option-codes/` mitgeliefert,
einschließlich des vollständigen Offline-Katalogs in diesem Repository. Die Auflösung
der Codes basiert damit ausschließlich auf lokalen Daten. Eigene JSON‑Dateien kannst du
zusätzlich in `data/public/option-codes` ablegen; **lokale Einträge gewinnen** bei
Kollisionen.

### Kompatibilität lokaler Daten
Dieser Fork führt beim Start jetzt eine begrenzte lokale Kompatibilitätsmigration für typische ältere Fork-Layouts aus. Veraltete Dateien im Projektwurzelverzeichnis wie `tesla_tokens.json`, `tesla_orders.json`, `tesla_order_history.json` und `settings.json` werden nach `data/private` verschoben, Konflikte unter `data/private/backup` gesichert und listenbasierte History-Daten lokal in das aktuelle referenzbasierte Format überführt, wenn das eindeutig möglich ist.

### Updates
Der Haupteinstieg übernimmt jetzt auch Updates. Verwende `python3 tesla_order_status.py --update`, um den Update-Ablauf direkt aus der primären CLI zu starten, statt in ein separates Werkzeug zu wechseln.

`python3 tesla_order_status.py --update` startet den interaktiven Prüf-/Download-/Anwendungs-Ablauf. Mit `python3 tesla_order_status.py --update pfad/zum/release.zip --sha256 <erwartete-sha256>` kannst du auch direkt ein lokales ZIP anwenden. Vor dem Entpacken bleibt immer eine SHA-256-Prüfung erforderlich.

## Historie & Vorschau

Die aktuellen Bestellinfos werden in `data/private/tesla_orders.json` gespeichert; Änderungen landen zusätzlich in `data/private/tesla_order_history.json`. Jede erkannte Abweichung, etwa VIN-Zuteilungen oder Änderungen am Lieferfenster, wird an die Historie angehängt und nach dem aktuellen Status angezeigt. Zuerst siehst du **Live‑Daten**, darunter die **Historie**.

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

#### Beispiel Share-Modus

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

## Datenschutz & Support

* Das Tool läuft lokal auf deinem Rechner und benötigt Tesla-API-Zugriff für Anmeldung und Bestelldaten.
* Optionaler GitHub-Traffic ist auf Release-Metadaten und explizite Release-Downloads im Update-Ablauf begrenzt.
* Telemetry, Remote-Banner und externe Option‑Code-Lookups sind nicht Teil des Laufzeitpfads.
* Tesla-Tokens werden nur dann lokal für spätere Läufe gespeichert, wenn du dem Speichern zustimmst.
* Wenn etwas schiefläuft, melde es über [GitHub Issues](https://github.com/enoch85/tesla-order-status/issues).
