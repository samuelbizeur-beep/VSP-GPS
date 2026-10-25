#!/usr/bin/env bash
set -e
FILE=app/src/main/java/fr/vspgps/app/MainActivity.kt
ROUTER=app/src/main/java/fr/vspgps/app/LocalValhallaRouter.kt
printf '\n=== V146 OSM/IGN symbols in MainActivity ===\n'
grep -n -E 'OSM rond|Overpass|IGN BD|hybrid|roundabout|exitNumber|exit_number|sortie' "$FILE" | tail -n 220 || true
printf '\n=== V146 OSM/roundabout symbols in LocalValhallaRouter ===\n'
grep -n -E 'Overpass|roundabout|exitNumber|exit_number|sortie|intersecting' "$ROUTER" | tail -n 220 || true
