package fr.vspgps.app

import android.Manifest
import android.content.pm.PackageManager
import android.location.Geocoder
import android.os.Bundle
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
import java.util.Locale

enum class VehicleType {
    VSP,
    SCOOTER_50
}

data class Destination(
    val label: String,
    val point: GeoPoint
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

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF07182E))
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {

        Spacer(Modifier.height(34.dp))

        Text(
            text = "VSP GPS",
            color = Color.White,
            fontSize = 38.sp,
            fontWeight = FontWeight.Bold
        )

        Text(
            text = "Le GPS pensé pour votre mobilité",
            color = Color(0xFF9CCBFF),
            fontSize = 17.sp
        )

        Spacer(Modifier.height(36.dp))

        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(28.dp),
            colors = CardDefaults.cardColors(
                containerColor = Color(0xFF102A46)
            )
        ) {

            Column(
                modifier = Modifier.padding(28.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {

                Text(
                    text = "🚗     🛵",
                    fontSize = 64.sp
                )

                Spacer(Modifier.height(14.dp))

                Text(
                    text = "Des itinéraires adaptés",
                    color = Color.White,
                    fontSize = 22.sp,
                    fontWeight = FontWeight.Bold
                )

                Text(
                    text = "Voiture sans permis • Cyclomoteur 50 cm³",
                    color = Color(0xFFC4D9ED),
                    fontSize = 15.sp
                )

                Spacer(Modifier.height(18.dp))

                Text(
                    text = "⌁  Votre route, sans les voies incompatibles",
                    color = Color(0xFF75B8FF)
                )
            }
        }

        Spacer(Modifier.height(28.dp))

        Text(
            text = "Choisissez votre véhicule",
            color = Color.White,
            fontWeight = FontWeight.SemiBold
        )

        Spacer(Modifier.height(12.dp))

        Row(
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {

            FilterChip(
                selected = vehicle == VehicleType.VSP,
                onClick = {
                    onVehicle(VehicleType.VSP)
                },
                label = {
                    Text("🚗  VSP")
                }
            )

            FilterChip(
                selected = vehicle == VehicleType.SCOOTER_50,
                onClick = {
                    onVehicle(VehicleType.SCOOTER_50)
                },
                label = {
                    Text("🛵  50 cm³")
                }
            )
        }

        Spacer(Modifier.weight(1f))

        Button(
            onClick = onStart,
            modifier = Modifier
                .fillMaxWidth()
                .height(58.dp),
            shape = RoundedCornerShape(18.dp)
        ) {
            Text(
                text = "Où allez-vous ?  →",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )
        }

        Spacer(Modifier.height(12.dp))

        Text(
            text = "V200-alpha.2 • Prototype de test",
            color = Color(0xFF71869C),
            fontSize = 12.sp
        )
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

    val permissionLauncher =
        rememberLauncherForActivityResult(
            ActivityResultContracts.RequestMultiplePermissions()
        ) { permissions ->

            locationGranted =
                permissions[
                    Manifest.permission.ACCESS_FINE_LOCATION
                ] == true ||
                permissions[
                    Manifest.permission.ACCESS_COARSE_LOCATION
                ] == true
        }

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

            if (result == null) {
                error =
                    "Adresse introuvable. Essayez avec la ville et le code postal."
            }

            searching = false
        }
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
                            it is Marker
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

                        map.overlays.add(
                            marker
                        )

                        map.controller.animateTo(
                            d.point
                        )

                        map.controller.setZoom(
                            16.0
                        )

                        map.invalidate()
                    }
                }
            )
        }

        Spacer(
            Modifier.height(8.dp)
        )

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
                "Le calcul d’itinéraire spécialisé VSP/50 cm³ sera ajouté à l’étape suivante.",

            color =
                Color(0xFF9CB0C4),

            fontSize =
                12.sp
        )
    }
}
