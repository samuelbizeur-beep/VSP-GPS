from pathlib import Path

# V143: part de la V142 restaurée puis corrige l'écran de comparaison.
gradle = Path('app/build.gradle.kts')
text = gradle.read_text(encoding='utf-8')
text = text.replace('versionCode = 142', 'versionCode = 143', 1)
text = text.replace('versionName = "V142"', 'versionName = "V143"', 1)
gradle.write_text(text, encoding='utf-8')

router = Path('app/src/main/java/fr/vspgps/app/LocalValhallaRouter.kt')
r = router.read_text(encoding='utf-8')
start_marker = '    @Synchronized\n    fun previewProfiles('
end_marker = '    /** Étape 14 : comparaison expérimentale, sans modifier le guidage principal. */'
start = r.find(start_marker)
end = r.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('previewProfiles block not found')

new_preview = '''    @Synchronized
    fun previewProfiles(startLatitude: Double, startLongitude: Double, endLatitude: Double, endLongitude: Double): Result<List<ProfilePreview>> = runCatching {
        val init = initialize()
        if (init is InitializationResult.Failed) error(init.message)

        fun previewFromRoot(label: String, root: org.json.JSONObject): ProfilePreview {
            val json = root.getJSONObject("trip")
            val summary = json.getJSONObject("summary")
            val legs = json.getJSONArray("legs")
            require(legs.length() > 0) { "Aucun tronçon $label" }
            val leg = legs.getJSONObject(0)
            val maneuvers = leg.optJSONArray("maneuvers")
            val previewManeuvers = (0 until (maneuvers?.length() ?: 0)).map { index ->
                val maneuver = maneuvers!!.getJSONObject(index)
                val namesJson = maneuver.optJSONArray("street_names")
                val names = (0 until (namesJson?.length() ?: 0)).map { namesJson!!.optString(it) }.filter { it.isNotBlank() }
                PreviewManeuver(
                    instruction = maneuver.optString("instruction"),
                    beginShapeIndex = maneuver.optInt("begin_shape_index", -1),
                    endShapeIndex = maneuver.optInt("end_shape_index", -1),
                    streetNames = names,
                    lengthKm = maneuver.optDouble("length", Double.NaN),
                    timeSeconds = maneuver.optDouble("time", Double.NaN),
                    maneuverType = maneuver.optInt("type", -1),
                    exposedFields = maneuver.keys().asSequence().toList().sorted(),
                    nativeFields = maneuver.optJSONObject("native_fields")?.let { nf ->
                        nf.keys().asSequence().associateWith { key -> nf.opt(key)?.toString().orEmpty() }
                    }.orEmpty()
                )
            }
            val instructions = previewManeuvers.map { it.instruction }.filter { it.isNotBlank() }
            val km = summary.getDouble("length")
            val minutes = summary.getDouble("time") / 60.0
            val encodedShape = leg.getString("shape")
            val (traceEdges, traceStatus) = traceAttributesForShape(encodedShape)
            return ProfilePreview(
                label,
                "${"%.2f".format(java.util.Locale.FRANCE, km)} km • ${"%.0f".format(java.util.Locale.FRANCE, minutes)} min (moteur)",
                encodedShape,
                instructions,
                previewManeuvers,
                traceEdges,
                traceStatus
            )
        }

        // Bleu = vrai calcul VSP 45 km/h : calculateRouteJson refuse tout candidat
        // contenant encore une arête motorway et recalcule jusqu'à 0 motorway.
        val vspRoot = calculateRouteJson(
            startLatitude = startLatitude,
            startLongitude = startLongitude,
            endLatitude = endLatitude,
            endLongitude = endLongitude
        ).getOrElse { error ->
            throw IllegalStateException("Comparaison VSP : ${error.message ?: error.javaClass.simpleName}")
        }

        // Orange = profil motor_scooter natif, conservé uniquement comme diagnostic.
        // Il n'est jamais présenté comme trajet VSP sûr tant que son audit n'est pas à 0 motorway.
        val scooterRequest = RouteRequest(
            locations = listOf(
                RoutingWaypoint(lat = startLatitude, lon = startLongitude),
                RoutingWaypoint(lat = endLatitude, lon = endLongitude)
            ),
            costing = CostingModel.motor_scooter
        )
        val scooterRoot = routeResponseForGps(requireNotNull(engine).route(scooterRequest))

        listOf(
            previewFromRoot("VSP 45 sécurisé", vspRoot),
            previewFromRoot("motor_scooter brut", scooterRoot)
        )
    }

'''
r = r[:start] + new_preview + r[end:]

# Résumé du bouton Comparer : le premier profil devient le vrai trajet VSP filtré.
old_return = '''        return test("auto", CostingModel.auto) + "\\n" +
            test("motor_scooter", CostingModel.motor_scooter) +
            "\\nComparaison expérimentale : aucun itinéraire certifié VSP."
'''
new_return = '''        val vspSummary = try {
            val root = calculateRouteJson(startLatitude, startLongitude, endLatitude, endLongitude).getOrThrow()
            val summary = root.getJSONObject("trip").getJSONObject("summary")
            val distance = summary.optDouble("length", Double.NaN)
            val seconds = summary.optDouble("time", Double.NaN)
            if (!distance.isFinite() || !seconds.isFinite()) "VSP 45 sécurisé : résumé incomplet"
            else "VSP 45 sécurisé : ${"%.2f".format(java.util.Locale.FRANCE, distance)} km • ${"%.0f".format(java.util.Locale.FRANCE, seconds / 60.0)} min (moteur)"
        } catch (error: Exception) {
            "VSP 45 sécurisé : échec (${error.message ?: error.javaClass.simpleName})"
        }
        return vspSummary + "\\n" +
            test("motor_scooter brut", CostingModel.motor_scooter) +
            "\\nBleu = trajet VSP filtré à 0 motorway. Orange = diagnostic scooter brut, non validé tant que son audit n'est pas à 0 motorway."
'''
if old_return not in r:
    raise SystemExit('compareProfiles return block not found')
r = r.replace(old_return, new_return, 1)
router.write_text(r, encoding='utf-8')

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
m = main.read_text(encoding='utf-8')
m = m.replace('V142', 'V143')
m = m.replace('Bleu : auto • Orange : motor_scooter', 'Bleu : VSP 45 sécurisé • Orange : scooter brut (diagnostic)', 1)
old_status = '''            val strictCandidateAccepted = flagged.isEmpty()
            Text(
                if (strictCandidateAccepted)
                    "🟡 Aucun attribut bloquant ni indice textuel détecté (trajet NON certifié VSP)."
                else
                    "⚠ ${flagged.size} tronçon(s) à contrôler dans les données réellement exposées.",
                color = if (strictCandidateAccepted) Color(0xFFFFC857) else Color(0xFFFF8A80),
                fontSize = 12.sp
            )
'''
new_status = '''            val motorwayInSelected = preview?.traceEdges?.count {
                it.roadClass?.equals("motorway", ignoreCase = true) == true
            } ?: 0
            Text(
                if (motorwayInSelected == 0)
                    "✓ ${preview?.label ?: "Profil"} : 0 arête motorway détectée"
                else
                    "⛔ ${preview?.label ?: "Profil"} : $motorwayInSelected arête(s) motorway — ne pas utiliser pour conduire",
                color = if (motorwayInSelected == 0) Color(0xFF81C784) else Color(0xFFFF8A80),
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold
            )
            if (flagged.isNotEmpty()) {
                Text("⚠ ${flagged.size} indice(s) textuel(s) supplémentaire(s) à contrôler.", color = Color(0xFFFFC857), fontSize = 11.sp)
            }
'''
if old_status not in m:
    raise SystemExit('comparison status block not found')
m = m.replace(old_status, new_status, 1)
old_help = 'Étape 28 : recalcul local automatique anti-motorway. Un candidat contenant motorway est rejeté, des points du tronçon sont exclus, puis Valhalla recalcule et trace_attributes revalide chaque nouveau candidat. Un trajet n’est accepté qu’à 0 arête motorway. Trunk et bretelles restent à contrôler.'
new_help = 'V143 : le tracé BLEU est maintenant le vrai calcul VSP 45 km/h passé par le verrou anti-motorway (0 motorway obligatoire). Le tracé ORANGE reste un profil scooter brut de comparaison : s’il contient motorway, il est affiché en rouge et ne doit pas être utilisé pour conduire. Trunk et bretelles restent des points à contrôler.'
if old_help not in m:
    raise SystemExit('comparison help text not found')
m = m.replace(old_help, new_help, 1)
main.write_text(m, encoding='utf-8')

print('V143 safe comparison patch applied')
