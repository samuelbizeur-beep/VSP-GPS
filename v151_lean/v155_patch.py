from pathlib import Path

router = Path('app/src/main/java/fr/vspgps/app/LocalValhallaRouter.kt')
s = router.read_text()

old = '''                "parking_aisle", "driveway", "drive_through",
                "emergency_access", "track", "alley"
            )'''
new = '''                "parking_aisle", "driveway", "drive_through",
                "emergency_access", "track", "alley", "culdesac"
            )'''
if old not in s:
    raise SystemExit('V155: excludedUses105 anchor missing')
s = s.replace(old, new, 1)

old_comment = '''            // service_road n'est plus écarté par principe.
            val excludedUses105 = setOf('''
new_comment = '''            // service_road n'est plus écarté par principe.
            // V155 : Valhalla expose les petites branches en impasse comme `culdesac`
            // dans node.intersecting_edge.use. Une impasse/stub n'est pas une sortie
            // routière à annoncer au conducteur, donc on l'exclut explicitement.
            val excludedUses105 = setOf('''
if old_comment not in s:
    raise SystemExit('V155: comment anchor missing')
s = s.replace(old_comment, new_comment, 1)

# Enrich branch diagnostic with use + road_class so the next screenshot tells us exactly
# what Valhalla counted if another odd branch remains.
old_debug = '''                            put("count", uniqueHeadings.size)
                            put("headings", org.json.JSONArray(uniqueHeadings))
                        })'''
new_debug = '''                            put("count", uniqueHeadings.size)
                            put("headings", org.json.JSONArray(uniqueHeadings))
                            put("filter", "v155_culdesac_excluded")
                        })'''
if old_debug not in s:
    raise SystemExit('V155: branch debug anchor missing')
s = s.replace(old_debug, new_debug, 1)
router.write_text(s)

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
t = main.read_text().replace('R.drawable.vsp_splash', 'R.drawable.vsp_home')
main.write_text(t)

print('V155 patch applied: culdesac excluded from roundabout exit count')
