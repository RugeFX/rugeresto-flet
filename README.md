# FletTest app

The restaurant menu data lives in `src/shared/menu.json`; order and payment rules
live in `src/shared/restaurant.py`.
`src/gui/` contains the Flet interface, and `src/cli/` contains the terminal
interface. Each interface creates its own `RestaurantOrder`, so orders do not
leak between sessions. The original `src/base.py` is kept as an untouched
reference.

```text
src/
├── main.py                 # Flet launcher
├── gui/
│   ├── __main__.py         # GUI module entry point
│   ├── app.py              # Page setup, order state, and event handlers
│   ├── theme.py            # Colors and menu icons
│   └── components/
│       ├── layout.py       # Page shell and responsive layout
│       ├── menu.py         # Menu sections and item cards
│       ├── order_row.py    # Quantity controls and item removal
│       └── order_panel.py  # Order summary, payment, and feedback
├── cli/
│   ├── __main__.py         # Terminal entry point
│   └── app.py              # Terminal prompts and interaction loop
├── shared/
│   ├── __init__.py         # Shared package
│   ├── restaurant.py       # Shared ordering logic
│   └── menu.json           # Shared menu data
└── base.py                 # Original reference
```

## Shared order interface

`RestaurantOrder` exposes `add(number, quantity)`,
`set_quantity(number, quantity)`, `change_quantity(number, difference)`,
`remove(number)`, and `pay(amount)`. Read `lines`, `item_count`, and
`total` to display the current order. `pay` returns a receipt with the
paid amount and change, then clears that order. Invalid operations raise
`RestaurantError` subclasses and leave the order intact. Menu entries are
available as the immutable `MENU` tuple.

To add or edit menu items, edit `src/shared/menu.json` and restart the app or CLI.
Each record has a unique positive integer `number`, a `name`, an integer
`price` in rupiah (for example, `20000`), a `category`, and a `detail`.
The file is loaded on startup relative to `restaurant.py`, so it works
regardless of the current working directory. Invalid records cause a startup
error. This is a simple file-backed menu; the app does not write changes to it.

## Run the app

### uv

Run as a desktop app:

```bash
uv run flet run
```

Run as a web app:

```bash
uv run flet run --web
```

Run the terminal interface:

```bash
PYTHONPATH=src uv run python -m cli
```

Run the core and CLI tests:

```bash
uv run pytest tests/test_restaurant.py tests/test_menu.py tests/test_cli.py
```

For more details on running the app, refer to the [Getting Started Guide](https://flet.dev/docs/).

## Build the app

### Android

```bash
flet build apk -v
```

For more details on building and signing `.apk` or `.aab`, refer to the [Android Packaging Guide](https://flet.dev/docs/publish/android/).

### iOS

```bash
flet build ipa -v
```

For more details on building and signing `.ipa`, refer to the [iOS Packaging Guide](https://flet.dev/docs/publish/ios/).

### macOS

```bash
flet build macos -v
```

For more details on building macOS package, refer to the [macOS Packaging Guide](https://flet.dev/docs/publish/macos/).

### Linux

```bash
flet build linux -v
```

For more details on building Linux package, refer to the [Linux Packaging Guide](https://flet.dev/docs/publish/linux/).

### Windows

```bash
flet build windows -v
```

For more details on building Windows package, refer to the [Windows Packaging Guide](https://flet.dev/docs/publish/windows/).

### Web

```bash
flet build web -v
```

For more details on building Web app, refer to the [Web Packaging Guide](https://flet.dev/docs/publish/web/).
