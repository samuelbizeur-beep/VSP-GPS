from pathlib import Path

# V148 — Le contrôle OSM V146/V147 ne voyait que les voies partageant exactement
# un nœud OSM avec l'anneau. Certaines sorties carrossables (aires/parkings, voies
# de service, géométries légèrement décalées) peuvent être dessinées à quelques
# mètres du giratoire sans nœud partagé. V148 élargit la requête Overpass aux
# highways proches et ajoute un secours géométrique très local, regroupé par
# direction physique pour éviter les doubles comptages.

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
m = main.read_text(encoding='utf-8')

old_query = '''        val query = buildString {
            append("[out:json][timeout:12];(")
            targets.forEach { indexed ->
                val m = indexed.value
                val mid = ((m.beginShapeIndex + m.endShapeIndex) / 2).coerceIn(0, points.lastIndex)
                val p = points[mid]
                append("way(around:110,${p.latitude},${p.longitude})[\\\"junction\\\"~\\\"^(roundabout|circular)$\\\"];")
            }
            append(")->.r;node(w.r)->.rn;way(bn.rn)[\\\"highway\\\"]->.roads;(.r;.roads;);out body geom;")
        }
'''
new_query = '''        val query = buildString {
            append("[out:json][timeout:12];(")
            targets.forEach { indexed ->
                val m = indexed.value
                val mid = ((m.beginShapeIndex + m.endShapeIndex) / 2).coerceIn(0, points.lastIndex)
                val p = points[mid]
                append("way(around:110,${p.latitude},${p.longitude})[\\\"junction\\\"~\\\"^(roundabout|circular)$\\\"];")
            }
            append(")->.r;node(w.r)->.rn;way(bn.rn)[\\\"highway\\\"]->.roads;(")
            // V148 : récupérer aussi les voies carrossables proches du giratoire,
            // même si OSM ne partage pas exactement le même nœud avec l'anneau.
            targets.forEach { indexed ->
                val m = indexed.value
                val mid = ((m.beginShapeIndex + m.endShapeIndex) / 2).coerceIn(0, points.lastIndex)
                val p = points[mid]
                append("way(around:145,${p.latitude},${p.longitude})[\\\"highway\\\"];")
            }
            append(")->.nearRoads;(.r;.roads;.nearRoads;);out body geom;")
        }
'''
if old_query not in m:
    raise SystemExit('V148 Overpass query anchor not found')
m = m.replace(old_query, new_query, 1)

anchor = '''        val roundWays = ways.filter(::isRoundabout)
'''
helper = '''        // V148 : secours géométrique pour les sorties carrossables dessinées à quelques
        // mètres de l'anneau sans nœud OSM partagé. On ne remplace pas la topologie exacte :
        // on l'enrichit uniquement avec des branches très proches et orientées vers l'extérieur.
        fun motorTagsAllowBranch(way: OsmWay146): Boolean {
            if (isRoundabout(way)) return false
            val highway = way.tags.optString("highway", "").lowercase(Locale.ROOT)
            if (highway.isBlank() || highway in setOf(
                    "footway", "cycleway", "path", "pedestrian", "steps", "bridleway",
                    "platform", "corridor", "construction", "proposed"
                )) return false
            val accessValues = listOf("access", "vehicle", "motor_vehicle").map {
                way.tags.optString(it, "").lowercase(Locale.ROOT)
            }
            return accessValues.none { it == "no" || it == "private" }
        }

        fun bearingDegreesV148(from: GeoPoint, to: GeoPoint): Double {
            val lat1 = Math.toRadians(from.latitude)
            val lat2 = Math.toRadians(to.latitude)
            val dLon = Math.toRadians(to.longitude - from.longitude)
            val y = kotlin.math.sin(dLon) * kotlin.math.cos(lat2)
            val x = kotlin.math.cos(lat1) * kotlin.math.sin(lat2) -
                kotlin.math.sin(lat1) * kotlin.math.cos(lat2) * kotlin.math.cos(dLon)
            return (Math.toDegrees(kotlin.math.atan2(y, x)) + 360.0) % 360.0
        }

        fun bearingDifferenceV148(a: Double, b: Double): Double {
            val d = kotlin.math.abs(a - b) % 360.0
            return kotlin.math.min(d, 360.0 - d)
        }

        fun outboundBearingFromSharedNodeV148(
            way: OsmWay146,
            sharedNode: Long,
            ringPoint: GeoPoint
        ): Double? {
            if (!motorTagsAllowBranch(way)) return null
            val idx = way.nodes.indexOf(sharedNode)
            if (idx < 0 || way.geometry.size < 2) return null
            val oneway = way.tags.optString("oneway", "").lowercase(Locale.ROOT)
            val neighborIndex = when (oneway) {
                "yes", "1", "true" -> if (idx < way.geometry.lastIndex) idx + 1 else return null
                "-1" -> if (idx > 0) idx - 1 else return null
                else -> {
                    val candidates = buildList {
                        if (idx > 0) add(idx - 1)
                        if (idx < way.geometry.lastIndex) add(idx + 1)
                    }
                    candidates.maxByOrNull { distanceMetersBetween(ringPoint, way.geometry[it]) }
                        ?: return null
                }
            }
            return bearingDegreesV148(ringPoint, way.geometry[neighborIndex])
        }

        fun nearestRingAttachmentV148(
            way: OsmWay146,
            ringGeometry: List<GeoPoint>
        ): Triple<Int, Int, Double>? {
            if (!motorTagsAllowBranch(way) || way.geometry.size < 2 || ringGeometry.isEmpty()) return null
            val endpointIndices = listOf(0, way.geometry.lastIndex).distinct()
            var bestRing = -1
            var bestEndpoint = -1
            var bestDistance = Double.POSITIVE_INFINITY
            endpointIndices.forEach { endpointIndex ->
                val endpoint = way.geometry[endpointIndex]
                ringGeometry.forEachIndexed { ringIndex, ringPoint ->
                    val d = distanceMetersBetween(endpoint, ringPoint)
                    if (d < bestDistance) {
                        bestDistance = d
                        bestRing = ringIndex
                        bestEndpoint = endpointIndex
                    }
                }
            }
            if (bestRing < 0 || bestEndpoint < 0) return null
            return Triple(bestRing, bestEndpoint, bestDistance)
        }

        fun outboundBearingFromNearGeometryV148(
            way: OsmWay146,
            ringGeometry: List<GeoPoint>,
            ringIndex: Int
        ): Double? {
            val attachment = nearestRingAttachmentV148(way, ringGeometry) ?: return null
            val (nearestRingIndex, endpointIndex, endpointDistance) = attachment
            if (nearestRingIndex != ringIndex || endpointDistance > 14.0) return null
            val oneway = way.tags.optString("oneway", "").lowercase(Locale.ROOT)
            val outwardAllowed = when (oneway) {
                "yes", "1", "true" -> endpointIndex == 0
                "-1" -> endpointIndex == way.geometry.lastIndex
                else -> true
            }
            if (!outwardAllowed) return null
            val neighborIndex = if (endpointIndex == 0) 1 else way.geometry.lastIndex - 1
            if (neighborIndex !in way.geometry.indices) return null
            val ringPoint = ringGeometry[ringIndex]
            val neighbor = way.geometry[neighborIndex]
            // Une vraie branche doit s'éloigner nettement du giratoire. Cela évite de
            // compter une voie parallèle simplement proche de l'anneau.
            if (distanceMetersBetween(ringPoint, neighbor) < endpointDistance + 4.0) return null
            return bearingDegreesV148(ringPoint, neighbor)
        }

'''
if anchor not in m:
    raise SystemExit('V148 helper anchor not found')
m = m.replace(anchor, helper + anchor, 1)

old_count = '''            var cursor = (entryIndex + 1) % nodes.size
            var exitCount = 0
            var safety = 0
            while (safety < nodes.size) {
                val nodeId = nodes[cursor]
                val hasPhysicalExit = ways.any { way ->
                    way.id != selected.id && nodeId in way.nodes && isMotorBranchUsableFromNode(way, nodeId)
                }
                if (hasPhysicalExit) exitCount++
                if (cursor == exitIndex) break
                cursor = (cursor + 1) % nodes.size
                safety++
            }
'''
new_count = '''            var cursor = (entryIndex + 1) % nodes.size
            var exitCount = 0
            var safety = 0
            while (safety < nodes.size) {
                val nodeId = nodes[cursor]
                val ringPoint = geometry[cursor]
                val bearings = mutableListOf<Double>()

                // 1) Topologie OSM exacte : toujours prioritaire.
                ways.forEach { way ->
                    if (way.id == selected.id) return@forEach
                    if (nodeId in way.nodes && isMotorBranchUsableFromNode(way, nodeId)) {
                        outboundBearingFromSharedNodeV148(way, nodeId, ringPoint)?.let(bearings::add)
                    }
                }

                // 2) V148 : branche carrossable quasi-raccordée. On n'ajoute que les
                // voies qui ne partagent PAS déjà ce nœud, pour éviter un double comptage.
                ways.forEach { way ->
                    if (way.id == selected.id || nodeId in way.nodes) return@forEach
                    outboundBearingFromNearGeometryV148(way, geometry, cursor)?.let(bearings::add)
                }

                // Plusieurs ways OSM peuvent représenter la même sortie (changement de nom,
                // de surface, voie séparée...). On les regroupe par direction physique.
                val uniqueDirections = mutableListOf<Double>()
                bearings.forEach { bearing ->
                    if (uniqueDirections.none { bearingDifferenceV148(it, bearing) < 22.0 }) {
                        uniqueDirections += bearing
                    }
                }
                exitCount += uniqueDirections.size

                if (cursor == exitIndex) break
                cursor = (cursor + 1) % nodes.size
                safety++
            }
'''
if old_count not in m:
    raise SystemExit('V148 count block anchor not found')
m = m.replace(old_count, new_count, 1)

# Version Android et badge visible.
gradle = Path('app/build.gradle.kts')
g = gradle.read_text(encoding='utf-8')
g = g.replace('versionCode = 147', 'versionCode = 148', 1)
g = g.replace('versionName = "V147"', 'versionName = "V148"', 1)
gradle.write_text(g, encoding='utf-8')

m = m.replace('V147', 'V148')
main.write_text(m, encoding='utf-8')

print('V148 near-geometry roundabout exits patch applied')
