"""Build index.html: inline every image from src/assets as an optimized WebP data URI.

    python src/build.py

Run from the project root. Edit src/template.html, never index.html.
"""
import base64
import io
import math
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
ASSETS = os.path.join(SRC, "assets")

# token -> (source file, max width, webp quality)
SPEC = {
    "hero":     ("inv_img1.jpg",            1800, 76),
    "heroM":    ("inv_img1m.jpg",            900, 74),
    "care1":    ("inv_img2.jpg",             640, 80),
    "care2":    ("inv_img3.jpg",             640, 80),
    "care3":    ("inv_img4.jpg",             640, 80),
    "hands":    ("inv_img8.jpg",             900, 76),
    "facility": ("inv_img9.jpg",            1500, 70),
    "g1":       ("img6_gallery1_pmax2.jpg",  780, 78),
    "g2":       ("img7_gallery2_pmax2.jpg",  780, 78),
    "g3":       ("img8_gallery32_pmax2.jpg", 780, 78),
    "g4":       ("img9_gallery4_pmax2.jpg",  780, 78),
    "g5":       ("img10_gallery5_pmax2.jpg", 780, 78),
    "logo":     ("logo.jpg",                 440, 90),
    "logoW":    ("inv_img10.png",            300, 92),
    "jcaho":    ("jcaho.webp",               180, 92),
    "legitscript": ("legitscript.png",       220, 92),
}

# Insurance carriers named in the page copy, in display order.
# Drop a logo into src/assets/carriers/<file>; a missing file falls back to a
# text chip so the row never renders a gap.
CARRIERS = [
    ("Anthem",   "Anthem.png"),
    ("Aetna",    "Aetna.png"),
    ("BCBS",     "BCBS.png"),
    ("Carelon",  "carelon behavioral health logo.png"),
    ("Cigna",    "cigna.png"),
    ("Magellan", "magellan health.png"),
    ("Surest",   "surest.png"),
    ("UHC",      "uhc.png"),
    ("UMR",      "umr-insurance-logo.png"),
]
CARRIER_DIR = os.path.join(ASSETS, "carriers")

# These lockups range from ~1.7:1 (Cigna, stacked) to ~5.2:1 (Aetna, wordmark).
# Sizing them all to one height makes the square marks look tiny next to the
# wide ones, so height is set to hold roughly constant optical AREA instead:
# area = aspect x height^2, so height = K / sqrt(aspect). K is tuned so a
# typical 4:1 wordmark lands at 30px.
LOGO_K = 60.0
LOGO_MIN, LOGO_MAX = 24, 42


def logo_height(width, height):
    aspect = width / float(height)
    return int(max(LOGO_MIN, min(LOGO_MAX, round(LOGO_K / math.sqrt(aspect)))))


def encode_logo(filename, display_height, quality=88):
    """Encode at ~2.6x the display height so it stays crisp on retina."""
    im = Image.open(os.path.join(CARRIER_DIR, filename))
    if im.mode != "RGBA":
        im = im.convert("RGBA")          # keeps transparency; these sit on white
    target_h = min(im.height, int(display_height * 2.6))
    if target_h < im.height:
        im = im.resize((max(1, round(im.width * target_h / im.height)), target_h),
                       Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    raw = buf.getvalue()
    return "data:image/webp;base64," + base64.b64encode(raw).decode(), len(raw), im.size


def carrier_strip():
    """Render the carrier row: logos where we have them, text chips where we don't."""
    cells, found, total = [], 0, 0
    for name, filename in CARRIERS:
        path = os.path.join(CARRIER_DIR, filename)
        if not os.path.exists(path):
            cells.append('<span class="carrier carrier--text">%s</span>' % name)
            continue
        with Image.open(path) as probe:
            h = logo_height(probe.width, probe.height)
        uri, size, dims = encode_logo(filename, h)
        total += size
        found += 1
        print("  %-9s %-34s %dpx tall  %5.1f KB" % (name, filename, h, size / 1024))
        cells.append(
            '<span class="carrier"><img src="%s" alt="%s" style="--h:%dpx" loading="lazy"></span>'
            % (uri, name, h)
        )
    print("carriers %d of %d logos, %.1f KB raw" % (found, len(CARRIERS), total / 1024))
    missing = [f for _, f in CARRIERS if not os.path.exists(os.path.join(CARRIER_DIR, f))]
    if missing:
        print("         missing: %s" % ", ".join(missing))
    return "\n      ".join(cells)


def encode(filename, width, quality):
    im = Image.open(os.path.join(ASSETS, filename))
    if im.mode == "P":
        im = im.convert("RGBA")
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=quality, method=6)
    raw = buf.getvalue()
    return "data:image/webp;base64," + base64.b64encode(raw).decode(), len(raw)


# --------------------------------------------------------------------------
# Landing page variants. One template, four pages.
# --------------------------------------------------------------------------
CTM_FRT = "FRT472ABB2C5B9B141AA1D47C9406B9291393156F273CE48E0DCD60EFC245C42561"
CTM_KEY = "ZGqlN1PcmOHHscx_x5U8kGU8ZJmZfN5str-gtzy1VcqnE0O6"
GTM_ID = "GTM-PHZHNGJ6"
LEGITSCRIPT_URL = "https://static.legitscript.com/seals/25550278.png"
SITE_HOST = "help.invigoratebh.com"

VARIANTS = [
    {
        "id": "lpc", "slug": "lpc", "label": "lpc",
        "phone": "8888912240", "dyn": "none",
        "title": "Invigorate Behavioral Health",
        "desc": "Dual-diagnosis addiction treatment with same-day admissions. "
                "Detox, residential and outpatient care. Call (888) 891-2240.",
    },
    {
        "id": "lpc-dli", "slug": "lpc-dli", "label": "lpc-dli",
        "phone": "8888912240", "dyn": "dli",
        "title": "Invigorate Behavioral Health",
        "desc": "Dual-diagnosis addiction treatment with same-day admissions, "
                "wherever you are. Call (888) 891-2240.",
    },
    {
        "id": "lpc-dki", "slug": "lpc-dki", "label": "lpc-dki",
        "phone": "8888912240", "dyn": "dki",
        "title": "Invigorate Behavioral Health",
        "desc": "Dual-diagnosis addiction treatment with same-day admissions. "
                "Detox, residential and outpatient care. Call (888) 891-2240.",
    },
    {
        "id": "bing-lpc", "slug": "bing-lpc", "label": "bing-lpc",
        "phone": "8882776026", "dyn": "none",
        "title": "Invigorate Behavioral Health",
        "desc": "Dual-diagnosis addiction treatment with same-day admissions. "
                "Detox, residential and outpatient care. Call (888) 277-6026.",
    },
]


def pretty_phone(raw):
    return "(%s) %s-%s" % (raw[0:3], raw[3:6], raw[6:10])


# --------------------------------------------------------------------------
# Google review rail
# --------------------------------------------------------------------------
STAR_D = ("M10 1.7l2.47 5.01 5.53.8-4 3.9.94 5.51L10 14.33 5.06 16.92"
          "l.94-5.51-4-3.9 5.53-.8z")
GOLD = "#FBBC04"

# Verbatim from the client's Google Business Profile. `stars` is per-review so
# an individual rating can be corrected without touching anything else.
# Ordered to alternate long and short so the rail never shows a run of one.
REVIEWS = [
    ("Kailey", 5, "My experience at Invigorate was filled with understanding, love and "
     "compassion. The techs felt like family. Always there to help me navigate any and "
     "all issues. Shane was also a huge advocate for me. He made sure I felt heard and "
     "knew he would make sure it was handled. I’m so grateful to Invigorate for "
     "saving my life."),
    ("Carl", 5, "Invigorate changed my life — without Invigorate I would have lost "
     "my child and work. Truly blessed — 5-star treatment for sure! The staff are a "
     "true testament to this place. Without their support and help, my recovery would "
     "have been so much harder. The family you create while in treatment is truly a "
     "blessing!"),
    ("Jeff", 5, "I had a wonderful experience at Invigorate! Checked in for 30 days of "
     "treatment — I ended up staying for 35. I really didn’t want to leave. The "
     "staff is amazing. I felt safe and learned a lot about myself. The food was great. "
     "I’m excited for my new journey in life."),
    ("Jacob", 5, "It has helped me greatly — this facility has made it easier to "
     "focus on my recovery. The staff here have genuine love and support towards the "
     "clients. If you are feeling afraid to make that decision to come to treatment, "
     "don’t be — they accommodate you. Reassure you that the way you are feeling "
     "are indeed valid. That everything will be alright. It’s a great place to be "
     "— it has helped me start my life all over again."),
    ("Dylon", 5, "Invigorate definitely saved me from a difficult situation. I was down "
     "to literally nothing and finally decided to seek help. Staff immediately took me "
     "in very kindly, also helped me medically as I needed to see a doctor right away. "
     "My time spent there was great — the fellow clients, the staff, food, the "
     "resources. Everything was set up perfectly. Highly recommend this program to "
     "anyone in need."),
    ("Rich", 5, "The program and the staff were outstanding. I was well treated, and my "
     "mental health has improved tremendously. Will certainly recommend to a friend or "
     "family member."),
    ("Taylor", 5, "Stayed for a month in a clean, modern complex in a single with its "
     "own shower and bathroom. Met a welcoming community and became friends with many. "
     "They provide meals and as much groceries as you’ll ever need."),
    ("Joey", 5, "This place changed my life! Don’t know where I would be without it. "
     "The staff are fantastic. Everyone there was very helpful. Highly recommended."),
    ("Antonio", 5, "Great place to reset and start your journey to recovery — as long "
     "as you’re willing to put in the work for yourself. You have to want to change. "
     "And most times in life you have to separate from your comfort zone in order to "
     "elevate."),
    ("Bryan", 5, "Spending two months at Invigorate genuinely changed my life. When I "
     "first arrived, I was overwhelmed, scared, and honestly unsure what my future was "
     "going to look like. Over time, this place became so much more than just a rehab "
     "facility to me. The staff truly cared about me as a person, not just another "
     "client walking through the door. The support, structure, conversations, and "
     "friendships I built there gave me the foundation I needed to finally start over. "
     "I’m still sober today, and I constantly think about how different my life could "
     "look if I hadn’t made the decision to go to treatment. I speak highly of "
     "Invigorate all the time and have specifically referred people there because I "
     "genuinely believe in what they do. I’ll always be grateful for the role they "
     "played in helping me get my life back."),
    ("Chris", 5, "Literally a life saving experience. Great staff, therapists, and "
     "facility. If you are ready and truly want to find peace, reach out to IBH and "
     "begin your recovery journey."),
    ("Lisa", 5, "I can honestly say it was an amazing experience. The care every single "
     "person showed me from the time I got there to the time I left was exceptional. "
     "There wasn’t one moment that I felt like I didn’t matter. I would highly "
     "recommend Invigorate to anyone needing addiction help. If I ever needed a place "
     "to go again, which we never plan on coming back, it would be there. I can’t "
     "thank everyone enough for the life changing help I received."),
    ("Jimmy Mack", 5, "Being at Invigorate was a wonderful experience. The therapists "
     "were very knowledgeable and extremely helpful in my coping with my deep seeded "
     "grief. The techs were very friendly and really supportive in my journey to "
     "sobriety. In every class I gained valuable knowledge and the necessary tools to "
     "maintain my sobriety after leaving. The other clients that were there became good "
     "friends and have been wonderful support after my departure. If you are looking "
     "for, or know someone that needs to recover from any addiction or mental health "
     "issue, I strongly recommend them contacting Invigorate Behavioral Health. It "
     "truly was a great experience in a beautiful facility in an awesome location."),
    ("amirreza", 5, "I only stayed here for one week, just to make sure my body was "
     "completely clean from the medication my doctor had prescribed. I truly want to "
     "thank the whole team for helping me during that week. Now, after one year, I feel "
     "so much better without any medication and my life is in a much better place. I "
     "honestly wish I had come here sooner instead of going to the wrong doctor. Thank "
     "you again for all your help, care, and support."),
    ("Anthony Ball", 5, "Invigorate Behavioral Health truly stands out for the level of "
     "care and compassion they provide. The team is incredibly professional, "
     "knowledgeable, and genuinely committed to helping people improve their mental "
     "health and overall well-being. From the moment you walk in, you feel welcomed, "
     "supported, and respected. Their personalized approach to treatment makes a real "
     "difference, and it’s clear they care deeply about the success and recovery of "
     "every individual they work with. I highly recommend Invigorate Behavioral Health "
     "to anyone looking for a supportive and effective behavioral health program. Also, "
     "huge shout out to Gabe and Teresa! They are amazing workers that made my "
     "experience that much better."),
    ("Dan", 5, "An incredible program with knowledgeable staff and supportive "
     "environment. The team is highly experienced and truly invested in long-term "
     "recovery, not just short-term fixes. The therapy sessions, groups work, and "
     "structure helped me develop discipline, self-awareness, and coping skills that i "
     "use everyday. I walked in feeling lost and left with clarity and confidence. "
     "Highly recommend."),
    ("Marilyn", 5, "Invigorate Behavioral Health truly saved my life. The community and "
     "relationships you build there are something special—connections you’ll carry "
     "with you for the rest of your life. From the moment I arrived, I felt surrounded "
     "by people who genuinely cared and wanted to see me succeed. The staff, especially "
     "the technicians who came to your aid and helped resolve immediate issues, were "
     "fantastic (most of them anyway). What meant the most to me was that many of the "
     "techs had been in recovery themselves. They truly understood where we were coming "
     "from and the struggles that come with it, which made their advice feel authentic, "
     "comforting, and easier to trust. My case manager, in particular, never left me in "
     "the dark and was always there when things became hard. Having someone "
     "consistently present, supportive, and willing to help made a huge difference "
     "during my recovery. The first few days were rough—as I imagine they are at any "
     "facility when you’re trying to fix yourself for the first time—but the staff and "
     "case managers did what they could to support me through intake and detox. They "
     "understood that cleansing your body is already difficult and did not deprive "
     "smokers of nicotine products, something I truly appreciated, especially knowing "
     "some facilities do. That consideration alone made coping easier. Invigorate also "
     "goes out of its way to make sure residents don’t feel like they’re in a prison. "
     "They offer two weekly outings and even cosmetic and salon trips when needed, "
     "helping restore a sense of normalcy, dignity, and hope. If you are ever in need "
     "of help for drug or alcohol dependency, Invigorate Behavioral Health is "
     "absolutely one to strongly consider. Even if it’s far from home, the sun, the "
     "staff, the community, and the facility make it completely worth it."),
    ("Donna", 5, "I don’t know how to describe my experience at Invigorate, nor how to "
     "put into words how much gratitude I feel, without it sounding like a dang paid "
     "advertisement! But I’ll try. These guys are the BEST! I was here a total of 5 "
     "months and it was WONDERFUL. The staff and the therapists and the programming … "
     "didn’t just SAVE my life, they helped me to build a life worth living! I feel so "
     "incredibly blessed that I ended up at Invigorate. I can whole heartedly recommend "
     "this place to anyone who needs help with substance use and/ or mental health. I "
     "am FOREVER grateful!"),
    ("Erika", 5, "Being in this Recovery Center is like winning the lottery. Rosie the "
     "housekeeper is amazing, Geronimo the chef makes delicious, nutritious meals, the "
     "staff is loving, kind and helpful, and the owners are very involved and truly "
     "care about your recovery."),
    ("Koltun", 5, "Invigorate changed my life in 30 days. I loved everything about it. "
     "The groups, the staff, the outings, and all the meetings we went to. 100% "
     "recommend."),
    ("Katie", 5, "This place truly saved my life. I am so thankful for all of the staff "
     "and mentors I’ve met in treatment and I could not ask for more! 10/10 would "
     "recommend."),
    ("Dan", 5, "Greatest place on Earth!!!! Absolutely changed my life, I’m so glad I "
     "picked up the phone and called. All the staff at the facility care about you, "
     "make you feel welcomed, cared for and go out of their way to help you transition "
     "into your next chapter of life. CLEAN. 5 stars isn’t enough, the daily agenda is "
     "there to push you, build you back up from rock bottom and give you the tools you "
     "need to achieve your best life. I love you all, thank you."),
    ("Patrick", 5, "My time at Invigorate Behavioral Health was most definitely a "
     "five-star experience. It was, in fact, life-changing. When I made the initial "
     "call and flew to Invigorate two hours later, I felt cared for. The center staff "
     "and management handled all the details I usually plan for. The only thing I "
     "needed to focus on was my recovery. The recovery doctors, therapists, "
     "psychiatrists, group leaders, and technicians are soulfully skilled. "
     "Participating in their groups and one-on-one sessions always proved helpful and "
     "inward-seeking. The living accommodations were lovely and comfortable, and the "
     "meals were catered. In addition, I made lifelong friendships that I’ll cherish "
     "forever. We took “field trips” to see some of the area’s monuments on several "
     "occasions, which were very enjoyable. What was clear from the moment I made my "
     "first call to the end of my 30 days of treatment was that Invigorate puts YOU "
     "first and tailors your journey to your needs. Make that call to Invigorate "
     "Behavioral Health. It may just save your life, too!"),
    ("Danielle", 5, "I was in the worst part of my addiction when I found this place. "
     "They were so kind and so helpful and very accommodating to any needs I had. I "
     "loved being there and would recommend anyone needing help to go. I would go back "
     "in a heart beat if I needed to."),
    ("robin", 5, "Invigorate is a wonderful place! The best part about this treatment is "
     "not only do you get clean and sober but you also learn the behavior patterns "
     "surrounding the disease! What keeps YOU stuck, what makes YOU crave and especially "
     "YOUR personal signs and triggers that lead you to relapse! I HIGHLY recommend this "
     "excellent recovery and behavioral program! A lot of people don’t understand WHY "
     "they get drunk or high but if you dig deep, listen to the instructors and learn "
     "the behavior behind YOUR personal destructive actions you WILL begin to understand "
     "YOURSELF and get on the road to recovery! The BONUS of all this hard work is that "
     "you get to be YOUR REAL SELF, you’ll begin to understand YOUR good and bad "
     "behaviors which lead YOU to get drunk and/or high and also understand the places "
     "in YOUR life that you stumbled! Best of all, is that this program helps you by "
     "giving you LOTS of understanding, concern, laughter and plenty of LOVE! ❤️"),
    ("Chuck", 5, "Invigorate Behavioral Health literally saved my life. From the moment "
     "I arrived, I felt supported, listened to, and, most importantly, safe. The "
     "facilities are absolutely gorgeous and top-notch—truly a space where healing "
     "feels possible. The staff at Invigorate are incredible beyond words. Each person "
     "I encountered showed such compassion and expertise, and they genuinely cared "
     "about my journey to recovery. I want to give a heartfelt thank-you to Garret, "
     "Marcus, Melissa Darrin, Jim, Jen, Savannah, Risley, Sarah, Shanika, Kassai, "
     "Sydney, and especially Jennifer. These counselors went above and beyond to guide "
     "me through the hardest moments with understanding and encouragement. The food was "
     "excellent, and the sense of community I found there is something I’ll carry with "
     "me forever. I met people who I know will be my friends for life. I cannot "
     "recommend Invigorate enough—it’s truly a place of transformation and hope. Thank "
     "you to everyone at Invigorate for giving me a second chance at life. You’ve made "
     "an impact I’ll never forget!"),
]


def _interleave(reviews, long_at=320):
    """Alternate long and short entries so the rail never shows a run of one
    length. Keeps working as reviews are added, unlike a hand-written order."""
    short = [r for r in reviews if len(r[2]) < long_at]
    tall = [r for r in reviews if len(r[2]) >= long_at]
    out = []
    while short or tall:
        if tall:
            out.append(tall.pop(0))
        if short:
            out.append(short.pop(0))
    return out


REVIEWS = _interleave(REVIEWS)

AVATARS = ["#1a73e8", "#188038", "#c5221f", "#e37400", "#7b1fa2",
           "#00796b", "#ad1457", "#0b8043", "#4285f4"]


def stars_svg(rating, empty, uid=None, height=16):
    """Five stars with the last one partially filled for fractional ratings."""
    if rating == 5:
        w = int(height * 116 / 20.0)
        return ('<svg class="stars" viewBox="0 0 116 20" width="%d" height="%d" role="img" '
                'aria-label="5 out of 5 stars"><use href="#stars5"/></svg>' % (w, height))
    full = int(rating)
    frac = round(rating - full, 2)
    width = int(height * 116 / 20.0)
    out = ['<svg class="stars" viewBox="0 0 116 20" width="%d" height="%d" '
           'role="img" aria-label="%s out of 5 stars">' % (width, height, rating)]
    if frac and uid:
        pct = "%.4g%%" % (frac * 100)
        out.append('<defs><linearGradient id="%s" x1="0" x2="1" y1="0" y2="0">'
                   '<stop offset="%s" stop-color="%s"/>'
                   '<stop offset="%s" stop-color="%s"/></linearGradient></defs>'
                   % (uid, pct, GOLD, pct, empty))
    for i in range(5):
        if i < full:
            fill = GOLD
        elif i == full and frac and uid:
            fill = "url(#%s)" % uid
        else:
            fill = empty
        out.append('<path transform="translate(%d,0)" d="%s" fill="%s"/>'
                   % (i * 24, STAR_D, fill))
    out.append("</svg>")
    return "".join(out)


def rating_badge(uid, rating=4.8):
    return (
        '<div class="grate">'
        '<svg viewBox="0 0 48 48" width="31" height="31" aria-hidden="true"><use href="#g-logo"/></svg>'
        '<div class="grate__body">'
        '<div class="grate__row"><span class="grate__n">%s</span>%s</div>'
        '<div class="grate__sub"><b>Google Reviews</b>'
        '<span class="vchk" aria-hidden="true"><svg viewBox="0 0 24 24" width="14" height="14">'
        '<use href="#verified"/></svg></span>Verified</div>'
        "</div></div>"
        % (rating, stars_svg(rating, "#bdc1c6", uid, 19))
    )


def review_cards():
    """Two identical passes so the rail can wrap seamlessly mid-scroll."""
    def card(i, name, rating, text, clone):
        return (
            '<article class="rev"%s>'
            '<header class="rev__hd">'
            '<span class="rev__av" style="background:%s" aria-hidden="true">%s</span>'
            '<span class="rev__who"><b>%s</b><span class="rev__meta">Google review</span></span>'
            '<svg class="rev__g" viewBox="0 0 48 48" width="18" height="18" aria-hidden="true">'
            '<use href="#g-logo"/></svg>'
            '</header>%s<p class="rev__body">%s</p></article>'
            % (' aria-hidden="true"' if clone else "",
               AVATARS[i % len(AVATARS)], name[0].upper(), name,
               stars_svg(rating, "#dadce0"), text)
        )

    passes = []
    for clone in (False, True):
        passes.append('<div class="revs__pass">%s</div>' % "".join(
            card(i, n, r, t, clone) for i, (n, r, t) in enumerate(REVIEWS)))
    return "\n      ".join(passes)


def variant_links(current):
    """Preview-only switcher. The main artifact page is served at ./ so it
    links differently from the standalone sibling files."""
    out = []
    for v in VARIANTS:
        href = "./" if v["id"] == VARIANTS[0]["id"] else "%s.html" % v["slug"]
        cur = ' aria-current="page"' if v["id"] == current else ""
        out.append('<a href="%s"%s>%s</a>' % (href, cur, v["label"]))
    return "\n  ".join(out)


def standalone(fragment, v):
    """Wrap the fragment in a real document, GTM script inside <head>."""
    head, _, body = fragment.partition("<!--/HEAD-->")
    if not body:
        sys.exit("head divider <!--/HEAD--> missing from template")
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<meta name="description" content="%s">\n'
        '<meta name="robots" content="noindex, nofollow">\n'
        '<link rel="canonical" href="https://%s/%s/">\n'
        "%s\n</head>\n"
        '<body style="margin:0;background:#fbfcfb;color:#0f2429;font:400 14px/1.65 system-ui,sans-serif">\n'
        "%s\n</body>\n</html>\n" % (v["desc"], SITE_HOST, v["slug"], head.strip(), body.strip())
    )


def render(base, v, preview):
    html = base
    html = html.replace("__VARIANT_ID__", v["id"])
    html = html.replace("__DYN_MODE__", v["dyn"])
    html = html.replace("__PHONE_RAW__", v["phone"])
    html = html.replace("__PHONE_DISPLAY__", pretty_phone(v["phone"]))
    html = html.replace("__CTM_FRT__", CTM_FRT)
    html = html.replace("__CTM_KEY__", CTM_KEY)
    if preview:
        html = html.replace("__VARIANT_LINKS__", variant_links(v["id"]))
    else:
        # strip the switcher entirely from production rather than ship dead markup
        html = re.sub(r"<!-- =+ VARIANT SWITCHER.*?</nav>\s*", "", html, flags=re.S)
        html = re.sub(r"/\* =+ Variant switcher.*?\{\.vswitch[^\n]*\n", "", html, flags=re.S)
        html = html.replace(
            "    document.getElementById('vswitch').hidden = false;\n", "")
    html = html.replace("<title>Invigorate Behavioral Health</title>",
                        "<title>%s</title>" % v["title"])
    if not preview:
        # Production serves the seal from LegitScript's own domain so it verifies.
        html = re.sub(r'src="data:image/webp;base64,[^"]+"(\s+alt="Verify Approval)',
                      'src="%s"\\1' % LEGITSCRIPT_URL, html)
    return html


def main():
    base = open(os.path.join(SRC, "template.html"), encoding="utf-8").read()
    base = base.replace("__CARRIER_STRIP__", carrier_strip())
    base = base.replace("__RATING_BADGE_DARK__", rating_badge("st-hero"))
    base = base.replace("__STARS_LIGHT__", stars_svg(4.8, "#bdc1c6", "st-trust", 20))
    base = base.replace("__REVIEW_CARDS__", review_cards())
    print("reviews  %d cards x2 passes" % len(REVIEWS))

    total = 0
    for token, (filename, width, quality) in SPEC.items():
        uri, size = encode(filename, width, quality)
        total += size
        needle = "__IMG_%s__" % token
        if needle not in base:
            print("  ! unused token %s" % needle)
        base = base.replace(needle, uri)

    leftover = re.findall(r"__IMG_\w+__", base)
    if leftover:
        sys.exit("Unresolved image tokens: %s" % ", ".join(sorted(set(leftover))))
    print("images   %6.1f KB raw -> %6.1f KB base64" % (total / 1024, total * 1.34 / 1024))

    # site/ is the Cloudways webroot: site/<slug>/index.html serves /<slug>/
    site = os.path.join(ROOT, "site")
    prev = os.path.join(ROOT, "preview")
    for d in [prev] + [os.path.join(site, v["slug"]) for v in VARIANTS]:
        if not os.path.isdir(d):
            os.makedirs(d)

    for v in VARIANTS:
        # production: standalone document, GTM in <head>, remote LegitScript seal
        prod = standalone(render(base, v, preview=False), v)
        pp = os.path.join(site, v["slug"], "index.html")
        open(pp, "w", encoding="utf-8").write(prod)

        # preview: inlined seal, variant switcher on
        pre = render(base, v, preview=True)
        if v["id"] == VARIANTS[0]["id"]:
            # the artifact's main page is a fragment; the wrapper owns <head>
            open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(
                pre.replace("<!--/HEAD-->", ""))
            target = os.path.join(ROOT, "index.html")
        else:
            target = os.path.join(prev, "%s.html" % v["slug"])
            open(target, "w", encoding="utf-8").write(standalone(pre, v))

        left = re.findall(r"__[A-Z_]+__", prod)
        if left:
            sys.exit("Unresolved token in %s: %s" % (v["slug"], sorted(set(left))))
        print("  %-9s %s  site/%-19s %6.1f KB" % (
            v["id"], pretty_phone(v["phone"]), v["slug"] + "/index.html",
            os.path.getsize(pp) / 1024))


if __name__ == "__main__":
    main()
