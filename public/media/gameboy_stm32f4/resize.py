#!/usr/bin/env python3

import os
import subprocess

IMG_EXT = ['.jpg', '.jpeg', '.gif', '.png']
BIG_SIZE = 100 * 1024

path = '.'
for f in os.listdir(path):
    base_ext = os.path.splitext(f)
    base, ext = base_ext[0], base_ext[1]
    f = os.path.join(path, f)
    if os.path.isfile(f) and ext.lower() in IMG_EXT and not base.endswith('_1000'):
        f_small = os.path.join(path, base + '_1000' + ext)
        if os.path.exists(f_small):
            continue
        if os.path.getsize(f) >= BIG_SIZE:
            subprocess.call(['convert', f, '-resize', '1000>', '-quality', '85', f_small])
            subprocess.call(['exiftool', '-all=', f_small])
        else:
            os.symlink(f, f_small)
