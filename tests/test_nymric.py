import asyncio
import hashlib
import io

import httpx
import pytest
import respx

from nymric.faces import dhash, fingerprint, hamming
from nymric.links import extract
from nymric.mailto import _parse, is_email, resolve
from nymric.probe import Hit, probe
from nymric.sites import load
from nymric.stitch import Account, _avatar_matches, mosaic


class Resp:
    def __init__(self, status=200, text=""):
        self.status_code = status
        self.text = text


class Client:
    def __init__(self, resp):
        self.resp = resp

    async def get(self, url):
        return self.resp


def run(site, resp, handle="alice"):
    return asyncio.run(probe(Client(resp), site, handle))


def test_status_found():
    assert run({"name": "github", "url": "https://github.com/{}", "method": "status"}, Resp(200)).state == "found"


def test_status_missing():
    assert run({"name": "github", "url": "https://github.com/{}", "method": "status"}, Resp(404)).state == "missing"


def test_403_is_inconclusive_not_missing():
    assert run({"name": "npm", "url": "https://www.npmjs.com/~{}", "method": "status"}, Resp(403)).state == "error"


def test_text_inverse_marker():
    site = {"name": "steam", "url": "https://steamcommunity.com/id/{}", "method": "text",
            "absent": "The specified profile could not be found."}
    assert run(site, Resp(200, "hi alice")).state == "found"
    assert run(site, Resp(200, "The specified profile could not be found.")).state == "missing"


def test_text_marker_with_handle():
    site = {"name": "pypi", "url": "https://pypi.org/user/{}/", "method": "text", "found": "Profile of {}"}
    assert run(site, Resp(200, "Profile of alice · PyPI")).state == "found"
    assert run(site, Resp(200, "nope")).state == "missing"


def test_extract_maps_known_domains():
    body = "links: https://twitter.com/alice https://lichess.org/@/alice https://twitch.tv/aliceplays"
    got = {p: h for p, h, _ in extract(body)}
    assert got == {"twitter": "alice", "lichess": "alice", "twitch": "aliceplays"}


def test_extract_drops_self_links_brands_and_assets():
    body = ("https://github.com/features/copilot https://github.com/fluidicon.png "
            "https://twitter.com/github https://github.com/torvalds")
    assert extract(body, source="github") == []


def test_extract_keeps_real_cross_links():
    body = "https://twitter.com/alice https://linkedin.com/in/alice-b https://github.com/pricing"
    got = {p: h for p, h, _ in extract(body, source="gravatar")}
    assert got == {"twitter": "alice", "linkedin": "alice-b"}


def test_mosaic_confirms_cross_link():
    hits = [
        Hit("github", "github", "https://github.com/alice", "alice", "found",
            [("lichess", "alice", "https://lichess.org/@/alice")]),
        Hit("lichess", "lichess", "https://lichess.org/api/user/alice", "alice", "found", []),
    ]
    primary, network = mosaic("alice", hits)
    conf = {a.platform: a.confidence for a in primary}
    assert conf["lichess"] == "confirmed"
    assert conf["github"] == "possible"


def _png(fn):
    from PIL import Image
    img = Image.new("L", (16, 16))
    img.putdata([fn(x, y) for y in range(16) for x in range(16)])
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def test_dhash_identical_is_zero_opposite_is_far():
    pytest.importorskip("PIL")
    up = _png(lambda x, y: x * 16)
    down = _png(lambda x, y: (15 - x) * 16)
    assert hamming(dhash(up), dhash(up)) == 0
    assert hamming(dhash(up), dhash(down)) > 6


def _face(site, platform, ahash):
    h = Hit(site, platform, f"https://{site}/alice", "alice", "found")
    h.ahash = ahash
    return h


def test_avatar_matches_cross_platform():
    a = _face("github", "github", 0x0F0F0F0F0F0F0F0F)
    b = _face("gravatar", "gravatar", 0x0F0F0F0F0F0F0F0F)
    assert _avatar_matches([a, b]) == {"github": {"gravatar"}, "gravatar": {"github"}}


def test_avatar_ignores_flat_image():
    a = _face("github", "github", 0x0F0F0F0F0F0F0F0F)
    flat = _face("gitlab", "gitlab", 0)
    assert _avatar_matches([a, flat]) == {}


def test_mosaic_confirms_by_avatar():
    hits = [
        Hit("github", "github", "https://github.com/alice", "alice", "found"),
        Hit("gravatar", "gravatar", "https://gravatar.com/alice.json", "alice", "found"),
    ]
    hits[0].ahash = hits[1].ahash = 0x0F0F0F0F0F0F0F0F
    primary, _ = mosaic("alice", hits)
    assert all(a.confidence == "confirmed" for a in primary)
    assert any("same avatar" in r for a in primary for r in a.reasons)


def test_is_email():
    assert is_email("a@b.com")
    assert is_email("first.last@sub.domain.io")
    assert not is_email("justaname")
    assert not is_email("@handle")
    assert not is_email("nope@nodot")


def test_parse_gravatar_payload():
    payload = {"entry": [{"preferredUsername": "alice", "displayName": "Alice A",
                          "profileUrl": "https://gravatar.com/alice"}]}
    info = _parse(payload)
    assert info["username"] == "alice"
    assert info["name"] == "Alice A"


def test_parse_empty_payload():
    assert _parse({"entry": []}) is None
    assert _parse({}) is None


@respx.mock
def test_probe_over_real_httpx():
    respx.get("https://github.com/alice").mock(return_value=httpx.Response(200, text="ok"))
    respx.get("https://github.com/ghost").mock(return_value=httpx.Response(404))
    respx.get("https://github.com/blocked").mock(return_value=httpx.Response(403))
    site = {"name": "github", "url": "https://github.com/{}", "method": "status"}

    async def state(handle):
        async with httpx.AsyncClient() as c:
            return (await probe(c, site, handle)).state

    assert asyncio.run(state("alice")) == "found"
    assert asyncio.run(state("ghost")) == "missing"
    assert asyncio.run(state("blocked")) == "error"


def test_sites_load_and_filter():
    assert len(load()) >= 20
    only = load(["github", "gravatar"])
    assert {s["name"] for s in only} == {"github", "gravatar"}


def test_show_renders_json_markdown_and_terminal():
    from rich.console import Console

    from nymric.show import render, to_json, to_markdown
    primary = [Account("github", "alice", "https://github.com/alice", "confirmed", ["x"])]
    network = [Account("twitter", "alice", "https://twitter.com/alice", "likely", ["y"])]
    assert '"confirmed"' in to_json("alice", primary, network)
    md = to_markdown("alice", primary, network)
    assert "| github |" in md and "twitter" in md
    con = Console(record=True, width=80)
    render("alice", primary, network, 21, 1, console=con)
    assert "alice" in con.export_text()


@respx.mock
def test_resolve_email_via_gravatar():
    digest = hashlib.md5(b"a@b.com").hexdigest()
    respx.get(f"https://gravatar.com/{digest}.json").mock(
        return_value=httpx.Response(200, json={"entry": [{"preferredUsername": "alice", "displayName": "A"}]}))
    info = asyncio.run(resolve("A@B.com", 5, "ua"))
    assert info["username"] == "alice"


@respx.mock
def test_fingerprint_sets_hash_from_image():
    respx.get("https://img.test/a.png").mock(return_value=httpx.Response(200, content=_png(lambda x, y: x * 16)))
    h = Hit("github", "github", "https://github.com/alice", "alice", "found")
    h.avatar = "https://img.test/a.png"

    async def go():
        async with httpx.AsyncClient() as c:
            await fingerprint(c, [h])

    asyncio.run(go())
    assert h.ahash is not None


@respx.mock
def test_main_json_end_to_end(capsys):
    from nymric.__main__ import main
    respx.get("https://github.com/alice").mock(return_value=httpx.Response(200, text="ok"))
    main(["alice", "-s", "github", "--json", "--no-avatars"])
    out = capsys.readouterr().out
    assert '"seed": "alice"' in out
    assert "github" in out
