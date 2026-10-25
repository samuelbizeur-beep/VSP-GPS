from pathlib import Path

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
m = main.read_text(encoding='utf-8')

old = '''        val corrected = maneuvers.toMutableList()\n        var checked = 0\n        var changed = 0\n\n        targets.forEach { indexed ->\n'''
new = '''        val corrected = maneuvers.toMutableList()\n        var checked = 0\n        var changed = 0\n        val diagnosticLinesV149 = mutableListOf<String>()\n\n        targets.forEach { indexed ->\n'''
if old not in m:
    raise SystemExit('V149 diagnostic start anchor not found')
m = m.replace(old, new, 1)

old = '''            val selected = roundWays.minByOrNull { distanceToWay(midPoint, it) } ?: return@forEach\n            if (distanceToWay(midPoint, selected) > 130.0) return@forEach\n'''
new = '''            val selected = roundWays.minByOrNull { distanceToWay(midPoint, it) } ?: return@forEach\n            val selectedDistanceV149 = distanceToWay(midPoint, selected)\n            val primaryDiagnosticV149 = maneuver.type != 27 || previousRoundabout == null\n            if (selectedDistanceV149 > 130.0) {\n                if (primaryDiagnosticV149) {\n                    diagnosticLinesV149 += "RP m${indexed.index + 1}: anneau trop loin (${selectedDistanceV149.roundToInt()} m)"\n                }\n                return@forEach\n            }\n'''
if old not in m:
    raise SystemExit('V149 selected ring anchor not found')
m = m.replace(old, new, 1)

old = '''            val (entryIndex, entryDistance) = nearestIndex(entryPoint)\n            val (exitIndex, exitDistance) = nearestIndex(exitPoint)\n            if (entryIndex < 0 || exitIndex < 0 || entryDistance > 70.0 || exitDistance > 70.0 || entryIndex == exitIndex) {\n                return@forEach\n            }\n\n            var cursor = (entryIndex + 1) % nodes.size\n'''
new = '''            val (entryIndex, entryDistance) = nearestIndex(entryPoint)\n            val (exitIndex, exitDistance) = nearestIndex(exitPoint)\n            if (entryIndex < 0 || exitIndex < 0 || entryDistance > 70.0 || exitDistance > 70.0 || entryIndex == exitIndex) {\n                if (primaryDiagnosticV149) {\n                    diagnosticLinesV149 += "RP m${indexed.index + 1}: appairage impossible entrée=${entryDistance.roundToInt()}m sortie=${exitDistance.roundToInt()}m"\n                }\n                return@forEach\n            }\n\n            // V149 : photographie des voies carrossables proches de l'anneau, même si elles\n            // ne sont finalement pas comptées. Ce diagnostic permet d'identifier précisément\n            // une sortie d'aire/parking absente, filtrée ou mal orientée.\n            val nearbyWaysV149 = ways.asSequence()\n                .filter { it.id != selected.id && motorTagsAllowBranch(it) }\n                .mapNotNull { way ->\n                    val attachment = nearestRingAttachmentV148(way, geometry) ?: return@mapNotNull null\n                    val (_, _, d) = attachment\n                    if (d > 30.0) return@mapNotNull null\n                    val highway = way.tags.optString("highway", "?")\n                    val label = way.tags.optString("name", "").ifBlank { way.tags.optString("ref", "") }.ifBlank { "sans_nom" }\n                    val oneway = way.tags.optString("oneway", "-")\n                    val access = way.tags.optString("motor_vehicle", "").ifBlank { way.tags.optString("vehicle", "") }.ifBlank { way.tags.optString("access", "-") }\n                    Triple(d, way.id, "$highway/$label d=${d.roundToInt()}m one=$oneway acc=$access")\n                }\n                .sortedBy { it.first }\n                .take(12)\n                .map { it.third }\n                .toList()\n\n            var cursor = (entryIndex + 1) % nodes.size\n'''
if old not in m:
    raise SystemExit('V149 entry/exit anchor not found')
m = m.replace(old, new, 1)

old = '''            if (cursor != exitIndex || exitCount !in 1..12) return@forEach\n            checked++\n            val currentBefore = corrected[indexed.index]\n'''
new = '''            if (primaryDiagnosticV149) {\n                val nativeExitV149 = listOf(\n                    maneuver.roundaboutExitCount,\n                    previousRoundabout?.roundaboutExitCount ?: 0,\n                    nextRoundabout?.roundaboutExitCount ?: 0\n                ).firstOrNull { it > 0 } ?: 0\n                val nearTextV149 = if (nearbyWaysV149.isEmpty()) "aucune voie carrossable <=30m" else nearbyWaysV149.joinToString(" | ")\n                diagnosticLinesV149 += "RP m${indexed.index + 1}: natif=$nativeExitV149 calcul=$exitCount ring=${selected.id} entrée=${entryDistance.roundToInt()}m sortie=${exitDistance.roundToInt()}m :: $nearTextV149"\n            }\n\n            if (cursor != exitIndex || exitCount !in 1..12) return@forEach\n            checked++\n            val currentBefore = corrected[indexed.index]\n'''
if old not in m:
    raise SystemExit('V149 final count anchor not found')
m = m.replace(old, new, 1)

old = '''        corrected to when {\n            checked == 0 -> "OSM rond-points : topologie trouvée mais aucun comptage suffisamment fiable"\n            changed > 0 -> "✓ OSM rond-points : $checked contrôlé(s), $changed numéro(s) corrigé(s) depuis la topologie réelle"\n            else -> "✓ OSM rond-points : $checked contrôlé(s), numéros confirmés"\n        }\n'''
new = '''        val summaryV149 = when {\n            checked == 0 -> "OSM rond-points : topologie trouvée mais aucun comptage suffisamment fiable"\n            changed > 0 -> "✓ OSM rond-points : $checked contrôlé(s), $changed numéro(s) corrigé(s) depuis la topologie réelle"\n            else -> "✓ OSM rond-points : $checked contrôlé(s), numéros confirmés"\n        }\n        val detailsV149 = diagnosticLinesV149.take(8).joinToString("\\n")\n        corrected to if (detailsV149.isBlank()) summaryV149 else "$summaryV149\\nDIAG RONDS-POINTS V149\\n$detailsV149"\n'''
if old not in m:
    raise SystemExit('V149 return anchor not found')
m = m.replace(old, new, 1)

# Version Android + badge visible.
gradle = Path('app/build.gradle.kts')
g = gradle.read_text(encoding='utf-8')
g = g.replace('versionCode = 148', 'versionCode = 149', 1)
g = g.replace('versionName = "V148"', 'versionName = "V149"', 1)
gradle.write_text(g, encoding='utf-8')
m = m.replace('V148', 'V149')
main.write_text(m, encoding='utf-8')
print('V149 roundabout diagnostic patch applied')
