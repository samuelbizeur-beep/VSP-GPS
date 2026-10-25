from pathlib import Path

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
s = main.read_text()

# State for indoor precision testing. Only affects the simulated GPS fix.
anchor = '''    var simulationPaused by remember { mutableStateOf(false) }
'''
insert = anchor + '''    // V157 : banc d'essai précision à domicile. Le fix GPS simulé peut être
    // volontairement décalé latéralement du tracé pour vérifier le recalage visuel,
    // la détection hors itinéraire et le recalcul sans prendre la route.
    var simulationDriftMeters157 by remember { mutableStateOf(0.0) }
'''
if anchor not in s:
    raise SystemExit('V157: simulationPaused anchor missing')
s = s.replace(anchor, insert, 1)

# Inject a lateral offset in the simulated raw GPS location.
old = '''            val loc = Location("VSP_SIMULATION").apply {
                latitude = a.latitude + (b.latitude - a.latitude) * t
                longitude = a.longitude + (b.longitude - a.longitude) * t
                accuracy = 3f
                speed = speedMps.toFloat()
                bearing = segmentBearing
                elapsedRealtimeNanos = android.os.SystemClock.elapsedRealtimeNanos()
                time = System.currentTimeMillis()
            }'''
new = '''            val routeLatitude157 = a.latitude + (b.latitude - a.latitude) * t
            val routeLongitude157 = a.longitude + (b.longitude - a.longitude) * t
            val drift157 = simulationDriftMeters157
            val perpendicularBearing157 = Math.toRadians((segmentBearing + 90f).toDouble())
            val latitudeOffset157 = if (drift157 == 0.0) 0.0 else
                (drift157 * kotlin.math.cos(perpendicularBearing157)) / 111_320.0
            val longitudeScale157 = kotlin.math.cos(Math.toRadians(routeLatitude157)).coerceAtLeast(0.2)
            val longitudeOffset157 = if (drift157 == 0.0) 0.0 else
                (drift157 * kotlin.math.sin(perpendicularBearing157)) / (111_320.0 * longitudeScale157)
            val loc = Location("VSP_SIMULATION").apply {
                latitude = routeLatitude157 + latitudeOffset157
                longitude = routeLongitude157 + longitudeOffset157
                accuracy = 3f
                speed = speedMps.toFloat()
                bearing = segmentBearing
                elapsedRealtimeNanos = android.os.SystemClock.elapsedRealtimeNanos()
                time = System.currentTimeMillis()
            }'''
if old not in s:
    raise SystemExit('V157: simulated location anchor missing')
s = s.replace(old, new, 1)

# Reset drift when stopping test, so ordinary simulation always starts clean.
old = '''                        simulationRewinding = false
                        simulationPaused = false
                        activeRealGpsTestStopMeters93 = null'''
new = '''                        simulationRewinding = false
                        simulationPaused = false
                        simulationDriftMeters157 = 0.0
                        activeRealGpsTestStopMeters93 = null'''
if old not in s:
    raise SystemExit('V157: stop test reset anchor missing')
s = s.replace(old, new, 1)

# Add home precision controls below the speed controls.
anchor = '''                // ETAPE 57 : Pause/Reprendre rejoint la rangée des commandes de test.
'''
block = '''                // V157 : dérive GPS artificielle pour tests à domicile. 0 m = simulation
                // normale ; 8/20/40 m permettent de vérifier progressivement le recalage
                // visuel puis la bascule vers la détection hors itinéraire.
                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 5.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Text("Dérive GPS", color = Color(0xFF9FC7F7), fontSize = 10.sp)
                    listOf(0, 8, 20, 40).forEach { driftMeters157 ->
                        if (simulationDriftMeters157.toInt() == driftMeters157) {
                            Button(
                                onClick = { simulationDriftMeters157 = driftMeters157.toDouble() },
                                modifier = Modifier.weight(1f),
                                contentPadding = PaddingValues(horizontal = 2.dp, vertical = 1.dp)
                            ) { Text("${driftMeters157}m", fontSize = 10.sp) }
                        } else {
                            OutlinedButton(
                                onClick = { simulationDriftMeters157 = driftMeters157.toDouble() },
                                modifier = Modifier.weight(1f),
                                contentPadding = PaddingValues(horizontal = 2.dp, vertical = 1.dp)
                            ) { Text("${driftMeters157}m", fontSize = 10.sp) }
                        }
                    }
                }
                Text(
                    when {
                        simulationDriftMeters157 <= 0.0 -> "Test précision : GPS simulé exactement sur le tracé"
                        simulationDriftMeters157 <= 8.0 -> "Test précision : petite dérive • la flèche doit rester stable sur la route"
                        simulationDriftMeters157 <= 20.0 -> "Test précision : dérive moyenne • vérifier le recalage sans saut"
                        else -> "Test précision : forte dérive • le hors-itinéraire doit finir par être détecté"
                    },
                    color = if (simulationDriftMeters157 >= 40.0) Color(0xFFFFC857) else Color(0xFF8FD7A8),
                    fontSize = 9.sp,
                    modifier = Modifier.fillMaxWidth().padding(top = 2.dp)
                )

'''
if anchor not in s:
    raise SystemExit('V157: test controls anchor missing')
s = s.replace(anchor, block + anchor, 1)

# Add the drift amount to the mode banner, making screenshots self-explanatory.
old = '''                            "MODE TEST — position GPS simulée • accélération ×$simulationMultiplier"
'''
new = '''                            "MODE TEST — position GPS simulée • accélération ×$simulationMultiplier • dérive ${simulationDriftMeters157.toInt()} m"
'''
if old not in s:
    raise SystemExit('V157: mode banner normal anchor missing')
s = s.replace(old, new, 1)
old = '''                            "MODE TEST — position GPS simulée • ×16 intelligent (ralentissement auto)"
'''
new = '''                            "MODE TEST — position GPS simulée • ×16 intelligent • dérive ${simulationDriftMeters157.toInt()} m"
'''
if old not in s:
    raise SystemExit('V157: mode banner x16 anchor missing')
s = s.replace(old, new, 1)

main.write_text(s)
print('V157 patch applied: indoor GPS drift test 0/8/20/40 m')
