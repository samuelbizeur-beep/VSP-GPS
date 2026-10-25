from pathlib import Path

path = Path("app/src/main/java/fr/vspgps/app/MainActivity.kt")
text = path.read_text(encoding="utf-8")

# Imports used by the Photon/OSM search.
import_anchor = "import java.util.Locale\n"
imports = "import java.util.Locale\nimport java.net.URLEncoder\nimport java.nio.charset.StandardCharsets\n"
if import_anchor not in text:
    raise SystemExit("V135 patch: import anchor not found")
text = text.replace(import_anchor, imports, 1)

# Keep distance with each result so nearby POIs can be ranked and shown.
old_destination = '''data class Destination(
    val label: String,
    val point: GeoPoint
)'''
new_destination = '''data class Destination(
    val label: String,
    val point: GeoPoint,
    val distanceMeters: Double? = null
)'''
if old_destination not in text:
    raise SystemExit("V135 patch: Destination block not found")
text = text.replace(old_destination, new_destination, 1)

# Store several candidates instead of keeping only the first Android Geocoder match.
destination_state = '''    var destination by remember {
        mutableStateOf<Destination?>(null)
    }
'''
search_state = destination_state + '''
    var searchResults by remember {
        mutableStateOf<List<Destination>>(emptyList())
    }
'''
if destination_state not in text:
    raise SystemExit("V135 patch: destination state not found")
text = text.replace(destination_state, search_state, 1)

# Replace the old one-result Geocoder search with Photon/OSM + Android Geocoder fallback.
start_marker = "    fun searchAddress() {\n"
end_marker = "\n    if (navigationStarted && destination != null && routePoints.isNotEmpty()) {"
start = text.find(start_marker)
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("V135 patch: searchAddress markers not found")

new_search = '''    fun searchAddress() {

        if (query.isBlank() || searching) {
            return
        }

        searching = true
        error = null

        scope.launch {
            val results = withContext(Dispatchers.IO) {
                val candidates = mutableListOf<Destination>()

                fun distanceTo(latitude: Double, longitude: Double): Double? {
                    val location = currentLocation ?: return null
                    val output = FloatArray(1)
                    Location.distanceBetween(
                        location.latitude,
                        location.longitude,
                        latitude,
                        longitude,
                        output
                    )
                    return output[0].toDouble()
                }

                // 1) Photon (OpenStreetMap): better for shops, pharmacies, restaurants,
                // POIs and named places, with a bias around the current GPS position.
                try {
                    val encodedQuery = URLEncoder.encode(
                        query.trim(),
                        StandardCharsets.UTF_8.toString()
                    )

                    val locationBias = currentLocation?.let {
                        "&lat=${it.latitude}&lon=${it.longitude}"
                    }.orEmpty()

                    val url =
                        "https://photon.komoot.io/api/?q=$encodedQuery&limit=20&lang=fr$locationBias"

                    val request = Request.Builder()
                        .url(url)
                        .header("User-Agent", "VSP-GPS/1.35 Android")
                        .build()

                    OkHttpClient().newCall(request).execute().use { response ->
                        val body = response.body?.string()
                        if (response.isSuccessful && !body.isNullOrBlank()) {
                            val features = JSONObject(body).optJSONArray("features")
                            if (features != null) {
                                for (i in 0 until features.length()) {
                                    val feature = features.optJSONObject(i) ?: continue
                                    val geometry = feature.optJSONObject("geometry") ?: continue
                                    val coordinates = geometry.optJSONArray("coordinates") ?: continue
                                    if (coordinates.length() < 2) continue

                                    val longitude = coordinates.optDouble(0, Double.NaN)
                                    val latitude = coordinates.optDouble(1, Double.NaN)
                                    if (!latitude.isFinite() || !longitude.isFinite()) continue

                                    val properties = feature.optJSONObject("properties") ?: JSONObject()
                                    val name = properties.optString("name")
                                        .takeIf { it.isNotBlank() }
                                    val houseNumber = properties.optString("housenumber")
                                        .takeIf { it.isNotBlank() }
                                    val street = properties.optString("street")
                                        .takeIf { it.isNotBlank() }
                                    val streetLine = listOfNotNull(houseNumber, street)
                                        .joinToString(" ")
                                        .takeIf { it.isNotBlank() }
                                    val city = listOf(
                                        "city", "town", "village", "locality", "district"
                                    ).firstNotNullOfOrNull { key ->
                                        properties.optString(key).takeIf { it.isNotBlank() }
                                    }
                                    val postcode = properties.optString("postcode")
                                        .takeIf { it.isNotBlank() }

                                    val label = listOfNotNull(
                                        name,
                                        streetLine,
                                        city,
                                        postcode
                                    ).distinct().joinToString(", ").ifBlank { query }

                                    candidates += Destination(
                                        label = label,
                                        point = GeoPoint(latitude, longitude),
                                        distanceMeters = distanceTo(latitude, longitude)
                                    )
                                }
                            }
                        }
                    }
                } catch (_: Exception) {
                    // Android Geocoder below remains available as a fallback/supplement.
                }

                // 2) Android Geocoder supplements exact street addresses and towns.
                try {
                    @Suppress("DEPRECATION")
                    val found = Geocoder(context, Locale.FRANCE)
                        .getFromLocationName(query, 8)
                        .orEmpty()

                    found.forEach { address ->
                        val label = listOfNotNull(
                            address.featureName,
                            address.thoroughfare,
                            address.locality,
                            address.postalCode
                        ).distinct().joinToString(", ").ifBlank { query }

                        candidates += Destination(
                            label = label,
                            point = GeoPoint(address.latitude, address.longitude),
                            distanceMeters = distanceTo(address.latitude, address.longitude)
                        )
                    }
                } catch (_: Exception) {
                    // If both providers fail, the empty result is handled below.
                }

                candidates
                    .distinctBy {
                        val lat = String.format(Locale.US, "%.5f", it.point.latitude)
                        val lon = String.format(Locale.US, "%.5f", it.point.longitude)
                        "${it.label.lowercase(Locale.FRANCE)}|$lat|$lon"
                    }
                    .sortedWith(
                        compareBy<Destination> { it.distanceMeters ?: Double.MAX_VALUE }
                            .thenBy { it.label }
                    )
                    .take(8)
            }

            searchResults = results
            destination = null
            routeOptions = emptyList()
            selectedRouteIndex = 0

            if (results.isEmpty()) {
                error = "Aucun résultat. Essayez le nom du commerce, la ville ou le code postal."
            }

            searching = false
        }
    }
'''
text = text[:start] + new_search + text[end:]

# Show selectable nearby results before the chosen destination.
ui_anchor = '''        destination?.let {

            Text(
                text =
                    "Destination : ${it.label}",
'''
results_ui = '''        if (searchResults.isNotEmpty()) {
            Text(
                text = "Résultats les plus proches",
                color = Color.White,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(top = 4.dp, bottom = 4.dp)
            )

            searchResults.take(5).forEach { result ->
                val distanceText = result.distanceMeters?.let { distance ->
                    if (distance < 1000.0) {
                        "${distance.toInt()} m"
                    } else {
                        String.format(Locale.FRANCE, "%.1f km", distance / 1000.0)
                    }
                }

                OutlinedButton(
                    onClick = {
                        destination = result
                        searchResults = emptyList()
                        routeOptions = emptyList()
                        selectedRouteIndex = 0
                        currentLocation?.let { location ->
                            calculateRoute(
                                GeoPoint(location.latitude, location.longitude),
                                result.point
                            )
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 2.dp)
                ) {
                    Text(
                        text = if (distanceText != null) {
                            "${result.label}  •  $distanceText"
                        } else {
                            result.label
                        },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }
        }

''' + ui_anchor
if ui_anchor not in text:
    raise SystemExit("V135 patch: destination UI anchor not found")
text = text.replace(ui_anchor, results_ui, 1)

# Slightly clearer wording now that places and shops are first-class searches.
text = text.replace('Text("Adresse, ville ou lieu")', 'Text("Adresse, commerce ou lieu")', 1)
text = text.replace('Text(\n                "Rechercher l\'adresse"\n            )', 'Text(\n                "Rechercher"\n            )', 1)

path.write_text(text, encoding="utf-8")
print("V135 POI patch applied successfully")
