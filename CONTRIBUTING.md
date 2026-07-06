# contributing

prs welcome. keep them small. the whole point is that the tool stays readable in one
sitting.

## adding a site

sites are data, not code. drop an object into [nymric/data/sites.json](nymric/data/sites.json):

```json
{"name": "example", "url": "https://example.com/{}", "method": "status", "links": true}
```

`method: status` is judged on 200 vs 404. `method: text` needs a `found` marker (a string
only real profiles contain) or an `absent` marker (the not-found string, for sites that
200 either way). a `{}` in a marker gets the handle. set `links: true` if the profile is
worth scraping for outbound handles.

rules for a new site:

- public data only. no logins, no auth, nothing meant to be private.
- respect the site's tos and rate limits. conservative by default.
- prefer a clean 200/404 split. only reach for a text marker when you have to, and say why.
- 403, 429 and 5xx are inconclusive, never "missing".
- check it by hand before you open the pr: one real account, one random string, and paste
  what you saw.

## what won't get merged

anything that turns this into a target-package generator. block or anti-bot evasion,
private-data access, scraping behind auth, or bulk "find everyone" features. see
[ETHICS.md](ETHICS.md), it isn't decoration.

## dev

```
pip install -e ".[dev,avatars]"
pre-commit install
ruff check .
mypy nymric
pytest
```
