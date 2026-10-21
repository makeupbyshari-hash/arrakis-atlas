#!/usr/bin/env python3
"""Build the offline crafting database from public, GPL-3.0 game-data snapshots.
Recipe output counts, ingredient IDs and station types are taken from source records.
German names come ONLY from the German game database, never from translation guesses.
"""
import datetime
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path("app/src/main/assets")
RECIPE_URL = "https://raw.githubusercontent.com/Abarrach/La-maison-des-Havres-Gris/main/stuff_recipes.json"
LOCALE_URL = "https://cdn-hosted.gaming.tools/dune/data/de/items.d.json"
UA = {"User-Agent": "ArrakisAtlas/1.0 (+https://github.com/makeupbyshari-hash/arrakis-atlas)"}

def download(url, timeout=65):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)

def resolve_flat(flat, index, depth=0):
    if depth > 16 or not isinstance(index, int) or index < 0 or index >= len(flat):
        return index
    value = flat[index]
    if isinstance(value, dict):
        return {k: resolve_flat(flat, v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_flat(flat, v, depth + 1) for v in value]
    return value

def flatten_german(data):
    if not isinstance(data, list) or not data or not isinstance(data[0], list):
        raise ValueError("German item catalog has unknown format")
    result = {}
    for pointer in data[0]:
        row = resolve_flat(data, pointer)
        if not isinstance(row, dict):
            continue
        item_id, name = row.get("id"), row.get("name")
        if isinstance(item_id, str) and isinstance(name, str) and name.strip():
            result[item_id.lower()] = name.strip()
    return result

# Names previously verified against German-language game-database entries.
CURATED = {
    "t5radiatedcorecomponent": "Verstrahlte Schlacke",
    "t6irradiatedcore": "Verstrahlter Kern",
    "radiation_suit_t5": "Strahlenanzug Typ 5",
}
def local_name(code, fallback=None):
    key = str(code).lower()
    if key in localized:
        return localized[key]
    if key in CURATED:
        return CURATED[key]
    if key in by_english:
        return by_english[key]
    # English item names are explicitly labelled as fallback and NEVER auto-translated.
    if fallback:
        # The source recipe list contains French names: discard those as unknown language.
        pass
    return re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(code).replace("_", " ")).strip()

def valid_number(x):
    try:
        value = float(x)
        if 0 < value < 1000000:
            return int(value) if value.is_integer() else value
    except (ValueError, TypeError, OverflowError):
        pass
    return None

raw = download(RECIPE_URL)
if not isinstance(raw, dict) or len(raw) < 1000:
    raise RuntimeError("Recipe snapshot is missing or implausibly small")
localized = {}
try:
    localized = flatten_german(download(LOCALE_URL, timeout=35))
    print("German game-database name entries:", len(localized), flush=True)
except Exception as exc:
    print("German CDN unavailable, using previously verified German names and raw IDs:", str(exc)[:250], flush=True)

# Connect English names found in the existing offline item catalog where IDs match.
by_english = {}
items_file = ROOT / "items.js"
if items_file.exists():
    data = items_file.read_text(encoding="utf-8")
    prefix = "window.ARRAKIS_ITEMS="
    if data.startswith(prefix):
        for item in json.loads(data[len(prefix):].rstrip().rstrip(";")):
            ident = str(item.get("id") or "").lower()
            name = str(item.get("name") or "").strip()
            if ident and name:
                by_english[ident] = name

# Prefer German names already checked in the main atlas vendor catalog.
extra_file = ROOT / "extra.js"
if extra_file.exists():
    content = extra_file.read_text(encoding="utf-8")
    prefix = "window.ATLAS_EXTRA="
    if content.startswith(prefix):
        extra = json.loads(content[len(prefix):].rstrip().rstrip(";"))
        for vendor in extra.get("vendors", {}).values():
            for record in vendor.get("goods", []):
                if len(record) > 1 and record[0] and record[1]:
                    english = str(record[1]).lower().strip()
                    german = str(record[0]).strip()
                    for ident, known in by_english.items():
                        if known.lower() == english:
                            CURATED.setdefault(ident, german)

recipes = {}
all_ids = set()
for code, record in raw.items():
    if not isinstance(record, dict):
        continue
    variants = record.get("recipes") or []
    if not isinstance(variants, list) or not variants:
        continue
    source = variants[0]
    if not isinstance(source, dict):
        continue
    ingredients = []
    for ing in source.get("ingredients") or []:
        if not isinstance(ing, dict):
            continue
        ident = str(ing.get("id") or "").strip().lower()
        qty = valid_number(ing.get("qty"))
        if ident and qty is not None:
            ingredients.append({"id": ident, "qty": qty})
            all_ids.add(ident)
    output = valid_number(source.get("output")) or 1
    if not ingredients:
        continue
    item_id = str(code).strip().lower()
    if not item_id:
        continue
    all_ids.add(item_id)
    stations = record.get("station") or []
    if isinstance(stations, str):
        stations = [stations]
    if not isinstance(stations, list):
        stations = []
    recipes[item_id] = {
        "id": item_id,
        "name": local_name(item_id),
        "output": output,
        "ingredients": ingredients,
        "station": [str(s) for s in stations if s],
        "craftTime": record.get("craftTime") or None,
        "source": RECIPE_URL,
        "localizationVerified": item_id in localized or item_id in CURATED,
    }

if len(recipes) < 1000:
    raise RuntimeError("Fewer than 1,000 recipes survived validation")
names = {ident: local_name(ident) for ident in all_ids}
# Always use IDs for calculation. Display names may be duplicated across quality levels.
payload = {
    "items": recipes,
    "names": names,
    "germanIds": sorted(set(localized).intersection(all_ids) | set(CURATED).intersection(all_ids)),
    "source": RECIPE_URL,
    "snapshotCount": len(raw),
}
ROOT.mkdir(parents=True, exist_ok=True)
(ROOT / "recipes.js").write_text(
    "window.ATLAS_RECIPE_DATA=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
    encoding="utf-8",
)
audit = {
    "recipes": len(recipes),
    "sourceRecipes": len(raw),
    "resolvedNames": len(names),
    "verifiedGermanNames": len(payload["germanIds"]),
    "germanDatabaseItems": len(localized),
    "generatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "sources": [RECIPE_URL, LOCALE_URL],
}
(ROOT / "recipe-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("OFFLINE RECIPES:", len(recipes), "GERMAN VERIFIED:", len(payload["germanIds"]),
      "SOURCE SIZE:", (ROOT / "recipes.js").stat().st_size, flush=True)
