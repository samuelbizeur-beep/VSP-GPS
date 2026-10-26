from pathlib import Path

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
s = main.read_text()

# 1) Compact the two large test buttons into one row in portrait.
old = '''            OutlinedButton(
                onClick = {
                    simulationActive = !simulationActive
                    if (!simulationActive) {
                        simulationMeters = 0.0
                        simulationRewinding = false
                        simulationPaused = false
                        simulationDriftMeters157 = 0.0
                        activeRealGpsTestStopMeters93 = null
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)
            ) {
                Text(if (simulationActive) "■ Arrêter le test" else "▶ Mode test", fontSize = 12.sp)
            }
            OutlinedButton(
                onClick = { showRealGpsTests89 = true },
                modifier = Modifier.fillMaxWidth().padding(top = 4.dp),
                contentPadding = PaddingValues(horizontal = 10.dp, vertical = 4.dp)
            ) {
                Text("🧪 Tests GPS réels (${realGpsTests89.size})", fontSize = 12.sp)
            }'''
new = '''            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                OutlinedButton(
                    onClick = {
                        simulationActive = !simulationActive
                        if (!simulationActive) {
                            simulationMeters = 0.0
                            simulationRewinding = false
                            simulationPaused = false
                            simulationDriftMeters157 = 0.0
                            activeRealGpsTestStopMeters93 = null
                        }
                    },
                    modifier = Modifier.weight(1f),
                    contentPadding = PaddingValues(horizontal = 6.dp, vertical = 3.dp)
                ) {
                    Text(if (simulationActive) "■ Arrêter" else "▶ Test", fontSize = 11.sp)
                }
                OutlinedButton(
                    onClick = { showRealGpsTests89 = true },
                    modifier = Modifier.weight(1f),
                    contentPadding = PaddingValues(horizontal = 6.dp, vertical = 3.dp)
                ) {
                    Text("🧪 GPS réels (${realGpsTests89.size})", fontSize = 11.sp)
                }
            }'''
if old not in s:
    raise SystemExit('V160: top test buttons anchor missing')
s = s.replace(old, new, 1)

# 2) Shorter test banner, avoids wrapping over two lines.
s = s.replace('"MODE TEST — PAUSE • position conservée"', '"TEST • pause • dérive ${simulationDriftMeters157.toInt()} m"', 1)
s = s.replace('"MODE TEST — marche arrière ×2"', '"TEST • arrière ×2 • dérive ${simulationDriftMeters157.toInt()} m"', 1)
s = s.replace('"MODE TEST — position GPS simulée • ×16 intelligent • dérive ${simulationDriftMeters157.toInt()} m"', '"TEST • ×16 intelligent • dérive ${simulationDriftMeters157.toInt()} m"', 1)
s = s.replace('"MODE TEST — position GPS simulée • accélération ×$simulationMultiplier • dérive ${simulationDriftMeters157.toInt()} m"', '"TEST • ×$simulationMultiplier • dérive ${simulationDriftMeters157.toInt()} m"', 1)
s = s.replace('color = Color(0xFFFFC857),\n                    fontSize = 12.sp,\n                    modifier = Modifier.padding(top = 2.dp)',
              'color = Color(0xFFFFC857),\n                    fontSize = 10.sp,\n                    modifier = Modifier.padding(top = 1.dp)', 1)

# 3) Reduce spacing around the precision lab and helper text.
s = s.replace('modifier = Modifier.fillMaxWidth().padding(top = 5.dp),', 'modifier = Modifier.fillMaxWidth().padding(top = 2.dp),', 1)
s = s.replace('fontSize = 10.sp)\n                    listOf(0, 8, 20, 100)', 'fontSize = 9.sp)\n                    listOf(0, 8, 20, 100)', 1)
s = s.replace('fontSize = 9.sp,\n                    modifier = Modifier.fillMaxWidth().padding(top = 2.dp)',
              'fontSize = 8.sp,\n                    maxLines = 1,\n                    modifier = Modifier.fillMaxWidth().padding(top = 1.dp)', 1)

# 4) Give a little more height back to the map.
s = s.replace('Spacer(Modifier.height(if (navigationLandscape) 0.dp else 10.dp))',
              'Spacer(Modifier.height(if (navigationLandscape) 0.dp else 6.dp))', 1)

# 5) Portrait destination card: tighter header / replay / stats spacing.
s = s.replace('.padding(start = 18.dp, end = 14.dp, top = 12.dp, bottom = 2.dp),',
              '.padding(start = 16.dp, end = 12.dp, top = 8.dp, bottom = 0.dp),', 1)
s = s.replace('fontSize = 14.sp,\n                            fontWeight = FontWeight.ExtraBold,',
              'fontSize = 13.sp,\n                            fontWeight = FontWeight.ExtraBold,', 1)
s = s.replace('modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 4.dp),',
              'modifier = Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 0.dp),', 1)
s = s.replace('.padding(start = 18.dp, end = 18.dp, bottom = if (navigationLandscape) 5.dp else 16.dp),',
              '.padding(start = 16.dp, end = 16.dp, bottom = if (navigationLandscape) 5.dp else 9.dp),', 1)

# 6) Slightly more compact landscape guidance, already close to final.
s = s.replace('.fillMaxWidth(0.58f),', '.fillMaxWidth(0.55f),', 1)

# 7) Steps button follows the newly compact test area.
s = s.replace('top = if (navigationLandscape) 88.dp else if (simulationActive) 300.dp else 78.dp,',
              'top = if (navigationLandscape) 88.dp else if (simulationActive) 245.dp else 78.dp,', 1)

main.write_text(s)
print('V160 patch applied: compact portrait controls and destination card')
