import json
import re
import time

def get_index(p):
    m = re.search(r'(\d+)$', p.stem)
    return int(m.group(1)) if m else 0


def get_end(path):
    if not path["path_elements"]:
        print("Warning: empty path")
        return None, None, None
    el = path["path_elements"][-1]
    if el["type"] == "translation":
        return el["x_meters"], el["y_meters"], None
    else:
        return (
            el["translation_target"]["x_meters"],
            el["translation_target"]["y_meters"],
            el["rotation_target"]["rotation_radians"]
        )


def set_start(path, x, y, rad):
    if not path["path_elements"]:
        return
    el = path["path_elements"][0]
        

    if el["type"] == "translation":
        if x is not None:
            el["x_meters"] = x
        if y is not None:
            el["y_meters"] = y

    elif el["type"] == "waypoint":
        if x is not None:
            el["translation_target"]["x_meters"] = x
        if y is not None:
            el["translation_target"]["y_meters"] = y
        if rad is not None:
            el["rotation_target"]["rotation_radians"] = rad


def fix_routines(routines):
    for rk in routines:
        routines[rk].sort(key=get_index)

        prev_end = None

        for p in routines[rk]:
            path = safe_load_json(p)
            if not path:
                continue
            
            if prev_end is not None:
                set_start(path, *prev_end)

            prev_end = get_end(path)

            with open(p, "w") as f:
                json.dump(path, f, indent=2)
                
def safe_load_json(path, retries=20, delay=0.05):  # ~1 second total
    for _ in range(retries):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            time.sleep(delay)
    print(f"Could not read valid JSON: {path}")
    return None