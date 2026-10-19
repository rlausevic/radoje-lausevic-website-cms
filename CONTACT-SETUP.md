# Contact: activation on Cloudflare

Recipient: the owner-approved Gmail plus address, stored privately as encrypted `CONTACT_RECIPIENT`. Do not put this address in public source files.
Sender: `website@radojelausevic.com`.
The visitor's address is used only as Reply-To. The form cannot choose recipients.

## Published code

- Pages: `/functions/api/contact.js` and `contact-config.js`.
- Workers: `worker/index.mjs`, static assets from `dist`, API routes handled first.
- Both use `server/contact.mjs`; the public configuration endpoint never exposes secrets.
- Until the EMAIL binding and live Turnstile keys exist, the endpoint returns unavailable and the UI offers the email link. No message is falsely marked as sent.

## Account activation (required before real sending)

1. Cloudflare Email Service: add and verify destination the owner-approved Gmail plus address. Open Cloudflare's verification email in Gmail and confirm the exact alias.
2. Onboard `radojelausevic.com` as the sending domain. Review authentication DNS records Cloudflare requires. Preserve existing MX records for any current mailbox provider; use a sending subdomain instead if needed, and update SENDER in server/contact.mjs accordingly. This is independent of the registrar transfer.
3. Create a Turnstile widget for `radojelausevic.com`, `www.radojelausevic.com`, and `radoje-lausevic-website-cms.pages.dev`. Store the public key as `TURNSTILE_SITE_KEY` and the secret as encrypted `TURNSTILE_SECRET_KEY` in the environment actually serving the domain. Do not commit the secret. Production rejects known Turnstile test-key prefixes.
4. Bind Cloudflare Email Service as `EMAIL`, with the recipient fixed privately in `CONTACT_RECIPIENT`. Browser input cannot select or override it. For **Workers**, add this top-level property in wrangler.jsonc after verification, then deploy:
   ```json
   "send_email": [{"name":"EMAIL"}]
   ```
   Set encrypted `CONTACT_RECIPIENT` and the two Turnstile environment values on that Worker. `keep_vars` preserves dashboard variables; encrypted secrets stay outside git. `CONTACT_RATE_LIMITER` is configured at 5 attempts per minute per client IP per location. No external API key is needed.
5. For **Pages**, configure the same `EMAIL` binding, encrypted `CONTACT_RECIPIENT` and Turnstile keys on the Pages project production environment, then redeploy. Worker configuration does not apply to Pages. Where a rate-limit binding is available, use `CONTACT_RATE_LIMITER`; otherwise an in-memory per-isolate attempt limiter supplements mandatory Turnstile validation. It is best-effort, not an exact account-wide quota. For stricter limits, add a Cloudflare rate limit rule for POST `/api/contact`.

## Verification

- GET `/api/contact-config` must return `enabled:true` and only the public site key.
- Submit a clearly labelled test inquiry from Contact, confirm Gmail receipt and correct Reply-To. Success means the email service accepted the message, not a guarantee of inbox placement.
- Test expired security check, server failure and network failure. Fields must remain populated on failure. The UI prevents parallel submissions; no automatic resend happens after a timeout because the first message may already have been accepted.
- Check the same on the custom domain and Pages URL if both are used.
- Tests: `node --test tests/contact*.test.mjs`; site tests: `python3 -m unittest test_cms.py test_archives.py test_navigation.py test_projects.py test_bibliography.py test_video.py`.
- The server logs no message contents, email addresses, tokens or raw service errors. No database of inquiries is created.
