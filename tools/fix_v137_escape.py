from pathlib import Path

path = Path("app/src/main/java/fr/vspgps/app/MainActivity.kt")
text = path.read_text(encoding="utf-8")
old = r'"e\.?[ -]?leclerc|leclerc"'
new = '"e[.]?[ -]?leclerc|leclerc"'
if old not in text:
    raise SystemExit("V137 escape fix: target not found")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("V137 escape fix applied successfully")
