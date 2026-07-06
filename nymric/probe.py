import re
from dataclasses import dataclass, field

import httpx

from .links import extract

INCONCLUSIVE = {403, 429, 500, 502, 503}

_OG = re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', re.I)
_OG_REV = re.compile(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', re.I)
_GRAVATAR = re.compile(r'"thumbnailUrl":"([^"]+)"')


@dataclass(slots=True)
class Hit:
    site: str
    platform: str
    url: str
    handle: str
    state: str
    links: list = field(default_factory=list)
    avatar: str | None = None
    ahash: int | None = None


def _marker(m, handle):
    if not m:
        return None
    return m.format(handle) if "{}" in m else m


def _avatar(site, body, handle):
    if site["name"] == "github":
        return f"https://github.com/{handle}.png"
    if site["name"] == "gravatar":
        m = _GRAVATAR.search(body)
        return m.group(1).replace("\\/", "/") if m else None
    m = _OG.search(body) or _OG_REV.search(body)
    return m.group(1) if m else None


async def probe(client, site, handle):
    url = site["url"].format(handle)
    platform = site.get("platform", site["name"])
    try:
        r = await client.get(url)
    except httpx.HTTPError:
        return Hit(site["name"], platform, url, handle, "error")

    if r.status_code in INCONCLUSIVE:
        return Hit(site["name"], platform, url, handle, "error")

    if site["method"] == "status":
        state = "found" if r.status_code == 200 else "missing"
    else:
        absent = _marker(site.get("absent"), handle)
        found = _marker(site.get("found"), handle)
        if absent is not None:
            state = "missing" if absent in r.text else "found"
        else:
            state = "found" if found and found in r.text else "missing"

    hit = Hit(site["name"], platform, url, handle, state)
    if state == "found":
        if site.get("links"):
            hit.links = extract(r.text, platform)
        hit.avatar = _avatar(site, r.text, handle)
    return hit
