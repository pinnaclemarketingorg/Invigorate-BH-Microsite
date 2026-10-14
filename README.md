# Invigorate Behavioral Health — landing pages

One template, four landing pages. Same content and section order as the
original `/lpc/`; new visual execution, markup and tracking.

| Variant | Replaces | Tracking number | Dynamic insertion |
| --- | --- | --- | --- |
| `home` | homepage (indexable) | (888) 891-2240 | — |
| `lpc` | `/lpc/` | (888) 891-2240 | — |
| `lpc-dli` | `/lpc-dli/` | (888) 891-2240 | state, from IP |
| `lpc-dki` | `/lpc-dki/` | (888) 891-2240 | `?area=` parameter |
| `bing-lpc` | `/bing-lpc/` | **(888) 277-6026** | — |

## Build

```
python src/build.py
```

Edit `src/template.html` — **never** the generated output.

| Path | What it is |
| --- | --- |
| `src/template.html` | source of truth — markup, CSS, JS |
| `src/build.py` | variants, image inlining, carrier logo sizing |
| `src/assets/`, `src/assets/carriers/` | photography, logo, seals, carrier logos |
| `site/<slug>/index.html` | **deployed** — standalone documents, served at `https://help.invigoratebh.com/<slug>/` |
| `preview/*.html`, `index.html` | review copies (see Live vs preview) |

`site/` pages are complete HTML documents: GTM in `<head>`, the GTM `<noscript>`
immediately after `<body>`, LegitScript served from LegitScript's own domain,
canonical and description per variant, `noindex` while they are staging. Every
image is an inlined WebP data URI, so each page is one ~630 KB file with no
external requests except Google Fonts, GTM and the LegitScript seal.

## Two designs

`design` on each variant picks the layout. One template serves both: blocks are
fenced with `<!--C:start--> … <!--C:end-->` and `<!--D:start--> … <!--D:end-->`,
and `strip_designs()` unwraps the matching fences and deletes the rest, so
neither design ships the other's markup.

**C** — `home`, `lpc`, `lpc-dli`, `lpc-dki`, `bing-lpc`.

**D** — `lpd`, `lpd-dli`, `lpd-dki`, `bing-lpd`. Same content, reworked:

- Hero closes on the Google rating badge rather than a plain reassurance line.
- "You are not the first" is a photograph carrying a pulled review line, headed
  *Recovery isn't just possible. It happens here, every day.* (the pull-quote
  that repeated this further down is gone).
- Levels of care each open a **What to expect** dialog — four specifics and a
  benefits check. Still three cards.
- Reviews are static until touched, in a much shorter section: one header row,
  and the AI summary sits **in** the rail as a card on brand colour so it reads
  as a summary rather than somebody's testimonial. Single pass, 26 cards.
- FAQ is 35/65, prompts left (sticky) and answers right.

## Variants

`VARIANTS` in `src/build.py` drives everything. Each entry sets the tracking
number, the dynamic-insertion mode and the meta description; the build
substitutes the number into all nine places it appears (display text, `tel:`
links, and the number handed to CTM) so the variants cannot drift apart.

### Dynamic insertion

Both modes write with `textContent` and only ever **replace** copy that is
already in the HTML, so the page is complete before any of this runs and stays
complete if it fails. Fallback is always `Admissions Available Today`.

Both render into the hero pill as `{Place} Admissions Available Today`, and
fall back to plain `Admissions Available Today` when nothing resolves.

**`lpc-dki`** reads `?area=`. Values are stripped to letters, spaces, hyphens
and apostrophes, limited to 2–38 characters and 5 words, then title-cased:

```
?area=round+rock  ->  "Round Rock Admissions Available Today"
?area=            ->  "Admissions Available Today"
```

> **Set `DKI_ALLOW` before running ads.** `?area=` is attacker-controllable —
> anyone can send traffic to `?area=<anything>` and have it render on a page
> carrying your branding. Sanitising stops script injection, it does not stop
> someone putting an embarrassing phrase in your headline. Fill `DKI_ALLOW` in
> `src/template.html` with the areas your ads actually use; anything not on the
> list falls back to the default copy. While it is empty, any sanitised value
> renders.

**`lpc-dli`** resolves the visitor's state from their IP via IPinfo — the same
endpoint and token as the current `/lpc-dli/` page, reading `data.region`. The
result is cached in `sessionStorage`, the request gives up after 2.5s, and any
failure falls back silently:

```
"Florida Admissions Available Today"  /  "Admissions Available Today"
```

## Reviews

`REVIEWS` in `src/build.py` holds the Google reviews as `(name, stars, text)`,
a curated selection from a profile averaging 4.8. The build renders the list
twice into a single horizontal rail so it can wrap seamlessly mid-scroll, which
is why the page contains twice as many cards as reviews.

Running order is set by `REVIEW_ORDER`, strongest first — ranked on concrete
specifics, a clear before/after, and unusual detail, with generic superlatives
at the back. A review not named in that list keeps its place at the end and the
build says so.

Reviews run from two lines to several paragraphs, so cards clamp to 9 lines to
hold one row height. Anything actually cut off gets a **Read more** that expands
it in place and pauses the drift — nothing is permanently hidden.

The rail drifts at ~25px/s but is a real scroll container — wheel, drag, touch
and keyboard all work, and the drift yields the moment anyone touches it and
resumes about 2 seconds after they stop. It does not auto-scroll at all under
`prefers-reduced-motion`.

The narrative block beside the rating is labelled **AI summary of Google
reviews** with a footnote saying it was written by AI rather than by Invigorate.
It reads as a synthesis of the reviews, so it should not be presented as the
provider's own claim.

## Carrier logos

`CARRIERS` in `src/build.py` lists the nine carriers named in the page copy. A
missing file degrades to a text chip rather than a gap.

Logos are **not** sized to a uniform height — these lockups run from ~1.7:1
(Cigna, stacked) to ~5.2:1 (Aetna, wordmark), and one height makes the compact
marks look tiny beside the wide ones. Height holds roughly constant optical
area: `height = LOGO_K / sqrt(aspect)`, clamped 24–42px. Tune `LOGO_K` to scale
the row. Each is encoded at ~2.6x its display height to stay crisp on retina.

## Tracking

**GTM `GTM-PHZHNGJ6`** carries GA4, Google Ads and Microsoft Clarity. Two
`dataLayer` events are pushed for conversion tracking:

- `generate_lead` — on successful submit, with `form_name` and `variant`
  (`lpc`, `lpc-dli`, `lpc-dki`, `bing-lpc`) so each page reports separately
- `call_click` — on any `tel:` click, with `link_location` set to `header`,
  `sticky_bar`, `closing_cta` or `body`

**CallTrackingMetrics FormReactor** (account 374183, FormReactor
`FRT472…C42561`). The form takes CTM's own embed API when it is available:

```js
__ctm.form.track('app.calltrackingmetrics.com', FRT, '8888912240', {
  country_code: '1', name, phone, custom: { … }
});
```

This is preferred because it ties the lead to the visitor's CTM session, so the
tracking number, referrer and keyword data stitch together on CTM's side.
**It needs the standard CTM embed script on the page** — add it through GTM,
since the container is already there. Until then the form falls back to a direct
REST post to the FormReactor endpoint, which records the lead but carries only
the attribution passed explicitly. Both paths are wired and tested.

Field mapping (identical on both paths):

| Form field | CTM |
| --- | --- |
| phone | `phone`, country code `1` (REST: `phone_number=+1XXXXXXXXXX`) |
| first + last | `name` and `custom.patient_name` |
| date of birth | `custom.date_of_birth` (`MM/DD/YYYY`) |
| insurance provider | `custom.insurance` |
| member ID | `custom.policy_id` |
| — | `custom.landing_page` (first-touch URL, full query string) |
| — | `custom.utm_source` |
| — | REST only: `paid_attribution[gclid|campaign_id|adgroup_id|creative_id]` |

`custom.looking_for` is not sent — the form does not ask it.

Attribution is captured on the first pageview into `sessionStorage`, so a
visitor who scrolls around and opens the FAQ still posts the click IDs they
arrived with. `gclid` also accepts `wbraid` / `gbraid`; campaign, adgroup and
creative read Google's ValueTrack names first and fall back to `utm_*`.

### Live vs preview

The form only posts from `invigoratebh.com`. Anywhere else it validates, shows
the success state and sends nothing. The visible "Preview mode" note has been
removed, so this is now silent — the gate itself remains, and is what stops a
design review from firing real leads into CTM. `site/` builds have the switcher stripped entirely.

## Before going live

- [ ] **Add the CTM embed script via GTM** so `__ctm.form.track` is used instead
      of the REST fallback.
- [ ] **Confirm the REST fallback's CORS** with one real post from
      `help.invigoratebh.com`, in case the embed script is not present. On failure
      the form shows an error pointing at the phone number — it never reports a
      false success.
- [ ] **Fill `DKI_ALLOW`** before sending traffic to `lpc-dki`.
- [ ] Swap the facility photography. Two gallery images are the same file, and
      the "Wellness Amenities" and "Dining Areas" captions sit over what are
      clearly living-room shots.

## Notes

- Single-theme by design (light) — a brand marketing page should render the same
  regardless of the viewer's OS theme.
- Type: Newsreader (display) + Manrope (body), both Google Fonts.
- Palette derived from the logo — `--teal: #0d5c63`, leaf green `#8ac302` used
  only as a small accent.
- The FormReactor key is public by design and only accepts posts into this one
  form. If spam leads appear, CTM's form spam filtering is where to look.

## Deploy

Hosted on Cloudways (Custom PHP app) at `help.invigoratebh.com`, deployed from
`git@github.com:pinnaclemarketingorg/Invigorate-BH-Microsite.git` (`main`).
Cloudways pulls the whole repo into `public_html`; the app's **Webroot** is set
to `public_html/site` so only the built pages are public — `src/`, `preview/`
and this README are not served.

1. Edit `src/template.html` (or `VARIANTS` in `src/build.py`)
2. `python src/build.py`
3. Commit **including `site/`** — Cloudways has no build step
4. Push, then **Deployment via Git → Pull** in Cloudways
