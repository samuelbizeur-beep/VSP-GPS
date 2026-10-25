from pathlib import Path

# V146 — Pour numéroter les sorties physiques d'un rond-point, ne pas dépendre
# uniquement de driveability=forward/both. Une branche peut être exposée par
# Valhalla comme backward (sens de numérisation de l'arête) ou sans valeur alors
# qu'elle constitue visuellement une vraie sortie carrossable. Le cas Aix-Noulette
# avec l'aire de covoiturage est confirmé comme 2e sortie par une source routière.
# On compte donc toutes les branches motorisées physiques sauf driveability=none
# et les usages explicitement non automobiles.

router = Path('app/src/main/java/fr/vspgps/app/LocalValhallaRouter.kt')
r = router.read_text(encoding='utf-8')

old_drive = '''                        val driveability = branch.optString("driveability", "")
                            .lowercase(java.util.Locale.ROOT)
                        if (driveability != "forward" && driveability != "both") continue
'''
new_drive = '''                        val driveability = branch.optString("driveability", "")
                            .lowercase(java.util.Locale.ROOT)
                        // V146 : pour le NUMÉRO de sortie, on compte la branche physique
                        // même si l'orientation Valhalla est backward ou non renseignée.
                        // Seule une branche explicitement non carrossable est rejetée.
                        if (driveability == "none") continue
'''
if old_drive not in r:
    raise SystemExit('V146 driveability anchor not found')
r = r.replace(old_drive, new_drive, 1)

old_excluded = '''            val excludedUses105 = setOf(
                "footway", "sidewalk", "steps", "cycleway", "path", "pedestrian",
                "driveway", "drive_through", "emergency_access", "track", "alley"
            )
'''
new_excluded = '''            val excludedUses105 = setOf(
                "footway", "sidewalk", "steps", "cycleway", "path", "pedestrian",
                "mountain_bike", "emergency_access", "track", "alley",
                "transit_connection", "platform_connection", "egress_connection"
            )
'''
if old_excluded not in r:
    raise SystemExit('V146 excluded-use anchor not found')
r = r.replace(old_excluded, new_excluded, 1)

router.write_text(r, encoding='utf-8')

gradle = Path('app/build.gradle.kts')
g = gradle.read_text(encoding='utf-8')
g = g.replace('versionCode = 145', 'versionCode = 146', 1)
g = g.replace('versionName = "V145"', 'versionName = "V146"', 1)
gradle.write_text(g, encoding='utf-8')

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
m = main.read_text(encoding='utf-8')
if 'V145' not in m:
    raise SystemExit('V145 visible badge not found')
m = m.replace('V145', 'V146')
main.write_text(m, encoding='utf-8')

print('V146 physical roundabout exit patch applied')
