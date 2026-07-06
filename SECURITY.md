# security

## reporting

if you find a security issue in nymric itself (not in a site it queries), please don't
open a public issue. use github's private "report a vulnerability" flow, and give it a few
days before disclosing. i'll credit you unless you'd rather stay anonymous.

## in scope

nymric only reads public data. no auth, nothing behind an access control, no
password-reset probing (see [ETHICS.md](ETHICS.md)). worth flagging:

- an ssrf-style bug where a crafted bio link makes the tool fetch somewhere it shouldn't
- a site module that reaches a private or authenticated endpoint
- anything that lets it be pointed at a target harder than the polite defaults allow

## not in scope

- a site changing its markup so a detector goes stale. that's a normal bug, open a pr.
- a queried site rate-limiting or blocking you. expected, don't work around it.
