from pathlib import Path

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
s = main.read_text()

# Import scale for the car-only splash crop.
anchor = 'import androidx.compose.ui.graphics.drawscope.Stroke\n'
if 'import androidx.compose.ui.draw.scale' not in s:
    if anchor not in s:
        raise SystemExit('V156: import anchor missing')
    s = s.replace(anchor, anchor + 'import androidx.compose.ui.draw.scale\n', 1)

# Modern splash using the existing artwork, cropped to the VSP side so the scooter is not visible.
old = '''    Box(Modifier.fillMaxSize().background(Color.Black), contentAlignment = Alignment.Center) {
        Image(
            painter = painterResource(id = R.drawable.vsp_home),
            contentDescription = "VSP GPS",
            modifier = Modifier.fillMaxSize(),
            // V383 : en paysage, montrer l’image entière au lieu de couper fortement
            // la voiture et le visuel d’itinéraire avec ContentScale.Crop.
            contentScale = if (isLandscape) ContentScale.Fit else ContentScale.Crop
        )
    }'''
new = '''    Box(Modifier.fillMaxSize().background(Color(0xFF061426)), contentAlignment = Alignment.Center) {
        // V156 : conserver l’illustration validée, mais cadrer la partie gauche en portrait
        // afin de ne montrer que la VSP. Le scooter sort du champ sans toucher au fichier image.
        Image(
            painter = painterResource(id = R.drawable.vsp_home),
            contentDescription = "VSP GPS",
            modifier = Modifier
                .fillMaxSize()
                .then(if (isLandscape) Modifier else Modifier.scale(1.14f)),
            contentScale = if (isLandscape) ContentScale.Fit else ContentScale.Crop,
            alignment = if (isLandscape) Alignment.Center else Alignment.CenterStart
        )
        if (!isLandscape) {
            Card(
                modifier = Modifier
                    .align(Alignment.TopStart)
                    .statusBarsPadding()
                    .padding(start = 22.dp, top = 20.dp),
                shape = RoundedCornerShape(22.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xD9081B30))
            ) {
                Column(Modifier.padding(horizontal = 16.dp, vertical = 11.dp)) {
                    Text("VSP GPS", color = Color.White, fontSize = 26.sp, fontWeight = FontWeight.ExtraBold)
                    Text("La route pensée pour les voitures sans permis", color = Color(0xFFB9D9FF), fontSize = 11.sp)
                }
            }
        }
    }'''
if old not in s:
    raise SystemExit('V156: WelcomeScreen anchor missing')
s = s.replace(old, new, 1)

# Visual map matching: guidance/safety keep using raw GPS. Only the displayed icon is projected.
anchor = '''    val gpsAccuracyMeters = liveLocation
        ?.takeIf { it.hasAccuracy() }
        ?.accuracy
        ?.toDouble()
        ?: Double.POSITIVE_INFINITY
'''
insert = anchor + '''
    // V156 UI/PRÉCISION : la sécurité et le guidage continuent d'utiliser le fix GPS brut.
    // Seule l'icône affichée est projetée sur le segment routier cohérent quand le signal
    // est suffisamment précis. Un vrai hors-itinéraire reste donc visible et détectable.
    fun visualMatchedPoint(location: Location?): GeoPoint? {
        if (location == null) return null
        val raw = GeoPoint(location.latitude, location.longitude)
        if (simulationActive || route.points.size < 2) return raw
        val accuracy = location.takeIf { it.hasAccuracy() }?.accuracy?.toDouble() ?: return raw
        if (!gpsFixFresh || accuracy > 45.0 || offRoute) return raw

        val nearest = nearestRouteSegment(location) ?: return raw
        val anchorSegment = trackedRouteSegment ?: nearest.first
        val start = (anchorSegment - 4).coerceAtLeast(0)
        val end = (anchorSegment + 9).coerceAtMost(route.points.lastIndex - 1)
        val lat0 = Math.toRadians(location.latitude)
        val earthRadius = 6_371_000.0
        var bestDistance = Double.POSITIVE_INFINITY
        var bestPoint: GeoPoint? = null
        for (i in start..end) {
            val a = route.points[i]
            val b = route.points[i + 1]
            val ax = earthRadius * Math.toRadians(a.longitude - location.longitude) * kotlin.math.cos(lat0)
            val ay = earthRadius * Math.toRadians(a.latitude - location.latitude)
            val bx = earthRadius * Math.toRadians(b.longitude - location.longitude) * kotlin.math.cos(lat0)
            val by = earthRadius * Math.toRadians(b.latitude - location.latitude)
            val vx = bx - ax
            val vy = by - ay
            val len2 = vx * vx + vy * vy
            val t = if (len2 <= 0.0001) 0.0 else ((-ax * vx - ay * vy) / len2).coerceIn(0.0, 1.0)
            val px = ax + t * vx
            val py = ay + t * vy
            val d = kotlin.math.sqrt(px * px + py * py)
            if (d < bestDistance) {
                bestDistance = d
                bestPoint = GeoPoint(
                    a.latitude + (b.latitude - a.latitude) * t,
                    a.longitude + (b.longitude - a.longitude) * t
                )
            }
        }
        val snapLimit = kotlin.math.max(18.0, accuracy * 1.35).coerceAtMost(42.0)
        return if (bestDistance <= snapLimit) bestPoint ?: raw else raw
    }

    val matchedVisualPoint = visualMatchedPoint(liveLocation)
    var smoothedVisualPoint by remember(routeRevisionKey) { mutableStateOf<GeoPoint?>(null) }
    LaunchedEffect(matchedVisualPoint?.latitude, matchedVisualPoint?.longitude, simulationActive) {
        val target = matchedVisualPoint ?: run {
            smoothedVisualPoint = null
            return@LaunchedEffect
        }
        val previous = smoothedVisualPoint
        if (previous == null || simulationActive || previous.distanceToAsDouble(target) > 35.0) {
            smoothedVisualPoint = target
        } else {
            val speed = liveLocation?.takeIf { it.hasSpeed() }?.speed ?: 0f
            val alpha = when {
                speed >= 12f -> 0.82
                speed >= 6f -> 0.72
                speed >= 2f -> 0.62
                else -> 0.48
            }
            smoothedVisualPoint = GeoPoint(
                previous.latitude + (target.latitude - previous.latitude) * alpha,
                previous.longitude + (target.longitude - previous.longitude) * alpha
            )
        }
    }
'''
if anchor not in s:
    raise SystemExit('V156: gpsAccuracy anchor missing')
s = s.replace(anchor, insert, 1)

# Adaptive bearing smoothing.
old = '''                    // Lisse les changements de cap pour éviter les rotations brusques de la carte.
                    val targetBearing = location.bearing
                    var delta = (targetBearing - liveBearing + 540f) % 360f - 180f
                    if (kotlin.math.abs(delta) < 2f) delta = 0f
                    liveBearing = (liveBearing + delta * 0.28f + 360f) % 360f'''
new = '''                    // V156 : lissage adaptatif du cap. À faible vitesse on filtre davantage
                    // les oscillations GPS ; à vitesse normale on suit plus vite un vrai virage.
                    val targetBearing = location.bearing
                    var delta = (targetBearing - liveBearing + 540f) % 360f - 180f
                    val deadZone = if (location.speed < 3f) 4f else 2f
                    if (kotlin.math.abs(delta) < deadZone) delta = 0f
                    val bearingAlpha = when {
                        location.speed < 3f -> 0.18f
                        location.speed < 8f -> 0.32f
                        else -> 0.46f
                    }
                    liveBearing = (liveBearing + delta * bearingAlpha + 360f) % 360f'''
if old not in s:
    raise SystemExit('V156: bearing anchor missing')
s = s.replace(old, new, 1)

# Display the visually matched point; raw GPS remains the source for all calculations.
old = '''                        val position = liveLocation?.let {
                            GeoPoint(it.latitude, it.longitude)
                        }
'''
new = '''                        val position = smoothedVisualPoint ?: liveLocation?.let {
                            GeoPoint(it.latitude, it.longitude)
                        }
'''
if old not in s:
    raise SystemExit('V156: map position anchor missing')
s = s.replace(old, new, 1)

# Modernize the instruction panel while retaining all maneuver logic.
old = '''                            .padding(start = 12.dp, top = 12.dp, end = 12.dp),
                        shape = RoundedCornerShape(18.dp),
                        colors = CardDefaults.cardColors(containerColor = Color(0xF0102A46))'''
new = '''                            .padding(start = 12.dp, top = 12.dp, end = 12.dp)
                            .border(1.dp, Color(0x554C9DFF), RoundedCornerShape(24.dp)),
                        shape = RoundedCornerShape(24.dp),
                        colors = CardDefaults.cardColors(containerColor = Color(0xF20A2038))'''
if old not in s:
    raise SystemExit('V156: guidance card anchor missing')
s = s.replace(old, new, 1)
s = s.replace('modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp),', 'modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),', 1)
s = s.replace('fontSize = 38.sp,', 'fontSize = 42.sp,', 1)
s = s.replace('fontSize = 22.sp,', 'fontSize = 24.sp,', 1)
s = s.replace('fontSize = 17.sp,', 'fontSize = 18.sp,', 1)

# Modernize the portrait information card.
old = '''            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF102A46))'''
new = '''            shape = RoundedCornerShape(24.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF0B2038))'''
if old not in s:
    raise SystemExit('V156: bottom card anchor missing')
s = s.replace(old, new, 1)
s = s.replace('.padding(start = 18.dp, end = 18.dp, bottom = if (navigationLandscape) 5.dp else 12.dp),', '.padding(start = 18.dp, end = 18.dp, bottom = if (navigationLandscape) 5.dp else 16.dp),', 1)
# First arrival value in portrait: slightly stronger visual hierarchy.
s = s.replace('fontWeight = FontWeight.Bold, fontSize = if (navigationLandscape) 13.sp else 16.sp)', 'fontWeight = FontWeight.ExtraBold, fontSize = if (navigationLandscape) 13.sp else 18.sp)', 1)

main.write_text(s)
print('V156 patch applied: modern splash/navigation + visual GPS map matching')
