from pathlib import Path

path = Path("app/src/main/java/fr/vspgps/app/MainActivity.kt")
text = path.read_text(encoding="utf-8")

start_marker = "    fun searchAddress() {\n"
end_marker = "\n    if (navigationStarted && destination != null && routePoints.isNotEmpty()) {"
start = text.find(start_marker)
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit("V136 patch: searchAddress markers not found")

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
                        normalizedQuery == "frite" ||
                        normalizedQuery == "frites"

                val supermarketBrands = listOf(
                    "leclerc", "e.leclerc", "lidl", "aldi", "carrefour",
                    "intermarche", "intermarché", "auchan", "match"
                )
                val matchedBrand = supermarketBrands.firstOrNull {
                    normalizedQuery.contains(it)
                }

                var localTown: String? = null
                currentLocation?.let { location ->
                    try {
                        @Suppress("DEPRECATION")
                        val address = Geocoder(context, Locale.FRANCE)
                            .getFromLocation(location.latitude, location.longitude, 1)
                            ?.firstOrNull()
                        localTown = listOfNotNull(
                            address?.locality,
                            address?.subLocality,
                            address?.postalCode
                        ).firstOrNull { it.isNotBlank() }
                    } catch (_: Exception) {
                        localTown = null
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
                        val url = "https://photon.komoot.io/api/?q=$encodedQuery&limit=30&lang=fr$locationBias"
                        val request = Request.Builder()
                            .url(url)
                            .header("User-Agent", "VSP-GPS/1.36 Android")
                            .build()

                        OkHttpClient().newCall(request).execute().use { response ->
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
                                val cuisine = properties.optString("cuisine").takeIf { it.isNotBlank() }
                                val osmKey = properties.optString("osm_key")
                                val osmValue = properties.optString("osm_value")
                                val houseNumber = properties.optString("housenumber").takeIf { it.isNotBlank() }
                                val street = properties.optString("street").takeIf { it.isNotBlank() }
                                val city = listOf("city", "town", "village", "locality", "district")
                                    .firstNotNullOfOrNull { key ->
                                        properties.optString(key).takeIf { it.isNotBlank() }
                                    }
                                val postcode = properties.optString("postcode").takeIf { it.isNotBlank() }

                                val combined = listOfNotNull(name, brand, cuisine)
                                    .joinToString(" ")
                                    .lowercase(Locale.FRANCE)
                                val distance = distanceTo(latitude, longitude)

                                val accepted = when {
                                    isPharmacy ->
                                        osmValue == "pharmacy" ||
                                                combined.contains("pharmac")

                                    isFriterie ->
                                        combined.contains("frit") ||
                                                osmValue == "fast_food" ||
                                                (osmValue == "restaurant" && (distance ?: Double.MAX_VALUE) <= 5000.0)

                                    matchedBrand != null -> {
                                        val isStreetLike = osmKey == "highway" || osmValue == "street"
                                        val brandMatch = combined.contains(matchedBrand.lowercase(Locale.FRANCE))
                                        !isStreetLike && brandMatch &&
                                                (osmKey == "shop" || osmValue in setOf(
                                                    "supermarket", "convenience", "department_store", "mall"
                                                ))
                                    }

                                    else -> true
                                }

                                if (!accepted) continue

                                val streetLine = listOfNotNull(houseNumber, street)
                                    .joinToString(" ")
                                    .takeIf { it.isNotBlank() }
                                val label = listOfNotNull(
                                    name ?: brand,
                                    streetLine,
                                    city,
                                    postcode
                                ).distinct().joinToString(", ").ifBlank { rawQuery }

                                addCandidate(label, latitude, longitude)
                            }
                        }
                    } catch (_: Exception) {
                    }
                }

                // Priorité à la commune réelle de l'utilisateur : évite de sauter
                // directement vers Liévin/Arras quand le POI existe dans la commune.
                localTown?.let { town ->
                    parsePhoton("$rawQuery $town")
                }
                parsePhoton(rawQuery)

                // Complément direct OpenStreetMap pour les catégories locales courantes.
                // Photon peut rater certains commerces pourtant bien présents dans OSM.
                val location = currentLocation
                if (location != null && (isPharmacy || isFriterie)) {
                    try {
                        val overpassQuery = if (isPharmacy) {
                            """
                            [out:json][timeout:10];
                            (
                              nwr(around:12000,${location.latitude},${location.longitude})[\"amenity\"=\"pharmacy\"];
                            );
                            out center tags 40;
                            """.trimIndent()
                        } else {
                            """
                            [out:json][timeout:10];
                            (
                              nwr(around:12000,${location.latitude},${location.longitude})[\"name\"~\"frit\",i];
                              nwr(around:12000,${location.latitude},${location.longitude})[\"cuisine\"~\"frit|french_fries\",i];
                              nwr(around:7000,${location.latitude},${location.longitude})[\"amenity\"=\"fast_food\"];
                            );
                            out center tags 60;
                            """.trimIndent()
                        }

                        val encoded = URLEncoder.encode(
                            overpassQuery,
                            StandardCharsets.UTF_8.toString()
                        )
                        val url = "https://overpass-api.de/api/interpreter?data=$encoded"
                        val request = Request.Builder()
                            .url(url)
                            .header("User-Agent", "VSP-GPS/1.36 Android")
                            .build()

                        OkHttpClient().newCall(request).execute().use { response ->
                            val body = response.body?.string()
                            if (response.isSuccessful && !body.isNullOrBlank()) {
                                val elements = JSONObject(body).optJSONArray("elements")
                                if (elements != null) {
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
                                        val houseNumber = tags.optString("addr:housenumber").takeIf { it.isNotBlank() }
                                        val street = tags.optString("addr:street").takeIf { it.isNotBlank() }
                                        val city = tags.optString("addr:city").takeIf { it.isNotBlank() }
                                        val postcode = tags.optString("addr:postcode").takeIf { it.isNotBlank() }
                                        val streetLine = listOfNotNull(houseNumber, street)
                                            .joinToString(" ")
                                            .takeIf { it.isNotBlank() }
                                        val label = listOfNotNull(
                                            name ?: brand ?: if (isPharmacy) "Pharmacie" else "Restauration rapide",
                                            streetLine,
                                            city,
                                            postcode
                                        ).distinct().joinToString(", ")

                                        addCandidate(label, latitude, longitude)
                                    }
                                }
                            }
                        }
                    } catch (_: Exception) {
                    }
                }

                // Pour une adresse classique, on garde Android Geocoder en secours.
                // On l'évite pour les catégories/enseignes afin de ne pas mélanger rues et commerces.
                if (!isPharmacy && !isFriterie && matchedBrand == null) {
                    try {
                        @Suppress("DEPRECATION")
                        val found = Geocoder(context, Locale.FRANCE)
                            .getFromLocationName(rawQuery, 8)
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
                    .sortedWith(
                        compareBy<Destination> { it.distanceMeters ?: Double.MAX_VALUE }
                            .thenBy { it.label }
                    )
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
print("V136 local POI patch applied successfully")
