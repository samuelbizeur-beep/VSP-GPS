from pathlib import Path

# V142 = vraie base avancée + signature permanente + version visible.

# 1) Version Android + signature permanente
gradle = Path('app/build.gradle.kts')
text = gradle.read_text(encoding='utf-8')
text = text.replace('versionCode = 1', 'versionCode = 142', 1)
text = text.replace('versionName = "200.0-alpha"', 'versionName = "V142"', 1)
anchor = '''    buildFeatures {\n        compose = true\n        buildConfig = true\n    }\n'''
signing = '''    signingConfigs {\n        create("vspUpdate") {\n            val keyStorePath = System.getenv("VSP_KEYSTORE_PATH")\n                ?: error("VSP_KEYSTORE_PATH missing")\n            val signingPassword = System.getenv("VSP_KEYSTORE_PASSWORD")\n                ?: error("VSP_KEYSTORE_PASSWORD missing")\n            storeFile = file(keyStorePath)\n            storePassword = signingPassword\n            keyAlias = "vspgps"\n            keyPassword = signingPassword\n        }\n    }\n\n    buildTypes {\n        getByName("debug") {\n            signingConfig = signingConfigs.getByName("vspUpdate")\n        }\n    }\n\n''' + anchor
if anchor not in text:
    raise SystemExit('buildFeatures anchor not found')
text = text.replace(anchor, signing, 1)
gradle.write_text(text, encoding='utf-8')

# 2) Ne pas planter si le gros pack Valhalla n'est pas encore embarqué
router = Path('app/src/main/java/fr/vspgps/app/LocalValhallaRouter.kt')
r = router.read_text(encoding='utf-8')
old = '''        appContext.assets.open(TILE_ARCHIVE_NAME).use { input ->\n\n            FileOutputStream(bundledTileArchive).use { output ->\n'''
new = '''        val bundledAssets = appContext.assets.list("")?.toSet().orEmpty()\n        if (TILE_ARCHIVE_NAME !in bundledAssets) {\n            return\n        }\n\n        appContext.assets.open(TILE_ARCHIVE_NAME).use { input ->\n\n            FileOutputStream(bundledTileArchive).use { output ->\n'''
if old not in r:
    raise SystemExit('asset-open anchor not found')
r = r.replace(old, new, 1)
old2 = '''            val archive = selectedTileArchive()\n            val config =\n'''
new2 = '''            val archive = selectedTileArchive()\n            if (!archive.isFile || archive.length() <= 0L) {\n                return InitializationResult.Failed(\n                    message = "Pack Valhalla absent : importez un pack régional ou France",\n                    cause = null\n                )\n            }\n            val config =\n'''
if old2 not in r:
    raise SystemExit('archive anchor not found')
r = r.replace(old2, new2, 1)
router.write_text(r, encoding='utf-8')

# 3) Afficher la version DIRECTEMENT dans les écrans visibles
main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
m = main.read_text(encoding='utf-8')

# Écran énergie paysage
old_land = '''            Text("Quelle énergie utilise votre voiture ?", color = Color(0xFFAAB8C8), fontSize = 15.sp)\n            Spacer(Modifier.height(14.dp))'''
new_land = '''            Text("Quelle énergie utilise votre voiture ?", color = Color(0xFFAAB8C8), fontSize = 15.sp)\n            Text("Version V142", color = Color(0xFF58A6FF), fontSize = 13.sp, fontWeight = FontWeight.Bold)\n            Spacer(Modifier.height(14.dp))'''
if old_land not in m:
    raise SystemExit('energy landscape anchor not found')
m = m.replace(old_land, new_land, 1)

# Écran énergie portrait
old_portrait = '''            Text("Quelle énergie utilise votre voiture ?", color = Color(0xFFAAB8C8), fontSize = 17.sp)\n            Spacer(Modifier.height(38.dp))'''
new_portrait = '''            Text("Quelle énergie utilise votre voiture ?", color = Color(0xFFAAB8C8), fontSize = 17.sp)\n            Spacer(Modifier.height(6.dp))\n            Text("Version V142", color = Color(0xFF58A6FF), fontSize = 15.sp, fontWeight = FontWeight.Bold)\n            Spacer(Modifier.height(28.dp))'''
if old_portrait not in m:
    raise SystemExit('energy portrait anchor not found')
m = m.replace(old_portrait, new_portrait, 1)

# Écran principal : version à droite de l'icône Maison
old_header = '''            }\n        }\n\n        OutlinedTextField(\n            value = query,'''
new_header = '''            }\n            Spacer(Modifier.weight(1f))\n            Text(\n                text = "V142",\n                color = Color(0xFF58A6FF),\n                fontSize = 15.sp,\n                fontWeight = FontWeight.Bold\n            )\n        }\n\n        OutlinedTextField(\n            value = query,'''
if old_header not in m:
    raise SystemExit('map header anchor not found')
m = m.replace(old_header, new_header, 1)

main.write_text(m, encoding='utf-8')
print('V142 restore/version patch applied successfully')
