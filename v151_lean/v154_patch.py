from pathlib import Path

router = Path('app/src/main/java/fr/vspgps/app/LocalValhallaRouter.kt')
s = router.read_text()

needle = '''                return kotlin.math.min(d, 360.0 - d)
            }'''
helper = '''                return kotlin.math.min(d, 360.0 - d)
            }

            // V154 : une aire/parking peut être relié au rond-point par deux branches
            // distinctes (entrée + sortie) que Valhalla expose avec des headings opposés.
            // Pour le numéro de sortie, ces deux branches doivent compter comme UN accès
            // physique. On ne fusionne que des branches de type service/service_road et
            // seulement si leurs points de raccordement sur le rond-point sont proches.
            val shapePoints154 = decodePolyline6Local(encodedShape)
            fun branchNodeDistance154(a: Int, b: Int): Double {
                if (a !in shapePoints154.indices || b !in shapePoints154.indices) return Double.POSITIVE_INFINITY
                return distanceMetersLocal(shapePoints154[a], shapePoints154[b])
            }
            data class ServiceBranch154(val shapeIndex: Int)
            val serviceUses154 = setOf("service", "service_road")'''
if needle not in s:
    raise SystemExit('V154: angularDistance105 anchor missing')
s = s.replace(needle, helper, 1)

needle = '''                var priorUsableExits = 0
                val branchDebug = org.json.JSONArray()'''
replacement = '''                var priorUsableExits = 0
                val branchDebug = org.json.JSONArray()
                val serviceBranches154 = mutableListOf<ServiceBranch154>()
                var mergedServicePairs154 = 0'''
if needle not in s:
    raise SystemExit('V154: group-state anchor missing')
s = s.replace(needle, replacement, 1)

needle = '''                        val heading = branch.optDouble("begin_heading", Double.NaN)
                        if (!heading.isFinite()) continue

                        // Une chaussée divisée / deux arêtes parallèles au même noeud représentent
                        // souvent une seule sortie physique. 25° garde les branches distinctes tout
                        // en supprimant ce doublonnage de graphe.
                        if (uniqueHeadings.none { angularDistance105(it, heading) < 25.0 }) {
                            uniqueHeadings += heading
                        }'''
replacement = '''                        val heading = branch.optDouble("begin_heading", Double.NaN)
                        if (!heading.isFinite()) continue

                        val nodeShapeIndex154 = edge.optInt("end_shape_index", -1)
                        val serviceLike154 = use in serviceUses154
                        val samePhysicalServiceAccess154 = serviceLike154 && nodeShapeIndex154 >= 0 &&
                            serviceBranches154.any { previous ->
                                branchNodeDistance154(previous.shapeIndex, nodeShapeIndex154) <= 45.0
                            }
                        if (samePhysicalServiceAccess154) {
                            // Même aire / même accès latéral : entrée et sortie opposées
                            // ne doivent pas augmenter le numéro de sortie deux fois.
                            mergedServicePairs154 += 1
                            continue
                        }

                        // Une chaussée divisée / deux arêtes parallèles au même noeud représentent
                        // souvent une seule sortie physique. 25° garde les branches distinctes tout
                        // en supprimant ce doublonnage de graphe.
                        if (uniqueHeadings.none { angularDistance105(it, heading) < 25.0 }) {
                            uniqueHeadings += heading
                            if (serviceLike154 && nodeShapeIndex154 >= 0) {
                                serviceBranches154 += ServiceBranch154(nodeShapeIndex154)
                            }
                        }'''
if needle not in s:
    raise SystemExit('V154: branch filter anchor missing')
s = s.replace(needle, replacement, 1)

needle = '''                        put("prior_usable_exits", priorUsableExits)
                        put("branches", branchDebug)
                        put("source", "v105_path_topology")'''
replacement = '''                        put("prior_usable_exits", priorUsableExits)
                        put("merged_service_pairs", mergedServicePairs154)
                        put("branches", branchDebug)
                        put("source", "v154_path_topology_service_pair")'''
if needle not in s:
    raise SystemExit('V154: audit anchor missing')
s = s.replace(needle, replacement, 1)
router.write_text(s)

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
t = main.read_text()
needle = '''                                val src151 = item151.optString("match_source", item151.optString("source", "topologie locale"))
                                add("RP $rpNumber151 : natif=$native151 → topologie=$topo151 • $src151")'''
replacement = '''                                val src151 = item151.optString("match_source", item151.optString("source", "topologie locale"))
                                val merged154 = item151.optInt("merged_service_pairs", 0)
                                val mergedText154 = if (merged154 > 0) " • paires accès fusionnées=$merged154" else ""
                                add("RP $rpNumber151 : natif=$native151 → topologie=$topo151 • $src151$mergedText154")'''
if needle not in t:
    raise SystemExit('V154: diagnostic anchor missing')
t = t.replace(needle, replacement, 1)
t = t.replace('R.drawable.vsp_splash', 'R.drawable.vsp_home')
main.write_text(t)

print('V154 patch applied')
