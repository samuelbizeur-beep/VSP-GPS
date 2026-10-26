from pathlib import Path

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
s = main.read_text()

# 1) Map card: slightly more premium, stronger rounding and subtle border.
old = '''        Card(Modifier.fillMaxWidth().weight(1f), shape = RoundedCornerShape(22.dp)) {
            Box(Modifier.fillMaxSize()) {'''
new = '''        Card(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .border(1.dp, Color(0x334C9DFF), RoundedCornerShape(28.dp)),
            shape = RoundedCornerShape(28.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF08192C))
        ) {
            Box(Modifier.fillMaxSize()) {'''
if old not in s:
    raise SystemExit('V159: map card anchor missing')
s = s.replace(old, new, 1)

# 2) Route line: brighter and more readable, without touching routing logic.
s = s.replace('polyline.outlinePaint.strokeWidth = 13f', 'polyline.outlinePaint.strokeWidth = 15f', 1)
s = s.replace('polyline.outlinePaint.color = android.graphics.Color.rgb(35, 126, 255)',
              'polyline.outlinePaint.color = android.graphics.Color.rgb(49, 145, 255)', 1)

# 3) Speed badge: modern glass-like chip with accent ring.
old = '''                Card(
                    modifier = Modifier
                        .align(Alignment.BottomStart)
                        .padding(12.dp)
                        .size(76.dp)
                        .border(3.dp, Color.White, RoundedCornerShape(50)),
                    shape = RoundedCornerShape(50),
                    colors = CardDefaults.cardColors(containerColor = Color(0xE6102A46))
                ) {
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = speedKmh.toString(),
                            color = Color.White,
                            fontSize = 28.sp,
                            fontWeight = FontWeight.ExtraBold,
                            maxLines = 1
                        )
                        Text(
                            text = "km/h",
                            color = Color(0xFFB9D9FF),
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }'''
new = '''                Card(
                    modifier = Modifier
                        .align(Alignment.BottomStart)
                        .padding(14.dp)
                        .size(84.dp)
                        .border(3.dp, Color(0xFFEAF4FF), RoundedCornerShape(50)),
                    shape = RoundedCornerShape(50),
                    colors = CardDefaults.cardColors(containerColor = Color(0xF20A2038))
                ) {
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = speedKmh.toString(),
                            color = Color.White,
                            fontSize = 30.sp,
                            fontWeight = FontWeight.ExtraBold,
                            maxLines = 1
                        )
                        Text(
                            text = "km/h",
                            color = Color(0xFF8CC7FF),
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }'''
if old not in s:
    raise SystemExit('V159: speed badge anchor missing')
s = s.replace(old, new, 1)

# 4) GPS badge: more compact modern pill.
old = '''                        shape = RoundedCornerShape(14.dp),
                        colors = CardDefaults.cardColors(containerColor = Color(0xE6102A46))'''
new = '''                        shape = RoundedCornerShape(18.dp),
                        colors = CardDefaults.cardColors(containerColor = Color(0xEE0B2038))'''
if old not in s:
    raise SystemExit('V159: GPS badge style anchor missing')
s = s.replace(old, new, 1)

# 5) Bottom portrait card: add destination header and modern hierarchy.
anchor = '''            Column(modifier = Modifier.fillMaxWidth()) {
                // ETAPE 80 : suppression de la seconde copie de la manœuvre.'''
insert = '''            Column(modifier = Modifier.fillMaxWidth()) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = 18.dp, end = 14.dp, top = 12.dp, bottom = 2.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(
                            text = displayedTripDestination.label,
                            color = Color.White,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.ExtraBold,
                            maxLines = 1
                        )
                        Text(
                            text = "Destination",
                            color = Color(0xFF8FA9C3),
                            fontSize = 9.sp
                        )
                    }
                }
                // ETAPE 80 : suppression de la seconde copie de la manœuvre.'''
if anchor not in s:
    raise SystemExit('V159: bottom destination anchor missing')
s = s.replace(anchor, insert, 1)

# 6) More premium bottom card and values.
s = s.replace('shape = RoundedCornerShape(24.dp),\n            colors = CardDefaults.cardColors(containerColor = Color(0xFF0B2038))',
              'shape = RoundedCornerShape(28.dp),\n            colors = CardDefaults.cardColors(containerColor = Color(0xFF091D34))', 1)

# 7) Floating Steps button: use same design language as the mockup.
old = '''        Button(
            onClick = { showRoadmap = true },
            modifier = if (navigationLandscape) Modifier.size(52.dp) else Modifier,
            shape = if (navigationLandscape) RoundedCornerShape(50) else ButtonDefaults.shape,
            contentPadding = if (navigationLandscape) PaddingValues(0.dp) else PaddingValues(horizontal = 12.dp, vertical = 6.dp)
        ) {'''
new = '''        Button(
            onClick = { showRoadmap = true },
            modifier = if (navigationLandscape) Modifier.size(52.dp) else Modifier,
            shape = if (navigationLandscape) RoundedCornerShape(50) else RoundedCornerShape(20.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF4C9DFF), contentColor = Color.White),
            contentPadding = if (navigationLandscape) PaddingValues(0.dp) else PaddingValues(horizontal = 14.dp, vertical = 8.dp)
        ) {'''
if old not in s:
    raise SystemExit('V159: Steps button anchor missing')
s = s.replace(old, new, 1)

# 8) Main guidance card: even cleaner glass panel.
s = s.replace('colors = CardDefaults.cardColors(containerColor = Color(0xF20A2038))',
              'colors = CardDefaults.cardColors(containerColor = Color(0xF5081D34))', 1)

main.write_text(s)
print('V159 patch applied: modern navigation UI')
