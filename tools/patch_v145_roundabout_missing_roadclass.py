from pathlib import Path

# V145 — Certaines branches carrossables de parking/aire n'exposent pas road_class
# dans trace_attributes. V144 les autorisait par use, mais elles restaient rejetées
# par le filtre roadClass.isBlank(). Si driveability est forward/both, on les compte
# donc comme sorties physiques sauf si leur use est explicitement non routier/privé.

router = Path('app/src/main/java/fr/vspgps/app/LocalValhallaRouter.kt')
r = router.read_text(encoding='utf-8')
old = '                        if (use in excludedUses105 || roadClass.isBlank()) continue\n'
new = '''                        // V145 : une sortie carrossable peut ne pas exposer de road_class
                        // (cas fréquent des accès d'aires/parkings). driveability est ici
                        // la source de vérité pour savoir si la branche peut être empruntée.
                        if (use in excludedUses105) continue
'''
if old not in r:
    raise SystemExit('V145 roadClass filter anchor not found')
r = r.replace(old, new, 1)
router.write_text(r, encoding='utf-8')

gradle = Path('app/build.gradle.kts')
g = gradle.read_text(encoding='utf-8')
g = g.replace('versionCode = 144', 'versionCode = 145', 1)
g = g.replace('versionName = "V144"', 'versionName = "V145"', 1)
gradle.write_text(g, encoding='utf-8')

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
m = main.read_text(encoding='utf-8')
if 'V144' not in m:
    raise SystemExit('V144 visible badge not found')
m = m.replace('V144', 'V145')
main.write_text(m, encoding='utf-8')

print('V145 roundabout missing-roadclass patch applied')
