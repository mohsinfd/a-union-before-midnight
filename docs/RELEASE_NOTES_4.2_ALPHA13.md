# A Union Before Midnight 4.2.0-alpha.13

## Command Reserve

- Added 31 real Indian and subcontinental officers as plausibly accelerated
  wartime commanders, without replacing the established leader roster.
- India now fields at least 80 active land leaders in 1938 and 90 in 1940.
- Restored Commando qualifications to historically appropriate Gurkha, INA,
  airborne and frontier officers; nine are active by 1938.
- Added production gates that reject future releases if the land or commando
  leader reserve falls below these campaign requirements.

## Fleet Structure

- Rebuilt the Arabian Sea Fleet around one battleship, two light cruisers and
  two destroyer flotillas.
- Rebuilt the Bay of Bengal Fleet to the same capital-led standard.
- Ensured every Indian Ocean programme has a true capital core: fleet carrier,
  two light carriers, or battlecruiser. Heavy and light cruisers remain
  auxiliaries rather than being misclassified as capital ships.
- Event syntax can fit only one brigade directly to a commissioned hull. Each
  contract therefore attaches one legal module and supplies the remaining
  current-model capital/cruiser components to the deployment pool.

## Naval Construction

- Mature national yards now reduce new orders for every hull class by 50
  percent of model-zero build time while retaining normal daily IC cost.
- Added a migration event that brings campaigns with the older 10/15/20
  percent dockyard standard to the new target without editing their save.
- Existing ships already in production retain their serialized completion
  dates; place a new order after the standard fires to see the new schedule.

## Legal Equipment

- Removed escort-fighter brigades from interceptors, multi-role fighters and
  CAS, which cannot mount them in Darkest Hour.
- Retained escort brigades on transport and bomber airframes where the engine
  explicitly permits them.
- Corrected invalid submarine, mountain, garrison, airborne, armoured and jet
  event attachments to legal, role-appropriate equipment.
- Validation now cross-checks every event attachment against the receiving
  unit's effective `allowed_brigades` table.

## Specialist Formations

- Gurkhas specialize in mountain and snow combat.
- Frontier Forces emphasize mountain, hill and desert mobility and defence.
- Chindit columns specialize in jungle, forest, swamp and night operations.
- Indian Airborne, Coromandel Marines and Pioneers receive distinct airborne,
  amphibious, river-crossing and urban-engineering doctrine bonuses.
- Added an automatic doctrine migration event for formations commissioned in
  an existing campaign before Alpha 13.

## Save Compatibility

The leader roster requires a new campaign because leaders are serialized into
the save. Dockyard and specialist-doctrine migrations work in an existing
Alpha 12 campaign. Regional fleet contracts that have not yet been selected
use the new composition; ships already ordered cannot be rewritten safely.
