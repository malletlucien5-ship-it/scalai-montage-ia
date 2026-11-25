"""Décodeur protobuf générique pour le corps décompressé d'un PowerGrade Resolve (.drx)."""
import struct
import sys
from pathlib import Path


def varint(b, i):
    v = s = 0
    while True:
        c = b[i]
        i += 1
        v |= (c & 0x7F) << s
        s += 7
        if c < 0x80:
            return v, i


def walk(b, depth=0, path="", out=None, maxdepth=12):
    i = 0
    ok = True
    items = []
    while i < len(b):
        try:
            key, i = varint(b, i)
        except IndexError:
            return None
        f, wt = key >> 3, key & 7
        if f == 0:
            return None
        if wt == 0:
            v, i = varint(b, i)
            items.append((f, "int", v))
        elif wt == 1:
            if i + 8 > len(b):
                return None
            items.append((f, "f64", struct.unpack("<d", b[i:i + 8])[0]))
            i += 8
        elif wt == 5:
            if i + 4 > len(b):
                return None
            items.append((f, "f32", struct.unpack("<f", b[i:i + 4])[0]))
            i += 4
        elif wt == 2:
            n, i = varint(b, i)
            if i + n > len(b):
                return None
            items.append((f, "bytes", b[i:i + n]))
            i += n
        else:
            return None
    return items


def show(b, depth=0, path=""):
    items = walk(b)
    if items is None:
        return False
    for f, t, v in items:
        p = f"{path}.{f}"
        if t == "bytes":
            txt = None
            try:
                s = v.decode("utf-8")
                if s.isprintable() and len(s) > 0:
                    txt = s
            except UnicodeDecodeError:
                pass
            if txt is not None and walk(v) is None:
                print("  " * depth + f"{p} = '{txt}'")
            elif depth < 14 and show(v, depth + 1, p):
                pass
            else:
                print("  " * depth + f"{p} = <{len(v)} octets>")
        elif t == "f32":
            print("  " * depth + f"{p} f32 = {v:.6g}")
        elif t == "f64":
            print("  " * depth + f"{p} f64 = {v:.6g}")
        else:
            print("  " * depth + f"{p} int = {v}")
    return True


show(Path(sys.argv[1]).read_bytes())
