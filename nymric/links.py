import re

_URL = re.compile(r"""https?://[^\s"'<>)\]}&,`|]+""", re.I)
_HANDLE = re.compile(r"[A-Za-z0-9_.-]{2,40}")
_ASSET = re.compile(r"\.(png|jpe?g|gif|svg|css|js|ico|json|xml|txt|webp|woff2?|map|pdf)$", re.I)

_DOMAINS = {
    "github.com": "github", "gitlab.com": "gitlab", "codeberg.org": "codeberg",
    "twitter.com": "twitter", "x.com": "twitter", "instagram.com": "instagram",
    "t.me": "telegram", "telegram.me": "telegram", "youtube.com": "youtube",
    "twitch.tv": "twitch", "reddit.com": "reddit", "keybase.io": "keybase",
    "linkedin.com": "linkedin", "soundcloud.com": "soundcloud", "last.fm": "lastfm",
    "medium.com": "medium", "dev.to": "devto", "lichess.org": "lichess",
    "chess.com": "chess", "facebook.com": "facebook", "mastodon.social": "mastodon",
    "bsky.app": "bluesky", "pinterest.com": "pinterest", "about.me": "aboutme",
    "buymeacoffee.com": "buymeacoffee", "hackerone.com": "hackerone",
    "bugcrowd.com": "bugcrowd", "hub.docker.com": "dockerhub", "gitea.com": "gitea",
    "kaggle.com": "kaggle",
}

_PREFIX = {"@", "in", "u", "user", "users", "people", "profile", "member", "id", "gh"}

_SKIP = set(_DOMAINS.values()) | {
    "about", "home", "login", "logout", "signup", "join", "settings", "explore",
    "search", "help", "support", "pricing", "features", "security", "enterprise",
    "team", "topics", "trending", "collections", "sponsors", "marketplace", "docs",
    "notifications", "new", "contact", "careers", "jobs", "press", "legal", "blog",
    "privacy", "terms", "tos", "status", "developer", "developers", "api", "www",
}


def _handle(path):
    segs = [s for s in path.split("?")[0].split("#")[0].split("/") if s]
    if not segs:
        return None
    if segs[0].lower() in _PREFIX:
        return segs[1] if len(segs) == 2 else None
    return segs[0].lstrip("@") if len(segs) == 1 else None


def extract(body, source=None):
    out, seen = [], set()
    for raw in _URL.findall(body):
        url = raw.rstrip(".,);'\"/")
        host, _, path = url.split("://", 1)[-1].partition("/")
        host = host.lower().removeprefix("www.")
        platform = _DOMAINS.get(host)
        if not platform or platform == source:
            continue
        handle = _handle(path)
        if not handle:
            continue
        low = handle.lower()
        if low in _SKIP or _ASSET.search(low) or not _HANDLE.fullmatch(handle):
            continue
        if (platform, low) in seen:
            continue
        seen.add((platform, low))
        out.append((platform, handle, url))
    return out
