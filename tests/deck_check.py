#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deck_check.py — automated content contract for the Sombra reveal.js deck.

Target:  index.html (single-file deck, vendored reveal.js, no build step).
Status:  written TDD-style BEFORE the planned v1-feedback edits. Checks A, B
         and C are expected to be RED until the deck is edited; checks D and
         F must be GREEN now and must stay GREEN after the edits.

Usage (one command; Python 3 stdlib only; no network; deterministic):
    python3 tests/deck_check.py             # run all checks (exit 0 = all green)
    python3 tests/deck_check.py --snapshot  # (re)capture tests/fixtures/ from the CURRENT deck

Spec mapping:
  A  slide "What Sombra is": cipher fix — "ChaCha20" appears nowhere in
     index.html (checked case-insensitively); "AES-256-GCM" appears on the
     "What Sombra is" slide; "ML-KEM-768" stays on that slide.
  B  slide "Precise about post-quantum": "ML-DSA-65" appears on that slide;
     "hybrid ML-KEM TLS" (case-insensitive, incl. "hybrid" within 40
     non-tag chars of "TLS") appears nowhere; no bare "ML-DSA" without the
     "-65" suffix anywhere (regex ML-DSA(?!-65)).
  C  five NEW top-level <section> slides with exact ids, positions and
     content:
       intro-you-we      immediately after the title slide
       privacy-not-funds after the first divider, before harvest-now slide
       bunker-mode       immediately after the Q-Day slide
       crypto-agility    immediately after "Precise about post-quantum"
       latency           immediately after the comparison table slide
     total top-level <section> count == 25.
  D  unchanged slides compared (whitespace-normalized) against snapshots in
     tests/fixtures/: Compliance posture, Integration points, Live demo.
     Plus surviving strings: "Live · devnet", "rotated after every use",
     "trial-decrypt", "odd amounts" (all case-insensitive substrings).
  E  agenda slide: no check (per spec).
  F  sanity: HTML parses, every <section> tag balanced (strict tag balance
     checked too), no duplicate id attributes.

Slides are located by unique content markers (never by hard-coded index),
because the planned edits insert five slides and shift all later positions.
Markers were verified unique against the current 20-slide deck.
"""

import html
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DECK = REPO / "index.html"
FIXTURES = HERE / "fixtures"

# HTML5 void elements (no end tag, must not be pushed on the tag stack).
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# D-group: fixture file -> (unique content marker, human label).
# Fixtures are captured from the UNEDITED deck via `--snapshot`.
FIXTURE_SPECS = [
    ("compliance-posture.html", "compliance posture", "Compliance posture slide"),
    ("integration-points.html", "integration points", "Integration points slide"),
    ("live-demo.html", "live demo · devnet", "Live demo slide"),
]

# D-group: strings that must survive the edits (case-insensitive substrings).
SURVIVING_STRINGS = [
    ("d_badge_live_devnet_still_present", "live · devnet"),
    ("d_rotated_after_every_use_still_present", "rotated after every use"),
    ("d_trial_decrypt_still_present", "trial-decrypt"),
    ("d_odd_amounts_still_present", "odd amounts"),
]

# "hybrid" adjacent to "TLS": within 40 chars, not crossing a tag boundary.
HYBRID_TLS_RE = re.compile(
    r"hybrid\b[^<>]{0,40}\btls\b|\btls\b[^<>]{0,40}\bhybrid", re.IGNORECASE
)
# Bare ML-DSA without the -65 suffix (case-sensitive, per spec).
BARE_MLDSA_RE = re.compile(r"ML-DSA(?!-65)")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

@dataclass
class Slide:
    seq: int          # 1-based order of appearance (all sections)
    depth: int        # 0 = top-level <section>, >0 = nested (reveal vertical)
    id: object        # id attribute value (None if absent)
    cls: object       # class attribute value (None if absent)
    raw: str          # exact inner HTML, sliced from the source

    @property
    def text(self):
        """Inner HTML with tags stripped and entities decoded."""
        return html.unescape(re.sub(r"<[^>]*>", " ", self.raw))


class DeckParser(HTMLParser):
    """Extracts <section> slides (with exact inner HTML), tag balance state
    and all id attributes from the raw deck source."""

    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.raw = raw
        self.line_starts = [0]
        for i, ch in enumerate(raw):
            if ch == "\n":
                self.line_starts.append(i + 1)
        self.tag_stack = []       # open non-void tags
        self.section_stack = []   # open <section> frames: [inner_start, depth, attrs]
        self.sections = []        # all sections, in document order
        self.ids = []
        self.errors = []
        self.balanced = True

    def _abs(self, line, col):
        return self.line_starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "section":
            depth = len(self.section_stack)
            tag_start = self._abs(*self.getpos())
            tag_end = self.raw.find(">", tag_start) + 1
            self.section_stack.append([tag_end, depth, attrs])
        if tag not in VOID_TAGS:
            self.tag_stack.append(tag)
        if "id" in attrs:
            self.ids.append(attrs["id"])

    def handle_endtag(self, tag):
        if tag == "section":
            if not self.section_stack:
                self.balanced = False
                self.errors.append("stray </section> with no open <section>")
                return
            end_pos = self._abs(*self.getpos())
            inner_start, depth, attrs = self.section_stack.pop()
            self.sections.append(Slide(
                seq=len(self.sections) + 1,
                depth=depth,
                id=attrs.get("id"),
                cls=attrs.get("class"),
                raw=self.raw[inner_start:end_pos],
            ))
        if tag not in VOID_TAGS:
            if tag in self.tag_stack:
                while self.tag_stack and self.tag_stack[-1] != tag:
                    skipped = self.tag_stack.pop()
                    self.balanced = False
                    self.errors.append(
                        f"<{skipped}> implicitly closed by </{tag}> (unbalanced)")
                self.tag_stack.pop()
            elif self.tag_stack:
                self.balanced = False
                self.errors.append(f"stray </{tag}> (top of stack: <{self.tag_stack[-1]}>)")
            else:
                self.balanced = False
                self.errors.append(f"stray </{tag}> on empty tag stack")

    def close(self):
        super().close()
        if self.tag_stack:
            self.balanced = False
            for tag in self.tag_stack:
                self.errors.append(f"<{tag}> never closed")
        if self.section_stack:
            self.balanced = False
            for _, depth, _ in self.section_stack:
                self.errors.append(f"<section> (depth {depth}) never closed")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_slides(slides, marker):
    m = marker.lower()
    return [s for s in slides if m in s.text.lower()]


def anchor(slides, marker, label):
    """Return the unique top-level slide matching `marker`, else an error."""
    hits = find_slides(slides, marker)
    if len(hits) != 1:
        return None, f"anchor slide '{label}' not found uniquely (matched {len(hits)})"
    return hits[0], None


def norm_ws(s):
    """Whitespace normalization for D-group snapshot comparison."""
    return re.sub(r"\s+", " ", s).strip()


def content_failures(text, spec):
    """spec: list of (predicate(text) -> bool, description). Returns [failed]."""
    return [desc for pred, desc in spec if not pred(text)]


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def run_checks(raw, parser, slides):
    results = []  # (name, ok, detail)

    def add(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    # ---- F: sanity ---------------------------------------------------------
    add("sanity_html_parses_and_sections_balanced",
        parser.balanced, "; ".join(parser.errors[:6]))

    dups = sorted({i for i in parser.ids if parser.ids.count(i) > 1})
    add("sanity_no_duplicate_ids", not dups,
        "duplicate id(s): " + ", ".join(dups) if dups else "")

    # ---- A: "What Sombra is" cipher fix ------------------------------------
    a1 = "chacha20" not in raw.lower()
    add("a_no_chacha20_anywhere", a1,
        "'ChaCha20' (case-insensitive) still present in index.html" if not a1 else "")

    what, err = anchor(slides, "what sombra is", "What Sombra is")
    if err:
        add("a_aes256gcm_in_what_sombra_is_slide", False, err)
        add("a_mlkem768_in_what_sombra_is_slide", False, err)
    else:
        t = what.text
        add("a_aes256gcm_in_what_sombra_is_slide", "AES-256-GCM" in t,
            "'AES-256-GCM' missing from 'What Sombra is' slide")
        add("a_mlkem768_in_what_sombra_is_slide", "ML-KEM-768" in t,
            "'ML-KEM-768' missing from 'What Sombra is' slide")

    # ---- B: "Precise about post-quantum" fixes -----------------------------
    pq, err = anchor(slides, "precise about", "Precise about post-quantum")
    if err:
        add("b_mldsa65_in_precise_slide", False, err)
    else:
        add("b_mldsa65_in_precise_slide", "ML-DSA-65" in pq.text,
            "'ML-DSA-65' missing from 'Precise about post-quantum' slide")

    hyb = HYBRID_TLS_RE.search(raw)
    add("b_no_hybrid_ml_kem_tls_anywhere", hyb is None,
        f"'hybrid … TLS' found near char {hyb.start()}" if hyb else "")

    bare = BARE_MLDSA_RE.search(raw)
    add("b_no_bare_mldsa_anywhere", bare is None,
        f"bare 'ML-DSA' (no -65 suffix) found near char {bare.start()}" if bare else "")

    # ---- C: five new top-level slides ---------------------------------------
    def slide_by_id(sid):
        return [s for s in slides if s.id == sid]

    def position_after(sid, anchor_marker, anchor_label, slides_by_pos=slides):
        hits = slide_by_id(sid)
        if len(hits) != 1:
            return f"no top-level <section id=\"{sid}\"> exists"
        a, err = anchor(slides, anchor_marker, anchor_label)
        if err:
            return err
        want = slides.index(a) + 1
        got = slides.index(hits[0])
        if got != want:
            return (f"id=\"{sid}\" at position {got + 1} (1-based); "
                    f"expected {want + 1} (immediately after {anchor_label})")
        return None

    def between(sid, lo_marker, hi_marker):
        hits = slide_by_id(sid)
        if len(hits) != 1:
            return f"no top-level <section id=\"{sid}\"> exists"
        lo, e1 = anchor(slides, lo_marker, "first divider")
        hi, e2 = anchor(slides, hi_marker, "harvest-now slide")
        if e1 or e2:
            return e1 or e2
        i = slides.index(hits[0])
        if not (slides.index(lo) < i < slides.index(hi)):
            return (f"id=\"{sid}\" at position {i + 1} (1-based); expected "
                    f"between the first divider (pos {slides.index(lo) + 1}) "
                    f"and the harvest-now slide (pos {slides.index(hi) + 1})")
        return None

    # C1: intro-you-we
    hits = slide_by_id("intro-you-we")
    add("c_intro_you_we_exists_after_title",
        len(hits) == 1 and position_after("intro-you-we",
            "scale or die", "title slide") is None,
        position_after("intro-you-we", "scale or die", "title slide")
        or f"no top-level <section id=\"intro-you-we\"> exists")
    add("c_intro_you_we_content", len(hits) == 1 and not content_failures(
        hits[0].text, [
            (lambda t: re.search(r"\byou\b", t, re.IGNORECASE), 'word "You" present'),
            (lambda t: re.search(r"\bwe\b", t, re.IGNORECASE), 'word "We" present'),
            (lambda t: ("forever" in t.lower() or "permanent" in t.lower()),
             '"forever" or "permanent" present'),
        ]),
        "; ".join(content_failures(hits[0].text, [
            (lambda t: re.search(r"\byou\b", t, re.IGNORECASE), 'word "You" present'),
            (lambda t: re.search(r"\bwe\b", t, re.IGNORECASE), 'word "We" present'),
            (lambda t: ("forever" in t.lower() or "permanent" in t.lower()),
             '"forever" or "permanent" present'),
        ])) if hits else "slide does not exist")

    # C2: privacy-not-funds
    hits = slide_by_id("privacy-not-funds")
    pos_err = between("privacy-not-funds", "part one", "harvest now, decrypt later")
    add("c_privacy_not_funds_exists_between_divider1_and_harvest",
        len(hits) == 1 and pos_err is None, pos_err or
        f"no top-level <section id=\"privacy-not-funds\"> exists")
    spec = [
        (lambda t: "privacy" in t.lower(), '"privacy" present'),
        (lambda t: "harvester" in t.lower(), '"harvester" present'),
        (lambda t: ("fork" in t.lower() or "migrat" in t.lower()),
         '"fork" or "migrat" present'),
    ]
    add("c_privacy_not_funds_content",
        len(hits) == 1 and not content_failures(hits[0].text, spec),
        "; ".join(content_failures(hits[0].text, spec)) if hits else "slide does not exist")

    # C3: bunker-mode
    hits = slide_by_id("bunker-mode")
    pos_err = position_after("bunker-mode", "q-day is a moving target", "Q-Day slide")
    add("c_bunker_mode_exists_after_qday",
        len(hits) == 1 and pos_err is None, pos_err or
        f"no top-level <section id=\"bunker-mode\"> exists")
    spec = [
        (lambda t: re.search(r"bunker\s+mode", t, re.IGNORECASE), '"bunker mode" present'),
        (lambda t: "Drake" in t, '"Drake" present'),
        (lambda t: "Vitalik" in t, '"Vitalik" present'),
        (lambda t: "signature" in t.lower(), '"signature" present'),
    ]
    add("c_bunker_mode_content",
        len(hits) == 1 and not content_failures(hits[0].text, spec),
        "; ".join(content_failures(hits[0].text, spec)) if hits else "slide does not exist")

    # C4: crypto-agility
    hits = slide_by_id("crypto-agility")
    pos_err = position_after("crypto-agility", "precise about",
                             "Precise about post-quantum slide")
    add("c_crypto_agility_exists_after_precise",
        len(hits) == 1 and pos_err is None, pos_err or
        f"no top-level <section id=\"crypto-agility\"> exists")
    spec = [
        (lambda t: "agility" in t.lower(), '"agility" present'),
        (lambda t: "harvest" in t.lower(), '"harvest" present'),
        (lambda t: "circuit" in t, '"circuit" present'),
        (lambda t: "HQC" in t, '"HQC" present'),
        (lambda t: "Ed25519" in t, '"Ed25519" present'),
    ]
    add("c_crypto_agility_content",
        len(hits) == 1 and not content_failures(hits[0].text, spec),
        "; ".join(content_failures(hits[0].text, spec)) if hits else "slide does not exist")

    # C5: latency
    hits = slide_by_id("latency")
    pos_err = position_after("latency", "how sombra compares", "comparison table slide")
    add("c_latency_exists_after_table",
        len(hits) == 1 and pos_err is None, pos_err or
        f"no top-level <section id=\"latency\"> exists")
    spec = [
        (lambda t: "latency" in t.lower(), '"latency" present'),
        (lambda t: "proof" in t, '"proof" present'),
        (lambda t: "finality" in t.lower(), '"finality" present'),
        (lambda t: "bytes" in t.lower(), '"bytes" present'),
        (lambda t: "1,088" in t, '"1,088" present'),
    ]
    add("c_latency_content",
        len(hits) == 1 and not content_failures(hits[0].text, spec),
        "; ".join(content_failures(hits[0].text, spec)) if hits else "slide does not exist")

    # C6: total count
    add("c_total_top_level_sections_is_25", len(slides) == 25,
        f"found {len(slides)} top-level <section> slides (expected 25)")

    # ---- D: unchanged slides + surviving strings -----------------------------
    for fname, marker, label in FIXTURE_SPECS:
        name = "d_" + Path(fname).stem.replace("-", "_") + "_unchanged"
        slide, err = anchor(slides, marker, label)
        if err:
            add(name, False, err)
            continue
        fpath = FIXTURES / fname
        if not fpath.exists():
            add(name, False,
                f"fixture tests/fixtures/{fname} missing — run "
                "python3 tests/deck_check.py --snapshot")
            continue
        live, stored = norm_ws(slide.raw), norm_ws(fpath.read_text(encoding="utf-8"))
        add(name, live == stored,
            "" if live == stored
            else f"{label} drifted from tests/fixtures/{fname} "
                 "(whitespace-normalized comparison)")

    for name, needle in SURVIVING_STRINGS:
        add(name, needle in raw.lower(), f"'{needle}' (case-insensitive) not found")

    return results


def snapshot_fixtures(slides):
    """Capture D-group fixtures from the CURRENT deck. Returns exit code."""
    FIXTURES.mkdir(parents=True, exist_ok=True)
    rc = 0
    for fname, marker, label in FIXTURE_SPECS:
        hits = find_slides(slides, marker)
        if len(hits) != 1:
            print(f"[FAIL] snapshot {fname}: anchor '{label}' matched "
                  f"{len(hits)} slides — nothing written")
            rc = 1
            continue
        (FIXTURES / fname).write_text(hits[0].raw + "\n", encoding="utf-8")
        print(f"[OK]   wrote tests/fixtures/{fname} "
              f"({len(hits[0].raw)} chars) from '{label}' slide")
    return rc


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv):
    if not DECK.exists():
        print(f"ERROR: deck not found at {DECK}")
        return 2
    raw = DECK.read_text(encoding="utf-8")
    parser = DeckParser(raw)
    parser.feed(raw)
    parser.close()
    slides = [s for s in parser.sections if s.depth == 0]

    if "--snapshot" in argv:
        print(f"snapshot mode: capturing fixtures from {DECK} "
              f"({len(slides)} top-level sections)")
        return snapshot_fixtures(slides)

    results = run_checks(raw, parser, slides)
    print(f"deck_check: {DECK}")
    print(f"top-level <section> slides found: {len(slides)}\n")
    for name, ok, detail in results:
        tag = "PASS" if ok else "FAIL"
        line = f"[{tag}] {name}"
        if not ok and detail:
            line += f" — {detail}"
        print(line)
    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed
    print(f"\n{passed} passed, {failed} failed, {len(results)} total")
    if failed:
        print("RESULT: RED (failures listed above)")
        return 1
    print("RESULT: GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
