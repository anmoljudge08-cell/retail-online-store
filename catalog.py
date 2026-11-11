"""Catalogue content for Aurum & Ivy.

Product copy lives in code so the seed is deterministic; everything else
(stock, reviews, orders, customers) lives in SQLite.
"""

from __future__ import annotations

STORE = {
    "name": "Aurum & Ivy",
    "tagline": "Objects of quiet luxury",
    "established": 2014,
    "email": "concierge@aurumivy.com",
    "phone": "+91 22 4000 1900",
    "address": "12 Kala Ghoda, Fort, Mumbai 400001, India",
}

SHIPPING = {
    "free_threshold": 10000,
    "standard": 199,
    "express": 399,
}

TAX_RATE = 0.18  # GST

# code -> (percent, minimum subtotal, maximum discount, label)
PROMOS = {
    "WELCOME10": {"percent": 10, "min_subtotal": 0, "max_discount": 2000, "label": "Welcome offer — 10% off"},
    "AURUM15": {"percent": 15, "min_subtotal": 15000, "max_discount": 6000, "label": "Atelier offer — 15% off orders over ₹15,000"},
    "FREESHIP": {"percent": 0, "min_subtotal": 0, "max_discount": 0, "label": "Complimentary delivery", "free_shipping": True},
}

CATEGORIES = [
    {
        "slug": "audio",
        "name": "Audio",
        "blurb": "Listening, considered.",
        "image": "meridian-headphones.jpg",
    },
    {
        "slug": "timepieces",
        "name": "Timepieces",
        "blurb": "Mechanical calm.",
        "image": "solstice-watch.jpg",
    },
    {
        "slug": "leather",
        "name": "Leather Goods",
        "blurb": "Vegetable-tanned, hand-finished.",
        "image": "fold-cardholder.jpg",
    },
    {
        "slug": "home",
        "name": "Home & Living",
        "blurb": "The art of the everyday.",
        "image": "halo-lamp.jpg",
    },
    {
        "slug": "travel",
        "name": "Travel",
        "blurb": "Packed with intent.",
        "image": "atlas-weekender.jpg",
    },
    {
        "slug": "wellness",
        "name": "Wellness",
        "blurb": "Slow rituals.",
        "image": "aura-diffuser.jpg",
    },
]

CATEGORY_NAMES = {c["slug"]: c["name"] for c in CATEGORIES}

PRODUCTS = [
    # ---------------------------------------------------------------- audio
    {
        "slug": "meridian-anc-headphones",
        "name": "Meridian ANC Headphones",
        "category": "audio",
        "price": 24900,
        "compare_at": 29900,
        "stock": 8,
        "featured": 1,
        "badge": "Signature",
        "image": "meridian-headphones.jpg",
        "tagline": "Forty hours of silence, in ivory leather.",
        "summary": "Reference-grade active noise cancelling wrapped in hand-stitched leather and brushed brass.",
        "description": (
            "The Meridian is our most considered listening instrument. Machined brass yokes hold "
            "memory-foam earcups wrapped in full-grain leather, while a 40-hour battery and "
            "six-microphone adaptive cancellation disappear into the background. Tuned by our "
            "studio in Mumbai for a warm, unhurried signature."
        ),
        "details": [
            "40-hour battery life, 5-minute quick charge for 6 hours",
            "Adaptive hybrid ANC with transparency mode",
            "40 mm beryllium-coated drivers, tuned in-house",
            "Bluetooth 5.3, LDAC and multipoint pairing",
            "Folds flat into a wool-felt travel case",
        ],
        "materials": "Full-grain Italian leather, machined brass, recycled aluminium, wool felt.",
        "variants": ["Ivory / Brass", "Emerald / Brass", "Obsidian / Brass"],
    },
    # ----------------------------------------------------------- timepieces
    {
        "slug": "solstice-automatic-watch",
        "name": "Solstice Automatic Watch",
        "category": "timepieces",
        "price": 38500,
        "compare_at": 42000,
        "stock": 5,
        "featured": 1,
        "badge": "Limited",
        "image": "solstice-watch.jpg",
        "tagline": "A 38 mm case, a deep green dial.",
        "summary": "Swiss-assembled automatic movement in a brushed brass case with a hand-finished leather strap.",
        "description": (
            "The Solstice is built around a 24-jewel automatic movement with a 42-hour reserve, "
            "visible through a sapphire caseback. The dial is lacquered in seven coats of deep "
            "emerald before the indices are applied by hand. Each strap is cut from a single hide "
            "and finished with beeswax."
        ),
        "details": [
            "Swiss automatic movement, 42-hour power reserve",
            "38 mm brushed brass case, 9.4 mm thin",
            "Anti-reflective sapphire crystal and caseback",
            "Hand-lacquered emerald dial with applied indices",
            "5 ATM water resistance",
        ],
        "materials": "Brass case, sapphire crystal, vegetable-tanned leather strap.",
        "variants": ["Emerald dial / Tan", "Ivory dial / Black", "Emerald dial / Black"],
    },
    # -------------------------------------------------------------- travel
    {
        "slug": "atlas-leather-weekender",
        "name": "Atlas Leather Weekender",
        "category": "travel",
        "price": 18900,
        "compare_at": 0,
        "stock": 6,
        "featured": 1,
        "badge": "Handmade",
        "image": "atlas-weekender.jpg",
        "tagline": "Three days, one bag.",
        "summary": "A 42-litre cabin-sized holdall in vegetable-tanned leather with solid brass hardware.",
        "description": (
            "Cut from a single side of vegetable-tanned leather and saddle-stitched by hand in our "
            "Mumbai atelier, the Atlas holds three days of clothing without ever needing to be "
            "checked. Solid brass feet keep the base clear of the floor, and the lining is a "
            "brushed cotton twill that softens with every trip."
        ),
        "details": [
            "42 L capacity, cabin-compliant for most carriers",
            "Solid brass hardware, feet and YKK Excella zip",
            "Detachable, adjustable shoulder strap",
            "Interior zip pocket and two slip pockets",
            "Develops a unique patina over time",
        ],
        "materials": "Vegetable-tanned full-grain leather, cotton twill lining, solid brass.",
        "variants": ["Tan", "Chestnut", "Black"],
    },
    # ---------------------------------------------------------------- home
    {
        "slug": "halo-brass-desk-lamp",
        "name": "Halo Brass Desk Lamp",
        "category": "home",
        "price": 12400,
        "compare_at": 13900,
        "stock": 11,
        "featured": 1,
        "badge": "",
        "image": "halo-lamp.jpg",
        "tagline": "Light that behaves like furniture.",
        "summary": "A slender solid-brass lamp with a dimmable warm LED and a hand-spun dome shade.",
        "description": (
            "The Halo is spun from a single sheet of brass, then left unlacquered so it darkens "
            "gently with use. A weighted base keeps it steady, and the dimmable 2700 K LED can be "
            "warmed or cooled across five settings with a touch on the stem."
        ),
        "details": [
            "Solid brass, unlacquered and hand-spun",
            "Dimmable 2700–4000 K LED, 5 settings",
            "Weighted base, 1.8 m braided fabric cord",
            "Touch control on the stem",
            "Replaceable LED module rated for 25,000 hours",
        ],
        "materials": "Solid brass, braided cotton cord, aluminium LED housing.",
        "variants": ["Brass", "Matte Black"],
    },
    {
        "slug": "ember-pour-over-set",
        "name": "Ember Pour-Over Set",
        "category": "home",
        "price": 6800,
        "compare_at": 0,
        "stock": 14,
        "featured": 1,
        "badge": "",
        "image": "ember-pourover.jpg",
        "tagline": "The morning ritual, refined.",
        "summary": "A hand-thrown ceramic dripper and 400 ml carafe, glazed in a soft matte cream.",
        "description": (
            "Thrown on the wheel in small batches, the Ember dripper uses a 60-degree cone and "
            "spiral ribs to keep the filter from sealing. The matching carafe holds 400 ml — two "
            "generous cups — and pours without a drip thanks to a hand-cut spout."
        ),
        "details": [
            "Hand-thrown stoneware, food-safe matte glaze",
            "60-degree cone with spiral ribs",
            "400 ml carafe with hand-cut spout",
            "Fits standard #2 paper filters",
            "Dishwasher safe, though hand washing keeps the glaze bright",
        ],
        "materials": "High-fired stoneware, lead-free matte glaze.",
        "variants": ["Cream", "Slate"],
    },
    {
        "slug": "nocturne-cashmere-throw",
        "name": "Nocturne Cashmere Throw",
        "category": "home",
        "price": 14600,
        "compare_at": 16800,
        "stock": 9,
        "featured": 1,
        "badge": "New",
        "image": "nocturne-throw.jpg",
        "tagline": "Woven in Nepal, from Grade-A cashmere.",
        "summary": "A 130 × 180 cm throw in three-ply Grade-A cashmere with a hand-knotted fringe.",
        "description": (
            "Spun from the soft underfleece of Himalayan goats and woven on handlooms in "
            "Kathmandu, the Nocturne weighs just 620 grams but holds warmth like a much heavier "
            "blanket. The fringe is knotted by hand, strand by strand."
        ),
        "details": [
            "130 × 180 cm, 620 g",
            "Three-ply Grade-A Himalayan cashmere",
            "Hand-knotted fringe",
            "Woven on handlooms in Kathmandu",
            "Comes in a reusable cotton storage pouch",
        ],
        "materials": "100% Grade-A cashmere.",
        "variants": ["Emerald", "Oat", "Charcoal"],
    },
    {
        "slug": "terra-oak-serving-board",
        "name": "Terra Oak Serving Board",
        "category": "home",
        "price": 7200,
        "compare_at": 0,
        "stock": 12,
        "featured": 0,
        "badge": "",
        "image": "terra-board.jpg",
        "tagline": "One piece of oak, one brass handle.",
        "summary": "A solid European oak board finished with food-safe oil and a solid brass handle.",
        "description": (
            "Milled from a single plank of European oak so the grain runs unbroken from edge to "
            "edge. The brass handle is set by hand and will patina with use. Finished with a "
            "beeswax and jojoba oil that is safe for direct contact with food."
        ),
        "details": [
            "Solid European oak, 38 × 24 × 2 cm",
            "Solid brass handle, hand-set",
            "Finished with beeswax and jojoba oil",
            "Re-oil every few months to keep it sealed",
            "Hand wash and dry flat",
        ],
        "materials": "Solid European oak, solid brass.",
        "variants": ["Oak", "Walnut"],
    },
    # -------------------------------------------------------------- leather
    {
        "slug": "fold-leather-cardholder",
        "name": "Fold Leather Cardholder",
        "category": "leather",
        "price": 4400,
        "compare_at": 0,
        "stock": 2,
        "featured": 1,
        "badge": "Low stock",
        "image": "fold-cardholder.jpg",
        "tagline": "Four cards. No bulk.",
        "summary": "A two-pocket cardholder cut from a single piece of full-grain leather and saddle-stitched by hand.",
        "description": (
            "There is no lining, no glue and no plastic in the Fold — just one piece of "
            "full-grain leather, folded twice and saddle-stitched with waxed linen thread. It "
            "holds four to six cards and a note or two, and it will mould to your pocket within a "
            "fortnight."
        ),
        "details": [
            "Holds 4–6 cards plus folded notes",
            "Single-piece construction, no lining or glue",
            "Hand saddle-stitched with waxed linen thread",
            "Edges burnished and waxed by hand",
            "2.5 mm thin",
        ],
        "materials": "Full-grain vegetable-tanned leather, waxed linen thread.",
        "variants": ["Chestnut", "Black", "Tan"],
    },
    # --------------------------------------------------------------- travel
    {
        "slug": "voyage-insulated-flask",
        "name": "Voyage Insulated Flask",
        "category": "travel",
        "price": 3200,
        "compare_at": 3800,
        "stock": 26,
        "featured": 1,
        "badge": "",
        "image": "voyage-flask.jpg",
        "tagline": "Cold for 24 hours, hot for 12.",
        "summary": "A 750 ml double-walled steel flask with a brushed brass cap and a powder-coated finish.",
        "description": (
            "Vacuum-sealed between two walls of 18/8 stainless steel, the Voyage keeps water cold "
            "for a full day and tea hot through a long morning. The cap is machined brass with a "
            "silicone seal, and the mouth is wide enough for ice."
        ),
        "details": [
            "750 ml, double-walled vacuum insulation",
            "18/8 stainless steel, powder-coated exterior",
            "Machined brass cap with silicone seal",
            "Wide mouth takes ice cubes",
            "Hand wash only",
        ],
        "materials": "18/8 stainless steel, brass, food-grade silicone.",
        "variants": ["Emerald", "Ivory", "Slate"],
    },
    # ------------------------------------------------------------- wellness
    {
        "slug": "aura-ceramic-diffuser",
        "name": "Aura Ceramic Diffuser",
        "category": "wellness",
        "price": 5600,
        "compare_at": 0,
        "stock": 17,
        "featured": 0,
        "badge": "",
        "image": "aura-diffuser.jpg",
        "tagline": "The room, quietly changed.",
        "summary": "An ultrasonic diffuser in matte ceramic with an eight-hour timer and no plastic in the mist path.",
        "description": (
            "A matte ceramic shell hides a near-silent ultrasonic plate that carries scent without "
            "heat. The mist path is glass and ceramic rather than plastic, so essential oils arrive "
            "unaltered. Eight hours of runtime, and a warm light that dims to almost nothing."
        ),
        "details": [
            "200 ml reservoir, up to 8 hours runtime",
            "Near-silent ultrasonic diffusion",
            "Ceramic and glass mist path — no plastic",
            "Warm dimmable light, optional",
            "Auto shut-off when empty",
        ],
        "materials": "Matte ceramic shell, borosilicate glass, bamboo base.",
        "variants": ["Sand", "Stone"],
    },
]

REVIEWS = [
    ("meridian-anc-headphones", "Ananya R.", 5, "Worth every rupee", "The noise cancelling is uncanny on a Mumbai local. Leather is beautiful and the brass ages well."),
    ("meridian-anc-headphones", "Karan M.", 5, "Quiet luxury, literally", "Bought these for flights. They disappear on my head and the battery outlasts any trip I take."),
    ("meridian-anc-headphones", "Devika S.", 4, "Gorgeous, slightly heavy", "Sound is warm and detailed. Slightly heavier than my old pair, but the build quality is another league."),
    ("solstice-automatic-watch", "Rohan A.", 5, "The dial is the star", "Photos do not do the emerald lacquer justice. Wears beautifully at 38 mm."),
    ("solstice-automatic-watch", "Meera K.", 5, "My everyday watch now", "Understated enough for work, special enough for evenings. The strap softened within a week."),
    ("solstice-automatic-watch", "Aditya V.", 4, "Lovely, wish it had lume", "Beautiful finishing for the price. I do miss lume at night."),
    ("atlas-leather-weekender", "Nisha P.", 5, "Cabin-friendly and handsome", "Fits three days easily and still slides into the overhead bin. The leather creases beautifully."),
    ("atlas-leather-weekender", "Farhan Q.", 5, "Heirloom quality", "Stitching is impeccable. Three trips in and the patina is already lovely."),
    ("halo-brass-desk-lamp", "Ishita B.", 5, "Elevated my desk instantly", "The warm setting is perfect for evening work. Brass has darkened slightly, as promised."),
    ("halo-brass-desk-lamp", "Sameer T.", 4, "Beautiful light", "Wish the cord were a little longer, otherwise flawless."),
    ("ember-pour-over-set", "Priya N.", 5, "Morning ritual sorted", "The glaze is beautiful in person and it pours cleanly. Coffee tastes better, honestly."),
    ("ember-pour-over-set", "Arjun D.", 4, "Great set", "Slightly smaller carafe than expected, but two cups is exactly right."),
    ("nocturne-cashmere-throw", "Tara G.", 5, "Impossibly soft", "Light as a scarf but genuinely warm. The emerald is deep and rich, not bright."),
    ("nocturne-cashmere-throw", "Vikram J.", 5, "Best purchase this year", "No pilling after two months of daily use. The storage pouch is a nice touch."),
    ("terra-oak-serving-board", "Leela M.", 4, "Simple and solid", "Grain is gorgeous. Needs re-oiling, as the card says, but that is a pleasure."),
    ("terra-oak-serving-board", "Nikhil R.", 5, "Brass handle is the detail", "Looks lovely on the counter and cleans up easily."),
    ("fold-leather-cardholder", "Zoya H.", 5, "Perfectly minimal", "Holds five cards and a note without any bulk. The chestnut is a beautiful tone."),
    ("fold-leather-cardholder", "Rahul S.", 4, "Tight at first", "Took a week to stretch to five cards, but now it is perfect."),
    ("voyage-insulated-flask", "Ananya R.", 5, "Actually keeps ice", "Ice cubes survived a full day in the car. The brass cap looks great."),
    ("voyage-insulated-flask", "Kabir L.", 4, "Great flask", "Only hand wash, but the finish still looks new after months."),
    ("aura-ceramic-diffuser", "Meera K.", 5, "Beautiful object", "Almost silent and the ceramic looks like a sculpture. No plastic smell at all."),
    ("aura-ceramic-diffuser", "Ishita B.", 4, "Lovely", "Light is a nice touch. Reservoir could be bigger for a large room."),
]
