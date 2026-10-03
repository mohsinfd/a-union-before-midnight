# Steam Deck Product Standard

The Steam Deck edition is a platform layer around the exact V4.2 gameplay
payload. It targets a personal installation with the same discipline expected
from an officially supported build.

## Default Controls

| Deck control | Darkest Hour action |
| --- | --- |
| Right trackpad | Mouse cursor |
| Right trigger / left trigger | Left click / right click |
| A / B / X / Y | Pause / cancel / confirm / game menu |
| Right stick up / down | Move through the event or decision action strip |
| Right-stick click / X | Select the hovered action / press Enter |
| Left stick | Pan the map |
| Left / right bumper | Reduce / increase game speed |
| D-pad up / down | Zoom in / out |
| D-pad right / left | Political map / statistics |
| Left trackpad slots 1-0 | Recall numbered control groups |
| Upper-left rear button | Hold Shift for additive selection and queued orders |
| Upper-right rear button | Hold Ctrl while touching a numbered slot to assign a group |
| Lower-left rear button | Quick save |
| Lower-right rear button | Steam keyboard |

The profile exposes Darkest Hour's existing Shift-click and Ctrl-number
shortcuts in Gaming Mode. The engine has no global "select every cavalry" or
"convert every eligible ship" command, so type-wide selection and batch
cross-type conversion cannot be added by a controller layout alone.

The layout follows the useful part of Age of Empires II's controller approach:
keep frequent map actions immediately available, then expose a second held
layer for selection and groups. Darkest Hour cannot switch native action sets,
so the upper rear buttons act as held Shift and Ctrl layers while both triggers
remain dedicated mouse buttons. The left trackpad's labelled group menu follows
Valve's guidance for strategy-game touch and radial menus.

- Age of Empires II controller reference: https://support.ageofempires.com/hc/en-us/articles/37041870568468-Age-of-Empires-II-Definitive-Edition-Default-Controller-Layouts
- Steam Input menus: https://partner.steamgames.com/doc/features/steam_controller/radial_menus

## Acceptance Gates

### Installation

- Fresh install and managed update both pass all SHA-256 checks.
- `Darkest Hour Full` remains unchanged.
- Internal storage and microSD Steam libraries are discovered.
- Launch options bypass only the DH launcher and retain Steam/Proton arguments.
- Reinstalling does not delete campaigns or protected save backups.
- Managed updates back up and replace AppID 73170's stale AUBM controller
  autosave, so an obsolete profile cannot survive a successful deployment.

### Handheld Experience

- 1280x800 fills the 16:10 display without clipping.
- The smallest interface characters are at least 9 pixels high at 1280x800;
  12 pixels is the preferred target.
- The right trackpad reaches every interface control precisely.
- The right stick is a vertical-only mouse region constrained to the fixed
  event-action strip; it cannot pan the map or roam across the interface.
- Pause, speed, zoom, pan, confirmation, cancellation, and orders need no keyboard.
- Text fields can invoke the Steam keyboard.
- A complete 1933-1945 session can be played without Desktop Mode.

### Reliability

- A save mirror is refreshed on every launch.
- Changed saves receive pre/post-session snapshots; unchanged saves do not create
  duplicate archives.
- The latest snapshot can be restored without deleting newer manual save names.
- Normal play keeps debug logging off; a debug launch is available for diagnosis.

### Performance

- Stable frame pacing at the Deck's 60 Hz mode is preferred over an arbitrary
  high frame rate.
- Battery and thermal profiles will be measured on hardware before choosing a
  final TDP or frame-rate cap.
- Resume/suspend behavior must be tested at the map, event popup, and save dialog.

## Hardware Test Card

The first Deck session should test only platform behavior:

1. Launch from Gaming Mode into the 1933 scenario.
2. Inspect the map and each top-level interface at native 1280x800.
3. Pan, zoom, Shift-select several formations, assign and recall a control
   group, issue an order, pause, and change speed.
4. Open an event and use only the right stick plus its click to choose an action.
5. Open a decision, research, production, diplomacy, and the save dialog.
6. Enter a save name with the Steam keyboard.
7. Suspend for five minutes, resume, save, exit, and relaunch.
8. Confirm a post-session snapshot exists.

Gameplay balancing is outside this card; the test is deliberately short and
should not consume another campaign.

## Valve References

- Compatibility checklist: https://partner.steamgames.com/doc/steamhardware/compat
- Deck recommendations: https://partner.steamgames.com/doc/steamhardware/recommendations
- Proton guidance: https://partner.steamgames.com/doc/steamhardware/proton
