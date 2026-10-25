#!/usr/bin/env bash
set -e
FILE=app/src/main/java/fr/vspgps/app/MainActivity.kt
printf '\n===== V146/V147 hybrid markers =====\n'
grep -n -C 10 -E 'V146|OSM rond|IGN BD|Overpass|overpass|roundabout.*correct|correct.*roundabout|exitNumber|roundaboutExitCount' "$FILE" | head -n 650 || true
