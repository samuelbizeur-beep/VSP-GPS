package fr.vspgps.app

import android.Manifest
import android.content.pm.PackageManager
import android.location.Location
import android.location.Geocoder
import android.os.Bundle
import androidx.compose.foundation.Image
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.osmdroid.config.Configuration
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker
import org.osmdroid.views.overlay.Polyline
import java.util.Locale
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
enum class VehicleType {
    VSP,
    SCOOTER_50
}

data class Destination(
    val label: String,
    val point: GeoPoint
)

data class RouteOption(
    val points: List<GeoPoint>,
    val distanceMeters: Double,
    val durationSeconds: Double
)

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        Configuration.getInstance().userAgentValue = packageName

        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    primary = Color(0xFF4DA3FF),
                    background = Color(0xFF07182E),
                    surface = Color(0xFF102A46)
                )
            ) {
                VspGpsApp()
            }
        }
    }
}

@Composable
fun VspGpsApp() {

    var started by remember { mutableStateOf(false) }
    var vehicle by remember { mutableStateOf(VehicleType.VSP) }

    if (!started) {
        WelcomeScreen(
            vehicle = vehicle,
            onVehicle = { vehicle = it },
            onStart = { started = true }
        )
    } else {
        MapSearchScreen(
            vehicle = vehicle,
            onBack = { started = false }
        )
    }
}

@Composable
fun WelcomeScreen(
    vehicle: VehicleType,
    onVehicle: (VehicleType) -> Unit,
    onStart: () -> Unit
) {
    Box(
        modifier = Modifier.fillMaxSize()
    ) {
        // Image de fond
        Image(
            painter = painterResource(id = R.drawable.vsp_home),
            contentDescription = null,
            modifier = Modifier.fillMaxSize(),
            contentScale = ContentScale.Crop
        )

        // Voile sombre léger pour garder les textes lisibles
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0x6603152B))
        )

        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 24.dp)
                .padding(top = 34.dp, bottom = 28.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {

            Text(
                text = "VSP GPS",
                color = Color.White,
                fontSize = 42.sp,
                fontWeight = FontWeight.Bold
            )

            Text(
                text = "Le GPS pensé pour votre mobilité",
                color = Color(0xFFB9D9FF),
                fontSize = 18.sp
            )

            Spacer(modifier = Modifier.height(24.dp))

            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(24.dp),
                colors = CardDefaults.cardColors(
                    containerColor = Color(0xCC082744)
                )
            ) {
                Column(
                    modifier = Modifier.padding(20.dp)
                ) {
                    Text(
                        text = "Où allez-vous ?",
                        color = Color.White,
                        fontSize = 27.sp,
                        fontWeight = FontWeight.Bold
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = "Trouvez votre destination et prenez la route.",
                        color = Color(0xFFD2E6FA),
                        fontSize = 16.sp
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    Button(
                        onClick = onStart,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(58.dp),
                        shape = RoundedCornerShape(18.dp)
                    ) {
                        Text(
                            text = "Rechercher une destination  →",
                            fontSize = 17.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            // Espace laissant apparaître la voiture et le scooter
            Spacer(modifier = Modifier.weight(1f))

            Text(
                text = "Choisissez votre véhicule",
                color = Color.White,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(14.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Button(
                    onClick = { onVehicle(VehicleType.VSP) },
                    modifier = Modifier
                        .weight(1f)
                        .height(54.dp),
                    shape = RoundedCornerShape(18.dp)
                ) {
                    Text(
                        text = "🚗  VSP",
                        fontSize = 16.sp
                    )
                }

                OutlinedButton(
                    onClick = { onVehicle(VehicleType.SCOOTER_50) },
                    modifier = Modifier
                        .weight(1f)
                        .height(54.dp),
                    shape = RoundedCornerShape(18.dp)
                ) {
                    Text(
                        text = "🛵  50 cm³",
                        fontSize = 16.sp,
                        color = Color.White
                    )
                }
            }
        }
    }
}
@Composable
fun MapSearchScreen(
    vehicle: VehicleType,
    onBack: () -> Unit
) {

    val context =
        androidx.compose.ui.platform.LocalContext.current

    val scope = rememberCoroutineScope()

    var query by remember {
        mutableStateOf("")
    }

    var destination by remember {
        mutableStateOf<Destination?>(null)
    }

    var searching by remember {
        mutableStateOf(false)
    }

    var error by remember {
        mutableStateOf<String?>(null)
    }

    var locationGranted by remember {
        mutableStateOf(false)
    }

    var currentLocation by remember {
        mutableStateOf<Location?>(null)
    }

    val startPoint = currentLocation?.let {
        GeoPoint(it.latitude, it.longitude)
    }
    var routeOptions by remember {
        mutableStateOf<List<RouteOption>>(emptyList())
    }

    var selectedRouteIndex by remember {
        mutableStateOf(0)
    }

    var navigationStarted by remember {
        mutableStateOf(false)
    }

    val routePoints =
        routeOptions.getOrNull(selectedRouteIndex)?.points ?: emptyList()
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions(),
        onResult = { permissions: Map<String, Boolean> ->
            locationGranted =
                permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
                        permissions[Manifest.permission.ACCESS_COARSE_LOCATION] == true
        }
    )

    val locationManager = context.getSystemService(
        android.content.Context.LOCATION_SERVICE
    ) as android.location.LocationManager
    LaunchedEffect(Unit) {

        locationGranted =
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.ACCESS_COARSE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED

        if (!locationGranted) {

            permissionLauncher.launch(
                arrayOf(
                    Manifest.permission.ACCESS_FINE_LOCATION,
                    Manifest.permission.ACCESS_COARSE_LOCATION
                )
            )
        }
        if (locationGranted) {
            try {
                currentLocation =
                    locationManager.getLastKnownLocation(
                        android.location.LocationManager.GPS_PROVIDER
                    )
                        ?: locationManager.getLastKnownLocation(
                            android.location.LocationManager.NETWORK_PROVIDER
                        )
            } catch (e: SecurityException) {
                currentLocation = null
            }
        }
    }
    fun calculateRoute(
        start: GeoPoint,
        end: GeoPoint
    ) {
        scope.launch {
            // Étape transitoire : le serveur public OSRM ne propose qu'un profil
            // routier générique. Le véhicule est néanmoins transmis à cette
            // fonction pour préparer le futur moteur spécialisé VSP / 50 cm³.
            val routeProfile = when (vehicle) {
                VehicleType.VSP -> "driving"
                VehicleType.SCOOTER_50 -> "driving"
            }

            val url =
                "https://router.project-osrm.org/route/v1/$routeProfile/" +
                        "${start.longitude},${start.latitude};" +
                        "${end.longitude},${end.latitude}" +
                        "?overview=full&geometries=geojson&alternatives=true"
            val request = Request.Builder()
                .url(url)
                .build()

            val client = OkHttpClient()
            val response = withContext(Dispatchers.IO) {
                client.newCall(request).execute()
            }

            val body = response.body?.string()

            if (body != null) {
                val json = JSONObject(body)
                val routes = json.getJSONArray("routes")
                val parsedRoutes = mutableListOf<RouteOption>()

                for (routeIndex in 0 until routes.length()) {
                    val route = routes.getJSONObject(routeIndex)
                    val geometry = route.getJSONObject("geometry")
                    val coordinates = geometry.getJSONArray("coordinates")
                    val points = mutableListOf<GeoPoint>()

                    for (i in 0 until coordinates.length()) {
                        val coordinate = coordinates.getJSONArray(i)
                        points.add(
                            GeoPoint(
                                coordinate.getDouble(1),
                                coordinate.getDouble(0)
                            )
                        )
                    }

                    parsedRoutes.add(
                        RouteOption(
                            points = points,
                            distanceMeters = route.optDouble("distance", 0.0),
                            durationSeconds = route.optDouble("duration", 0.0)
                        )
                    )
                }

                routeOptions = parsedRoutes
                selectedRouteIndex = 0
            }
        }
    }
    fun searchAddress() {

        if (query.isBlank() || searching) {
            return
        }

        searching = true
        error = null

        scope.launch {

            val result =
                withContext(Dispatchers.IO) {

                    try {

                        @Suppress("DEPRECATION")

                        val found =
                            Geocoder(
                                context,
                                Locale.FRANCE
                            ).getFromLocationName(
                                query,
                                1
                            )

                        found
                            ?.firstOrNull()
                            ?.let {

                                Destination(
                                    label =
                                        listOfNotNull(
                                            it.featureName,
                                            it.locality,
                                            it.postalCode
                                        )
                                            .distinct()
                                            .joinToString(", ")
                                            .ifBlank {
                                                query
                                            },

                                    point =
                                        GeoPoint(
                                            it.latitude,
                                            it.longitude
                                        )
                                )
                            }

                    } catch (_: Exception) {
                        null
                    }
                }

            destination = result
            currentLocation?.let { location ->
                result?.let { dest ->
                    calculateRoute(
                        GeoPoint(location.latitude, location.longitude),
                        dest.point
                    )
                }
            }

            if (result == null) {
                error =
                    "Adresse introuvable. Essayez avec la ville et le code postal."
            }

            searching = false
        }
    }

    if (navigationStarted && destination != null && routePoints.isNotEmpty()) {
        NavigationScreen(vehicle, destination!!, currentLocation, routeOptions[selectedRouteIndex]) { navigationStarted = false }
        return
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF07182E))
            .padding(12.dp)
    ) {

        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {

            TextButton(
                onClick = onBack
            ) {
                Text("‹ Accueil")
            }

            Spacer(
                Modifier.weight(1f)
            )

            Text(
                text =
                    if (vehicle == VehicleType.VSP)
                        "🚗 VSP"
                    else
                        "🛵 50 cm³",

                color = Color.White,
                fontWeight = FontWeight.Bold
            )
        }

        OutlinedTextField(
            value = query,

            onValueChange = {
                query = it
            },

            modifier =
                Modifier.fillMaxWidth(),

            singleLine = true,

            label = {
                Text("Où allez-vous ?")
            },

            placeholder = {
                Text("Adresse, ville ou lieu")
            },

            leadingIcon = {
                Text("🔎")
            },

            trailingIcon = {

                if (searching) {

                    CircularProgressIndicator(
                        modifier =
                            Modifier.size(22.dp),

                        strokeWidth = 2.dp
                    )
                }
            },

            keyboardOptions =
                KeyboardOptions(
                    imeAction =
                        ImeAction.Search
                ),

            keyboardActions =
                KeyboardActions(
                    onSearch = {
                        searchAddress()
                    }
                )
        )

        Spacer(
            Modifier.height(8.dp)
        )

        Button(
            onClick = {
                searchAddress()
            },

            enabled =
                query.isNotBlank() &&
                !searching,

            modifier =
                Modifier.fillMaxWidth()
        ) {

            Text(
                "Rechercher l'adresse"
            )
        }

        error?.let {

            Text(
                text = it,
                color = Color(0xFFFFC857),
                modifier =
                    Modifier.padding(
                        vertical = 6.dp
                    )
            )
        }

        destination?.let {

            Text(
                text =
                    "Destination : ${it.label}",

                color =
                    Color(0xFF65D68A),

                modifier =
                    Modifier.padding(
                        vertical = 6.dp
                    )
            )
        }

        if (routeOptions.size > 1) {
            Text(
                text = "Itinéraires proposés",
                color = Color.White,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(top = 4.dp, bottom = 4.dp)
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                routeOptions.take(3).forEachIndexed { index, option ->
                    val km = option.distanceMeters / 1000.0
                    val minutes = (option.durationSeconds / 60.0).toInt()

                    if (index == selectedRouteIndex) {
                        Button(
                            onClick = { selectedRouteIndex = index },
                            modifier = Modifier.weight(1f)
                        ) {
                            Text(String.format(Locale.FRANCE, "%.1f km\n%d min", km, minutes))
                        }
                    } else {
                        OutlinedButton(
                            onClick = { selectedRouteIndex = index },
                            modifier = Modifier.weight(1f)
                        ) {
                            Text(String.format(Locale.FRANCE, "%.1f km\n%d min", km, minutes))
                        }
                    }
                }
            }

            Spacer(Modifier.height(8.dp))
        }

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
        ) {

            AndroidView(
                modifier =
                    Modifier.fillMaxSize(),

                factory = { ctx ->

                    MapView(ctx).apply {

                        setMultiTouchControls(true)

                        controller.setZoom(
                            13.0
                        )

                        controller.setCenter(
                            GeoPoint(
                                50.425,
                                2.710
                            )
                        )
                    }
                },

                update = { map ->

                    destination?.let { d ->

                        map.overlays.removeAll {
                            it is Marker || it is Polyline
                        }

                        currentLocation?.let { location ->
                            val startMarker = Marker(map).apply {
                                position = GeoPoint(location.latitude, location.longitude)
                                title = "Ma position"
                                icon = ContextCompat.getDrawable(map.context, android.R.drawable.presence_online)
                                setAnchor(
                                    Marker.ANCHOR_CENTER,
                                    Marker.ANCHOR_CENTER
                                )
                            }
                            map.overlays.add(startMarker)
                        }

                        val marker =
                            Marker(map).apply {

                                position =
                                    d.point

                                title =
                                    d.label

                                setAnchor(
                                    Marker.ANCHOR_CENTER,
                                    Marker.ANCHOR_BOTTOM
                                )
                            }

                        if (routePoints.isNotEmpty()) {
                            val routeLine = Polyline().apply {
                                setPoints(routePoints)
                                outlinePaint.strokeWidth = 10f
                                outlinePaint.color = android.graphics.Color.BLUE
                            }

                            map.overlays.add(routeLine)
                            map.invalidate()
                        }
                        map.overlays.add(
                            marker
                        )

                        if (routePoints.isNotEmpty()) {
                            val bounds = org.osmdroid.util.BoundingBox.fromGeoPoints(routePoints)
                            map.zoomToBoundingBox(bounds, true, 80)
                        } else {
                            map.controller.animateTo(d.point)
                            map.controller.setZoom(16.0)
                        }

                        map.invalidate()
                    }
                }
            )
        }

        Spacer(
            Modifier.height(8.dp)
        )

        if (routeOptions.isNotEmpty()) {
            Button(
                onClick = { navigationStarted = true },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(18.dp)
            ) {
                Text(
                    text = if (navigationStarted) "Navigation prête ✓" else "▶  Démarrer",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(Modifier.height(8.dp))
        }

        Text(
            text =
                if (locationGranted)
                    "GPS autorisé ✓"
                else
                    "Autorisation GPS nécessaire",

            color =
                if (locationGranted)
                    Color(0xFF65D68A)
                else
                    Color(0xFFFFC857)
        )

        Text(
            text =
                if (vehicle == VehicleType.VSP)
                    "Mode VSP : itinéraire de démonstration. Le filtrage des routes interdites sera activé avec le moteur VSP dédié."
                else
                    "Mode 50 cm³ : itinéraire de démonstration. Le filtrage des routes interdites sera activé avec le moteur 50 cm³ dédié.",

            color =
                Color(0xFF9CB0C4),

            fontSize =
                12.sp
        )
    }
}


@Composable
fun NavigationScreen(
    vehicle: VehicleType,
    destination: Destination,
    currentLocation: Location?,
    route: RouteOption,
    onBack: () -> Unit
) {
    val distanceKm = route.distanceMeters / 1000.0
    val minutes = (route.durationSeconds / 60.0).toInt()
    Column(Modifier.fillMaxSize().background(Color(0xFF07182E)).padding(12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            TextButton(onClick = onBack) { Text("‹ Itinéraire") }
            Spacer(Modifier.weight(1f))
            Text(if (vehicle == VehicleType.VSP) "🚗 VSP" else "🛵 50 cm³", color = Color.White, fontWeight = FontWeight.Bold)
        }
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF102A46))
        ) {
            Column(Modifier.padding(16.dp)) {
                Text("Navigation en cours", color = Color(0xFF65D68A), fontWeight = FontWeight.Bold)
                Text(destination.label, color = Color.White, fontSize = 22.sp, fontWeight = FontWeight.Bold)
                Text(String.format(Locale.FRANCE, "%.1f km  •  %d min", distanceKm, minutes), color = Color(0xFFB9D9FF))
            }
        }
        Spacer(Modifier.height(10.dp))
        Card(Modifier.fillMaxWidth().weight(1f), shape = RoundedCornerShape(22.dp)) {
            AndroidView(
                modifier = Modifier.fillMaxSize(),
                factory = { ctx -> MapView(ctx).apply { setMultiTouchControls(true); controller.setZoom(17.0) } },
                update = { map ->
                    map.overlays.removeAll { it is Marker || it is Polyline }
                    map.overlays.add(Polyline().apply {
                        setPoints(route.points)
                        outlinePaint.strokeWidth = 12f
                        outlinePaint.color = android.graphics.Color.BLUE
                    })
                    val position = currentLocation?.let { GeoPoint(it.latitude, it.longitude) } ?: route.points.firstOrNull()
                    position?.let { point ->
                        map.overlays.add(Marker(map).apply {
                            this.position = point
                            title = "Ma position"
                            icon = ContextCompat.getDrawable(map.context, android.R.drawable.presence_online)
                            setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_CENTER)
                        })
                        map.controller.setCenter(point)
                        map.controller.setZoom(17.0)
                    }
                    map.overlays.add(Marker(map).apply {
                        this.position = destination.point
                        title = destination.label
                        setAnchor(Marker.ANCHOR_CENTER, Marker.ANCHOR_BOTTOM)
                    })
                    map.invalidate()
                }
            )
        }
        Spacer(Modifier.height(10.dp))
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(18.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF102A46))
        ) {
            Text("Suivez le tracé bleu vers " + destination.label, Modifier.padding(16.dp), color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.Bold)
        }
    }
}
