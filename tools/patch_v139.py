from pathlib import Path

# Make V139 install as a separate app so it cannot conflict with the existing VSP GPS signature.
build_path = Path("app/build.gradle.kts")
build = build_path.read_text(encoding="utf-8")
build = build.replace('applicationId = "fr.vspgps.app"', 'applicationId = "fr.vspgps.app.v139test"', 1)
build = build.replace('versionCode = 138', 'versionCode = 139', 1)
build = build.replace('versionName = "V138"', 'versionName = "V139"', 1)
build_path.write_text(build, encoding="utf-8")

manifest_path = Path("app/src/main/AndroidManifest.xml")
manifest = manifest_path.read_text(encoding="utf-8")
manifest = manifest.replace('android:label="VSP GPS"', 'android:label="VSP GPS V139"', 1)
manifest_path.write_text(manifest, encoding="utf-8")

print("V139 separate-package patch applied successfully")
