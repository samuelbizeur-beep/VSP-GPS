from pathlib import Path

# V138 test build: keep the displayed version synchronized with Android package metadata.
# Give Android a genuinely newer package version so manual installation cannot be
# confused with the previous test APKs.
build_path = Path("app/build.gradle.kts")
build = build_path.read_text(encoding="utf-8")
build = build.replace('versionCode = 1', 'versionCode = 138', 1)
build = build.replace('versionName = "200.0-alpha"', 'versionName = "V138"', 1)
build_path.write_text(build, encoding="utf-8")

path = Path("app/src/main/java/fr/vspgps/app/MainActivity.kt")
text = path.read_text(encoding="utf-8")

# Visible version on the welcome screen.
welcome_anchor = '''            Text(
                text = "VSP GPS",
                color = Color.White,
                fontSize = 42.sp,
                fontWeight = FontWeight.Bold
            )

            Text(
                text = "Le GPS pensé pour votre mobilité",
'''
welcome_replacement = '''            Text(
                text = "VSP GPS",
                color = Color.White,
                fontSize = 42.sp,
                fontWeight = FontWeight.Bold
            )

            Text(
                text = "Version ${BuildConfig.VERSION_NAME}",
                color = Color(0xFF4DA3FF),
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold
            )

            Text(
                text = "Le GPS pensé pour votre mobilité",
'''
if welcome_anchor not in text:
    raise SystemExit("V138 patch: welcome version anchor not found")
text = text.replace(welcome_anchor, welcome_replacement, 1)

# Also keep the version visible on the search screen, so the user can verify the
# installed APK directly while testing POI searches.
search_anchor = '''            TextButton(
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
'''
search_replacement = '''            TextButton(
                onClick = onBack
            ) {
                Text("‹ Accueil")
            }

            Text(
                text = BuildConfig.VERSION_NAME,
                color = Color(0xFF4DA3FF),
                fontWeight = FontWeight.Bold,
                fontSize = 14.sp
            )

            Spacer(
                Modifier.weight(1f)
            )

            Text(
                text =
                    if (vehicle == VehicleType.VSP)
'''
if search_anchor not in text:
    raise SystemExit("V138 patch: search version anchor not found")
text = text.replace(search_anchor, search_replacement, 1)

path.write_text(text, encoding="utf-8")
print("V138 version display patch applied successfully")
