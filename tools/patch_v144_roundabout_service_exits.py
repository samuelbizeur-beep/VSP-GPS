from pathlib import Path

# V144 — Les aires/parkings carrossables réellement connectés au rond-point
# doivent compter dans le numéro de sortie. Le compteur topologique V105
# excluait jusqu'ici parking_aisle et service_road, ce qui transformait par
# exemple une 2e sortie en 1re lorsqu'une aire de covoiturage précédait la
# route réellement empruntée.

router = Path('app/src/main/java/fr/vspgps/app/LocalValhallaRouter.kt')
r = router.read_text(encoding='utf-8')

old = '''            // Les accès de desserte/parking ne doivent pas devenir une "sortie" vocale.
            // Les routes normales (residential, tertiary, secondary, primary...) restent comptées.
            val excludedUses105 = setOf(
                "footway", "sidewalk", "steps", "cycleway", "path", "pedestrian",
                "parking_aisle", "driveway", "service_road", "drive_through",
                "emergency_access", "track", "alley"
            )
'''

new = '''            // V144 : une branche carrossable vers une aire de covoiturage ou un parking
            // est une vraie sortie physique du rond-point et doit compter dans le numéro.
            // On garde donc parking_aisle et service_road lorsqu'elles sont routables
            // depuis le noeud (driveability=forward/both). Les accès clairement non
            // destinés à la circulation générale restent exclus.
            val excludedUses105 = setOf(
                "footway", "sidewalk", "steps", "cycleway", "path", "pedestrian",
                "driveway", "drive_through", "emergency_access", "track", "alley"
            )
'''

if old not in r:
    raise SystemExit('V144 roundabout exclusion anchor not found')
r = r.replace(old, new, 1)
router.write_text(r, encoding='utf-8')

# Bump Android version and visible badges from V143 to V144 after the previous patches.
gradle = Path('app/build.gradle.kts')
g = gradle.read_text(encoding='utf-8')
g = g.replace('versionCode = 143', 'versionCode = 144', 1)
g = g.replace('versionName = "V143"', 'versionName = "V144"', 1)
gradle.write_text(g, encoding='utf-8')

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
m = main.read_text(encoding='utf-8')
if 'V143' not in m:
    raise SystemExit('V143 visible badge not found')
m = m.replace('V143', 'V144')
main.write_text(m, encoding='utf-8')

print('V144 roundabout service/parking exit patch applied')
