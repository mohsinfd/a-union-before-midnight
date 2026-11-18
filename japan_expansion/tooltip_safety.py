"""Keep specialist description/model tooltips below the observed native limit.

The 18 November 2026 crash has EIP 0x694d2820: exactly bytes 256..259
of the Mixed Brigade description + newline + model label (270 bytes total).
Only display strings are changed here. No catalogue or unit mechanics mutate.
"""
import re

MAX_DESCRIPTION_BYTES=140
MAX_TOOLTIP_BYTES=224
DESCRIPTIONS={
 'd_13':'Anti-aircraft destroyers for carrier defence. Strong AA fire, but weaker torpedo attack and higher cost than ordinary destroyers.',
 'd_14':'Long-range flying boats for sea patrols and reconnaissance. Excellent reach and detection, but weaker attacks and higher cost.',
 'd_15':'Airborne infantry with high morale and organisation. Needs transport aircraft and airborne doctrine. Costs more than ordinary paratroopers.',
 'd_16':'Shore-based naval fighters with long range. Greater fuel use and vulnerability than ordinary fighters. Cannot serve on carriers.',
 'd_17':'Long-range naval bombers. Good reach and low purchase cost, but greater fuel demand and vulnerability. Weak ground attack.',
 'd_18':'Cheap Matsu escorts for convoy and anti-submarine work. Weaker surface firepower, speed and range than fleet destroyers.',
 'd_19':'Expeditionary infantry for jungle and island campaigns. Easier to supply, but less defence and anti-armour firepower. Normal landing limits.',
 'b_01':'Oxygen torpedoes for destroyers and cruisers. Strong surface and convoy attack, with greater ammunition and supply demand.',
 'b_02':'Mixed troops for occupation and local defence. More suppression and firepower than military police. Movement is limited to four.',
 'b_03':'Small amphibious tank units for infantry and Marine landings. Stronger shore attacks, with less fuel demand than a full tank brigade.',
}


def player_text(key,value):
    match=re.fullmatch(r'JX_([db]_\d+)_DESC',key)
    if match and match[1] in DESCRIPTIONS:value=DESCRIPTIONS[match[1]]
    # Owned narrative strings contain literal percentages, not printf fields.
    # Never rewrite stock format strings or engine-owned CSV entries.
    if key.startswith('JX_'):value=re.sub(r'\s*%', ' percent',value)
    if match and len(value.encode('latin1'))>MAX_DESCRIPTION_BYTES:
        raise ValueError('Specialist description exceeds the native safety budget: '+key)
    return value


def check_payload(description,model_label):
    if '%' in description+model_label or '\xa7' in description+model_label:
        raise ValueError('Unsafe formatting code in specialist tooltip')
    size=len((description+'\n'+model_label+'\0').encode('latin1'))
    if size>MAX_TOOLTIP_BYTES:
        raise ValueError('Specialist tooltip exceeds safety budget: '+str(size)+' '+model_label)
    return size
