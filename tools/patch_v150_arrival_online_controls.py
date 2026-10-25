from pathlib import Path

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
m = main.read_text(encoding='utf-8')

# V150 — unifier le vrai point d'arrivée et arrêter le simulateur à cet endroit.
# Valhalla peut parfois accrocher un POI/adresse sur le réseau puis prolonger la
# géométrie au-delà du point réellement le plus proche de la destination choisie.
anchor = '''    fun remainingDistanceMeters(location: Location?): Double {\n'''
insert = '''    // V150 : point d'arrivée routier recalé sur la destination réellement choisie.\n    // On ne raccourcit le trajet que si, dans les 2 derniers km, un point de la route\n    // est nettement plus proche de la destination brute que la fin de polyline.\n    val navigationArrivalShapeIndex = run {\n        if (route.points.isEmpty()) 0 else {\n            val lastIndex = route.points.lastIndex\n            val distanceBuffer = FloatArray(1)\n            fun distanceToRawDestination(index: Int): Double {\n                val point = route.points[index]\n                Location.distanceBetween(\n                    point.latitude, point.longitude,\n                    destination.point.latitude, destination.point.longitude,\n                    distanceBuffer\n                )\n                return distanceBuffer[0].toDouble()\n            }\n            var windowStart = lastIndex\n            var backwardMeters = 0.0\n            while (windowStart > 0 && backwardMeters < 2_000.0) {\n                val a = route.points[windowStart - 1]\n                val b = route.points[windowStart]\n                Location.distanceBetween(a.latitude, a.longitude, b.latitude, b.longitude, distanceBuffer)\n                backwardMeters += distanceBuffer[0]\n                windowStart--\n            }\n            var bestIndex = lastIndex\n            var bestDistance = distanceToRawDestination(lastIndex)\n            for (i in windowStart..lastIndex) {\n                val d = distanceToRawDestination(i)\n                if (d < bestDistance) {\n                    bestDistance = d\n                    bestIndex = i\n                }\n            }\n            val endDistance = distanceToRawDestination(lastIndex)\n            if (endDistance > 60.0 && bestIndex < lastIndex && bestDistance + 25.0 < endDistance) {\n                bestIndex\n            } else lastIndex\n        }\n    }\n    val navigationArrivalPoint = route.points.getOrNull(navigationArrivalShapeIndex) ?: destination.point\n\n'''
if anchor not in m:
    raise SystemExit('V150 arrival insertion anchor not found')
m = m.replace(anchor, insert + anchor, 1)

old = '''        if (route.points.size == 1) {\n            val result = FloatArray(1)\n            Location.distanceBetween(\n                location.latitude, location.longitude,\n                route.points[0].latitude, route.points[0].longitude, result\n            )\n            return result[0].toDouble()\n        }\n\n        val lat0 = Math.toRadians(location.latitude)\n'''
new = '''        if (route.points.size == 1) {\n            val result = FloatArray(1)\n            Location.distanceBetween(\n                location.latitude, location.longitude,\n                route.points[0].latitude, route.points[0].longitude, result\n            )\n            return result[0].toDouble()\n        }\n        val effectiveArrivalIndex = navigationArrivalShapeIndex.coerceIn(1, route.points.lastIndex)\n\n        val lat0 = Math.toRadians(location.latitude)\n'''
if old not in m:
    raise SystemExit('V150 remaining-distance anchor not found')
m = m.replace(old, new, 1)

old = '''        val searchStart = progressAnchor?.let { (it - 2).coerceAtLeast(0) } ?: 0\n'''
new = '''        val searchStart = (progressAnchor?.let { (it - 2).coerceAtLeast(0) } ?: 0)\n            .coerceAtMost((effectiveArrivalIndex - 1).coerceAtLeast(0))\n'''
if old not in m:
    raise SystemExit('V150 searchStart anchor not found')
m = m.replace(old, new, 1)

old = '''            end.coerceAtMost(route.points.lastIndex)\n        } ?: route.points.lastIndex\n'''
new = '''            end.coerceAtMost(effectiveArrivalIndex)\n        } ?: effectiveArrivalIndex\n'''
if old not in m:
    raise SystemExit('V150 searchEnd anchor not found')
m = m.replace(old, new, 1)

old = '''        for (i in (bestSegment + 1) until route.points.lastIndex) {\n'''
new = '''        for (i in (bestSegment + 1) until effectiveArrivalIndex) {\n'''
if old not in m:
    raise SystemExit('V150 remaining sum anchor not found')
m = m.replace(old, new, 1)

old = '''    val routedArrivalPoint = route.points.lastOrNull() ?: destination.point\n'''
new = '''    val routedArrivalPoint = navigationArrivalPoint\n'''
if old not in m:
    raise SystemExit('V150 routedArrivalPoint anchor not found')
m = m.replace(old, new, 1)

# V150 : le mode test parcourt uniquement jusqu'au point d'arrivée recalé.
old = '''        val segmentLengths = route.points.zipWithNext { a, b -> a.distanceToAsDouble(b) }\n        val total = segmentLengths.sum().coerceAtLeast(1.0)\n        val cumulativeMeters131 = DoubleArray(route.points.size)\n        for (i131 in 1 until route.points.size) {\n            cumulativeMeters131[i131] = cumulativeMeters131[i131 - 1] + segmentLengths[i131 - 1]\n        }\n'''
new = '''        val simulationEndIndexV150 = navigationArrivalShapeIndex.coerceIn(1, route.points.lastIndex)\n        val segmentLengths = route.points.take(simulationEndIndexV150 + 1)\n            .zipWithNext { a, b -> a.distanceToAsDouble(b) }\n        val total = segmentLengths.sum().coerceAtLeast(1.0)\n        val cumulativeMeters131 = DoubleArray(route.points.size)\n        for (i131 in 1 until route.points.size) {\n            cumulativeMeters131[i131] = if (i131 <= simulationEndIndexV150) {\n                cumulativeMeters131[i131 - 1] + segmentLengths[i131 - 1]\n            } else total\n        }\n'''
if old not in m:
    raise SystemExit('V150 simulation range anchor not found')
m = m.replace(old, new, 1)

old = '''            val end = route.points.last()\n'''
new = '''            val end = navigationArrivalPoint\n'''
if old not in m:
    raise SystemExit('V150 simulation end anchor not found')
m = m.replace(old, new, 1)

old = '''                        route.points.lastOrNull()?.let { routedEnd ->\n'''
new = '''                        navigationArrivalPoint.let { routedEnd ->\n'''
if old not in m:
    raise SystemExit('V150 arrival marker anchor not found')
m = m.replace(old, new, 1)

# V150 — rendre le contrôle Overpass réellement exploitable sur réseau mobile :
# plus de temps, trois instances publiques et détails des erreurs dans l'audit.
old = '''        val endpoints = listOf(\n            "https://overpass-api.de/api/interpreter",\n            "https://overpass.private.coffee/api/interpreter"\n        )\n        var responseText: String? = null\n        for (endpoint in endpoints) {\n            try {\n                val request = Request.Builder()\n                    .url(endpoint)\n                    .post(okhttp3.FormBody.Builder().add("data", query).build())\n                    .header("User-Agent", "VSP-GPS/146")\n                    .build()\n                val client = routeHttpClient.newBuilder()\n                    .connectTimeout(4, java.util.concurrent.TimeUnit.SECONDS)\n                    .readTimeout(8, java.util.concurrent.TimeUnit.SECONDS)\n                    .callTimeout(9, java.util.concurrent.TimeUnit.SECONDS)\n                    .build()\n                client.newCall(request).execute().use { response ->\n                    if (response.isSuccessful) {\n                        responseText = response.body?.string()\n                    }\n                }\n                if (!responseText.isNullOrBlank()) break\n            } catch (_: Exception) { }\n        }\n        val raw = responseText ?: return@withContext maneuvers to "OSM rond-points : contrôle indisponible (mode local conservé)"\n'''
new = '''        val endpoints = listOf(\n            "https://overpass.private.coffee/api/interpreter",\n            "https://overpass-api.de/api/interpreter",\n            "https://maps.mail.ru/osm/tools/overpass/api/interpreter"\n        )\n        var responseText: String? = null\n        val overpassAttemptsV150 = mutableListOf<String>()\n        for (endpoint in endpoints) {\n            try {\n                val request = Request.Builder()\n                    .url(endpoint)\n                    .post(okhttp3.FormBody.Builder().add("data", query).build())\n                    .header("User-Agent", "VSP-GPS/150")\n                    .build()\n                val client = routeHttpClient.newBuilder()\n                    .connectTimeout(6, java.util.concurrent.TimeUnit.SECONDS)\n                    .readTimeout(18, java.util.concurrent.TimeUnit.SECONDS)\n                    .callTimeout(20, java.util.concurrent.TimeUnit.SECONDS)\n                    .build()\n                client.newCall(request).execute().use { response ->\n                    val host = runCatching { java.net.URI(endpoint).host }.getOrNull() ?: "overpass"\n                    if (response.isSuccessful) {\n                        val body = response.body?.string().orEmpty()\n                        if (body.isNotBlank()) responseText = body\n                        else overpassAttemptsV150 += "$host:vide"\n                    } else {\n                        overpassAttemptsV150 += "$host:HTTP${response.code}"\n                    }\n                }\n                if (!responseText.isNullOrBlank()) break\n            } catch (e: Exception) {\n                val host = runCatching { java.net.URI(endpoint).host }.getOrNull() ?: "overpass"\n                overpassAttemptsV150 += "$host:${e.javaClass.simpleName}"\n            }\n        }\n        val raw = responseText ?: return@withContext maneuvers to\n            "OSM rond-points : contrôle indisponible (${overpassAttemptsV150.take(3).joinToString(" • ")})"\n'''
if old not in m:
    raise SystemExit('V150 Overpass network anchor not found')
m = m.replace(old, new, 1)

# V150 — utiliser l'appel POST JSON officiellement documenté par la Géoplateforme.
start_marker = '    suspend fun ignAutorouteFreeCrossCheck(start: GeoPoint, end: GeoPoint): String? = withContext(Dispatchers.IO) {'
end_marker = '    // V59 : seconde barrière de sécurité.'
start = m.find(start_marker)
end = m.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('V150 IGN function anchors not found')
new_ign = '''    suspend fun ignAutorouteFreeCrossCheck(start: GeoPoint, end: GeoPoint): String? = withContext(Dispatchers.IO) {\n        try {\n            val constraint = JSONObject().apply {\n                put("constraintType", "banned")\n                put("key", "wayType")\n                put("operator", "=")\n                put("value", "autoroute")\n            }\n            val payload = JSONObject().apply {\n                put("start", "${start.longitude},${start.latitude}")\n                put("end", "${end.longitude},${end.latitude}")\n                put("resource", "bdtopo-osrm")\n                put("profile", "car")\n                put("optimization", "fastest")\n                put("constraints", constraint)\n                put("getSteps", true)\n                put("getBbox", true)\n                put("distanceUnit", "meter")\n                put("timeUnit", "second")\n                put("crs", "EPSG:4326")\n            }\n            val request = Request.Builder()\n                .url("https://data.geopf.fr/navigation/itineraire")\n                .post(okhttp3.RequestBody.create(null, payload.toString()))\n                .header("Content-Type", "application/json")\n                .header("Accept", "application/json")\n                .header("User-Agent", "VSP-GPS/150")\n                .build()\n            val client = routeHttpClient.newBuilder()\n                .connectTimeout(6, java.util.concurrent.TimeUnit.SECONDS)\n                .readTimeout(12, java.util.concurrent.TimeUnit.SECONDS)\n                .callTimeout(14, java.util.concurrent.TimeUnit.SECONDS)\n                .build()\n            client.newCall(request).execute().use { response ->\n                val body = response.body?.string().orEmpty()\n                if (!response.isSuccessful) {\n                    val detail = body.replace('\\n', ' ').take(90)\n                    return@withContext "IGN BD TOPO : contrôle indisponible (HTTP ${response.code}${if (detail.isNotBlank()) " • $detail" else ""})"\n                }\n                if (body.isBlank()) return@withContext "IGN BD TOPO : réponse vide"\n                val json = JSONObject(body)\n                if (json.has("error")) return@withContext "IGN BD TOPO : aucun contrôle exploitable"\n                return@withContext "✓ IGN BD TOPO : itinéraire de référence trouvé avec autoroutes exclues"\n            }\n        } catch (e: Exception) {\n            "IGN BD TOPO : contrôle réseau indisponible (${e.javaClass.simpleName})"\n        }\n    }\n\n'''
m = m[:start] + new_ign + m[end:]

# Version Android + badge visible.
gradle = Path('app/build.gradle.kts')
g = gradle.read_text(encoding='utf-8')
g = g.replace('versionCode = 149', 'versionCode = 150', 1)
g = g.replace('versionName = "V149"', 'versionName = "V150"', 1)
if 'versionCode = 150' not in g:
    raise SystemExit('V150 versionCode anchor not found')
gradle.write_text(g, encoding='utf-8')
m = m.replace('V149', 'V150')
main.write_text(m, encoding='utf-8')
print('V150 arrival + online controls patch applied')
