from pathlib import Path

router = Path('app/src/main/java/fr/vspgps/app/LocalValhallaRouter.kt')
s = router.read_text()

# 1. Helpers for cross-node clustering of service branches.
needle = '''                return kotlin.math.min(d, 360.0 - d)
            }'''
helper = '''                return kotlin.math.min(d, 360.0 - d)
            }

            // V152 : deux branches de service raccordées à deux noeuds voisins peuvent
            // représenter le même accès physique (entrée/sortie d'un parking ou d'une aire).
            // V151 ne dédoublonnait que les headings du même noeud.
            val shapePoints152 = decodePolyline6Local(encodedShape)
            fun branchNodeDistance152(a: Int, b: Int): Double {
                if (a !in shapePoints152.indices || b !in shapePoints152.indices) return Double.POSITIVE_INFINITY
                return distanceMetersLocal(shapePoints152[a], shapePoints152[b])
            }
            data class ServiceBranch152(val shapeIndex: Int, val heading: Double)
            val serviceUses152 = setOf("service", "service_road")'''
if needle not in s:
    raise SystemExit('V152: angularDistance105 anchor missing')
s = s.replace(needle, helper, 1)

# 2. State per roundabout group.
needle = '''                var priorUsableExits = 0
                val branchDebug = org.json.JSONArray()'''
replacement = '''                var priorUsableExits = 0
                val branchDebug = org.json.JSONArray()
                val serviceBranches152 = mutableListOf<ServiceBranch152>()
                var mergedServiceDuplicates152 = 0'''
if needle not in s:
    raise SystemExit('V152: group-state anchor missing')
s = s.replace(needle, replacement, 1)

# 3. Cross-node clustering. Normal roads are not clustered; only service/service_road.
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

                        val nodeShapeIndex152 = edge.optInt("end_shape_index", -1)
                        val serviceLike152 = use in serviceUses152
                        val samePhysicalServiceAccess152 = serviceLike152 && nodeShapeIndex152 >= 0 &&
                            serviceBranches152.any { previous ->
                                branchNodeDistance152(previous.shapeIndex, nodeShapeIndex152) <= 45.0 &&
                                    angularDistance105(previous.heading, heading) <= 70.0
                            }
                        if (samePhysicalServiceAccess152) {
                            mergedServiceDuplicates152 += 1
                            continue
                        }

                        // Une chaussée divisée / deux arêtes parallèles au même noeud représentent
                        // souvent une seule sortie physique. 25° garde les branches distinctes tout
                        // en supprimant ce doublonnage de graphe.
                        if (uniqueHeadings.none { angularDistance105(it, heading) < 25.0 }) {
                            uniqueHeadings += heading
                            if (serviceLike152 && nodeShapeIndex152 >= 0) {
                                serviceBranches152 += ServiceBranch152(nodeShapeIndex152, heading)
                            }
                        }'''
if needle not in s:
    raise SystemExit('V152: branch filter anchor missing')
s = s.replace(needle, replacement, 1)

# 4. Expose how many duplicated service branches were merged.
needle = '''                        put("prior_usable_exits", priorUsableExits)
                        put("branches", branchDebug)
                        put("source", "v105_path_topology")'''
replacement = '''                        put("prior_usable_exits", priorUsableExits)
                        put("merged_service_duplicates", mergedServiceDuplicates152)
                        put("branches", branchDebug)
                        put("source", "v152_path_topology_service_cluster")'''
if needle not in s:
    raise SystemExit('V152: audit anchor missing')
s = s.replace(needle, replacement, 1)
router.write_text(s)

# 5. Show clustering in the diagnostic screen.
main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
t = main.read_text()
needle = '''                                val src151 = item151.optString("match_source", item151.optString("source", "topologie locale"))
                                add("RP $rpNumber151 : natif=$native151 → topologie=$topo151 • $src151")'''
replacement = '''                                val src151 = item151.optString("match_source", item151.optString("source", "topologie locale"))
                                val merged152 = item151.optInt("merged_service_duplicates", 0)
                                val mergedText152 = if (merged152 > 0) " • accès service fusionnés=$merged152" else ""
                                add("RP $rpNumber151 : natif=$native151 → topologie=$topo151 • $src151$mergedText152")'''
if needle not in t:
    raise SystemExit('V152: diagnostic anchor missing')
t = t.replace(needle, replacement, 1)
t = t.replace('R.drawable.vsp_splash', 'R.drawable.vsp_home')
main.write_text(t)

print('V152 patch applied')
