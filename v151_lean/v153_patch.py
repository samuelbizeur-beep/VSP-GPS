from pathlib import Path

router = Path('app/src/main/java/fr/vspgps/app/LocalValhallaRouter.kt')
s = router.read_text()

needle = '''                return kotlin.math.min(d, 360.0 - d)
            }'''
helper = '''                return kotlin.math.min(d, 360.0 - d)
            }

            // V153 : dédoublonnage inter-noeuds des branches qui représentent la même
            // sortie physique. Certains accès sont cartographiés avec deux raccordements
            // voisins mais ne sont pas étiquetés service/service_road. On applique donc :
            //  - un critère géométrique très strict à toutes les branches carrossables ;
            //  - un critère un peu plus large uniquement aux voies de service.
            val shapePoints153 = decodePolyline6Local(encodedShape)
            fun branchNodeDistance153(a: Int, b: Int): Double {
                if (a !in shapePoints153.indices || b !in shapePoints153.indices) return Double.POSITIVE_INFINITY
                return distanceMetersLocal(shapePoints153[a], shapePoints153[b])
            }
            data class CountedBranch153(
                val shapeIndex: Int,
                val heading: Double,
                val serviceLike: Boolean
            )
            val serviceUses153 = setOf("service", "service_road")'''
if needle not in s:
    raise SystemExit('V153: angularDistance105 anchor missing')
s = s.replace(needle, helper, 1)

needle = '''                var priorUsableExits = 0
                val branchDebug = org.json.JSONArray()'''
replacement = '''                var priorUsableExits = 0
                val branchDebug = org.json.JSONArray()
                val countedBranches153 = mutableListOf<CountedBranch153>()
                var mergedCloseParallel153 = 0
                var mergedService153 = 0'''
if needle not in s:
    raise SystemExit('V153: group-state anchor missing')
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

                        val nodeShapeIndex153 = edge.optInt("end_shape_index", -1)
                        val serviceLike153 = use in serviceUses153
                        var duplicateKind153 = 0
                        if (nodeShapeIndex153 >= 0) {
                            for (previous in countedBranches153) {
                                val nodeMeters153 = branchNodeDistance153(previous.shapeIndex, nodeShapeIndex153)
                                val headingDiff153 = angularDistance105(previous.heading, heading)

                                // Critère universel volontairement serré : deux raccordements à
                                // <= 22 m et quasi parallèles (<= 30°) sont considérés comme une
                                // seule sortie physique, même si leur type OSM diffère.
                                if (nodeMeters153 <= 22.0 && headingDiff153 <= 30.0) {
                                    duplicateKind153 = 1
                                    break
                                }

                                // Pour les voies de service, autoriser un regroupement un peu plus
                                // large afin de couvrir entrée/sortie d'aire ou de parking.
                                if (serviceLike153 && previous.serviceLike &&
                                    nodeMeters153 <= 45.0 && headingDiff153 <= 70.0) {
                                    duplicateKind153 = 2
                                    break
                                }
                            }
                        }
                        if (duplicateKind153 != 0) {
                            if (duplicateKind153 == 1) mergedCloseParallel153 += 1
                            else mergedService153 += 1
                            continue
                        }

                        // Une chaussée divisée / deux arêtes parallèles au même noeud représentent
                        // souvent une seule sortie physique. 25° garde les branches distinctes tout
                        // en supprimant ce doublonnage de graphe.
                        if (uniqueHeadings.none { angularDistance105(it, heading) < 25.0 }) {
                            uniqueHeadings += heading
                            if (nodeShapeIndex153 >= 0) {
                                countedBranches153 += CountedBranch153(nodeShapeIndex153, heading, serviceLike153)
                            }
                        }'''
if needle not in s:
    raise SystemExit('V153: branch filter anchor missing')
s = s.replace(needle, replacement, 1)

needle = '''                        put("prior_usable_exits", priorUsableExits)
                        put("branches", branchDebug)
                        put("source", "v105_path_topology")'''
replacement = '''                        put("prior_usable_exits", priorUsableExits)
                        put("merged_close_parallel", mergedCloseParallel153)
                        put("merged_service_duplicates", mergedService153)
                        put("branches", branchDebug)
                        put("source", "v153_path_topology_close_parallel_cluster")'''
if needle not in s:
    raise SystemExit('V153: audit anchor missing')
s = s.replace(needle, replacement, 1)
router.write_text(s)

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
t = main.read_text()
needle = '''                                val src151 = item151.optString("match_source", item151.optString("source", "topologie locale"))
                                add("RP $rpNumber151 : natif=$native151 → topologie=$topo151 • $src151")'''
replacement = '''                                val src151 = item151.optString("match_source", item151.optString("source", "topologie locale"))
                                val mergedClose153 = item151.optInt("merged_close_parallel", 0)
                                val mergedService153 = item151.optInt("merged_service_duplicates", 0)
                                val mergedText153 = buildString {
                                    if (mergedClose153 > 0) append(" • branches proches fusionnées=$mergedClose153")
                                    if (mergedService153 > 0) append(" • accès service fusionnés=$mergedService153")
                                }
                                add("RP $rpNumber151 : natif=$native151 → topologie=$topo151 • $src151$mergedText153")'''
if needle not in t:
    raise SystemExit('V153: diagnostic anchor missing')
t = t.replace(needle, replacement, 1)
t = t.replace('R.drawable.vsp_splash', 'R.drawable.vsp_home')
main.write_text(t)

print('V153 patch applied')
