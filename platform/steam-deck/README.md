# A Union Before Midnight: Steam Deck Edition

This directory is the platform layer for a private, console-quality Steam Deck
installation. It does not fork gameplay data. The same hash-validated V4.2
overlay is installed over the Deck's own `Darkest Hour Full` files.

## Current Contract

- Native 1280x800 configuration with sprites, sound, and country graphics on.
- Direct `Darkest Hour.exe` launch while preserving Steam's Proton wrapper.
- Isolated mod directory; no edits to `Darkest Hour Full`.
- Full SHA-256 validation before and after installation.
- Managed updates restore files removed from later overlays to their DH Full base.
- Save mirror plus rotating snapshots before and after every play session.
- Per-game Steam Deck controller layout with cursor, dedicated event-action
  navigation, orders, pause, speed, zoom, map pan, keyboard, menu, and modifiers.

## Install On Deck

1. Install Darkest Hour through Steam and launch it once in Desktop Mode.
2. Extract the AUBM Steam Deck package.
3. In Konsole, run:

   ```bash
   chmod +x platform/steam-deck/*.sh
   ./platform/steam-deck/install-aubm-deck.sh
   ```

4. Paste the printed launch option into Darkest Hour > Properties > Launch Options.
5. If Steam was open during installation, exit it completely and run the
   controller command printed by the installer. The layout is registered as
   Darkest Hour's per-game autosave and does not need to be selected manually.

The installer finds internal and common microSD Steam libraries. Use
`--game-root PATH` when the library has a nonstandard location.

## Useful Commands

```bash
~/.local/share/aubm-deck/bin/manage-aubm-saves status
~/.local/share/aubm-deck/bin/manage-aubm-saves list
~/.local/share/aubm-deck/bin/manage-aubm-saves restore-latest
~/.local/share/aubm-deck/bin/install-aubm-controller \
  --profile ~/.local/share/aubm-deck/controller/aubm-steam-deck.vdf
./platform/steam-deck/package-aubm-deck.sh --verify-only
./platform/steam-deck/test-aubm-deck.sh
```

Set `AUBM_DECK_SYNC_DIR` in `~/.local/share/aubm-deck/config.env` to mirror saves
to an existing Syncthing, cloud-drive, or removable-storage directory. The save
manager never deletes files from that directory.

## Verification Boundary

The Linux installer and launcher can be tested without running Darkest Hour.
Controller feel, text legibility, Steam keyboard behavior, and Proton version
must be verified once on the physical Deck. Those checks are intentionally not
claimed complete from desktop simulation.

Valve's current compatibility checklist requires 1280x800 support, at least
30 fps at default settings, complete physical-control access, launcher-free
startup, text-input support, and legible interface text. The absolute text
minimum is 9 pixels at 1280x800, with 12 pixels recommended. See:

- https://partner.steamgames.com/doc/steamhardware/compat
- https://partner.steamgames.com/doc/steamhardware/recommendations
- https://partner.steamgames.com/doc/steamhardware/proton
