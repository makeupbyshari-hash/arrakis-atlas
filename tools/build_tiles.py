#!/usr/bin/env python3
"""Create offline multiresolution map tile pyramids. Map image attribution/license preserved in assets."""
from PIL import Image, ImageOps
from pathlib import Path
import json, math, os
TILE=512
LEVELS=5
ROOT=Path('app/src/main/assets')
def build(code, filename):
    src=ROOT/filename
    with Image.open(src) as opened:
        base=ImageOps.exif_transpose(opened).convert('RGB')
    print(code, 'original:',base.size,flush=True)
    for level in range(LEVELS):
        grid=2**level
        dimension=TILE*grid
        if base.size != (dimension, dimension):
            im=base.resize((dimension,dimension),Image.Resampling.LANCZOS)
        else: im=base
        out=ROOT/'tiles'/code/str(level)
        out.mkdir(parents=True,exist_ok=True)
        for y in range(grid):
            for x in range(grid):
                crop=im.crop((x*TILE,y*TILE,(x+1)*TILE,(y+1)*TILE))
                crop.save(out/f'{x}_{y}.jpg',format='JPEG',quality=85,optimize=True,subsampling=0)
        print(code,'level',level,'tiles',grid*grid,flush=True)
    # full-size original is not loaded by the runtime; keep licensing in root assets
    src.unlink()
build('hagga','map.jpg')
build('deep','deep_desert.jpg')
(ROOT/'tiles_manifest.json').write_text(json.dumps({'tileSize':TILE,'maxLevel':LEVELS-1,'size':1100}),encoding='utf-8')
