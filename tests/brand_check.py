#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
brand_check.py — executable contracts for the Sombra reveal.js deck.

Phase 1 (brand re-theme: palette re-skin, effects removed, real logo in)
shipped at a8e95c2; the permanent brand rules (palette, effects, logo,
font freezes) must stay GREEN. Its migration freezes — c25b (slide texts),
c26 (HTML outside <svg>), c27 (non-paint CSS declarations), c30 (inline
style attrs), c31 (deck_check parity) — were retired on 2026-11-10: they
compared the deck against the pre-re-theme baseline 66369c3 to prove phase 1
changed no text and no geometry, and keeping them would forbid any
legitimate content edit.

The v2 slide system (2026-11-11) re-types the deck from the design canvas,
so c24 (the phase-1 typography freeze) and c28 (the phase-1 diagram
freeze) were retired with it. Palette,
effects, logo and font-face contracts still hold.

The e01–e19 contracts are the four approved content edits (divider
numerals/eyebrows, the compliance card, the comparison-table row tags, the
integration card). Written TDD-style BEFORE the edits: most are RED by
design on the current deck and turn green when the edits land.

Usage (one command; Python 3 stdlib only; no network; deterministic):
    python3 tests/brand_check.py                  # check the repo itself
    python3 tests/brand_check.py --root PATH      # check another tree

The BASELINE is always read from git in THIS repo, pinned to commit 66369c3
(`git --no-pager show 66369c3:index.html` / `66369c3:theme/sombra.css`) —
never HEAD, because HEAD moves.

Contract -> check mapping (contract numbers from the phase-1 spec):
  1  c01_css_hex_literals_in_palette
  2  c02_css_rgb_rgba_palette_and_alpha, c02b_css_no_exotic_colour_functions
  3  c03_css_no_named_colours_in_values
  4  c04_css_literals_only_in_root_plus_4_mask_inks
  5  c05a_root_colour_token_values, c05b_root_structural_tokens_unchanged,
     c05c_root_no_other_custom_properties
  6  c06a_no_legacy_token_names, c06b_all_var_references_defined
  7  c07a_html_hex_literals_in_palette, c07b_html_no_colour_functions,
     c07c_html_no_named_colours_in_paint_attrs
  8  c08_assets_exactly_favicon_with_ink_and_white
  9  c09_canyon_colour_only_in_no_rule
  10 c10a..c10h (one per forbidden effect: gradient(, box-shadow, blur(,
     mix-blend-mode, feTurbulence, background-clip, grad-text, filter:)
  11 c11_css_text_shadow_none_exactly_once
  12 c12a..c12i (one per forbidden markup token)
  13 c13_html_fragment_refs_resolve
  14 c14a_favicon_link_exactly_once, c14b_favicon_file_exists,
     c14c_no_sombra_mark_string
  15 c15_no_eclipse_or_corona
  16 c16_chrome_bar_markup_bytes
  17 c17a_symbol_mark_exact, c17b_symbol_wordmark_exact, c17c_no_lockup
  18 c18_favicon_svg_structure
  19 c19a_first_section_has_hero_mark, c19b_last_section_has_mark_and_wordmark,
     c19c_use_reference_counts
  20 c20a_hero_mark_520px, c20b_closing_logo_rules_exact,
     c20c_deck_chrome_svg_rule_unchanged
  21 c21a_favicon_no_transform_keywords, c21b_html_no_preserve_aspect_ratio,
     c21c_logo_css_rules_no_effect_props
  22 c22_font_face_blocks_unchanged
  23 c23_font_token_lines_unchanged
  24 (retired: c24_typography_declarations_unchanged)
  25 c25a_exactly_21_top_level_sections
  26 (retired: c26_html_outside_svg_equals_baseline_two_subs)
  27 (retired: c27_non_paint_declarations_frozen)
  28 (retired: c28_diagram_svgs_unchanged_minus_paint_attrs)
  29 c29a_icon_symbols_unchanged, c29b_markers_unchanged_apart_fill
  30 (retired: c30_inline_style_attrs_frozen)
  31 (retired: c31_deck_check_parity)
  E  e01_dividers_no_num_element, e02_dividers_no_numeral_text,
     e03_no_part_word_anywhere,
     e04_divider3_eyebrow_integration_architecture,
     e05_divider_headings_unchanged,
     e06_compliance_private_withdrawals_card,
     e07_compliance_no_onofframps_text,
     e08_withdrawals_card_body_terms,
     e09_compliance_card_set_unchanged,
     e10_table_exactly_two_row_tags, e11_row_tag_texts,
     e12_row_tags_in_right_rows, e13_row_tags_use_yes_mark,
     e14_table_headers_and_row_labels_unchanged,
     e15_table_body_row_widths_consistent,
     e16_integration_private_defi_card,
     e17_integration_no_onramp_offramp_headings,
     e18_private_defi_description_ok,
     e19_integration_card_set_unchanged

Verified facts baked into the checks (confirmed against the real files):
  * SHA-256 of the UTF-8 bytes of the `d` attribute value (exactly as
    written, no decoding) of the two logo paths in the architect's prototype
    /tmp/sombra-brand/proto/index.html:
      mark           7c4114063c89281884a53664106756618735d56e1a3497a682dcf04bbd6dcf3f
      lockup-stacked 784ef485746d8f78e066b3a16e34060226e63cec7299b5e4d694d32c32513622
  * The wordmark symbol (2026-11-11) is the lockup's letterforms, unaltered:
    the `d` up to the mark's "M204.39", hash
      wordmark       1ce5c86e5eff127ffb9819c4f9c58134b40a2381dbebc25c5ba723a4cd0ce727
    Logomark and wordmark are used apart; no stacked or standard lockup.
  * The baseline (66369c3) chrome bar bytes are exactly
      <svg><use href="#mark"/></svg><b>Sombra</b><span>·</span><span>Scale or Die</span>
    (no difference from the spec string, so the spec string is used).

Scanning rules per spec: CSS is scanned with /* */ comments stripped and
%23 treated as #; in HTML, href="#id" and url(#id) are masked before hex
scanning so fragment references are never mistaken for colours.
"""

import collections
import hashlib
import html as html_mod
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BASE_COMMIT = "66369c3"

# ---------------------------------------------------------------------------
# Palette and tokens
# ---------------------------------------------------------------------------

PALETTE_HEX = {
    "#fcf9f2": "white",
    "#1a1a1a": "ink",
    "#233a35": "pine",
    "#2a2954": "fjord",
    "#a73d13": "canyon",
    "#b1e0ff": "sky",
}
PALETTE_RGB = {
    (252, 249, 242),   # white
    (26, 26, 26),      # ink
    (35, 58, 53),      # pine
    (42, 41, 84),      # fjord
    (167, 61, 19),     # canyon
    (177, 224, 255),   # sky
}

# The thirteen colour tokens :root must define, with these values
# (--text-dim and --sky-line came with the v2 slide system, 2026-11-11).
ROOT_COLOUR_TOKENS = {
    "--white": "#FCF9F2",
    "--ink": "#1A1A1A",
    "--pine": "#233A35",
    "--fjord": "#2A2954",
    "--canyon": "#A73D13",
    "--sky": "#B1E0FF",
    "--text": "var(--white)",
    "--text-2": "rgba(252, 249, 242, 0.75)",
    "--text-3": "rgba(252, 249, 242, 0.60)",
    "--line": "rgba(252, 249, 242, 0.20)",
    "--line-strong": "rgba(252, 249, 242, 0.40)",
    "--text-dim": "rgba(252, 249, 242, 0.50)",
    "--sky-line": "rgba(177, 224, 255, 0.45)",
}

# Structural :root tokens that must be unchanged from baseline (contract 5).
STRUCTURAL_TOKENS = (
    "--radius",
    "--f-display", "--f-body", "--f-serif", "--f-mono",
    "--pad-x", "--pad-top", "--pad-bottom",
)

LEGACY_TOKENS = (
    "--violet", "--cyan", "--sol-", "--amber", "--mint", "--rose", "--glow",
    "--ink-0", "--ink-1", "--ink-2", "--ink-3",
)

MARK_HASH = "7c4114063c89281884a53664106756618735d56e1a3497a682dcf04bbd6dcf3f"
WORDMARK_HASH = "1ce5c86e5eff127ffb9819c4f9c58134b40a2381dbebc25c5ba723a4cd0ce727"

CHROME_BAR = ('<svg><use href="#mark"/></svg><b>Sombra</b>'
              '<span>·</span><span>Scale or Die</span>')

FAVICON_LINK = '<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">'

HERO_MARK_SVG = '<svg class="hero-mark" aria-hidden="true"><use href="#mark"/></svg>'
CLOSING_MARK_SVG = '<svg class="closing-mark" aria-hidden="true"><use href="#mark"/></svg>'
CLOSING_WORDMARK_SVG = '<svg class="closing-wordmark" role="img" aria-label="Sombra"><use href="#wordmark"/></svg>'

# Approved 2026-11-11: APK Galeria Roman replaces Space Grotesk as the display
# face. Applied to the baseline so the font freezes (c05b, c22, c23) accept
# exactly this swap and nothing else. Single static weight: the 100-900 range
# stops browsers faking bold on 500-700 headings.
FONT_SWAP = [
    ('  font-family: "Space Grotesk";\n'
     '  src: url("../vendor/fonts/space-grotesk-latin-wght-normal.woff2") format("woff2");\n'
     '  font-weight: 300 700;',
     '  font-family: "APK Galeria Roman";\n'
     '  src: url("../vendor/fonts/apk-galeria-roman-400-normal.woff2") format("woff2");\n'
     '  font-weight: 100 900;'),
    ('--f-display: "Space Grotesk", "Inter",',
     '--f-display: "APK Galeria Roman", "Inter",'),
]
DISPLAY_FONT_FILE = "vendor/fonts/apk-galeria-roman-400-normal.woff2"


def apply_font_swap(css):
    for old, new in FONT_SWAP:
        assert css.count(old) == 1, f"font swap anchor not found once in baseline: {old!r}"
        css = css.replace(old, new)
    return css


# The ten declarations' owning selectors (for contract 21).
LOGO_RULE_SELECTORS = (".s-title .hero-mark", ".s-closing .closing-mark", ".s-closing .closing-wordmark",
                       ".deck-chrome svg")

# CSS named colours (the full CSS3/CSS4 list of 147). transparent,
# currentColor and none are NOT in this list, so they are allowed.
NAMED_COLOURS = set("""
aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond
blue blueviolet brown burlywood cadetblue chartreuse chocolate coral
cornflowerblue cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray
darkgreen darkgrey darkkhaki darkmagenta darkolivegreen darkorange darkorchid
darkred darksalmon darkseagreen darkslateblue darkslategray darkslategrey
darkturquoise darkviolet deeppink deepskyblue dimgray dimgrey dodgerblue
firebrick floralwhite forestgreen fuchsia gainsboro ghostwhite gold goldenrod
gray green greenyellow grey honeydew hotpink indianred indigo ivory khaki
lavender lavenderblush lawngreen lemonchiffon lightblue lightcoral lightcyan
lightgoldenrodyellow lightgray lightgreen lightgrey lightpink lightsalmon
lightseagreen lightskyblue lightslategray lightslategrey lightsteelblue
lightyellow lime limegreen linen magenta maroon mediumaquamarine mediumblue
mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen
mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin
navajowhite navy oldlace olive olivedrab orange orangered orchid palegoldenrod
palegreen paleturquoise palevioletred papayawhip peachpuff peru pink plum
powderblue purple rebeccapurple red rosybrown royalblue saddlebrown salmon
sandybrown seagreen seashell sienna silver skyblue slateblue slategray
slategrey snow springgreen steelblue tan teal thistle tomato turquoise violet
wheat white whitesmoke yellow yellowgreen
""".split())

# ---------------------------------------------------------------------------
# Content-edit contract values (the e01–e19 checks)
# ---------------------------------------------------------------------------

# The three s-divider slides, by top-level <section> order (1-based).
DIVIDER_SLIDES = (7, 12, 17)

# Today's divider h2 text (hard-coded; must survive the content edits).
DIVIDER_HEADINGS = {
    7: "Enter Sombra",
    12: "How it works — and how it compares",
    17: "Going private used to mean leaving DeFi.",
}

# Slide 11 (compliance): the card set after the edit — one heading changes
# from "Private on/off-ramps" to "Private withdrawals", the other three are
# frozen at today's values.
COMPLIANCE_CARD_HEADINGS = (
    "Private withdrawals",
    "Scoped disclosure",
    "Lineage by design",
    "Association sets",
)

# Slide 15 (comparison table): the five data column headers by main text
# (the <small> subtitle excluded) and the five row labels, in order.
TABLE_COLUMN_HEADERS = ("Sombra", "Zcash", "Privacy Cash", "Rings", "Umbra")
TABLE_ROW_LABELS = (
    "Shielded transfers",
    "Native to Solana liquidity",
    "Proof system",
    "Quantum-safe proofs",
    "Quantum-safe note encryption",
)

# Slide 18 (integration grid): the card set after the edit — one heading
# changes from "Onramp / offramp" to "Private DeFi", the other five are
# frozen at today's values.
INTEGRATION_CARD_HEADINGS = (
    "Private staking via LSTs",
    "Wallet SDK",
    "Privacy Relayer",
    "Private Actions",
    "Any SPL token",
    "Private DeFi",
)

# The table's existing "yes" mark markup (confirmed against index.html).
YES_MARK = '<span class="yes" role="img" aria-label="yes"></span>'

PART_WORD_RE = re.compile(r"\bpart (one|two|three|four)\b", re.I)
ONOFFRAMP_RE = re.compile(r"\bon/off[\s-]?ramps\b", re.I)
# Any element carrying the row-tag class; group(2) is its inner HTML.
ROW_TAG_RE = re.compile(
    r'<([a-zA-Z][a-zA-Z0-9]*)\b[^>]*\bclass="[^"]*\brow-tag\b[^"]*"[^>]*>'
    r"(.*?)</\1>", re.S)
NOTES_RE = re.compile(r'<aside class="notes">.*?</aside>', re.S)
# class="card" or class="card …" — NOT "card-top" (a space, not a dash,
# separates the classes).
CARD_OPEN_RE = re.compile(r'<div class="card(?: [^"]*)?">')
DIV_RE = re.compile(r"<div\b|</div>")

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

# Hex literal: 3/4/6/8 hex digits, not part of a longer word, not %-encoded.
HEX_RE = re.compile(r"(?<![\w&])#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})(?![\w-])")
RGB_RE = re.compile(r"\brgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([0-9.]+)\s*)?\)")
EXOTIC_FN_RE = re.compile(r"\b(hsla?|hwb|lab|lch|oklab|oklch|color-mix|color)\(")
VAR_RE = re.compile(r"var\((--[\w-]+)\)")
FILL_ATTR_RE = re.compile(r'\sfill="[^"]*"')

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def git_show(relpath):
    """Baseline file content pinned to BASE_COMMIT (never HEAD)."""
    r = subprocess.run(
        ["git", "--no-pager", "-C", str(REPO), "show", f"{BASE_COMMIT}:{relpath}"],
        capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ERROR: cannot read baseline {BASE_COMMIT}:{relpath} "
                 f"from git: {r.stderr.strip()}")
    return r.stdout


def read_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def line_of(text, needle):
    """1-based line number of the first line containing needle, else None."""
    for i, line in enumerate(text.splitlines(), 1):
        if needle in line:
            return i
    return None


def mask_html_refs(html_text):
    """Mask href/src/url(...) so fragment refs are not read as hex colours."""
    t = re.sub(r'\b(?:href|src|xlink:href|poster)="[^"]*"', '=""', html_text)
    t = re.sub(r"url\([^)]*\)", "url()", t)
    return t


def norm_value(v):
    """Normalise a CSS value: lowercase, drop all whitespace, 0.60 == 0.6."""
    v = v.lower()
    v = re.sub(r"\s+", "", v)

    def _num(m):
        ip, fp = m.group(1), m.group(2).rstrip("0")
        return ip + ("." + fp if fp else "")

    v = re.sub(r"(\d+)\.(\d+)", _num, v)
    return v


def top_level_sections(html_text):
    """Raw inner text of depth-0 <section> elements, in document order."""
    out = []
    stack = []
    for m in re.finditer(r"<section\b[^>]*>|</section>", html_text, re.S):
        if m.group(0).startswith("</"):
            if stack:
                start = stack.pop()
                if not stack:
                    out.append(html_text[start:m.start()])
        else:
            stack.append(m.end())
    return out


def strip_tags(html_text):
    """Tag-stripped, entity-decoded, whitespace-normalised text."""
    return " ".join(html_mod.unescape(re.sub(r"<[^>]*>", " ", html_text)).split())


def strip_notes(section_html):
    """The section's HTML without its <aside class=\"notes\"> speaker notes."""
    return NOTES_RE.sub(" ", section_html)


def visible_text(section_html):
    """Visible (on-stage) text of a slide: speaker notes excluded."""
    return strip_tags(strip_notes(section_html))


def h2_text(section_html):
    m = re.search(r"<h2[^>]*>(.*?)</h2>", strip_notes(section_html), re.S)
    return strip_tags(m.group(1)) if m else None


def eyebrow_text(section_html):
    m = re.search(r'<div class="eyebrow"[^>]*>(.*?)</div>',
                  strip_notes(section_html), re.S)
    return strip_tags(m.group(1)) if m else None


def card_blocks(section_html):
    """The .card divs of a slide, in document order (depth-matched)."""
    out = []
    for m in CARD_OPEN_RE.finditer(section_html):
        depth, i = 1, m.end()
        while i < len(section_html) and depth:
            nxt = DIV_RE.search(section_html, i)
            if nxt is None:
                break
            depth += 1 if nxt.group(0)[1] == "d" else -1
            i = nxt.end()
        out.append(section_html[m.start():i])
    return out


def card_heading(card_html):
    m = re.search(r"<h3[^>]*>(.*?)</h3>", card_html, re.S)
    return strip_tags(m.group(1)) if m else None


def card_body(card_html):
    m = re.search(r"<p[^>]*>(.*?)</p>", card_html, re.S)
    return strip_tags(m.group(1)) if m else ""


def table_rows(section_html, part):
    """The <tr> blocks of a table's <thead>/<tbody>, in document order."""
    m = re.search(rf"<{part}>(.*?)</{part}>", section_html, re.S)
    if not m:
        return []
    return re.findall(r"<tr\b[^>]*>.*?</tr>", m.group(1), re.S)


def th_main_text(th_html):
    """A table header's main text (the <small> subtitle removed)."""
    return strip_tags(re.sub(r"<small.*?</small>", " ", th_html, flags=re.S))


def parse_declarations(css_nc):
    """css_nc (comments stripped) -> list of (selector, prop, value).

    Values are whitespace-normalised. At-rules: @font-face declarations get
    selector '@font-face'; @keyframes/@media recurse with a context prefix.
    Declaration splitting honours quotes and parentheses (data-URIs contain
    ';' inside url()).
    """
    out = []

    def add_decls(sel, body):
        decls, buf, q, par = [], "", None, 0
        for ch in body:
            if q:
                buf += ch
                if ch == q:
                    q = None
            elif ch in "\"'":
                q = ch
                buf += ch
            elif ch == "(":
                par += 1
                buf += ch
            elif ch == ")":
                par -= 1
                buf += ch
            elif ch == ";" and par == 0:
                decls.append(buf)
                buf = ""
            else:
                buf += ch
        decls.append(buf)
        for d in decls:
            if ":" in d:
                p, v = d.split(":", 1)
                p, v = p.strip(), " ".join(v.split())
                if p and v:
                    out.append((sel, p, v))

    def walk(text, ctx):
        i, n = 0, len(text)
        while i < n:
            j = text.find("{", i)
            if j < 0:
                break
            sel = " ".join(text[i:j].split())
            depth, k = 1, j + 1
            while k < n and depth:
                c = text[k]
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                k += 1
            body = text[j + 1:k - 1]
            if sel.startswith("@font-face"):
                add_decls(ctx + "@font-face", body)
            elif sel.startswith(("@keyframes", "@media", "@supports")):
                walk(body, ctx + sel + " ")
            else:
                add_decls(ctx + sel, body)
            i = k

    walk(css_nc, "")
    return out


def url_spans(text):
    """(start, end) spans of every url(...) occurrence, paren-matched."""
    spans = []
    for m in re.finditer(r"url\(", text):
        i, depth = m.end(), 1
        while i < len(text) and depth:
            if text[i] == "(":
                depth += 1
            elif text[i] == ")":
                depth -= 1
            i += 1
        spans.append((m.start(), i))
    return spans


def sha256_of(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Check runner
# ---------------------------------------------------------------------------

class Checker:
    def __init__(self, root, base_html, base_css):
        self.root = root
        self.base_html = base_html
        self.base_css = base_css
        self.css_raw = read_file(root / "theme" / "sombra.css")
        self.html_raw = read_file(root / "index.html")
        self.results = []  # (name, status, detail); status: pass|fail|skip

    def add(self, name, ok, detail=""):
        self.results.append((name, "pass" if ok else "fail", detail))

    def skip(self, name, detail=""):
        self.results.append((name, "skip", detail))

    # -- file-missing helpers ------------------------------------------------
    def _css_missing(self, name):
        self.add(name, False, f"theme/sombra.css not found under {self.root}")

    def _html_missing(self, name):
        self.add(name, False, f"index.html not found under {self.root}")

    # -- contracts -----------------------------------------------------------
    def run(self):
        self._run_all()

    def _run_all(self):
        css, htm = self.css_raw, self.html_raw
        css_nc = strip_comments(css) if css else ""
        css_scan = css_nc.replace("%23", "#")  # spec: %23 == # when scanning
        bhtml, bcss = self.base_html, apply_font_swap(self.base_css)
        bcss_nc = strip_comments(bcss)

        # ---- Contract 1: CSS hex literals in palette ------------------------
        if css is None:
            self._css_missing("c01_css_hex_literals_in_palette")
        else:
            bad = []
            for m in HEX_RE.finditer(css_scan):
                hx = "#" + m.group(1)
                if len(m.group(1)) != 6 or hx.lower() not in PALETTE_HEX:
                    ln = line_of(css, m.group(0))
                    bad.append(f"{m.group(0)} (line {ln})")
            self.add("c01_css_hex_literals_in_palette", not bad,
                     "hex literal(s) outside the six-colour palette in "
                     "theme/sombra.css: " + ", ".join(bad[:6]))

        # ---- Contract 2: rgb/rgba palette + alpha; no exotic functions ------
        if css is None:
            self._css_missing("c02_css_rgb_rgba_palette_and_alpha")
            self._css_missing("c02b_css_no_exotic_colour_functions")
        else:
            bad = []
            for m in RGB_RE.finditer(css_scan):
                triplet = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
                alpha = 1.0 if m.group(4) is None else float(m.group(4))
                if triplet not in PALETTE_RGB or not (0 < alpha <= 1):
                    ln = line_of(css, m.group(0))
                    bad.append(f"{m.group(0)} (line {ln})")
            self.add("c02_css_rgb_rgba_palette_and_alpha", not bad,
                     "rgb()/rgba() with non-palette triplet or alpha outside "
                     "(0,1] in theme/sombra.css: " + ", ".join(bad[:6]))
            bad = []
            for m in EXOTIC_FN_RE.finditer(css_scan):
                ln = line_of(css, m.group(0))
                bad.append(f"{m.group(0)} (line {ln})")
            self.add("c02b_css_no_exotic_colour_functions", not bad,
                     "forbidden colour function in theme/sombra.css "
                     "(hsl/hsla/hwb/lab/lch/oklab/oklch/color-mix/color): "
                     + ", ".join(bad[:6]))

        # ---- Contract 3: no named colours as CSS values ---------------------
        if css is None:
            self._css_missing("c03_css_no_named_colours_in_values")
        else:
            bad = []
            for sel, p, v in parse_declarations(css_nc):
                words = re.findall(r"[A-Za-z]+", re.sub(r"var\([^)]*\)", "", v))
                for w in words:
                    if w.lower() in NAMED_COLOURS:
                        bad.append(f"{sel} {p}: …{w}…")
                        break
            self.add("c03_css_no_named_colours_in_values", not bad,
                     "CSS named colour used as a value in theme/sombra.css "
                     "(incl. data-URIs): " + "; ".join(bad[:6]))

        # ---- Contract 4: literals only in :root + exactly 4 %231A1A1A ------
        if css is None:
            self._css_missing("c04_css_literals_only_in_root_plus_4_mask_inks")
        else:
            m = re.search(r":root\s*\{", css_nc)
            if not m:
                self.add("c04_css_literals_only_in_root_plus_4_mask_inks", False,
                         "no :root block found in theme/sombra.css")
            else:
                depth, k = 1, m.end()
                while k < len(css_nc) and depth:
                    if css_nc[k] == "{":
                        depth += 1
                    elif css_nc[k] == "}":
                        depth -= 1
                    k += 1
                outside = css_nc[:m.start()] + css_nc[k:]
                hexes = [f"{x.group(0)} (line {line_of(css, x.group(0))})"
                         for x in HEX_RE.finditer(outside)]
                rgbs = [f"{x.group(0)} (line {line_of(css, x.group(0))})"
                        for x in RGB_RE.finditer(outside)]
                inks = [x.start() for x in re.finditer(r"%231A1A1A", outside, re.I)]
                spans = url_spans(outside)
                in_data_uri = sum(
                    1 for pos in inks
                    if any(s <= pos < e and re.match(r'url\(\s*["\']?data:', outside[s:e])
                           for s, e in spans))
                problems = []
                if hexes:
                    problems.append("hex literal(s) outside :root: " + ", ".join(hexes[:4]))
                if rgbs:
                    problems.append("rgb()/rgba() outside :root: " + ", ".join(rgbs[:4]))
                if len(inks) != 4:
                    problems.append(f"{len(inks)} occurrence(s) of %231A1A1A outside "
                                    f":root (expected exactly 4)")
                elif in_data_uri != 4:
                    problems.append("not all %231A1A1A occurrences sit inside "
                                    "data: URIs (mask)")
                self.add("c04_css_literals_only_in_root_plus_4_mask_inks",
                         not problems,
                         "theme/sombra.css: " + "; ".join(problems))

        # ---- Contract 5: :root token set and values -------------------------
        if css is None:
            self._css_missing("c05a_root_colour_token_values")
            self._css_missing("c05b_root_structural_tokens_unchanged")
            self._css_missing("c05c_root_no_other_custom_properties")
        else:
            decls = parse_declarations(css_nc)
            got = {p: v for (s, p, v) in decls if s == ":root" and p.startswith("--")}
            bdecls = parse_declarations(bcss_nc)
            bgot = {p: v for (s, p, v) in bdecls if s == ":root" and p.startswith("--")}

            missing = [t for t in ROOT_COLOUR_TOKENS if t not in got]
            wrong = {t: (got[t], ROOT_COLOUR_TOKENS[t]) for t in ROOT_COLOUR_TOKENS
                     if t in got and norm_value(got[t]) != norm_value(ROOT_COLOUR_TOKENS[t])}
            detail = []
            if missing:
                detail.append("missing token(s): " + ", ".join(missing))
            if wrong:
                detail.append("wrong value(s): " + ", ".join(
                    f"{t} is {w[0]!r}, want {w[1]!r}" for t, w in sorted(wrong.items())))
            self.add("c05a_root_colour_token_values", not missing and not wrong,
                     "theme/sombra.css :root — " + "; ".join(detail))

            bmissing = [t for t in STRUCTURAL_TOKENS if t not in bgot]
            swrong = {t: (got.get(t), bgot[t]) for t in STRUCTURAL_TOKENS
                      if t in bgot and t in got
                      and norm_value(got[t]) != norm_value(bgot[t])}
            smissing = [t for t in STRUCTURAL_TOKENS if t in bgot and t not in got]
            detail = []
            if bmissing:
                detail.append(f"baseline itself missing {bmissing} (check the pin)")
            if smissing:
                detail.append("token(s) dropped vs baseline: " + ", ".join(smissing))
            if swrong:
                detail.append("value(s) changed vs baseline: " + ", ".join(
                    f"{t} is {w[0]!r}, baseline {w[1]!r}" for t, w in sorted(swrong.items())))
            self.add("c05b_root_structural_tokens_unchanged",
                     not (bmissing or smissing or swrong),
                     "theme/sombra.css :root — " + "; ".join(detail))

            expected = set(ROOT_COLOUR_TOKENS) | set(STRUCTURAL_TOKENS)
            extra = sorted(set(got) - expected)
            self.add("c05c_root_no_other_custom_properties", not extra,
                     "unexpected custom propertie(s) in theme/sombra.css :root: "
                     + ", ".join(extra))

        # ---- Contract 6: legacy token names gone; every var() defined -------
        if css is None and htm is None:
            self.add("c06a_no_legacy_token_names", False, "neither file found")
        else:
            bad = []
            for label, text in (("theme/sombra.css", css or ""),
                                ("index.html", htm or "")):
                for tok in LEGACY_TOKENS:
                    if tok in text:
                        ln = line_of(text, tok)
                        bad.append(f"{label} line {ln}: {tok}")
            self.add("c06a_no_legacy_token_names", not bad,
                     "legacy token name(s) still present — " + "; ".join(bad[:8]))

        if css is None:
            self._css_missing("c06b_all_var_references_defined")
        else:
            decls = parse_declarations(css_nc)
            defined = {p for (s, p, _v) in decls if s == ":root" and p.startswith("--")}
            used = set(VAR_RE.findall(css + (htm or "")))
            undef = sorted(used - defined)
            where = {}
            for u in undef:
                for label, text in (("theme/sombra.css", css), ("index.html", htm or "")):
                    ln = line_of(text, f"var({u})")
                    if ln:
                        where[u] = f"{label} line {ln}"
                        break
            self.add("c06b_all_var_references_defined", not undef,
                     "var() reference(s) not defined in :root — "
                     + "; ".join(f"{u} ({where.get(u, '?')})" for u in undef[:8]))

        # ---- Contract 7: index.html colours ----------------------------------
        if htm is None:
            self._html_missing("c07a_html_hex_literals_in_palette")
            self._html_missing("c07b_html_no_colour_functions")
            self._html_missing("c07c_html_no_named_colours_in_paint_attrs")
        else:
            bad = []
            for m in HEX_RE.finditer(mask_html_refs(htm)):
                hx = "#" + m.group(1)
                if len(m.group(1)) != 6 or hx.lower() not in PALETTE_HEX:
                    ln = line_of(htm, m.group(0))
                    bad.append(f"{m.group(0)} (line {ln})")
            self.add("c07a_html_hex_literals_in_palette", not bad,
                     "hex literal(s) outside the palette in index.html: "
                     + ", ".join(bad[:6]))

            bad = []
            for tok in ("rgb(", "rgba(", "hsl("):
                if tok in htm:
                    ln = line_of(htm, tok)
                    bad.append(f"{tok} (line {ln})")
            self.add("c07b_html_no_colour_functions", not bad,
                     "colour function(s) in index.html: " + ", ".join(bad))

            bad = []
            for m in re.finditer(r'\b(?:fill|stroke|color|stop-color)="([^"]*)"', htm):
                if m.group(1).lower() in NAMED_COLOURS:
                    ln = line_of(htm, m.group(0))
                    bad.append(f'{m.group(0)} (line {ln})')
            self.add("c07c_html_no_named_colours_in_paint_attrs", not bad,
                     "named colour in a fill/stroke/color/stop-color attribute "
                     "of index.html: " + ", ".join(bad[:6]))

        # ---- Contract 8: assets/ = exactly favicon.svg, Ink + White ----------
        assets = self.root / "assets"
        try:
            files = sorted(p.name for p in assets.iterdir() if p.is_file()) \
                if assets.is_dir() else []
        except OSError:
            files = []
        fav = read_file(assets / "favicon.svg")
        problems = []
        if files != ["favicon.svg"]:
            problems.append(f"assets/ contains {files!r}, want exactly ['favicon.svg']")
        if fav is None:
            if not problems:
                problems.append("assets/favicon.svg not found")
        else:
            hexes = {("#" + m.group(1)).lower() for m in HEX_RE.finditer(fav)}
            if hexes != {"#1a1a1a", "#fcf9f2"}:
                problems.append(f"hex literals are {sorted(hexes)}, want "
                                "exactly ['#1A1A1A', '#FCF9F2']")
            if RGB_RE.search(fav):
                problems.append("rgb()/rgba() present in assets/favicon.svg")
        self.add("c08_assets_exactly_favicon_with_ink_and_white", not problems,
                 " — ".join(problems))

        # ---- Contract 9: var(--canyon) in color/fill only in .no ------------
        if css is None:
            self._css_missing("c09_canyon_colour_only_in_no_rule")
        else:
            bad = []
            for sel, p, v in parse_declarations(css_nc):
                if p in ("color", "fill") and "var(--canyon)" in v \
                        and sel.strip() != ".no":
                    bad.append(f"{sel} {{{p}: {v}}}")
            self.add("c09_canyon_colour_only_in_no_rule", not bad,
                     "var(--canyon) in a color:/fill: declaration outside the "
                     ".no rule — " + "; ".join(bad[:4]))

        # ---- Contract 10: no effects in CSS (one check per token) -----------
        if css is None:
            for n in C10_NAMES:
                self._css_missing(n)
        else:
            for name, tok in C10_TOKENS:
                ln = line_of(css, tok)
                self.add(name, ln is None,
                         f"'{tok}' found in theme/sombra.css line {ln}")
            m = re.search(r"\bfilter\s*:", css)
            self.add("c10h_css_no_filter_declaration", m is None,
                     f"filter: declaration found in theme/sombra.css line "
                     f"{line_of(css, m.group(0)) if m else '?'}")

        # ---- Contract 11: text-shadow none, exactly once ---------------------
        if css is None:
            self._css_missing("c11_css_text_shadow_none_exactly_once")
        else:
            ts = [(s, v) for (s, p, v) in parse_declarations(css_nc)
                  if p == "text-shadow"]
            ok = len(ts) == 1 and ts[0][1] == "none"
            self.add("c11_css_text_shadow_none_exactly_once", ok,
                     f"text-shadow declarations in theme/sombra.css: "
                     f"{ts if ts else 'none found'} (want exactly one, value none)")

        # ---- Contract 12: no effect markup in HTML (one check per token) -----
        if htm is None:
            for n in C12_NAMES:
                self._html_missing(n)
        else:
            for name, tok in C12_TOKENS:
                ln = line_of(htm, tok)
                self.add(name, ln is None,
                         f"'{tok}' found in index.html line {ln}")

        # ---- Contract 13: fragment refs resolve ------------------------------
        if htm is None:
            self._html_missing("c13_html_fragment_refs_resolve")
        else:
            ids = set(re.findall(r'\bid="([^"]+)"', htm))
            refs = set(re.findall(r"url\(#([\w-]+)\)", htm)) | \
                   set(re.findall(r'href="#([\w-]+)"', htm))
            dangling = sorted(refs - ids)
            self.add("c13_html_fragment_refs_resolve", not dangling,
                     "url(#id)/href=\"#id\" in index.html that resolve to no id: "
                     + ", ".join(dangling[:8]))

        # ---- Contract 14: favicon link, file, no 'sombra-mark' ---------------
        if htm is None:
            self._html_missing("c14a_favicon_link_exactly_once")
            self.add("c14b_favicon_file_exists", False,
                     f"assets/favicon.svg not found under {self.root}")
            self._html_missing("c14c_no_sombra_mark_string")
        else:
            n = htm.count(FAVICON_LINK)
            self.add("c14a_favicon_link_exactly_once", n == 1,
                     f"<link rel=\"icon\" href=\"assets/favicon.svg\" …> appears "
                     f"{n} time(s) in index.html (want 1)")
            self.add("c14b_favicon_file_exists", fav is not None,
                     f"assets/favicon.svg not found under {self.root}")
            bad = []
            for label, text in (("index.html", htm), ("theme/sombra.css", css or "")):
                ln = line_of(text, "sombra-mark")
                if ln:
                    bad.append(f"{label} line {ln}")
            self.add("c14c_no_sombra_mark_string", not bad,
                     "'sombra-mark' still present in " + ", ".join(bad))

        # ---- Contract 15: no eclipse/corona ----------------------------------
        if htm is None and css is None:
            self.add("c15_no_eclipse_or_corona", False, "neither file found")
        else:
            bad = []
            for label, text in (("index.html", htm or ""),
                                ("theme/sombra.css", css or "")):
                for m in re.finditer(r"eclipse|corona", text, re.I):
                    ln = line_of(text, m.group(0))
                    bad.append(f"{label} line {ln}: {m.group(0)}")
            self.add("c15_no_eclipse_or_corona", not bad,
                     "'eclipse'/'corona' (case-insensitive) still present — "
                     + "; ".join(bad[:6]))

        # ---- Contract 16: chrome bar bytes -----------------------------------
        # Baseline verified: git 66369c3:index.html contains CHROME_BAR exactly.
        if htm is None:
            self._html_missing("c16_chrome_bar_markup_bytes")
        else:
            n = htm.count(CHROME_BAR)
            self.add("c16_chrome_bar_markup_bytes", n == 1,
                     f"chrome bar markup appears {n} time(s) in index.html "
                     f"(want 1, byte-identical to baseline)")

        # ---- Contract 17: the two sprite symbols ------------------------------
        self._check_symbol("c17a_symbol_mark_exact", htm, "mark",
                           "0 0 148.59 148.59", MARK_HASH)
        self._check_symbol("c17b_symbol_wordmark_exact", htm,
                           "wordmark", "0 257 373.53 86.88", WORDMARK_HASH)
        self.add("c17c_no_lockup", htm is not None and "lockup" not in htm.lower(),
                 "index.html still mentions a lockup — logomark and wordmark are used apart")

        # ---- Contract 18: favicon structure -----------------------------------
        if fav is None:
            self.add("c18_favicon_svg_structure", False,
                     f"assets/favicon.svg not found under {self.root}")
        else:
            problems = []
            root_tag = re.search(r"<svg[^>]*>", fav)
            if not root_tag or 'viewBox="0 0 32 32"' not in root_tag.group(0):
                problems.append(f"root <svg> is {root_tag.group(0) if root_tag else 'missing'}, "
                                'want viewBox="0 0 32 32"')
            if not re.search(r'<rect[^>]*fill="#1A1A1A"', fav):
                problems.append("no <rect … fill=\"#1A1A1A\"> found")
            ds = re.findall(r' d="([^"]+)"', fav)
            if len(ds) != 1:
                problems.append(f"{len(ds)} path d attribute(s), want exactly 1")
            elif sha256_of(ds[0]) != MARK_HASH:
                problems.append(f"path d hash {sha256_of(ds[0])}, want X-mark hash "
                                f"{MARK_HASH}")
            nested = re.search(r"<svg[^>]*viewBox=\"0 0 148\.59 148\.59\"[^>]*>", fav)
            if not nested:
                problems.append('no nested <svg viewBox="0 0 148.59 148.59">')
            else:
                w = re.search(r'\bwidth="([^"]*)"', nested.group(0))
                ht = re.search(r'\bheight="([^"]*)"', nested.group(0))
                if not (w and ht and w.group(1) == ht.group(1)):
                    problems.append(f"nested svg width/height are "
                                    f"{w.group(1) if w else '?'} / "
                                    f"{ht.group(1) if ht else '?'} (want equal)")
                end = fav.find("</svg>", nested.end())
                if ds and end > 0 and f' d="{ds[0]}"' not in fav[nested.start():end]:
                    problems.append("the X-mark path is not inside the nested svg")
            self.add("c18_favicon_svg_structure", not problems,
                     "assets/favicon.svg — " + "; ".join(problems))

        # ---- Contract 19: placements and use-ref counts -----------------------
        if htm is None:
            self._html_missing("c19a_first_section_has_hero_mark")
            self._html_missing("c19b_last_section_has_mark_and_wordmark")
            self._html_missing("c19c_use_reference_counts")
        else:
            secs = top_level_sections(htm)
            self.add("c19a_first_section_has_hero_mark",
                     bool(secs) and HERO_MARK_SVG in secs[0],
                     "first top-level <section> does not contain "
                     f"{HERO_MARK_SVG!r}" if secs else "no top-level <section> found")
            self.add("c19b_last_section_has_mark_and_wordmark",
                     bool(secs) and CLOSING_MARK_SVG in secs[-1] and CLOSING_WORDMARK_SVG in secs[-1],
                     "last top-level <section> must hold the logomark and the wordmark as "
                     f"separate elements: {CLOSING_MARK_SVG!r} and {CLOSING_WORDMARK_SVG!r}"
                     if secs else "no top-level <section> found")
            nm, nl = htm.count('href="#mark"'), htm.count('href="#wordmark"')
            # mark: title hero, chrome bar, value-flow tree root, closing slide
            ok = nm == 4 and nl == 1
            self.add("c19c_use_reference_counts", ok,
                     f'href="#mark" appears {nm}× (want 4), '
                     f'href="#wordmark" appears {nl}× (want 1) in index.html')

        # ---- Contract 20: logo rule sizes, chrome svg rule frozen -------------
        if css is None:
            self._css_missing("c20a_hero_mark_520px")
            self._css_missing("c20b_closing_logo_rules_exact")
            self._css_missing("c20c_deck_chrome_svg_rule_unchanged")
        else:
            rules = collections.defaultdict(dict)
            for sel, p, v in parse_declarations(css_nc):
                if sel in LOGO_RULE_SELECTORS:
                    rules[sel][p] = v
            hm = rules.get(".s-title .hero-mark", {})
            self.add("c20a_hero_mark_520px",
                     hm.get("width") == "520px" and hm.get("height") == "520px",
                     f".s-title .hero-mark has width={hm.get('width')!r} "
                     f"height={hm.get('height')!r} (want 520px/520px)"
                     if not hm else
                     f".s-title .hero-mark rule missing in theme/sombra.css")
            cm = rules.get(".s-closing .closing-mark")
            cw = rules.get(".s-closing .closing-wordmark", {})
            want_cm = {"width": "140px", "height": "140px", "margin-bottom": "56px"}
            ok = cm == want_cm and cw.get("width") == "258px" and cw.get("height") == "60px"
            self.add("c20b_closing_logo_rules_exact", ok,
                     f".s-closing .closing-mark is {cm!r} (want {want_cm!r}); "
                     f".s-closing .closing-wordmark is {cw!r} (want width 258px, height 60px)")

            def rule_text(c):
                m = re.search(r"\.deck-chrome svg\s*\{[^}]*\}", c)
                return m.group(0) if m else None

            got_rule, base_rule = rule_text(css), rule_text(bcss)
            self.add("c20c_deck_chrome_svg_rule_unchanged",
                     got_rule is not None and got_rule == base_rule,
                     f".deck-chrome svg rule is {got_rule!r}, baseline is "
                     f"{base_rule!r}" if got_rule != base_rule
                     else "")

        # ---- Contract 21: no transforms/tints on the logo --------------------
        if fav is None:
            self.add("c21a_favicon_no_transform_keywords", False,
                     f"assets/favicon.svg not found under {self.root}")
        else:
            bad = [t for t in ("preserveAspectRatio", "rotate(", "skew",
                               "matrix(", "scale(") if t in fav]
            self.add("c21a_favicon_no_transform_keywords", not bad,
                     "forbidden transform keyword(s) in assets/favicon.svg: "
                     + ", ".join(bad))
        if htm is None:
            self._html_missing("c21b_html_no_preserve_aspect_ratio")
        else:
            ln = line_of(htm, "preserveAspectRatio")
            self.add("c21b_html_no_preserve_aspect_ratio", ln is None,
                     f"preserveAspectRatio in index.html line {ln}" if ln else "")
        if css is None:
            self._css_missing("c21c_logo_css_rules_no_effect_props")
        else:
            bad = []
            for sel in LOGO_RULE_SELECTORS:
                for p, v in rules.get(sel, {}).items():
                    if p in ("opacity", "filter", "fill", "color"):
                        bad.append(f"{sel}: property {p!r}")
                    for kw in ("rotate", "scale", "skew", "matrix"):
                        if kw in v:
                            bad.append(f"{sel}: {p} value contains {kw!r} ({v})")
            self.add("c21c_logo_css_rules_no_effect_props", not bad,
                     "logo CSS rule(s) carry transform/opacity/filter/fill/color — "
                     + "; ".join(bad[:6]))

        # ---- Contract 22: @font-face blocks byte-identical --------------------
        self.add("c22_font_face_blocks_unchanged",
                 css is not None and
                 re.findall(r"@font-face\s*\{[^}]*\}", css, re.S) ==
                 re.findall(r"@font-face\s*\{[^}]*\}", bcss, re.S) and
                 len(re.findall(r"@font-face\s*\{[^}]*\}", bcss, re.S)) == 6,
                 self._diff_detail(
                     re.findall(r"@font-face\s*\{[^}]*\}", css, re.S) if css else [],
                     re.findall(r"@font-face\s*\{[^}]*\}", bcss, re.S),
                     "@font-face block(s) in theme/sombra.css differ from baseline"))

        self.add("c22b_display_font_file_exists",
                 (Path(self.root) / DISPLAY_FONT_FILE).is_file(),
                 f"{DISPLAY_FONT_FILE} is missing")

        # ---- Contract 23: the four --f-* lines byte-identical ------------------
        fline = lambda c: re.findall(r"^[ \t]*--f-(?:display|body|serif|mono):[^\n]*",
                                     c, re.M)
        self.add("c23_font_token_lines_unchanged",
                 css is not None and fline(css) == fline(bcss)
                 and len(fline(bcss)) == 4,
                 self._diff_detail(fline(css) if css else [], fline(bcss),
                                   "--f-* token line(s) in theme/sombra.css differ "
                                   "from baseline"))

        # ---- Contract 25: 21 sections -----------------------------------------
        self.add("c25a_exactly_21_top_level_sections",
                 htm is not None and len(top_level_sections(htm)) == 21,
                 f"index.html has {0 if htm is None else len(top_level_sections(htm))} "
                 f"top-level <section> elements (want 21)")

        # ------------------------------------------------------------------
        # RETIRED (2026-11-10), after phase 1 shipped at a8e95c2:
        #   c25b_slide_texts_unchanged,
        #   c26_html_outside_svg_equals_baseline_two_subs,
        #   c27_non_paint_declarations_frozen,
        #   c30_inline_style_attrs_frozen,
        #   c31_deck_check_parity
        # These migration guards compared the deck with the pre-re-theme
        # baseline 66369c3 to prove phase 1 changed no text and no geometry.
        # Their job is done; keeping them would forbid any legitimate
        # content edit (the e01–e19 contracts below are the new content
        # contract). Their now-unused helpers (slide_text, geo_counter et
        # al., _styles_ok, _first_diff) and constants (ADDED_DECLARATIONS,
        # REMOVED_SELECTORS, PAINT_PROPS, EXPECTED_DECK_FAILS) were removed.
        # ------------------------------------------------------------------

        # RETIRED (2026-11-11): c28_diagram_svgs_unchanged_minus_paint_attrs
        # froze the two phase-1 diagrams; the v2 slide system redraws them.

        # ---- Contract 29: icon symbols and markers -----------------------------
        icons = lambda h: re.findall(r'<symbol id="i-[^"]*"[^>]*>.*?</symbol>', h, re.S)
        self.add("c29a_icon_symbols_unchanged",
                 htm is not None and icons(htm) == icons(bhtml)
                 and len(icons(htm)) == 17,
                 f"icon <symbol id=\"i-…\"> set differs from baseline; candidate "
                 f"has {0 if htm is None else len(icons(htm))} (want 17)")
        markers = lambda h: [FILL_ATTR_RE.sub("", x)
                             for x in re.findall(r"<marker\b.*?</marker>", h, re.S)]
        self.add("c29b_markers_unchanged_apart_fill",
                 htm is not None and markers(htm) == markers(bhtml)
                 and len(markers(htm)) == 2,
                 f"<marker> elements differ from baseline apart from fill; "
                 f"candidate has {0 if htm is None else len(markers(htm))} (want 2)")

        # ---- Content-edit contracts (e01–e19) ----------------------------------
        # The four approved content edits. Written TDD-style BEFORE the
        # edits: most are RED on the current deck by design.
        if htm is None:
            for n in E_NAMES:
                self._html_missing(n)
        else:
            secs = top_level_sections(htm)

            # -- Edit 1: dividers (slides 7, 12, 17) --------------------------
            divs = {i: secs[i - 1] for i in DIVIDER_SLIDES if i <= len(secs)}
            bad = [i for i, s in sorted(divs.items())
                   if re.search(r'<div class="num"', s)]
            self.add("e01_dividers_no_num_element", not bad,
                     "divider slide(s) still contain a <div class=\"num\"> "
                     "numeral element: " + ", ".join(str(b) for b in bad))
            bad = [i for i, s in sorted(divs.items())
                   if re.search(r"\b0[123]\b", visible_text(s))]
            self.add("e02_dividers_no_numeral_text", not bad,
                     "divider slide(s) still show a '01'/'02'/'03' numeral: "
                     + ", ".join(str(b) for b in bad))
            bad = [i + 1 for i, s in enumerate(secs)
                   if PART_WORD_RE.search(visible_text(s))]
            self.add("e03_no_part_word_anywhere", not bad,
                     "'Part one/two/three/four' visible on slide(s): "
                     + ", ".join(str(b) for b in bad))
            got = eyebrow_text(divs[17]) if 17 in divs else None
            self.add("e04_divider3_eyebrow_integration_architecture",
                     got == "Integration architecture",
                     "slide 17 eyebrow is "
                     f"{got!r}, want 'Integration architecture'")
            bad = {i: h2_text(s) for i, s in divs.items()
                   if h2_text(s) != DIVIDER_HEADINGS.get(i)}
            self.add("e05_divider_headings_unchanged", not bad,
                     "divider h2 text changed — " + "; ".join(
                         f"slide {i}: {w!r}" for i, w in sorted(bad.items())))

            # -- Edit 2: slide 11 (compliance card) ----------------------------
            s11 = secs[10] if len(secs) > 10 else ""
            c11 = card_blocks(s11)
            h11 = [card_heading(c) for c in c11]
            self.add("e06_compliance_private_withdrawals_card",
                     "Private withdrawals" in h11,
                     "slide 11 has no card headed 'Private withdrawals' "
                     f"(headings found: {h11!r})")
            m = ONOFFRAMP_RE.search(visible_text(s11))
            self.add("e07_compliance_no_onofframps_text", m is None,
                     "slide 11 visible text still contains "
                     f"{m.group(0)!r}" if m else "")
            wd = [c for c in c11 if card_heading(c) == "Private withdrawals"]
            if not wd:
                self.add("e08_withdrawals_card_body_terms", False,
                         "no 'Private withdrawals' card to inspect on slide 11")
            else:
                body = card_body(wd[0]).lower()
                missing = [t for t in ("relayer", "private deposits",
                                       "coming soon") if t not in body]
                self.add("e08_withdrawals_card_body_terms", not missing,
                         "'Private withdrawals' card body is missing "
                         f"{missing!r}; body: {card_body(wd[0])[:90]!r}…")
            self.add("e09_compliance_card_set_unchanged",
                     collections.Counter(h11) ==
                     collections.Counter(COMPLIANCE_CARD_HEADINGS),
                     "slide 11 card headings are "
                     f"{h11!r}, want exactly {sorted(COMPLIANCE_CARD_HEADINGS)!r}")

            # -- Edit 3: slide 15 (comparison table row tags) -------------------
            s15 = secs[14] if len(secs) > 14 else ""
            tags = [inner for _name, inner in ROW_TAG_RE.findall(s15)]
            tag_texts = [strip_tags(t) for t in tags]
            self.add("e10_table_exactly_two_row_tags", len(tags) == 2,
                     f"slide 15 has {len(tags)} element(s) with class "
                     f"'row-tag' (want exactly 2): {tag_texts!r}")
            self.add("e11_row_tag_texts",
                     tag_texts == ["Fund safety", "Privacy"],
                     "row-tag visible texts are "
                     f"{tag_texts!r}, want ['Fund safety', 'Privacy']")
            rows = table_rows(s15, "tbody")

            def _tags_in(row):
                return [strip_tags(t) for _n, t in ROW_TAG_RE.findall(row)]

            fund_rows = [r for r in rows if "Proof system" in strip_tags(r)]
            priv_rows = [r for r in rows
                         if "Quantum-safe note encryption" in strip_tags(r)]
            problems = []
            if not fund_rows:
                problems.append("no <tr> containing the row label 'Proof system'")
            elif "Fund safety" not in _tags_in(fund_rows[0]):
                problems.append(
                    f"'Proof system' row tag(s) are {_tags_in(fund_rows[0])!r}, "
                    "want 'Fund safety'")
            if not priv_rows:
                problems.append(
                    "no <tr> containing the row label 'Quantum-safe note encryption'")
            elif "Privacy" not in _tags_in(priv_rows[0]):
                problems.append(
                    f"'Quantum-safe note encryption' row tag(s) are "
                    f"{_tags_in(priv_rows[0])!r}, want 'Privacy'")
            self.add("e12_row_tags_in_right_rows", not problems,
                     "slide 15 — " + "; ".join(problems))
            bad = [t for t in tags if YES_MARK not in t]
            self.add("e13_row_tags_use_yes_mark", not bad,
                     "row-tag cell(s) without the table's yes mark "
                     '<span class="yes" role="img" aria-label="yes"></span>: '
                     + ", ".join(repr(t[:60]) for t in bad))
            thead_m = re.search(r"<thead>(.*?)</thead>", s15, re.S)
            tbody_m = re.search(r"<tbody>(.*?)</tbody>", s15, re.S)
            headers = []
            if thead_m:
                ths = re.findall(r'<th[^>]*scope="col"[^>]*>(.*?)</th>',
                                 thead_m.group(1), re.S)
                headers = [th_main_text(t) for t in ths[1:]]
            labels = []
            if tbody_m:
                labels = [th_main_text(t) for t in re.findall(
                    r'<th[^>]*scope="row"[^>]*>(.*?)</th>', tbody_m.group(1), re.S)]
            bad = []
            if headers != list(TABLE_COLUMN_HEADERS):
                bad.append(f"column headers are {headers!r}, want "
                           f"{list(TABLE_COLUMN_HEADERS)!r}")
            if labels != list(TABLE_ROW_LABELS):
                bad.append(f"row labels are {labels!r}, want "
                           f"{list(TABLE_ROW_LABELS)!r}")
            self.add("e14_table_headers_and_row_labels_unchanged", not bad,
                     "slide 15 — " + "; ".join(bad))
            widths, carry = [], 0
            for row in rows:
                cells = re.findall(r"<t[dh]\b[^>]*>", row)
                widths.append(len(cells) + carry)
                rs = [int(m.group(1)) for m in
                      (re.search(r'\browspan="(\d+)"', c) for c in cells) if m]
                carry = sum(r - 1 for r in rs)
            ok = bool(widths) and all(w == widths[0] for w in widths)
            self.add("e15_table_body_row_widths_consistent", ok,
                     "slide 15 body row widths (own cells + carried rowspan) "
                     f"are {widths!r}, want all equal")

            # -- Edit 4: slide 18 (integration grid card) -----------------------
            s18 = secs[17] if len(secs) > 17 else ""
            c18 = card_blocks(s18)
            h18 = [card_heading(c) for c in c18]
            self.add("e16_integration_private_defi_card",
                     "Private DeFi" in h18,
                     "slide 18 has no card headed 'Private DeFi' "
                     f"(headings found: {h18!r})")
            bad = [h for h in h18 if h and re.search(r"onramp|offramp", h, re.I)]
            self.add("e17_integration_no_onramp_offramp_headings", not bad,
                     "slide 18 card heading(s) still contain 'onramp'/'offramp': "
                     + ", ".join(repr(h) for h in bad))
            pd = [c for c in c18 if card_heading(c) == "Private DeFi"]
            if not pd:
                self.add("e18_private_defi_description_ok", False,
                         "no 'Private DeFi' card to inspect on slide 18")
            else:
                body = card_body(pd[0])
                problems = []
                if len(body) < 40:
                    problems.append(f"description is {len(body)} char(s), "
                                    "want at least 40")
                if "private deposits" in body.lower():
                    problems.append("description contains the phrase "
                                    "'private deposits'")
                self.add("e18_private_defi_description_ok", not problems,
                         "slide 18 'Private DeFi' card — " + "; ".join(problems)
                         + (f"; description: {body[:90]!r}…" if problems else ""))
            self.add("e19_integration_card_set_unchanged",
                     collections.Counter(h18) ==
                     collections.Counter(INTEGRATION_CARD_HEADINGS),
                     "slide 18 card headings are "
                     f"{h18!r}, want exactly {sorted(INTEGRATION_CARD_HEADINGS)!r}")

    # -- helpers ---------------------------------------------------------------
    def _check_symbol(self, name, htm, sym_id, viewBox, want_hash):
        if htm is None:
            self._html_missing(name)
            return
        tag = f'<symbol id="{sym_id}" viewBox="{viewBox}">'
        hits = [m.start() for m in re.finditer(re.escape(tag), htm)]
        if len(hits) != 1:
            self.add(name, False,
                     f"exactly one {tag!r} required in index.html, found "
                     f"{len(hits)}")
            return
        end = htm.find("</symbol>", hits[0])
        if end < 0:
            self.add(name, False, f"{tag!r} has no </symbol>")
            return
        body = htm[hits[0] + len(tag):end]
        paths = re.findall(r'<path fill="#FCF9F2" fill-rule="evenodd" d="([^"]+)"/>',
                           body)
        if body.count("<") != 1 or len(paths) != 1:
            self.add(name, False,
                     f"symbol {sym_id!r} must hold exactly one "
                     '<path fill="#FCF9F2" fill-rule="evenodd" d="…"/>'
                     f" and nothing else; body is: {body[:80]!r}…")
            return
        got = sha256_of(paths[0])
        self.add(name, got == want_hash,
                 f"symbol {sym_id!r} path d hash is {got}, want {want_hash}")

    def _diff_detail(self, got, want, prefix):
        if got == want:
            return ""
        extra = [x for x in got if x not in want][:2]
        missing = [x for x in want if x not in got][:2]
        return (f"{prefix} — candidate-only: {extra}; baseline-only: {missing}")


# Contract 10 / 12 token tables (one named check each).
C10_TOKENS = (
    ("c10a_css_no_gradient", "gradient("),
    ("c10b_css_no_box_shadow", "box-shadow"),
    ("c10c_css_no_blur", "blur("),
    ("c10d_css_no_mix_blend_mode", "mix-blend-mode"),
    ("c10e_css_no_feturbulence", "feTurbulence"),
    ("c10f_css_no_background_clip", "background-clip"),
    ("c10g_css_no_grad_text", "grad-text"),
)
C10_NAMES = [n for n, _ in C10_TOKENS] + ["c10h_css_no_filter_declaration"]

C12_TOKENS = (
    ("c12a_html_no_linear_gradient", "<linearGradient"),
    ("c12b_html_no_radial_gradient", "<radialGradient"),
    ("c12c_html_no_filter_element", "<filter"),
    ("c12d_html_no_filter_attr", "filter="),
    ("c12e_html_no_fe_gaussian_blur", "feGaussianBlur"),
    ("c12f_html_no_url_g_refs", "url(#g-"),
    ("c12g_html_no_url_f_refs", "url(#f-"),
    ("c12h_html_no_stop_color", "stop-color"),
    ("c12i_html_no_grad_text", "grad-text"),
)
C12_NAMES = [n for n, _ in C12_TOKENS]

# The content-edit checks (e01–e19), in run order.
E_NAMES = (
    "e01_dividers_no_num_element",
    "e02_dividers_no_numeral_text",
    "e03_no_part_word_anywhere",
    "e04_divider3_eyebrow_integration_architecture",
    "e05_divider_headings_unchanged",
    "e06_compliance_private_withdrawals_card",
    "e07_compliance_no_onofframps_text",
    "e08_withdrawals_card_body_terms",
    "e09_compliance_card_set_unchanged",
    "e10_table_exactly_two_row_tags",
    "e11_row_tag_texts",
    "e12_row_tags_in_right_rows",
    "e13_row_tags_use_yes_mark",
    "e14_table_headers_and_row_labels_unchanged",
    "e15_table_body_row_widths_consistent",
    "e16_integration_private_defi_card",
    "e17_integration_no_onramp_offramp_headings",
    "e18_private_defi_description_ok",
    "e19_integration_card_set_unchanged",
)

CHECK_NAMES = (
    ["c01_css_hex_literals_in_palette", "c02_css_rgb_rgba_palette_and_alpha",
     "c02b_css_no_exotic_colour_functions", "c03_css_no_named_colours_in_values",
     "c04_css_literals_only_in_root_plus_4_mask_inks",
     "c05a_root_colour_token_values", "c05b_root_structural_tokens_unchanged",
     "c05c_root_no_other_custom_properties", "c06a_no_legacy_token_names",
     "c06b_all_var_references_defined", "c07a_html_hex_literals_in_palette",
     "c07b_html_no_colour_functions", "c07c_html_no_named_colours_in_paint_attrs",
     "c08_assets_exactly_favicon_with_ink_and_white",
     "c09_canyon_colour_only_in_no_rule"]
    + C10_NAMES
    + ["c11_css_text_shadow_none_exactly_once"]
    + C12_NAMES
    + ["c13_html_fragment_refs_resolve", "c14a_favicon_link_exactly_once",
       "c14b_favicon_file_exists", "c14c_no_sombra_mark_string",
       "c15_no_eclipse_or_corona", "c16_chrome_bar_markup_bytes",
       "c17a_symbol_mark_exact", "c17b_symbol_wordmark_exact", "c17c_no_lockup",
       "c18_favicon_svg_structure", "c19a_first_section_has_hero_mark",
       "c19b_last_section_has_mark_and_wordmark", "c19c_use_reference_counts",
       "c20a_hero_mark_520px", "c20b_closing_logo_rules_exact",
       "c20c_deck_chrome_svg_rule_unchanged",
       "c21a_favicon_no_transform_keywords",
       "c21b_html_no_preserve_aspect_ratio",
       "c21c_logo_css_rules_no_effect_props",
       "c22_font_face_blocks_unchanged", "c22b_display_font_file_exists",
       "c23_font_token_lines_unchanged",
       "c25a_exactly_21_top_level_sections",
       "c29a_icon_symbols_unchanged", "c29b_markers_unchanged_apart_fill"]
    + list(E_NAMES)
)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv):
    root = REPO
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--root":
            i += 1
            if i >= len(argv):
                print("ERROR: --root requires a PATH")
                return 2
            root = Path(argv[i]).resolve()
        elif a.startswith("--root="):
            root = Path(a.split("=", 1)[1]).resolve()
        else:
            print(f"ERROR: unknown argument: {a} "
                  f"(usage: brand_check.py [--root PATH])")
            return 2
        i += 1

    if not root.is_dir():
        print(f"ERROR: root not a directory: {root}")
        return 2

    base_html = git_show("index.html")
    base_css = git_show("theme/sombra.css")

    chk = Checker(root, base_html, base_css)
    chk.run()

    print(f"brand_check: {root}")
    print(f"baseline: git {BASE_COMMIT} (index.html {len(base_html.encode('utf-8'))} B, "
          f"theme/sombra.css {len(base_css.encode('utf-8'))} B)\n")
    for name, status, detail in chk.results:
        tag = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[status]
        line = f"[{tag}] {name}"
        if status == "fail" and detail:
            line += f" — {detail}"
        if status == "skip" and detail:
            line += f" — {detail}"
        print(line)
    passed = sum(1 for _, s, _ in chk.results if s == "pass")
    failed = sum(1 for _, s, _ in chk.results if s == "fail")
    skipped = sum(1 for _, s, _ in chk.results if s == "skip")
    total = len(chk.results)
    print(f"\n{passed} passed, {failed} failed"
          + (f", {skipped} skipped" if skipped else "")
          + f", {total} total")
    if failed:
        print("RESULT: RED (failures listed above)")
        return 1
    print("RESULT: GREEN" + (" (skips noted above)" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
