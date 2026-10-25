from pathlib import Path

# V147 — Valhalla fournit souvent un rond-point sous forme de deux manœuvres :
# entrée (26) puis sortie (27). V146 pouvait corriger une seule des deux via OSM,
# puis l'UI/voix privilégiait l'autre valeur restée native. V147 calcule la
# topologie sur la paire complète et propage le même numéro sur les deux.

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
m = main.read_text(encoding='utf-8')

old_points = '''            val maneuver = indexed.value
            val entryPoint = points[maneuver.beginShapeIndex]
            val exitPoint = points[maneuver.endShapeIndex]
            val midPoint = points[((maneuver.beginShapeIndex + maneuver.endShapeIndex) / 2).coerceIn(0, points.lastIndex)]
'''

new_points = '''            val maneuver = indexed.value
            // V147 : raisonner sur le groupe complet entrée(26) -> sortie(27).
            // Le point de sortie réel du rond-point est le beginShapeIndex de la
            // manœuvre 27, pas son endShapeIndex qui est déjà sur la route suivante.
            val previousRoundabout = corrected.getOrNull(indexed.index - 1)
                ?.takeIf { maneuver.type == 27 && it.type == 26 }
            val nextRoundabout = corrected.getOrNull(indexed.index + 1)
                ?.takeIf { maneuver.type == 26 && it.type == 27 }
            val groupEntry = previousRoundabout ?: maneuver
            val groupExit = nextRoundabout ?: maneuver
            val entryShapeIndex = groupEntry.beginShapeIndex.coerceIn(0, points.lastIndex)
            val exitShapeIndex = when {
                groupExit.type == 27 -> groupExit.beginShapeIndex
                else -> groupExit.endShapeIndex
            }.coerceIn(0, points.lastIndex)
            val entryPoint = points[entryShapeIndex]
            val exitPoint = points[exitShapeIndex]
            val midPoint = points[((entryShapeIndex + exitShapeIndex) / 2).coerceIn(0, points.lastIndex)]
'''

if old_points not in m:
    raise SystemExit('V147 group-point anchor not found')
m = m.replace(old_points, new_points, 1)

old_apply = '''            if (exitCount != maneuver.roundaboutExitCount) {
                corrected[indexed.index] = maneuver.copy(roundaboutExitCount = exitCount)
                changed++
            }
'''

new_apply = '''            val currentBefore = corrected[indexed.index]
            var groupChanged = false
            if (currentBefore.roundaboutExitCount != exitCount) {
                corrected[indexed.index] = currentBefore.copy(roundaboutExitCount = exitCount)
                groupChanged = true
            }
            // V147 : écrire le même numéro sur les deux manœuvres du même rond-point.
            // Ainsi la feuille de route, le bandeau et la voix ne peuvent plus diverger.
            if (maneuver.type == 26) {
                val partnerIndex = indexed.index + 1
                val partner = corrected.getOrNull(partnerIndex)
                if (partner?.type == 27 && partner.roundaboutExitCount != exitCount) {
                    corrected[partnerIndex] = partner.copy(roundaboutExitCount = exitCount)
                    groupChanged = true
                }
            } else if (maneuver.type == 27) {
                val partnerIndex = indexed.index - 1
                val partner = corrected.getOrNull(partnerIndex)
                if (partner?.type == 26 && partner.roundaboutExitCount != exitCount) {
                    corrected[partnerIndex] = partner.copy(roundaboutExitCount = exitCount)
                    groupChanged = true
                }
            }
            if (groupChanged) changed++
'''

if old_apply not in m:
    raise SystemExit('V147 propagation anchor not found')
m = m.replace(old_apply, new_apply, 1)

# Version Android + badge visible.
gradle = Path('app/build.gradle.kts')
g = gradle.read_text(encoding='utf-8')
g = g.replace('versionCode = 146', 'versionCode = 147', 1)
g = g.replace('versionName = "V146"', 'versionName = "V147"', 1)
gradle.write_text(g, encoding='utf-8')

m = m.replace('V146', 'V147')
main.write_text(m, encoding='utf-8')

print('V147 paired roundabout correction propagation applied')
