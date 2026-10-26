from pathlib import Path

main = Path('app/src/main/java/fr/vspgps/app/MainActivity.kt')
s = main.read_text()

# 1) Replace the minimal home icon row with a branded header while keeping the back action.
old = '''        // V62 : icône Home en contour, sans emoji ni texte.
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Start,
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(
                onClick = onBack,
                modifier = Modifier.size(44.dp)
            ) {
                Canvas(modifier = Modifier.size(30.dp)) {
                    val stroke = Stroke(width = 2.6.dp.toPx())
                    val home = Path().apply {
                        moveTo(size.width * 0.10f, size.height * 0.47f)
                        lineTo(size.width * 0.50f, size.height * 0.12f)
                        lineTo(size.width * 0.90f, size.height * 0.47f)
                        moveTo(size.width * 0.20f, size.height * 0.39f)
                        lineTo(size.width * 0.20f, size.height * 0.88f)
                        lineTo(size.width * 0.80f, size.height * 0.88f)
                        lineTo(size.width * 0.80f, size.height * 0.39f)
                        moveTo(size.width * 0.40f, size.height * 0.88f)
                        lineTo(size.width * 0.40f, size.height * 0.60f)
                        lineTo(size.width * 0.60f, size.height * 0.60f)
                        lineTo(size.width * 0.60f, size.height * 0.88f)
                    }
                    drawPath(home, color = Color(0xFFEAF2FF), style = stroke)
                }
            }
        }
'''
new = '''        Row(
            modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(
                onClick = onBack,
                modifier = Modifier
                    .size(44.dp)
                    .background(Color(0xFF0D223B), RoundedCornerShape(16.dp))
            ) {
                Canvas(modifier = Modifier.size(27.dp)) {
                    val stroke = Stroke(width = 2.5.dp.toPx())
                    val home = Path().apply {
                        moveTo(size.width * 0.10f, size.height * 0.47f)
                        lineTo(size.width * 0.50f, size.height * 0.12f)
                        lineTo(size.width * 0.90f, size.height * 0.47f)
                        moveTo(size.width * 0.20f, size.height * 0.39f)
                        lineTo(size.width * 0.20f, size.height * 0.88f)
                        lineTo(size.width * 0.80f, size.height * 0.88f)
                        lineTo(size.width * 0.80f, size.height * 0.39f)
                    }
                    drawPath(home, color = Color(0xFF9FD0FF), style = stroke)
                }
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)) {
                Text(
                    "VSP GPS",
                    color = Color.White,
                    fontSize = 24.sp,
                    fontWeight = FontWeight.ExtraBold
                )
                Text(
                    "La route pensée pour les voitures sans permis",
                    color = Color(0xFF8FA9C3),
                    fontSize = 11.sp,
                    maxLines = 1
                )
            }
            Surface(
                shape = RoundedCornerShape(16.dp),
                color = Color(0xFF123052),
                border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFF31577B))
            ) {
                Text(
                    "100% VSP",
                    color = Color(0xFF65D68A),
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp)
                )
            }
        }
'''
if old not in s:
    raise SystemExit('V161: home header anchor missing')
s = s.replace(old, new, 1)

# 2) Give the search field the rounded modern visual language used by the navigation screen.
anchor = '''            keyboardActions =
                KeyboardActions(
                    onSearch = {
                        searchAddress()
                    }
                )
        )'''
replacement = '''            keyboardActions =
                KeyboardActions(
                    onSearch = {
                        searchAddress()
                    }
                ),
            shape = RoundedCornerShape(24.dp),
            colors = androidx.compose.material3.OutlinedTextFieldDefaults.colors(
                focusedContainerColor = Color(0xFF0D223B),
                unfocusedContainerColor = Color(0xFF0B2038),
                focusedBorderColor = Color(0xFF4C9DFF),
                unfocusedBorderColor = Color(0xFF31577B),
                cursorColor = Color(0xFF4C9DFF),
                focusedTextColor = Color.White,
                unfocusedTextColor = Color.White,
                focusedLabelColor = Color(0xFF9FD0FF),
                unfocusedLabelColor = Color(0xFF8FA9C3),
                focusedPlaceholderColor = Color(0xFF7690A8),
                unfocusedPlaceholderColor = Color(0xFF7690A8)
            )
        )'''
if anchor not in s:
    raise SystemExit('V161: search field anchor missing')
s = s.replace(anchor, replacement, 1)

# 3) Modern rounded history and suggestion panels.
s = s.replace('colors = CardDefaults.cardColors(containerColor = Color(0xFF102A46))\n            ) {',
              'shape = RoundedCornerShape(20.dp),\n                colors = CardDefaults.cardColors(containerColor = Color(0xFF0D223B))\n            ) {', 2)

# 4) Rename sections to match the future product structure.
s = s.replace('"Raccourcis",', '"Accès rapides",', 1)
s = s.replace('"À proximité",', '"Services VSP",', 1)

# 5) Upgrade quick-access chips from outline-only to filled modern cards.
old = '''                        .height(48.dp)
                        .border(
                            1.dp,
                            Color(0xFF9AA7B8),
                            RoundedCornerShape(24.dp)
                        )
                        .combinedClickable('''
new = '''                        .height(54.dp)
                        .background(Color(0xFF0D223B), RoundedCornerShape(20.dp))
                        .border(
                            1.dp,
                            Color(0xFF31577B),
                            RoundedCornerShape(20.dp)
                        )
                        .combinedClickable('''
if old not in s:
    raise SystemExit('V161: quick access anchor missing')
s = s.replace(old, new, 1)
s = s.replace('color = Color(0xFF58A9FF),\n                        fontSize = 12.sp,',
              'color = Color(0xFF9FD0FF),\n                        fontSize = 12.sp,', 1)

# 6) Make the helper copy less dominant.
s = s.replace('color = Color.Gray,\n            fontSize = 11.sp,',
              'color = Color(0xFF70859A),\n            fontSize = 10.sp,', 1)

# 7) Modern primary search action.
old = '''Button(
            onClick = {
                searchAddress()
            },

            enabled =
                query.isNotBlank() &&
                !searching,

            modifier =
                Modifier.fillMaxWidth()
        ) {

            Text(
                "Rechercher l'adresse"
            )
        }'''
new = '''Button(
            onClick = {
                searchAddress()
            },
            enabled = query.isNotBlank() && !searching,
            modifier = Modifier.fillMaxWidth().height(52.dp),
            shape = RoundedCornerShape(20.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = Color(0xFF4C9DFF),
                contentColor = Color.White
            )
        ) {
            Text(
                "Rechercher",
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold
            )
        }'''
if old not in s:
    raise SystemExit('V161: search button anchor missing')
s = s.replace(old, new, 1)

main.write_text(s)
print('V161 patch applied: modern home/search UI')
