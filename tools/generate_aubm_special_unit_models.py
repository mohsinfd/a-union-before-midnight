#!/usr/bin/env python3
"""Generate deterministic AUBM specialist model ladders and upgrade events."""

from __future__ import annotations

import csv
import json
import pathlib
import re
from copy import deepcopy


ROOT = pathlib.Path(__file__).resolve().parents[1]
DIVISION_ROOT = ROOT / "mod/db/units/divisions"
LOCALIZATION_PATH = ROOT / "mod/config/aubm_special_unit_models.csv"
OBSOLETE_EVENT_PATH = ROOT / "mod/db/events/aubm_v4/41_special_unit_modernisation.txt"

STAT_FIELDS = (
    "cost",
    "buildtime",
    "manpower",
    "maxspeed",
    "defaultorganisation",
    "morale",
    "defensiveness",
    "toughness",
    "softness",
    "suppression",
    "airdefence",
    "softattack",
    "hardattack",
    "airattack",
    "transportweight",
    "supplyconsumption",
    "fuelconsumption",
    "upgrade_time_factor",
    "upgrade_cost_factor",
    "reinforce_time",
    "reinforce_cost",
)


def stage(label: str, techs: tuple[int, ...], **changes: object) -> dict[str, object]:
    return {"label": label, "techs": techs, **changes}


UNITS: dict[int, dict[str, object]] = {
    33: {
        "comment": "Gurkha Rifles, elite mountain formations with a selective training base.",
        "brigades": ("artillery", "anti_air", "engineer"),
        "commission_flag": "ind_aubm_gurkha_rifles_commissioned",
        "event_name": "The Gurkha Rifles Modernisation Board",
        "picture": "Gurkha",
        "base": {
            "cost": 8, "buildtime": 500, "manpower": 11, "maxspeed": 6,
            "defaultorganisation": 48, "morale": 60, "defensiveness": 42,
            "toughness": 44, "softness": 100, "suppression": 2,
            "airdefence": 14, "softattack": 12, "hardattack": 2,
            "airattack": 2, "transportweight": 7, "supplyconsumption": 0.75,
            "fuelconsumption": 0, "upgrade_time_factor": 0.20,
            "upgrade_cost_factor": 0.75, "reinforce_time": 0.50,
            "reinforce_cost": 0.40,
        },
        "equipment": {
            "manpower": 11000, "trucks": 550, "horses": 4400, "artillery": 50,
            "heavy_artillery": 12, "anti_tank": 20, "anti_air": 12,
        },
        "stages": (
            stage("Gurkha Rifles Division", ()),
            stage("1942 Reorganised Gurkha Rifles", (1270,), cost=8.5,
                  defaultorganisation=50, morale=62, defensiveness=44, toughness=46,
                  softness=95, airdefence=16, softattack=14, hardattack=3, airattack=3,
                  supplyconsumption=0.8,
                  equipment={"trucks": 620, "artillery": 60, "heavy_artillery": 16,
                             "anti_tank": 28, "anti_air": 16}),
            stage("1945 Integrated Gurkha Rifles", (1280,), cost=9,
                  defaultorganisation=52, morale=64, defensiveness=46, toughness=48,
                  softness=95, airdefence=18, softattack=16, hardattack=4, airattack=3,
                  supplyconsumption=0.9,
                  equipment={"trucks": 700, "artillery": 72, "heavy_artillery": 18,
                             "anti_tank": 36, "anti_air": 20}),
            stage("1951 Gurkha Brigade Group", (1300,), cost=9.5, maxspeed=7,
                  defaultorganisation=54, morale=66, defensiveness=48, toughness=50,
                  softness=90, airdefence=20, softattack=18, hardattack=6, airattack=4,
                  supplyconsumption=1.0, fuelconsumption=0.1,
                  equipment={"trucks": 900, "artillery": 84, "heavy_artillery": 20,
                             "anti_tank": 48, "anti_air": 24}),
            stage("1959 Modern Gurkha Rifles", (13040,), cost=10, buildtime=480,
                  manpower=10, maxspeed=7, defaultorganisation=56, morale=68,
                  defensiveness=50, toughness=52, softness=85, airdefence=22,
                  softattack=21, hardattack=8, airattack=5, supplyconsumption=1.1,
                  fuelconsumption=0.2,
                  equipment={"manpower": 10000, "trucks": 1200, "horses": 1800,
                             "artillery": 96, "heavy_artillery": 24, "anti_tank": 60,
                             "anti_air": 30}),
        ),
    },
    34: {
        "comment": "Frontier Force Rifles for mobile patrol, intelligence, and security.",
        "brigades": ("artillery", "anti_air", "armored_car", "engineer", "police"),
        "commission_flag": "ind_aubm_frontier_force_commissioned",
        "event_name": "Frontier Force Modernisation",
        "picture": "india_v3_elite_frontier",
        "base": {
            "cost": 7, "buildtime": 360, "manpower": 10, "maxspeed": 8,
            "defaultorganisation": 42, "morale": 48, "defensiveness": 38,
            "toughness": 38, "softness": 100, "suppression": 8,
            "airdefence": 14, "softattack": 9, "hardattack": 1, "airattack": 2,
            "transportweight": 6, "supplyconsumption": 0.6, "fuelconsumption": 0.05,
            "upgrade_time_factor": 0.20, "upgrade_cost_factor": 0.75,
            "reinforce_time": 0.45, "reinforce_cost": 0.40,
        },
        "equipment": {
            "manpower": 10000, "trucks": 720, "horses": 3900, "artillery": 42,
            "heavy_artillery": 8, "anti_tank": 20, "anti_air": 10, "armored_car": 12,
        },
        "stages": (
            stage("Frontier Force Division", ()),
            stage("1942 Frontier Mobile Group", (1270,), cost=7.5,
                  defaultorganisation=44, morale=50, defensiveness=40, toughness=40,
                  airdefence=16, softattack=11, hardattack=2, airattack=3,
                  supplyconsumption=0.65,
                  equipment={"trucks": 900, "artillery": 48, "anti_tank": 28,
                             "anti_air": 14, "armored_car": 18}),
            stage("1945 Frontier Brigade Group", (1280,), cost=8,
                  defaultorganisation=46, morale=52, defensiveness=42, toughness=42,
                  softness=95, suppression=9, airdefence=18, softattack=13,
                  hardattack=3, airattack=3, supplyconsumption=0.7,
                  equipment={"trucks": 1100, "horses": 3000, "artillery": 56,
                             "anti_tank": 36, "anti_air": 18, "armored_car": 24}),
            stage("1951 Frontier Surveillance Group", (1300,), cost=8.5, maxspeed=9,
                  defaultorganisation=48, morale=54, defensiveness=44, toughness=44,
                  softness=92, suppression=10, airdefence=20, softattack=15,
                  hardattack=5, airattack=4, supplyconsumption=0.8,
                  fuelconsumption=0.1,
                  equipment={"trucks": 1400, "horses": 2200, "artillery": 64,
                             "anti_tank": 44, "anti_air": 22, "armored_car": 36}),
            stage("1959 Modern Frontier Rifles", (13040,), cost=9, manpower=9,
                  maxspeed=9, defaultorganisation=50, morale=56, defensiveness=46,
                  toughness=46, softness=88, suppression=12, airdefence=22,
                  softattack=18, hardattack=7, airattack=5, supplyconsumption=0.9,
                  fuelconsumption=0.2,
                  equipment={"manpower": 9000, "trucks": 1800, "horses": 1000,
                             "artillery": 72, "anti_tank": 56, "anti_air": 28,
                             "armored_car": 48}),
        ),
    },
    35: {
        "comment": "Long-range penetration columns inspired by the historic Chindits.",
        "brigades": ("artillery", "armored_car", "engineer"),
        "commission_flag": "ind_aubm_chindit_columns_commissioned",
        "event_name": "Long-Range Group Modernisation",
        "picture": "india_v3_elite_penetration",
        "base": {
            "cost": 8, "buildtime": 450, "manpower": 9, "maxspeed": 8,
            "defaultorganisation": 50, "morale": 58, "defensiveness": 29,
            "toughness": 44, "softness": 100, "suppression": 2,
            "airdefence": 14, "softattack": 10, "hardattack": 1, "airattack": 2,
            "transportweight": 4, "supplyconsumption": 0.55, "fuelconsumption": 0.05,
            "upgrade_time_factor": 0.20, "upgrade_cost_factor": 0.75,
            "reinforce_time": 0.55, "reinforce_cost": 0.45,
        },
        "equipment": {
            "manpower": 9000, "trucks": 850, "horses": 1200, "artillery": 36,
            "heavy_artillery": 8, "anti_tank": 18, "anti_air": 12, "armored_car": 8,
        },
        "stages": (
            stage("Chindit Penetration Group", ()),
            stage("1942 Air-Supplied Penetration Group", (1270,), cost=8.5,
                  defaultorganisation=52, morale=60, defensiveness=31, toughness=46,
                  airdefence=16, softattack=12, hardattack=2, airattack=3,
                  equipment={"trucks": 1000, "artillery": 42, "anti_tank": 24,
                             "anti_air": 16, "armored_car": 12}),
            stage("1945 Integrated Long-Range Group", (1280,), cost=9,
                  defaultorganisation=54, morale=62, defensiveness=33, toughness=48,
                  softness=95, airdefence=18, softattack=14, hardattack=3, airattack=3,
                  supplyconsumption=0.6,
                  equipment={"trucks": 1200, "artillery": 48, "anti_tank": 30,
                             "anti_air": 20, "armored_car": 18}),
            stage("1951 Air-Mobile Penetration Group", (1300,), cost=9.5, maxspeed=9,
                  defaultorganisation=56, morale=64, defensiveness=35, toughness=50,
                  softness=90, airdefence=20, softattack=16, hardattack=5,
                  airattack=4, supplyconsumption=0.7, fuelconsumption=0.1,
                  equipment={"trucks": 1500, "horses": 600, "artillery": 56,
                             "anti_tank": 40, "anti_air": 24, "armored_car": 24}),
            stage("1959 Modern Penetration Division", (13040,), cost=10, manpower=8,
                  maxspeed=9, defaultorganisation=58, morale=66, defensiveness=37,
                  toughness=52, softness=86, airdefence=22, softattack=19,
                  hardattack=7, airattack=5, supplyconsumption=0.8,
                  fuelconsumption=0.2,
                  equipment={"manpower": 8000, "trucks": 1900, "horses": 200,
                             "artillery": 64, "anti_tank": 52, "anti_air": 30,
                             "armored_car": 36}),
        ),
    },
    36: {
        "comment": "Indian airborne formations based on the 50th Parachute Brigade.",
        "brigades": ("glider_armor", "glider_artillery"),
        "commission_flag": "ind_aubm_airborne_commissioned",
        "event_name": "The Airborne Equipment Board",
        "picture": "india_v3_elite_airborne",
        "base": {
            "cost": 11, "buildtime": 450, "manpower": 9, "maxspeed": 6,
            "defaultorganisation": 40, "morale": 45, "defensiveness": 35,
            "toughness": 40, "softness": 100, "suppression": 3,
            "airdefence": 14, "softattack": 11, "hardattack": 1, "airattack": 1,
            "transportweight": 7, "supplyconsumption": 1.0, "fuelconsumption": 0,
            "upgrade_time_factor": 0.15, "upgrade_cost_factor": 0.75,
            "reinforce_time": 0.60, "reinforce_cost": 0.40,
        },
        "equipment": {"manpower": 9000, "artillery": 8, "anti_tank": 4, "anti_air": 16},
        "stages": (
            stage("Indian Airborne Division", ()),
            stage("1941 Airborne Brigade Group", (1680,), cost=11.5,
                  defaultorganisation=42, morale=47, defensiveness=37, toughness=42,
                  airdefence=16, softattack=13, hardattack=2, airattack=2,
                  equipment={"artillery": 12, "anti_tank": 8, "anti_air": 20}),
            stage("1944 Integrated Airborne Division", (1690,), cost=12,
                  defaultorganisation=44, morale=49, defensiveness=39, toughness=44,
                  softness=95, airdefence=18, softattack=15, hardattack=5,
                  airattack=3, supplyconsumption=1.05,
                  equipment={"artillery": 18, "anti_tank": 16, "anti_air": 24}),
            stage("1950 Air-Mobile Division", (1710,), cost=12.5,
                  defaultorganisation=46, morale=52, defensiveness=42, toughness=46,
                  softness=90, airdefence=20, softattack=18, hardattack=7,
                  airattack=4, supplyconsumption=1.1,
                  equipment={"trucks": 300, "artillery": 24, "anti_tank": 24,
                             "anti_air": 30}),
            stage("1957 Modern Airborne Division", (1730,), cost=13, manpower=8,
                  maxspeed=7, defaultorganisation=48, morale=55, defensiveness=45,
                  toughness=48, softness=85, airdefence=22, softattack=21,
                  hardattack=9, airattack=5, supplyconsumption=1.2,
                  fuelconsumption=0.1,
                  equipment={"manpower": 8000, "trucks": 600, "artillery": 30,
                             "anti_tank": 32, "anti_air": 36}),
        ),
    },
    37: {
        "comment": "Coromandel Marines for Indian Ocean and littoral operations.",
        "brigades": ("artillery", "anti_air", "engineer"),
        "commission_flag": "ind_aubm_coromandel_marines_commissioned",
        "event_name": "Coromandel Marine Modernisation",
        "picture": "india_v3_elite_marines",
        "base": {
            "cost": 9, "buildtime": 450, "manpower": 13, "maxspeed": 6,
            "defaultorganisation": 40, "morale": 45, "defensiveness": 35,
            "toughness": 40, "softness": 100, "suppression": 3,
            "airdefence": 14, "softattack": 10, "hardattack": 1, "airattack": 2,
            "transportweight": 9, "supplyconsumption": 1.0, "fuelconsumption": 0.1,
            "upgrade_time_factor": 0.25, "upgrade_cost_factor": 0.75,
            "reinforce_time": 0.60, "reinforce_cost": 0.40,
        },
        "equipment": {
            "manpower": 13000, "trucks": 120, "artillery": 48,
            "heavy_artillery": 8, "anti_tank": 36, "anti_air": 18,
        },
        "stages": (
            stage("Coromandel Marine Division", ()),
            stage("1940 Coromandel Landing Group", (1600,), cost=9.5,
                  defaultorganisation=42, morale=47, defensiveness=37, toughness=42,
                  softness=95, airdefence=16, softattack=12, hardattack=2,
                  airattack=3, supplyconsumption=1.05,
                  equipment={"trucks": 200, "artillery": 56, "anti_tank": 42,
                             "anti_air": 22}),
            stage("1943 Fleet Marine Division", (1610,), cost=10,
                  defaultorganisation=44, morale=49, defensiveness=39, toughness=44,
                  softness=95, airdefence=18, softattack=14, hardattack=4,
                  airattack=3, supplyconsumption=1.1, fuelconsumption=0.2,
                  equipment={"trucks": 320, "artillery": 64, "anti_tank": 50,
                             "anti_air": 26}),
            stage("1949 Amphibious Brigade Group", (1630,), cost=10.5,
                  manpower=12, maxspeed=7, defaultorganisation=46, morale=52,
                  defensiveness=42, toughness=46, softness=90, airdefence=20,
                  softattack=17, hardattack=6, airattack=4, supplyconsumption=1.2,
                  fuelconsumption=0.3,
                  equipment={"manpower": 12000, "trucks": 500, "artillery": 74,
                             "heavy_artillery": 12, "anti_tank": 60, "anti_air": 32}),
            stage("1957 Modern Coromandel Marines", (1650,), cost=11,
                  manpower=12, maxspeed=7, defaultorganisation=48, morale=55,
                  defensiveness=45, toughness=48, softness=85, airdefence=22,
                  softattack=20, hardattack=8, airattack=5, supplyconsumption=1.3,
                  fuelconsumption=0.5,
                  equipment={"manpower": 12000, "trucks": 800, "artillery": 84,
                             "heavy_artillery": 16, "anti_tank": 72, "anti_air": 40}),
        ),
    },
    38: {
        "comment": "Guards Armoured Division, a selective Indian heavy field formation.",
        "brigades": ("medium_armor", "anti_air", "sp_artillery", "sp_anti_air",
                     "tank_destroyer", "heavy_armor", "light_armor_brigade",
                     "armored_car", "engineer"),
        "commission_flag": "ind_aubm_guards_armour_commissioned",
        "event_name": "Guards Armour Modernisation",
        "picture": "aubm_v4_army_commands",
        "base": {
            "cost": 23, "buildtime": 390, "manpower": 8, "maxspeed": 18,
            "defaultorganisation": 35, "morale": 35, "defensiveness": 19,
            "toughness": 23, "softness": 30, "suppression": 1,
            "airdefence": 8, "softattack": 16, "hardattack": 8, "airattack": 4,
            "transportweight": 32, "supplyconsumption": 2.4, "fuelconsumption": 13,
            "upgrade_time_factor": 0.60, "upgrade_cost_factor": 0.75,
            "reinforce_time": 0.65, "reinforce_cost": 0.75,
        },
        "extra": {"no_fuel_combat_mod": -0.3},
        "equipment": {
            "manpower": 8000, "trucks": 800, "artillery": 60,
            "heavy_artillery": 10, "anti_tank": 20, "anti_air": 18,
            "armored_car": 52, "medium_armor": 320,
        },
        "stages": (
            stage("Guards Armoured Division", ()),
            stage("1941 Guards Armoured Division", (2080,), cost=24,
                  defaultorganisation=37, morale=37, defensiveness=20, toughness=24,
                  softness=28, airdefence=10, softattack=17, hardattack=9,
                  airattack=5, supplyconsumption=2.6,
                  equipment={"trucks": 900, "artillery": 68, "anti_tank": 28,
                             "anti_air": 22, "armored_car": 60, "medium_armor": 340}),
            stage("1943 Guards Armoured Division", (2090,), cost=25, maxspeed=20,
                  defaultorganisation=39, morale=39, defensiveness=21, toughness=25,
                  softness=26, airdefence=12, softattack=18, hardattack=10,
                  airattack=5, supplyconsumption=2.8, fuelconsumption=13.5,
                  equipment={"trucks": 1000, "artillery": 76, "anti_tank": 36,
                             "anti_air": 26, "armored_car": 64, "medium_armor": 350}),
            stage("1945 Guards Armoured Division", (2140,), cost=26, maxspeed=20,
                  defaultorganisation=41, morale=41, defensiveness=22, toughness=26,
                  softness=25, airdefence=14, softattack=19, hardattack=11,
                  airattack=6, supplyconsumption=3.0, fuelconsumption=13.5,
                  equipment={"trucks": 1100, "artillery": 84, "heavy_artillery": 14,
                             "anti_tank": 44, "anti_air": 30, "armored_car": 68,
                             "medium_armor": 360}),
            stage("1952 Guards Main Battle Group", (2660,), cost=28, maxspeed=20,
                  defaultorganisation=43, morale=43, defensiveness=24, toughness=28,
                  softness=22, airdefence=16, softattack=21, hardattack=13,
                  airattack=7, supplyconsumption=3.1, fuelconsumption=13.5,
                  equipment={"trucks": 1250, "artillery": 96, "heavy_artillery": 18,
                             "anti_tank": 56, "anti_air": 36, "armored_car": 72,
                             "medium_armor": 380}),
            stage("1962 Modern Guards Armoured Division", (2670,), cost=30,
                  maxspeed=22, defaultorganisation=45, morale=45, defensiveness=26,
                  toughness=30, softness=18, airdefence=18, softattack=23,
                  hardattack=15, airattack=8, supplyconsumption=3.3,
                  fuelconsumption=14,
                  equipment={"trucks": 1500, "artillery": 110, "heavy_artillery": 22,
                             "anti_tank": 70, "anti_air": 44, "armored_car": 80,
                             "medium_armor": 400}),
        ),
    },
    39: {
        "comment": "Guards Motorised Division for operational reserve and exploitation.",
        "brigades": ("medium_armor", "sp_artillery", "sp_anti_air", "tank_destroyer",
                     "light_armor_brigade", "armored_car", "engineer"),
        "commission_flag": "ind_aubm_guards_motorised_commissioned",
        "event_name": "Guards Motorised Modernisation",
        "picture": "aubm_v4_army_commands",
        "base": {
            "cost": 16, "buildtime": 345, "manpower": 12, "maxspeed": 26,
            "defaultorganisation": 35, "morale": 35, "defensiveness": 23,
            "toughness": 29, "softness": 85, "suppression": 4,
            "airdefence": 8, "softattack": 12, "hardattack": 3, "airattack": 3,
            "transportweight": 30, "supplyconsumption": 1.7, "fuelconsumption": 6.5,
            "upgrade_time_factor": 0.45, "upgrade_cost_factor": 0.66,
            "reinforce_time": 0.50, "reinforce_cost": 0.66,
        },
        "equipment": {
            "manpower": 12000, "trucks": 3000, "horses": 900, "artillery": 70,
            "heavy_artillery": 10, "anti_tank": 36, "anti_air": 56, "armored_car": 36,
        },
        "stages": (
            stage("Guards Motorised Division", ()),
            stage("1939 Guards Mobile Division", (1400,), cost=15.5, maxspeed=27,
                  defaultorganisation=37, morale=37, defensiveness=24, toughness=30,
                  softness=82, airdefence=10, softattack=13, hardattack=3,
                  airattack=4, supplyconsumption=1.55,
                  equipment={"trucks": 3200, "horses": 500, "artillery": 78,
                             "anti_tank": 42, "anti_air": 62, "armored_car": 42}),
            stage("1942 Guards Mobile Division", (1410,), cost=15, maxspeed=27,
                  defaultorganisation=39, morale=39, defensiveness=25, toughness=31,
                  softness=78, airdefence=12, softattack=16, hardattack=4,
                  airattack=4, supplyconsumption=1.5,
                  equipment={"trucks": 3400, "horses": 200, "artillery": 86,
                             "anti_tank": 50, "anti_air": 68, "armored_car": 48}),
            stage("1945 Guards Mobile Division", (1420,), cost=15,
                  defaultorganisation=41, morale=41, defensiveness=26, toughness=32,
                  softness=75, airdefence=14, softattack=17, hardattack=5,
                  airattack=5, supplyconsumption=1.5,
                  equipment={"trucks": 3600, "horses": 0, "artillery": 94,
                             "anti_tank": 58, "anti_air": 74, "armored_car": 54}),
            stage("1952 Guards Mechanised Reserve", (1440,), cost=16, maxspeed=28,
                  defaultorganisation=43, morale=43, defensiveness=28, toughness=34,
                  softness=70, airdefence=16, softattack=20, hardattack=7,
                  airattack=6, supplyconsumption=1.6,
                  equipment={"trucks": 3900, "horses": 0, "artillery": 104,
                             "anti_tank": 70, "anti_air": 82, "armored_car": 66}),
            stage("1960 Modern Guards Mobile Division", (1460,), cost=17,
                  manpower=11, maxspeed=30, defaultorganisation=45, morale=45,
                  defensiveness=30, toughness=36, softness=65, airdefence=18,
                  softattack=24, hardattack=9, airattack=7, supplyconsumption=1.7,
                  equipment={"manpower": 11000, "trucks": 4300, "horses": 0,
                             "artillery": 116, "anti_tank": 84, "anti_air": 92,
                             "armored_car": 80}),
        ),
    },
    40: {
        "comment": "Indian Pioneer Division for bridging, field works, and assault support.",
        "brigades": ("artillery", "anti_air", "engineer", "police"),
        "commission_flag": "ind_aubm_pioneers_commissioned",
        "event_name": "The Pioneer Equipment Board",
        "picture": "aubm_v4_army_commands",
        "base": {
            "cost": 8, "buildtime": 400, "manpower": 10, "maxspeed": 5,
            "defaultorganisation": 42, "morale": 48, "defensiveness": 46,
            "toughness": 46, "softness": 95, "suppression": 4,
            "airdefence": 16, "softattack": 10, "hardattack": 4, "airattack": 1,
            "transportweight": 14, "supplyconsumption": 1.35, "fuelconsumption": 0.6,
            "upgrade_time_factor": 0.30, "upgrade_cost_factor": 0.75,
            "reinforce_time": 0.50, "reinforce_cost": 0.40,
        },
        "equipment": {
            "manpower": 10000, "trucks": 1200, "horses": 2500, "artillery": 100,
            "heavy_artillery": 20, "anti_tank": 30, "anti_air": 20,
        },
        "stages": (
            stage("Indian Pioneer Division", ()),
            stage("1939 Mechanised Pioneer Group", (1110, 1870), cost=8.5,
                  defaultorganisation=44, morale=50, defensiveness=48, toughness=48,
                  airdefence=17, softattack=12, hardattack=5, airattack=2,
                  supplyconsumption=1.4,
                  equipment={"trucks": 1500, "horses": 1800, "artillery": 112,
                             "heavy_artillery": 24, "anti_tank": 40, "anti_air": 24}),
            stage("1945 Assault Pioneer Division", (1130, 1880), cost=9,
                  maxspeed=6, defaultorganisation=46, morale=52, defensiveness=50,
                  toughness=50, softness=90, airdefence=19, softattack=15,
                  hardattack=7, airattack=3, supplyconsumption=1.5,
                  fuelconsumption=0.7,
                  equipment={"trucks": 1900, "horses": 1000, "artillery": 126,
                             "heavy_artillery": 28, "anti_tank": 52, "anti_air": 30}),
            stage("1952 Combat Engineering Division", (1150, 1890), cost=9.5,
                  manpower=9, maxspeed=6, defaultorganisation=48, morale=54,
                  defensiveness=52, toughness=52, softness=85, airdefence=21,
                  softattack=17, hardattack=9, airattack=4, supplyconsumption=1.6,
                  fuelconsumption=0.8,
                  equipment={"manpower": 9000, "trucks": 2400, "horses": 400,
                             "artillery": 140, "heavy_artillery": 32, "anti_tank": 64,
                             "anti_air": 36}),
            stage("1960 Modern Pioneer Division", (13010, 1900), cost=10,
                  manpower=9, maxspeed=7, defaultorganisation=50, morale=56,
                  defensiveness=54, toughness=54, softness=80, airdefence=23,
                  softattack=20, hardattack=11, airattack=5, supplyconsumption=1.7,
                  fuelconsumption=1.0,
                  equipment={"manpower": 9000, "trucks": 3000, "horses": 0,
                             "artillery": 156, "heavy_artillery": 38, "anti_tank": 78,
                             "anti_air": 44}),
        ),
    },
}


def render_number(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def expanded_models(spec: dict[str, object]) -> list[dict[str, object]]:
    base_stats = deepcopy(spec["base"])
    base_equipment = deepcopy(spec["equipment"])
    models: list[dict[str, object]] = []
    for source in spec["stages"]:
        current = deepcopy(base_stats)
        current_equipment = deepcopy(base_equipment)
        for key, value in source.items():
            if key not in {"label", "techs", "equipment"}:
                current[key] = value
        current_equipment.update(source.get("equipment", {}))
        current["equipment"] = current_equipment
        current["label"] = source["label"]
        current["techs"] = source["techs"]
        models.append(current)
        base_stats = {key: value for key, value in current.items() if key not in {"equipment", "label", "techs"}}
        base_equipment = current_equipment
    return models


def render_division(slot: int, spec: dict[str, object]) -> str:
    lines = [f"# MODEL_{slot}_", f"# AUBM: {spec['comment']}", ""]
    for brigade in spec["brigades"]:
        lines.append(f"allowed_brigades = {brigade}")
    lines.append("")
    extra = spec.get("extra", {})
    for index, model in enumerate(expanded_models(spec)):
        lines.extend((f"# {index} - {model['label']}", "model = {"))
        for field in STAT_FIELDS:
            lines.append(f"\t{field:<24}= {render_number(model[field])}")
        for field, value in extra.items():
            lines.append(f"\t{field:<24}= {render_number(value)}")
        equipment = " ".join(
            f"{key} = {render_number(value)}" for key, value in model["equipment"].items()
        )
        lines.append(f"\tequipment = {{ {equipment} }}")
        lines.extend(("}", ""))
    return "\r\n".join(lines).rstrip() + "\r\n"


def matching_brace(text: str, opening: int) -> int:
    depth = 0
    quoted = False
    comment = False
    for index in range(opening, len(text)):
        char = text[index]
        if comment:
            if char in "\r\n":
                comment = False
            continue
        if not quoted and char == "#":
            comment = True
            continue
        if char == '"':
            quoted = not quoted
            continue
        if quoted:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError(f"Unmatched brace at byte {opening}")


def technology_commands() -> dict[str, dict[int, list[str]]]:
    commands: dict[str, dict[int, list[str]]] = {
        "infantry_tech.txt": {},
        "armor_tech.txt": {},
    }
    for slot, spec in UNITS.items():
        filename = "armor_tech.txt" if slot == 38 else "infantry_tech.txt"
        for model, source in enumerate(spec["stages"][1:], 1):
            techs = source["techs"]
            for tech in techs:
                other_techs = tuple(candidate for candidate in techs if candidate != tech)
                trigger = ""
                if other_techs:
                    requirements = " ".join(
                        f"technology = {candidate}" for candidate in other_techs
                    )
                    trigger = f"trigger = {{ {requirements} }} "
                target = commands[filename].setdefault(tech, [])
                target.append(
                    f"command = {{ {trigger}type = new_model which = d_rsv_{slot} value = {model} }}"
                )
                target.append(
                    f"command = {{ {trigger}type = scrap_model which = d_rsv_{slot} value = {model - 1} }}"
                )
    return commands


def patch_application(text: str, technology: int, commands: list[str]) -> str:
    pattern = re.compile(r"(?m)^\s*application\s*=\s*\{")
    for match in pattern.finditer(text):
        opening = text.find("{", match.start(), match.end())
        closing = matching_brace(text, opening)
        block = text[match.start() : closing + 1]
        if not re.search(rf"(?m)^\s*\{{?\s*id\s*=\s*{technology}\s*$", block):
            continue
        effects_match = re.search(r"(?m)^\s*effects\s*=\s*\{", block)
        if not effects_match:
            raise ValueError(f"Technology {technology} has no effects block")
        effects_opening = block.find("{", effects_match.start(), effects_match.end())
        effects_closing = matching_brace(block, effects_opening)
        indent_match = re.match(r"\s*", block[effects_match.start() :])
        indent = indent_match.group(0).replace("\r", "").replace("\n", "") if indent_match else "    "
        command_indent = indent + "  "
        insertion = (
            "\r\n"
            + command_indent
            + "# AUBM specialist equipment ladder\r\n"
            + "\r\n".join(command_indent + command for command in commands)
            + "\r\n"
            + indent
        )
        patched_block = block[:effects_closing] + insertion + block[effects_closing:]
        return text[: match.start()] + patched_block + text[closing + 1 :]
    raise ValueError(f"Could not locate technology application {technology}")


def write_technology_overlays() -> int:
    config = json.loads((ROOT / "tools/v4_config.json").read_text(encoding="utf-8"))
    baseline = pathlib.Path(config["baseline_mod"])
    output_root = ROOT / "mod/db/tech"
    output_root.mkdir(parents=True, exist_ok=True)
    application_count = 0
    for filename, applications in technology_commands().items():
        source = baseline / "db/tech" / filename
        text = source.read_text(encoding="cp1252")
        for technology, commands in applications.items():
            text = patch_application(text, technology, commands)
            application_count += 1
        (output_root / filename).write_text(text, encoding="cp1252", newline="")
    return application_count


def write_localization() -> None:
    LOCALIZATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCALIZATION_PATH.open("w", encoding="cp1252", newline="") as handle:
        writer = csv.writer(handle, delimiter=";", lineterminator="\r\n")
        writer.writerow(["# AUBM SPECIAL UNIT MODEL LOCALIZATION"] + [""] * 10 + ["X"])
        for slot, spec in UNITS.items():
            for index, model in enumerate(expanded_models(spec)[1:], 1):
                writer.writerow([f"MODEL_{slot}_{index}", model["label"], *("" for _ in range(9)), "X"])


def main() -> int:
    DIVISION_ROOT.mkdir(parents=True, exist_ok=True)
    for slot, spec in UNITS.items():
        (DIVISION_ROOT / f"d_rsv_{slot}.txt").write_text(
            render_division(slot, spec), encoding="cp1252", newline=""
        )
    write_localization()
    applications = write_technology_overlays()
    OBSOLETE_EVENT_PATH.unlink(missing_ok=True)
    print(
        f"Generated {sum(len(spec['stages']) for spec in UNITS.values())} specialist models "
        f"across {applications} parent-technology applications."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
