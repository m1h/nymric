import json
from importlib.resources import files


def load(only=None):
    sites = json.loads(files("nymric").joinpath("data/sites.json").read_text("utf-8"))
    if only:
        want = {n.lower() for n in only}
        sites = [s for s in sites if s["name"].lower() in want]
    return sites
