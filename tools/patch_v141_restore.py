from pathlib import Path

# 1) Version + signature permanente
gradle = Path('app/build.gradle.kts')
text = gradle.read_text(encoding='utf-8')
text = text.replace('versionCode = 1', 'versionCode = 141', 1)
text = text.replace('versionName = "200.0-alpha"', 'versionName = "V141"', 1)
anchor = '''    buildFeatures {
        compose = true
        buildConfig = true
    }
'''
signing = '''    signingConfigs {
        create("vspUpdate") {
            val keyStorePath = System.getenv("VSP_KEYSTORE_PATH")
                ?: error("VSP_KEYSTORE_PATH missing")
            val signingPassword = System.getenv("VSP_KEYSTORE_PASSWORD")
                ?: error("VSP_KEYSTORE_PASSWORD missing")
            storeFile = file(keyStorePath)
            storePassword = signingPassword
            keyAlias = "vspgps"
            keyPassword = signingPassword
        }
    }

    buildTypes {
        getByName("debug") {
            signingConfig = signingConfigs.getByName("vspUpdate")
        }
    }

''' + anchor
if anchor not in text:
    raise SystemExit('buildFeatures anchor not found')
text = text.replace(anchor, signing, 1)
gradle.write_text(text, encoding='utf-8')

# 2) Démarrage propre si le gros pack Valhalla n'est pas encore embarqué
router = Path('app/src/main/java/fr/vspgps/app/LocalValhallaRouter.kt')
r = router.read_text(encoding='utf-8')
old = '''        appContext.assets.open(TILE_ARCHIVE_NAME).use { input ->

            FileOutputStream(bundledTileArchive).use { output ->
'''
new = '''        val bundledAssets = appContext.assets.list("")?.toSet().orEmpty()
        if (TILE_ARCHIVE_NAME !in bundledAssets) {
            return
        }

        appContext.assets.open(TILE_ARCHIVE_NAME).use { input ->

            FileOutputStream(bundledTileArchive).use { output ->
'''
if old not in r:
    raise SystemExit('asset-open anchor not found')
r = r.replace(old, new, 1)
old2 = '''            val archive = selectedTileArchive()
            val config =
'''
new2 = '''            val archive = selectedTileArchive()
            if (!archive.isFile || archive.length() <= 0L) {
                return InitializationResult.Failed(
                    message = "Pack Valhalla absent : importez un pack régional ou France",
                    cause = null
                )
            }
            val config =
'''
if old2 not in r:
    raise SystemExit('archive anchor not found')
r = r.replace(old2, new2, 1)
router.write_text(r, encoding='utf-8')

# 3) Version V141 visible en permanence hors splash
main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
m = main.read_text(encoding='utf-8')
old3 = '''    when (screen) {
        "splash" -> WelcomeScreen(onFinished = { screen = "energy" })
        "energy" -> EnergyChoiceScreen { choice ->
            energyType = choice
            screen = "gps"
        }
        else -> MapSearchScreen(
            vehicle = vehicle,
            energyType = energyType ?: EnergyType.ELECTRIC,
            onBack = {
                clearStoredActiveTrip(appContext)
                screen = "energy"
            }
        )
    }
'''
new3 = '''    Box(Modifier.fillMaxSize()) {
        when (screen) {
            "splash" -> WelcomeScreen(onFinished = { screen = "energy" })
            "energy" -> EnergyChoiceScreen { choice ->
                energyType = choice
                screen = "gps"
            }
            else -> MapSearchScreen(
                vehicle = vehicle,
                energyType = energyType ?: EnergyType.ELECTRIC,
                onBack = {
                    clearStoredActiveTrip(appContext)
                    screen = "energy"
                }
            )
        }
        if (screen != "splash") {
            Text(
                text = "V141",
                color = Color(0xFF58A6FF),
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.align(Alignment.TopEnd).padding(top = 10.dp, end = 14.dp)
            )
        }
    }
'''
if old3 not in m:
    raise SystemExit('VspGpsApp screen anchor not found')
m = m.replace(old3, new3, 1)
main.write_text(m, encoding='utf-8')

print('V141 restore patch applied successfully')
