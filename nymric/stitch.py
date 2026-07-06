from dataclasses import dataclass, field

ORDER = {"confirmed": 0, "likely": 1, "possible": 2}


@dataclass
class Account:
    platform: str
    handle: str
    url: str
    confidence: str
    reasons: list = field(default_factory=list)


def _avatar_matches(found):
    hashed = [h for h in found if h.ahash and 8 <= bin(h.ahash).count("1") <= 56]
    out = {}
    for i, a in enumerate(hashed):
        for b in hashed[i + 1:]:
            if a.platform != b.platform and bin(a.ahash ^ b.ahash).count("1") <= 6:
                out.setdefault(a.site, set()).add(b.site)
                out.setdefault(b.site, set()).add(a.site)
    return out


def mosaic(seed, hits):
    found = [h for h in hits if h.state == "found"]
    seed_l = seed.lower()

    refs = {}
    for h in found:
        for platform, handle, url in h.links:
            r = refs.setdefault((platform, handle.lower()),
                                {"handle": handle, "url": url, "src": set()})
            r["src"].add(h.site)

    twins = _avatar_matches(found)

    primary, seen = [], set()
    for h in found:
        if h.platform in seen:
            continue
        seen.add(h.platform)
        backers = sorted(s for s in refs.get((h.platform, seed_l), {}).get("src", ()) if s != h.site)
        faces = sorted(twins.get(h.site, ()))
        reasons = []
        if backers:
            reasons.append(f"cross-linked from {', '.join(backers)}")
        if faces:
            reasons.append(f"same avatar as {', '.join(faces)}")
        if reasons:
            primary.append(Account(h.site, h.handle, h.url, "confirmed", reasons))
        else:
            primary.append(Account(h.site, h.handle, h.url, "possible",
                                   ["nothing links to it, could be a namesake"]))

    known = {h.platform for h in found}
    network = []
    for (platform, hl), r in refs.items():
        if hl == seed_l and platform in known:
            continue
        conf = "likely" if len(r["src"]) >= 2 else "possible"
        network.append(Account(platform, r["handle"], r["url"], conf,
                               [f"linked from {', '.join(sorted(r['src']))}"]))

    primary.sort(key=lambda a: (ORDER[a.confidence], a.platform))
    network.sort(key=lambda a: (ORDER[a.confidence], a.platform))
    return primary, network
