import hashlib
import re

import httpx

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_email(s):
    return bool(_EMAIL.match(s))


def _parse(payload):
    try:
        entry = payload["entry"][0]
    except (KeyError, IndexError, TypeError):
        return None
    return {"username": entry.get("preferredUsername"),
            "name": entry.get("displayName"),
            "url": entry.get("profileUrl")}


async def resolve(email, timeout, ua):
    digest = hashlib.md5(email.strip().lower().encode()).hexdigest()
    async with httpx.AsyncClient(headers={"user-agent": ua}, timeout=timeout,
                                 follow_redirects=True) as client:
        try:
            r = await client.get(f"https://gravatar.com/{digest}.json")
        except httpx.HTTPError:
            return None
    if r.status_code != 200:
        return None
    try:
        return _parse(r.json())
    except ValueError:
        return None
