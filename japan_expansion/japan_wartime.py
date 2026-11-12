"""Wartime manpower, industrial mobilisation and land-air capability."""
from catalog import *


def append_events():
    if any(e.key == "national_callup_1941" for e in EVENTS):
        return

    # These are a finite reserve released in waves, not recurring free units.
    # The manpower percentage scales against manpower in Japan's controlled
    # national provinces, so taking enemy territory does not inflate it.
    waves = [
        ("national_callup_1941", "The national reserve is called up", 1941, 0.35, 12,
         "The Pacific war puts the whole country on a war footing. The first national call-up adds manpower equal to 35% of the manpower in Japan's controlled national provinces, adds 0.25 manpower each day for five years, and raises wartime industrial output by 12%. It creates no divisions: you choose how to spend the reserve, and normal equipment, supplies and construction time still apply."),
        ("national_callup_1942", "The second wartime call-up", 1942, 0.25, 0,
         "The first reserve has been committed. A second intake adds manpower equal to 25% of the manpower in Japan's controlled national provinces. Use it to replace losses or raise new formations; units still need normal production, equipment, supplies and time."),
        ("national_callup_1943", "Japan draws on its final reserves", 1943, 0.20, 8,
         "The war has become a contest of endurance. A final national intake adds manpower equal to 20% of the manpower in Japan's controlled national provinces and adds 8% wartime industrial output. This is the last scripted call-up; later growth comes from the normal campaign."),
    ]
    for idx, (key, title, year, share, ic, copy) in enumerate(waves):
        gate = active() + " atwar = yes NOT = { flag = JX_" + key.upper() + "_DONE }"
        if idx:
            prev = waves[idx - 1][0].upper()
            gate += " flag = JX_" + prev + "_DONE"
        commands = [cmd("manpowerpool", value=share, when=1)]
        if idx == 0:
            commands += [cmd("free_manpower", value=0.25),
                         later("national_mobilization_end", 1825)]
        if ic:
            commands.append(cmd("wartime_ic_mod", value=ic))
        commands.append(flag(key.upper() + "_DONE"))
        event(key, title,
              copy, gate=gate, year=year, offset=15, persistent=True,
              actions=[Action("Release the reserve", commands, chance=100)],
              module="wartime_mobilization", art="army",
              purpose="One of three finite wartime manpower releases; no free formations or repeatable monthly manpower.")

    event("national_mobilization_end", "The five-year national call-up ends",
          "The temporary wartime recruitment programme has run its five-year course. Its extra 0.25 daily manpower production now ends; normal national recruitment continues.",
          triggered=True,
          actions=[Action("Return to the ordinary recruitment rate",
                          [cmd("free_manpower", value=-0.25),
                           flag("NATIONAL_MOBILIZATION_ENDED")], chance=100)],
          module="wartime_mobilization", art="army",
          purpose="Ends the finite five-year off-map manpower supplement; it cannot repeat.")

    # Japan's land-based aircraft are deliberately separated from carrier air
    # groups and naval bombers, which already have their own useful role.
    land_air = ("interceptor", "multi_role", "tactical_bomber", "cas")
    commands = []
    for unit in land_air:
        commands.append(cmd("range", which=unit, value=200))
        commands.append(cmd("build_cost", which=unit, when="on_upgrade",
                            where="relative", value=-10))
        commands.append(cmd("build_time", which=unit, when="on_upgrade",
                            where="relative", value=-10))
    event("land_air_reorganisation", "Japan reorganises its land air arm",
          "Land-based fighters and attack aircraft have too little reach and take too long to replace. "
          "New forward groups and standardised airframes add 200 km of range and cut future aircraft IC cost "
          "and construction time by 10% for Interceptors, Multirole Fighters, Tactical Bombers and Close Air Support. "
          "This affects land-based aircraft only; carrier aircraft and naval bombers keep their existing roles.",
          gate=active() + " atwar = yes NOT = { flag = JX_LAND_AIR_REORG_DONE }",
          year=1939, offset=10, persistent=True,
          actions=[Action("Put the new air organisation into service",
                          commands + [flag("LAND_AIR_REORG_DONE")], chance=100)],
          module="wartime_air", art="air",
          purpose="A one-time operational-range and replacement improvement for land-based aircraft.")

    # A second, bounded wartime improvement arrives after Japan has operated
    # the reorganised air service for a year. It does not touch CAG or naval
    # bomber statistics.
    follow = []
    for unit in land_air:
        follow.append(cmd("range", which=unit, value=250))
        follow.append(cmd("build_cost", which=unit, when="on_upgrade",
                          where="relative", value=-10))
        follow.append(cmd("build_time", which=unit, when="on_upgrade",
                          where="relative", value=-10))
    event("land_air_forward_network", "Forward air groups extend their reach",
          "The first air reorganisation is in service. Better forward control, dispersal and replacement "
          "depots add another 250 km of range and cut future aircraft IC cost and construction time by 10% for Interceptors, "
          "Multirole Fighters, Tactical Bombers and Close Air Support. This is a one-time improvement; "
          "it does not create aircraft or remove the need for airfields, oil and supplies.",
          gate=active() + " atwar = yes flag = JX_LAND_AIR_REORG_DONE "
               "NOT = { flag = JX_LAND_AIR_NETWORK_DONE }",
          year=1941, offset=15, persistent=True,
          actions=[Action("Open the forward air network", follow + [flag("LAND_AIR_NETWORK_DONE")], chance=100)],
          module="wartime_air", art="air",
          purpose="A single follow-up to the 1939 air reform; cumulative range gain is 450 km and future aircraft cost and build-time reductions are each 20%.")
