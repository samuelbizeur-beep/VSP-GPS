from pathlib import Path

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
m = main.read_text(encoding='utf-8')

old_targets = '''        val targets = maneuvers.withIndex().filter { indexed ->
            val m = indexed.value
            isValhallaRoundabout(m.type) &&
                m.beginShapeIndex in points.indices &&
                m.endShapeIndex in points.indices &&
                m.endShapeIndex >= m.beginShapeIndex
        }.take(10)
'''
new_targets = '''        val targets = maneuvers.withIndex().filter { indexed ->
            val m = indexed.value
            // V147 : le comptage topologique doit partir de la vraie manœuvre
            // d'ENTRÉE du rond-point (type 26). La manœuvre 27 commence déjà
            // au niveau de la sortie et ne contient donc pas le point d'entrée
            // nécessaire pour recompter correctement les branches précédentes.
            m.type == 26 &&
                m.beginShapeIndex in points.indices &&
                m.endShapeIndex in points.indices &&
                m.endShapeIndex >= m.beginShapeIndex
        }.take(10)
'''
if old_targets not in m:
    raise SystemExit('V147 targets anchor not found')
m = m.replace(old_targets, new_targets, 1)

old_apply = '''            if (cursor != exitIndex || exitCount !in 1..12) return@forEach
            checked++
            if (exitCount != maneuver.roundaboutExitCount) {
                corrected[indexed.index] = maneuver.copy(roundaboutExitCount = exitCount)
                changed++
            }
'''
new_apply = '''            if (cursor != exitIndex || exitCount !in 1..12) return@forEach
            checked++

            // V147 : Valhalla représente souvent un rond-point avec une paire
            // entrée(26) -> sortie(27). L'UI et la voix donnent volontairement
            // priorité au numéro porté par la sortie 27. En V146, OSM pouvait
            // corriger uniquement l'entrée 26 : la feuille de route continuait
            // donc à afficher l'ancien numéro de la sortie 27. On propage ici le
            // numéro topologique validé aux DEUX manœuvres du même rond-point.
            var pairChanged = false
            if (corrected[indexed.index].roundaboutExitCount != exitCount) {
                corrected[indexed.index] = corrected[indexed.index].copy(roundaboutExitCount = exitCount)
                pairChanged = true
            }

            val exitManeuverIndex = indexed.index + 1
            if (exitManeuverIndex in maneuvers.indices) {
                val exitManeuver = maneuvers[exitManeuverIndex]
                val sameRoundaboutPair =
                    exitManeuver.type == 27 &&
                    exitManeuver.beginShapeIndex >= maneuver.beginShapeIndex &&
                    exitManeuver.beginShapeIndex - maneuver.endShapeIndex <= 8
                if (sameRoundaboutPair && corrected[exitManeuverIndex].roundaboutExitCount != exitCount) {
                    corrected[exitManeuverIndex] = corrected[exitManeuverIndex].copy(roundaboutExitCount = exitCount)
                    pairChanged = true
                }
            }

            if (pairChanged) changed++
'''
if old_apply not in m:
    raise SystemExit('V147 apply anchor not found')
m = m.replace(old_apply, new_apply, 1)

# Visible version strings / diagnostics.
m = m.replace('V146', 'V147')
main.write_text(m, encoding='utf-8')

gradle = Path('app/build.gradle.kts')
g = gradle.read_text(encoding='utf-8')
g = g.replace('versionCode = 146', 'versionCode = 147', 1)
g = g.replace('versionName = "V146"', 'versionName = "V147"', 1)
gradle.write_text(g, encoding='utf-8')

print('V147 roundabout enter/exit pair synchronization patch applied')
