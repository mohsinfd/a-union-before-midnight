# A Union Before Midnight 4.2.0-alpha.11

## Runtime-Proven Special-Unit Repair

- Corrected the localization target from `extra_text.csv` to Darkest Hour's
  active `unit_names.csv`, following working custom division implementations
  in installed mods. All 40 special-unit type, short-name, description and
  model-name keys are now inserted once before the table's final `#EOF` row.
- Added the actual 67x44 division-card assets used by the interface:
  `IND_model_33_0.bmp` through `IND_model_40_0.bmp`, with matching generic
  `model_33_0.bmp` through `model_40_0.bmp` fallbacks.
- Retained the valid 192x104 `ill_div` panels and numeric animated map-sprite
  families `d_74` through `d_81` introduced in Alpha 10.
- Expanded the special-unit release gate to reject missing, malformed or
  misnamed small model icons and to require localization in `unit_names.csv`.
- Removed the obsolete generated `extra_text.csv` overlay.

## Compatibility

The corrected text and model icons are data-driven and apply to an existing
save after a complete game restart. No new campaign is required.
