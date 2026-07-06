import json
from dataclasses import asdict

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

COLOR = {"confirmed": "green", "likely": "yellow", "possible": "grey62"}


def render(seed, primary, network, checked, found_n, console=None):
    c = console or Console()
    c.print(Panel(
        f"[bold]nymric[/] · mosaic for [cyan]{seed}[/]\n"
        f"[dim]{found_n} hits across {checked} sites. tiles, not a photograph. every match is a lead.[/]",
        border_style="cyan", expand=False))
    if not primary and not network:
        c.print("[dim]nothing turned up. try another handle.[/]")
        return
    c.print(_table("primary accounts", primary))
    if network:
        c.print(_table("associated accounts (pulled from bios)", network))
    confirmed = sum(a.confidence == "confirmed" for a in primary)
    c.print(f"[dim]→ {len(primary)} primary · {len(network)} associated · "
            f"{confirmed} confirmed same-person link(s) · verify before you trust it[/]")


def _table(title, rows):
    t = Table(title=title, title_justify="left", title_style="bold", expand=True)
    t.add_column("site", style="bold")
    t.add_column("handle")
    t.add_column("url", style="blue", overflow="fold")
    t.add_column("confidence")
    t.add_column("why", style="dim")
    for a in rows:
        t.add_row(a.platform, a.handle, a.url,
                  f"[{COLOR[a.confidence]}]{a.confidence}[/]", "; ".join(a.reasons))
    return t


def _payload(seed, primary, network):
    return {"seed": seed,
            "primary": [asdict(a) for a in primary],
            "associated": [asdict(a) for a in network]}


def to_json(seed, primary, network):
    return json.dumps(_payload(seed, primary, network), indent=2)


def to_markdown(seed, primary, network):
    lines = [f"# nymric mosaic for {seed}", ""]
    for title, rows in (("primary accounts", primary), ("associated accounts", network)):
        lines += [f"## {title}", ""]
        if not rows:
            lines += ["_none_", ""]
            continue
        lines += ["| site | handle | url | confidence | why |", "|---|---|---|---|---|"]
        lines += [f"| {a.platform} | {a.handle} | {a.url} | {a.confidence} | {'; '.join(a.reasons)} |"
                  for a in rows]
        lines.append("")
    return "\n".join(lines)
