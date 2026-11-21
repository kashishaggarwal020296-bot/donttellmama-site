# Handoff — Koramangala Outlet Rollout

## Goal

Don't Tell Mama opened a second outlet in Koramangala (71-72, Jyoti Nivas
College Rd, 5th Block, Bengaluru 560095). The task: restructure
donttellmama.in from a single-location site into a multi-location site that
includes the new outlet — while keeping the existing HSR Layout content,
blog, and food menu intact — without fabricating anything (photos, weekly
events, exact club menu) that doesn't exist yet.

Repo: `https://github.com/kashishaggarwal020296-bot/donttellmama-site`
Branch: `main` (this project pushes directly to main, no PR workflow)

## What's done

1. **Location switcher** added to every shared page's header (`index.html`,
   `the-commons.html`, `food-menu.html`, `templates/layout.html` which the
   blog is generated from) — a small "HSR Layout / Koramangala" toggle next
   to the logo, wrapped in a new `.brand-group` div so it doesn't disturb
   the existing `justify-content:space-between` header layout.
2. **`koramangala.html`** — new outlet homepage (cloned from `index.html`,
   then heavily edited). Covers:
   - 6th-floor Rooftop (same food menu as HSR — confirmed by the client)
     and 5th-floor Club (shorter food menu, no smoke-effect cocktails).
   - Real address, phone (+91 87925 11311), hours (12 PM–1 AM, same as HSR).
   - Honest placeholders where real content doesn't exist yet: a gradient
     hero background (no photos yet), a "Photos On The Way" gallery
     section, and a "weekly line-up being finalised" note instead of
     invented events.
   - JSON-LD updated with Koramangala's own BarOrPub/NightClub schema (no
     fabricated recurring-events graph, no guessed geo-coordinates).
3. **`koramangala-club.html`** — the Club's own page (cloned from
   `the-commons.html`, the HSR private-events page). Differs from Commons
   in one key way: the client said the Club needs to support **both**
   walk-ins and private-event bookings, so this page has:
   - A "Just here for the night?" walk-in strip near the top with a
     Reserve-a-Table CTA.
   - The private-event enquiry form further down (same structure as
     Commons), with a venue dropdown for "The Club" vs. "Rooftop Buyout"
     (both Koramangala floors).
   - Submissions include a `location: "Koramangala"` field in the JSON
     payload sent to the Apps Script backend, so routing logic can use it
     later (see Remaining Steps #2).
4. **`sitemap.xml`** updated with both new URLs.
5. All of the above committed and pushed to `main` (commit `abd8935`,
   "Add Koramangala outlet: location switcher, outlet page, Club page").

## Current state of the files

- `index.html`, `the-commons.html`, `food-menu.html`,
  `templates/layout.html` — unchanged except for the added
  `.brand-group`/`.loc-switch` header markup and matching CSS. All other
  content is untouched HSR content.
- `blog/*.html` — regenerated via `python3 scripts/build_blog.py` after
  `templates/layout.html` changed (blog pages are generated, not
  hand-edited — **always rebuild after touching the template**).
- `koramangala.html` — new file, ~1400 lines, same CSS framework/fonts as
  `index.html` (same `--green`/`--gold`/`--cream` custom properties, same
  Montserrat/Cormorant Garamond font-faces).
- `koramangala-club.html` — new file, ~1030 lines, same CSS framework as
  `the-commons.html`.
- `CONFIG` objects in both new pages' inline `<script>` blocks are already
  set to Koramangala's real phone/WhatsApp/address/maps URL. `GA4_ID` is
  the same measurement ID used site-wide.
- The Apps Script enquiry backend (`apps-script/CommonsEnquiries.gs`) is
  **unchanged** — both the HSR Commons form and the new Koramangala Club
  form currently POST to the same endpoint
  (`CONFIG.COMMONS_FORM_ENDPOINT`). The Club form just adds a `location`
  field to the payload that the script doesn't yet read.

## Decisions made and why

These came from the client via direct Q&A in the prior session — treat them
as settled, not open questions:

- **Site structure**: one shared brand (nav pattern, footer, blog, food
  menu where shared) + a lightweight location switcher + dedicated
  per-outlet pages — not fully separate mini-sites. Client's explicit pick
  ("Simple location switcher").
- **Weekly events**: not decided yet by the client. Do **not** invent a
  schedule — the site currently shows "line-up being finalised, follow
  Instagram" and should keep saying that until the client supplies real
  programming.
- **Floors**: Koramangala is 2 floors — 6th floor Rooftop (same vibe/menu
  as HSR), 5th floor "the Club" (no separate brand name — client was
  explicit: "its called the club, no separate brand name").
- **Food/drinks**: rooftop menu is fully shared with HSR. Club has a
  shorter food menu and deliberately avoids smoke-effect cocktails (e.g.
  no Smoke Signal-style drinks on the club list) — client's words: "we are
  avoiding the smoke and other extra effects on cocktails."
- **Club bookability**: both walk-ins AND private event bookings — this is
  why `koramangala-club.html` has both a walk-in strip and a private-event
  enquiry form, unlike `the-commons.html` which is private-events-only.
- **Brand framing**: client said "decide on your own" — chose "new
  location, same heritage brand" (lean on "Since 2010" trust while being
  honest this specific outlet is new).
- **No fabrication policy**: explicitly agreed with the client — no fake
  address/phone/hours, no reused HSR photos mislabeled as Koramangala's, no
  invented weekly events or exact club menu items. Everything missing is a
  clearly-marked placeholder, never a guess dressed up as fact.
- **Capacity numbers**: the Club's exact guest capacity was never given, so
  `koramangala-club.html` deliberately avoids stating a number (unlike
  Commons, which states "100 guests" because that number was confirmed).
  Don't add one without client confirmation.
- **Instagram handle**: both new pages currently link to the existing
  `@donttellmama_hsr` handle — this was an **assumption**, not confirmed by
  the client. Worth double-checking before this goes live if a separate
  Koramangala handle exists or gets created.

## Remaining steps, in order

1. **Photos** — client said "I'll need a few days." Both new pages use
   honest placeholders (`hero-bg-placeholder` gradient and a "Photos On The
   Way" gallery section on `koramangala.html`; empty `<image-slot>`
   components on `koramangala-club.html`, which supports drag-and-drop
   fill once real images exist — see `assets/6ed898ba-....js` for how that
   component works). Once photos arrive: replace the hero placeholder with
   a real photo/video (follow `index.html`'s hero pattern), fill the
   gallery, and fill the `<image-slot>` elements on the Club page.
2. **CRM/enquiry routing** — client wants: "customers can select which
   venue they are looking for and then mail can either go to marketing or
   to that respective venue email id." The frontend already sends a
   `location` field; `apps-script/CommonsEnquiries.gs` needs to be updated
   to read it and route the alert email accordingly. **Blocked on the
   client providing the actual Koramangala contact email** — until then,
   keep routing everything to the existing marketing/alert address (with
   venue/location visible in the subject or sheet row so nothing is lost).
3. **Weekly programming** — once the client locks in Koramangala's weekly
   nights, replace the "being finalised" note in `koramangala.html`'s
   `#floors` section with real content (same pattern as HSR's event-night
   cards, which were removed from this page, not hidden — look at
   `index.html`'s `.week` section for the card markup to reuse).
4. **Exact Club menu/cocktail list** — currently described qualitatively
   ("shorter bites menu," "no smoke-effect cocktails") rather than
   itemized, since no exact list was provided. Add a real menu/PDF link
   once available.
5. **Confirm Instagram handle** — verify `@donttellmama_hsr` is correct for
   Koramangala too, or get a separate handle if one exists.
6. Re-test both pages after any content changes (see Gotchas below for the
   verification method that works in this sandboxed environment).

## Gotchas

- **No live network access to donttellmama.in or Google Maps tiles** in
  this sandbox — direct `WebFetch`/`curl` to the live site fails with DNS
  resolution errors, and the Google Maps iframe embed shows a broken-image
  icon locally. This is expected sandbox behavior, not a bug — the embed
  URLs are correctly formed (verified by inspecting the `src` attribute
  directly) and will render fine once deployed. To verify changes, serve
  the repo locally (`python3 -m http.server <port>`) and use Playwright
  (`/opt/pw-browsers/chromium`) against `localhost`, not the real domain.
- **Blog pages are generated, not hand-edited.** If you touch
  `templates/layout.html`, you must rerun
  `python3 scripts/build_blog.py` from the repo root afterward, or the
  live blog pages will silently drift out of sync with the template
  (header/footer/location switcher won't match).
- **Flexbox header risk**: `.bar` uses `justify-content:space-between`
  across 3 children (brand group / nav / reserve button). Any new header
  element must go *inside* one of those three groups (e.g. inside
  `.brand-group`), never added as a new direct sibling of `.bar`, or the
  whole header's spacing breaks.
- **Image-slot component**: `<image-slot>` (used throughout
  `the-commons.html`/`koramangala-club.html`) is a custom element with
  drag-and-drop fill + an `.image-slots.state.json` persistence sidecar
  (see `assets/6ed898ba-....js`). It gracefully shows a clean empty
  placeholder when no image is set — this is the intended, already-built
  mechanism for "add the photo later," so prefer it over hand-rolled CSS
  gradients for any new photo slot (the home/Koramangala hero uses a plain
  CSS gradient instead, because that hero slot is driven by a
  video/photo-pair mechanism that predates `image-slot`, not because
  `image-slot` wouldn't work there).
- **CONFIG object is per-page**, not shared via import — each HTML file
  has its own inline `CONFIG = {...}` JS object (WhatsApp/phone/maps
  URL/GA4 ID/etc). When copying a page as a template for a new one, always
  update this object — it's easy to miss and ship a page that silently
  points at the wrong outlet's phone number (this happened once during
  this build and was caught via `grep` for the old number before
  shipping).
- **Git**: this repo pushes straight to `main`, no PR step, no CI gate
  blocking merges (there is a separate GitHub Action that rebuilds the
  blog on push to `blog-content/`, unrelated to this work). Direct
  `git push` has worked reliably in recent sessions; if it's ever rejected
  with a 403, the established fallback in earlier sessions was a
  zip-and-manual-GitHub-upload workflow — ask the user before reaching for
  that.
