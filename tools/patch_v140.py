from pathlib import Path

path = Path("app/build.gradle.kts")
text = path.read_text(encoding="utf-8")

text = text.replace('versionCode = 138', 'versionCode = 140', 1)
text = text.replace('versionName = "V138"', 'versionName = "V140"', 1)

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
    raise SystemExit("V140 patch: buildFeatures anchor not found")

text = text.replace(anchor, signing, 1)
path.write_text(text, encoding="utf-8")
print("V140 permanent signing patch applied successfully")
