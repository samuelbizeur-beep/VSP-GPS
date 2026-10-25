from pathlib import Path

path = Path("app/src/main/java/fr/vspgps/app/MainActivity.kt")
text = path.read_text(encoding="utf-8")

start_marker = "    fun searchAddress() {\n"
end_marker = "\n    if (navigationStarted && destination != null && routePoints.isNotEmpty()) {"
start = text.find(start_marker)
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("V137 patch: searchAddress markers not found")

new_search = '''    fun searchAddress() {

        if (query.isBlank() || searching) {
            return
        }

        searching = true
        error = null

        scope.launch {
            val results = withContext(Dispatchers.IO) {
                val candidates = mutableListOf<Destination>()
                val seenCoordinates = mutableSetOf<String>()
                val fastClient = OkHttpClient.Builder()
                    .connectTimeout(3, java.util.concurrent.TimeUnit.SECONDS)
                    .readTimeout(5, java.util.concurrent.TimeUnit.SECONDS)
                    .callTimeout(6, java.util.concurrent.TimeUnit.SECONDS)
                    .build()

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

                fun addCandidate(label: String, latitude: Double, longitude: Double) {
                    if (!latitude.isFinite() || !longitude.isFinite()) return
                    val key = String.format(Locale.US, "%.5f|%.5f", latitude, longitude)
                    if (seenCoordinates.add(key)) {
                        candidates += Destination(
                            label = label,
                            point = GeoPoint(latitude, longitude),
                            distanceMeters = distanceTo(latitude, longitude)
                        )
                    }
                }

                val rawQuery = query.trim()
                val normalizedQuery = rawQuery.lowercase(Locale.FRANCE)
                val isPharmacy = normalizedQuery.contains("pharmac")
                val isFriterie = normalizedQuery.contains("friter") ||
                        normalizedQuery == "frite" || normalizedQuery == "frites"
                val supermarketBrands = listOf(
                    "leclerc", "e.leclerc", "lidl", "aldi", "carrefour",
                    "intermarche", "intermarché", "auchan", "match"
                )
                val matchedBrand = supermarketBrands.firstOrNull {
                    normalizedQuery.contains(it)
                }

                fun parseOverpass() {
                    val location = currentLocation ?: return
                    if (!isPharmacy && !isFriterie && matchedBrand == null) return

                    try {
                        val queryText = when {
                            isPharmacy -> """
                                [out:json][timeout:6];
                                nwr(around:10000,${location.latitude},${location.longitude})[\"amenity\"=\"pharmacy\"];
                                out center tags 40;
                            """.trimIndent()
                            isFriterie -> """
                                [out:json][timeout:6];
                                (
                                  nwr(around:8000,${location.latitude},${location.longitude})[\"name\"~\"frit\",i];
                                  nwr(around:8000,${location.latitude},${location.longitude})[\"cuisine\"~\"frit|french_fries\",i];
                                  nwr(around:6000,${location.latitude},${location.longitude})[\"amenity\"=\"fast_food\"];
                                );
                                out center tags 50;
                            """.trimIndent()
                            else -> {
                                val brandRegex = when (matchedBrand) {
                                    "leclerc", "e.leclerc" -> "e\\.?[ -]?leclerc|leclerc"
                                    "intermarche", "intermarché" -> "intermarch[eé]"
                                    else -> Regex.escape(matchedBrand ?: rawQuery)
                                }
                                """
                                    [out:json][timeout:6];
                                    (
                                      nwr(around:25000,${location.latitude},${location.longitude})[\"shop\"~\"supermarket|convenience|department_store\"][\"name\"~\"$brandRegex\",i];
                                      nwr(around:25000,${location.latitude},${location.longitude})[\"shop\"~\"supermarket|convenience|department_store\"][\"brand\"~\"$brandRegex\",i];
                                    );
                                    out center tags 40;
                                """.trimIndent()
                            }
                        }

                        val encoded = URLEncoder.encode(
                            queryText,
                            StandardCharsets.UTF_8.toString()
                        )
                        val request = Request.Builder()
                            .url("https://overpass-api.de/api/interpreter?data=$encoded")
                            .header("User-Agent", "VSP-GPS/1.37 Android")
                            .build()

                        fastClient.newCall(request).execute().use { response ->
                            val body = response.body?.string()
                            if (!response.isSuccessful || body.isNullOrBlank()) return
                            val elements = JSONObject(body).optJSONArray("elements") ?: return

                            for (i in 0 until elements.length()) {
                                val element = elements.optJSONObject(i) ?: continue
                                val center = element.optJSONObject("center")
                                val latitude = when {
                                    element.has("lat") -> element.optDouble("lat", Double.NaN)
                                    center != null -> center.optDouble("lat", Double.NaN)
                                    else -> Double.NaN
                                }
                                val longitude = when {
                                    element.has("lon") -> element.optDouble("lon", Double.NaN)
                                    center != null -> center.optDouble("lon", Double.NaN)
                                    else -> Double.NaN
                                }
                                if (!latitude.isFinite() || !longitude.isFinite()) continue

                                val tags = element.optJSONObject("tags") ?: JSONObject()
                                val name = tags.optString("name").takeIf { it.isNotBlank() }
                                val brand = tags.optString("brand").takeIf { it.isNotBlank() }
                                val cuisine = tags.optString("cuisine").takeIf { it.isNotBlank() }
                                val amenity = tags.optString("amenity")
                                val shop = tags.optString("shop")
                                val combined = listOfNotNull(name, brand, cuisine)
                                    .joinToString(" ")
                                    .lowercase(Locale.FRANCE)

                                val accepted = when {
                                    isPharmacy -> amenity == "pharmacy" || combined.contains("pharmac")
                                    isFriterie -> combined.contains("frit") || amenity == "fast_food"
                                    matchedBrand != null -> {
                                        val normalizedBrand = when (matchedBrand) {
                                            "e.leclerc" -> "leclerc"
                                            "intermarché" -> "intermarche"
                                            else -> matchedBrand
                                        }
                                        val normalizedCombined = combined
                                            .replace("é", "e")
                                            .replace(".", "")
                                        shop in setOf("supermarket", "convenience", "department_store") &&
                                                normalizedCombined.contains(normalizedBrand.replace("é", "e").replace(".", ""))
                                    }
                                    else -> true
                                }
                                if (!accepted) continue

                                val houseNumber = tags.optString("addr:housenumber").takeIf { it.isNotBlank() }
                                val street = tags.optString("addr:street").takeIf { it.isNotBlank() }
                                val city = tags.optString("addr:city").takeIf { it.isNotBlank() }
                                val postcode = tags.optString("addr:postcode").takeIf { it.isNotBlank() }
                                val streetLine = listOfNotNull(houseNumber, street)
                                    .joinToString(" ")
                                    .takeIf { it.isNotBlank() }
                                val defaultName = when {
                                    isPharmacy -> "Pharmacie"
                                    isFriterie -> "Restauration rapide"
                                    else -> matchedBrand ?: rawQuery
                                }
                                val label = listOfNotNull(
                                    name ?: brand ?: defaultName,
                                    streetLine,
                                    city,
                                    postcode
                                ).distinct().joinToString(", ")
                                addCandidate(label, latitude, longitude)
                            }
                        }
                    } catch (_: Exception) {
                    }
                }

                fun parsePhoton(searchText: String) {
                    try {
                        val encodedQuery = URLEncoder.encode(
                            searchText,
                            StandardCharsets.UTF_8.toString()
                        )
                        val locationBias = currentLocation?.let {
                            "&lat=${it.latitude}&lon=${it.longitude}"
                        }.orEmpty()
                        val request = Request.Builder()
                            .url("https://photon.komoot.io/api/?q=$encodedQuery&limit=20&lang=fr$locationBias")
                            .header("User-Agent", "VSP-GPS/1.37 Android")
                            .build()

                        fastClient.newCall(request).execute().use { response ->
                            val body = response.body?.string()
                            if (!response.isSuccessful || body.isNullOrBlank()) return
                            val features = JSONObject(body).optJSONArray("features") ?: return
                            for (i in 0 until features.length()) {
                                val feature = features.optJSONObject(i) ?: continue
                                val geometry = feature.optJSONObject("geometry") ?: continue
                                val coordinates = geometry.optJSONArray("coordinates") ?: continue
                                if (coordinates.length() < 2) continue
                                val longitude = coordinates.optDouble(0, Double.NaN)
                                val latitude = coordinates.optDouble(1, Double.NaN)
                                if (!latitude.isFinite() || !longitude.isFinite()) continue

                                val properties = feature.optJSONObject("properties") ?: JSONObject()
                                val name = properties.optString("name").takeIf { it.isNotBlank() }
                                val brand = properties.optString("brand").takeIf { it.isNotBlank() }
                                val osmKey = properties.optString("osm_key")
                                val osmValue = properties.optString("osm_value")
                                val combined = listOfNotNull(name, brand)
                                    .joinToString(" ")
                                    .lowercase(Locale.FRANCE)
                                    .replace("é", "e")
                                    .replace(".", "")

                                val accepted = when {
                                    isPharmacy -> osmValue == "pharmacy" || combined.contains("pharmac")
                                    isFriterie -> combined.contains("frit") || osmValue == "fast_food"
                                    matchedBrand != null -> {
                                        val wanted = matchedBrand.replace("é", "e").replace(".", "")
                                        val isStreet = osmKey == "highway" || osmValue == "street"
                                        !isStreet && combined.contains(wanted) &&
                                                (osmKey == "shop" || osmValue in setOf("supermarket", "convenience", "department_store"))
                                    }
                                    else -> true
                                }
                                if (!accepted) continue

                                val houseNumber = properties.optString("housenumber").takeIf { it.isNotBlank() }
                                val street = properties.optString("street").takeIf { it.isNotBlank() }
                                val city = listOf("city", "town", "village", "locality", "district")
                                    .firstNotNullOfOrNull { key ->
                                        properties.optString(key).takeIf { it.isNotBlank() }
                                    }
                                val postcode = properties.optString("postcode").takeIf { it.isNotBlank() }
                                val streetLine = listOfNotNull(houseNumber, street)
                                    .joinToString(" ")
                                    .takeIf { it.isNotBlank() }
                                val label = listOfNotNull(name ?: brand, streetLine, city, postcode)
                                    .distinct().joinToString(", ").ifBlank { rawQuery }
                                addCandidate(label, latitude, longitude)
                            }
                        }
                    } catch (_: Exception) {
                    }
                }

                // Fast path: one targeted nearby query first.
                parseOverpass()

                // Only one fallback web search if the targeted source did not return enough nearby results.
                if (candidates.size < 4) {
                    parsePhoton(rawQuery)
                }

                // Exact addresses still get Android Geocoder as a local fallback.
                if (!isPharmacy && !isFriterie && matchedBrand == null && candidates.size < 3) {
                    try {
                        @Suppress("DEPRECATION")
                        val found = Geocoder(context, Locale.FRANCE)
                            .getFromLocationName(rawQuery, 6)
                            .orEmpty()
                        found.forEach { address ->
                            val label = listOfNotNull(
                                address.featureName,
                                address.thoroughfare,
                                address.locality,
                                address.postalCode
                            ).distinct().joinToString(", ").ifBlank { rawQuery }
                            addCandidate(label, address.latitude, address.longitude)
                        }
                    } catch (_: Exception) {
                    }
                }

                candidates
                    .sortedBy { it.distanceMeters ?: Double.MAX_VALUE }
                    .take(10)
            }

            searchResults = results
            destination = null
            routeOptions = emptyList()
            selectedRouteIndex = 0

            if (results.isEmpty()) {
                error = "Aucun résultat proche. Essayez le nom du commerce avec la ville."
            }

            searching = false
        }
    }
'''

text = text[:start] + new_search + text[end:]
path.write_text(text, encoding="utf-8")
print("V137 fast POI patch applied successfully")
