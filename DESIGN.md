# design notes

how nymric works, and why it's built this way. the decisions matter more than the code,
so they're written down.

## the pipeline

```
seed -> probe every site -> pull bio links -> stitch the mosaic -> show it
                                  ^
                email seed -> gravatar (resolves to a username first)
```

one small file per step. `probe` (does the handle exist?), `links` (what other handles
does the profile point at?), `faces` (do the avatars match?), `stitch` (put it together
with a confidence), `show` (render), `mailto` (email to gravatar to username). sites live
as data in `sites.json`, so coverage is a config change, never a code change.

## detecting existence

two methods, both unauthenticated.

status sites are judged on 200 vs 404, which is clean when a site bothers to 404. text
sites return 200 for everything, so we match a marker instead: `found` is a string only
real profiles contain (hacker news has `karma:`), and `absent` is the not-found string, so
the profile exists when that string is missing (steam's "could not be found").

the rule that matters: 403, 429 and 5xx are inconclusive, never "missing". an anti-bot
block is not evidence the account is absent. this is the single biggest source of junk in
existence tools that don't draw the distinction, and it's why reddit got cut. its edge
returns byte-identical 403s for real and fake users when you aren't logged in, so there is
no honest way to check it unauthenticated.

## three ways it correlates

existence is the boring part. the point is deciding which accounts are the same person.

bio links come first. fetch a found profile, pull the outbound handles it advertises, and
if two accounts point at each other (or both at a third we already found) that's a link.
the extractor is strict on purpose: it drops same-platform self links, reserved and brand
words, asset files, and anything that isn't a bare profile path, because a github page
linking to `github.com/features` is chrome, not a person.

avatars come second. perceptual-hash (a 64-bit dhash) each profile picture and compare
across platforms. a near-identical match (hamming distance 6 or less) is a same-person
signal even when no bio connects them. comparing only across different sites, plus a tight
threshold, plus dropping near-flat images, keeps a platform's default avatar from forging a
match.

email is the third door in. an email seed is md5-hashed and looked up against gravatar's
public profile json, and its `preferredUsername` becomes the handle everything else runs
on. gravatar, not holehe-style password-reset probing, because reset-abuse would
contradict the project's own ethics.

## confidence

confirmed means a bio cross-link or an avatar match ties it to another found account.
likely means an associated account two or more bios point at. possible means it exists but
nothing corroborates it, and it's called out as a maybe-namesake rather than sold as a sure
thing, because usernames aren't unique.

every edge carries the reason it exists ("cross-linked from devto, keybase", "same avatar
as mastodon"), so the score is auditable instead of a black box. no ai in the core path.

## why curated, not 3000 sites

big lists rot. they quietly pile up broken detectors and false positives. the 21 sites
here were each probed with a real handle and a fake one before shipping, and the ones that
couldn't cleanly tell the two apart were cut. quality over coverage is the feature, and the
data-driven design means the list can grow the same careful way.

## concurrency

one shared httpx client, a bounded semaphore (default 10) so it stays polite, and honest
handling of redirects and timeouts. avatar fetches ride the same client. it's fast because
it queries a curated set, not because it hammers anyone.

## limits and what's next

markers break when a site redesigns, but they're data so the fix is one line. avatar
matching needs the optional pillow extra and falls back to bio-links-only without it. next
on the list: per-detector freshness hints, an avatar cache, a graphviz export of the
mosaic, and a config file for custom site sets.
