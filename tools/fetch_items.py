#!/usr/bin/env python3
"""Fetch public game item names for offline on-device search. No personal data or telemetry."""
import json, pathlib, time, urllib.request, urllib.error
BASE="https://api.awakening.wiki/items"
OUT=pathlib.Path("app/src/main/assets/items.js")
records=[]
page=1
while page<=70:
    url=f"{BASE}?limit=100&page={page}"
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"ArrakisAtlas-OpenSource-ItemCatalog/1.0"})
            with urllib.request.urlopen(req,timeout=35) as res: payload=json.load(res)
            break
        except Exception:
            if attempt==3: raise
            time.sleep(1+attempt*2)
    new=payload.get("list",[])
    if not isinstance(new,list): raise RuntimeError("Unexpected item schema")
    for item in new:
        name=item.get("name")
        if not name or not isinstance(name,str): continue
        tags=item.get("item_tags")
        if not isinstance(tags,str): tags=""
        records.append({
            "id":item.get("item_id") or "",
            "name":name.strip(),
            "desc":(item.get("short_description") or "").strip()[:280],
            "tags":tags[:230],
            "added":item.get("added") or ""
        })
    print("page",page,"fetched",len(new),"total",len(records),flush=True)
    pageinfo=payload.get("pageInfo",{})
    if pageinfo.get("isLastPage"):break
    page+=1
    time.sleep(.15)
expected=payload.get("pageInfo",{}).get("totalRows",0)
if len(records)<1500 or (expected and len(records)<expected-20): raise RuntimeError(f"Catalog incomplete: {len(records)}/{expected}")
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text("window.ARRAKIS_ITEMS="+json.dumps(records,ensure_ascii=False,separators=(",",":"))+";\n",encoding="utf-8")
print("OFFLINE ITEMS:",len(records),"OUTPUT BYTES",OUT.stat().st_size)
