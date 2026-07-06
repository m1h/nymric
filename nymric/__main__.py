import argparse
import asyncio
from pathlib import Path

import httpx
from rich.console import Console

from . import __version__, faces, mailto, show
from .probe import probe
from .sites import load
from .stitch import mosaic

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"


def _out(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


async def _sweep(seed, sites, concurrency, timeout, ua, avatars):
    sem = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(max_connections=concurrency)
    async with httpx.AsyncClient(headers={"user-agent": ua}, timeout=timeout,
                                 follow_redirects=True, limits=limits) as client:
        async def one(s):
            async with sem:
                return await probe(client, s, seed)
        hits = await asyncio.gather(*(one(s) for s in sites))
        if avatars and faces.available():
            await faces.fingerprint(client, hits)
        return hits


def main(argv=None):
    p = argparse.ArgumentParser(prog="nymric", description="trace a username or email across public sites")
    p.add_argument("username", metavar="username|email")
    p.add_argument("-s", "--sites", nargs="+", metavar="NAME", help="only check these sites")
    p.add_argument("-c", "--concurrency", type=int, default=10)
    p.add_argument("-t", "--timeout", type=float, default=10.0)
    p.add_argument("--ua", default=UA, help="user-agent override")
    p.add_argument("--no-follow", action="store_true", help="skip following bio links")
    p.add_argument("--no-avatars", action="store_true", help="skip avatar matching")
    p.add_argument("--json", action="store_true", help="dump json to stdout")
    p.add_argument("--md", metavar="FILE", help="also write a markdown report")
    p.add_argument("--svg", metavar="FILE", help="also save the mosaic as an svg screenshot")
    p.add_argument("-V", "--version", action="version", version=f"nymric {__version__}")
    a = p.parse_args(argv)

    seed = a.username
    if mailto.is_email(seed):
        info = asyncio.run(mailto.resolve(seed, a.timeout, a.ua))
        if not info or not info.get("username"):
            p.error("no public gravatar profile with a username for that email")
        Console(stderr=True).print(f"[dim]gravatar: {info['name'] or 'profile'} → @{info['username']}[/]")
        seed = info["username"]

    sites = load(a.sites)
    if not sites:
        p.error("no matching sites")
    if a.no_follow:
        for s in sites:
            s["links"] = False

    hits = asyncio.run(_sweep(seed, sites, a.concurrency, a.timeout, a.ua, not a.no_avatars))
    primary, network = mosaic(seed, hits)
    found_n = sum(h.state == "found" for h in hits)

    if a.json:
        print(show.to_json(seed, primary, network))
    else:
        con = Console(record=True, width=100) if a.svg else None
        show.render(seed, primary, network, len(sites), found_n, console=con)
        if a.svg:
            con.save_svg(_out(a.svg), title="nymric · mosaic")
    if a.md:
        _out(a.md).write_text(show.to_markdown(seed, primary, network), encoding="utf-8")


if __name__ == "__main__":
    main()
