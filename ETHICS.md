# ethics and scope

nymric builds a map of someone's public footprint. that's genuinely useful for checking
your own exposure, brand and impersonation monitoring, or authorized research. it's also
the exact shape of thing that helps a stalker. so, a few ground rules, and they're not
decoration.

public data only. it reads pages and public apis anyone can open in a browser. no logins,
no auth, nothing behind an access control, no password-reset probing. if a site needs you
signed in to see something, nymric doesn't touch it. email seeds go through gravatar's
public profile api and nothing else.

a match is a lead, not a verdict. the same handle on two sites is not proof of the same
human. results carry a confidence and a reason on purpose. don't publish or act on a "same
person" guess you haven't verified, because being wrong hurts an innocent bystander.

be polite. concurrency is low by default, and 403 / 429 / 5xx are treated as inconclusive,
never as "this account doesn't exist". don't crank the knobs to hammer a service. slow is
sustainable.

no harassment, stalking, doxxing, or intimidation. don't run this on a private person
without a lawful, consented, or authorized basis, and don't use it to build a target
package for someone else to do the same.

keep little. it stores nothing by default. if you export a report, treat it as sensitive
personal data. encrypt it, scope who can read it, delete it when you're done.

the law still applies to public data. gdpr, ccpa, and computer-misuse, anti-stalking, and
harassment statutes don't stop mattering just because the data was public. when in doubt,
get authorization in writing or don't run the query.

provided for lawful research only, with no warranty. you're responsible for how you use it.
