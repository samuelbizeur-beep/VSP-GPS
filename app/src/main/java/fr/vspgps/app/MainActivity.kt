package fr.vspgps.app

import android.Manifest
import android.content.pm.PackageManager
import android.location.Location
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import org.osmdroid.config.Configuration
import org.osmdroid.util.GeoPoint
import org.osmdroid.views.MapView
import org.osmdroid.views.overlay.Marker

enum class VehicleType {
    VSP,
    SCOOTER_50
}

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
                VspGpsScreen()
            }
        }
    }
}

@Composable
fun VspGpsScreen() {

    var vehicle by remember { mutableStateOf(VehicleType.VSP) }
    var locationGranted by remember { mutableStateOf(false) }

    val context = androidx.compose.ui.platform.LocalContext.current

    val permissionLauncher =
        rememberLauncherForActivityResult(
            ActivityResultContracts.RequestMultiplePermissions()
        ) { permissions ->
            locationGranted =
                permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
                permissions[Manifest.permission.ACCESS_COARSE_LOCATION] == true
        }

    LaunchedEffect(Unit) {
        locationGranted =
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.ACCESS_FINE_LOCATION
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

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(12.dp)
    ) {

        Text(
            text = "VSP GPS",
            style = MaterialTheme.typography.headlineMedium,
            color = Color.White
        )

        Text(
            text = "Navigation spécialisée VSP & 50 cm³",
            color = Color.LightGray
        )

        Spacer(modifier = Modifier.height(12.dp))

        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {

            Button(
                onClick = { vehicle = VehicleType.VSP },
                colors = ButtonDefaults.buttonColors(
                    containerColor =
                        if (vehicle == VehicleType.VSP)
                            Color(0xFF1976D2)
                        else
                            Color.DarkGray
                )
            ) {
                Text("🚗 VSP")
            }

            Button(
                onClick = { vehicle = VehicleType.SCOOTER_50 },
                colors = ButtonDefaults.buttonColors(
                    containerColor =
                        if (vehicle == VehicleType.SCOOTER_50)
                            Color(0xFF1976D2)
                        else
                            Color.DarkGray
                )
            ) {
                Text("🛵 50 cm³")
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
        ) {

            AndroidView(
                modifier = Modifier.fillMaxSize(),

                factory = { ctx ->

                    MapView(ctx).apply {

                        setMultiTouchControls(true)

                        controller.setZoom(14.0)

                        controller.setCenter(
                            GeoPoint(
                                50.425,
                                2.710
                            )
                        )
                    }
                }
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

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
                when (vehicle) {
                    VehicleType.VSP ->
                        "Profil actif : voiture sans permis"

                    VehicleType.SCOOTER_50 ->
                        "Profil actif : cyclomoteur / scooter 50 cm³"
                },
            color = Color.White
        )

        Spacer(modifier = Modifier.height(6.dp))

        Text(
            text = "Version 200.0-alpha • Prototype de test",
            color = Color.Gray
        )
    }
}
