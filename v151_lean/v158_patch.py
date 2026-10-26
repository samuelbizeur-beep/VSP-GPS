from pathlib import Path

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
s = main.read_text()

# V158: allow the V156 visual map-matching code to run during simulation too.
# Safety/off-route logic still uses the raw simulated Location, so this only affects the icon display.
old = '        if (simulationActive || route.points.size < 2) return raw\n'
new = '        if (route.points.size < 2) return raw\n'
if old not in s:
    raise SystemExit('V158: visualMatchedPoint simulation guard not found')
s = s.replace(old, new, 1)

# Calibrate the indoor test levels to the actual thresholds in the navigation code.
# 8 m should visually snap, 20 m should remain visibly offset without forcing reroute,
# 100 m should exceed the normal off-route threshold and trigger rerouting after confirmation.
old = '                    listOf(0, 8, 20, 40).forEach { driftMeters157 ->\n'
new = '                    listOf(0, 8, 20, 100).forEach { driftMeters157 ->\n'
if old not in s:
    raise SystemExit('V158: drift buttons anchor not found')
s = s.replace(old, new, 1)

old = '''                    when {
                        simulationDriftMeters157 <= 0.0 -> "Test précision : GPS simulé exactement sur le tracé"
                        simulationDriftMeters157 <= 8.0 -> "Test précision : petite dérive • la flèche doit rester stable sur la route"
                        simulationDriftMeters157 <= 20.0 -> "Test précision : dérive moyenne • vérifier le recalage sans saut"
                        else -> "Test précision : forte dérive • le hors-itinéraire doit finir par être détecté"
                    },'''
new = '''                    when {
                        simulationDriftMeters157 <= 0.0 -> "Test précision : GPS simulé exactement sur le tracé"
                        simulationDriftMeters157 <= 8.0 -> "Test précision : 8 m • l'icône doit être recalée sur la route"
                        simulationDriftMeters157 <= 20.0 -> "Test précision : 20 m • l'écart doit rester visible, sans faux recalcul"
                        else -> "Test précision : 100 m • hors-itinéraire puis recalcul automatique attendu"
                    },'''
if old not in s:
    raise SystemExit('V158: drift help text anchor not found')
s = s.replace(old, new, 1)

# Avoid warning color at 20 m; only the 100 m forced off-route test is highlighted.
s = s.replace('color = if (simulationDriftMeters157 >= 40.0) Color(0xFFFFC857) else Color(0xFF8FD7A8),',
              'color = if (simulationDriftMeters157 >= 100.0) Color(0xFFFFC857) else Color(0xFF8FD7A8),', 1)

main.write_text(s)
print('V158 patch applied: calibrated indoor visual snap/off-route test 0/8/20/100 m')
