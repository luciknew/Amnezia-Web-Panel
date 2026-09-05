"""Cover-site generator for the Telegram WEB proxy.

Upstream deliberately ships no starter site: identical bodies across relay
hosts are an easy active-probe signature (PUBLIC_SITE.md). So we synthesize a
per-install site instead of copying a template -- different palette, fonts,
section order and copy on every server. It is still only a starting point;
the panel tells the admin to replace it with real content.

The site is linked with real filenames (/about.html, /favicon.svg) because the
config selects `static_routes: "exact"` -- extensionless paths are only resolved
in the relay's legacy routing mode.

The relay no longer imposes a CSP or cache policy on static files, but we keep
the site free of inline <style>/<script>, forms, third-party resources, service
workers and frames: a service worker covering / could intercept the bridge
navigation, and the rest just keeps the page boring to a classifier.
"""

import random

_PALETTES = [
    ("#12161c", "#f4f6f8", "#5b8def", "#8a94a6"),
    ("#1d1a17", "#faf7f2", "#c2703d", "#8c8378"),
    ("#101a17", "#f2f7f5", "#3f9e7c", "#7d8f88"),
    ("#181422", "#f7f4fb", "#8b6bd9", "#8d86a0"),
    ("#1a1113", "#fbf4f5", "#c04a5c", "#9a868a"),
    ("#0f1720", "#f1f5f9", "#2f8fb0", "#7f8b96"),
]

_FONTS = [
    '"Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif',
    '"Helvetica Neue", Helvetica, Arial, sans-serif',
    '"Charter", "Bitstream Charter", Cambria, Georgia, serif',
    '"Segoe UI", Roboto, "Noto Sans", system-ui, sans-serif',
    'Optima, Candara, "Trebuchet MS", sans-serif',
]

_SECTION_POOL = [
    ("What we do", [
        "We keep a small workshop and take on a handful of projects each season.",
        "Most of our work starts as a conversation and ends as something physical.",
        "We prefer fewer commissions done properly over a full calendar.",
    ]),
    ("How we work", [
        "Every project begins with a survey and a written estimate.",
        "We quote once, in writing, and the number does not move afterwards.",
        "Scheduling is first come, first served; we do not keep a waiting list.",
    ]),
    ("Materials", [
        "Stock is sourced locally where we can and documented where we cannot.",
        "Offcuts go back into smaller pieces rather than into a skip.",
        "We keep records of every batch so a repair years later is still possible.",
    ]),
    ("Visiting", [
        "The workshop is open on weekday afternoons, though it is best to write first.",
        "Parking is limited; the tram stop two streets over is easier.",
        "There is usually coffee, and always sawdust.",
    ]),
    ("History", [
        "The business has changed hands twice and premises three times.",
        "Some of the machines predate the current building by decades.",
        "The archive of drawings goes back further than anyone still working here.",
    ]),
]

_ABOUT_LINES = [
    "This site is a small, deliberately plain record of what we do.",
    "There is no newsletter, no tracking and nothing to sign up for.",
    "If you want to reach us, the workshop address is on the front page.",
    "Pages here change rarely, which suits everyone involved.",
]


def generate_site(name, tagline='', seed=None):
    """Return {relative_path: content} for a self-contained static site."""
    rng = random.Random(seed)
    ink, paper, accent, muted = rng.choice(_PALETTES)
    font = rng.choice(_FONTS)
    radius = rng.choice(['0', '2px', '4px', '10px'])
    max_width = rng.choice(['34rem', '38rem', '42rem', '46rem'])
    name = (name or 'Workshop').strip()
    tagline = (tagline or '').strip()

    sections = rng.sample(_SECTION_POOL, rng.randint(2, 4))
    body = []
    for heading, options in sections:
        body.append(f"    <section>\n      <h2>{_esc(heading)}</h2>\n"
                    f"      <p>{_esc(rng.choice(options))}</p>\n    </section>")

    styles = f""":root {{
  --ink: {ink};
  --paper: {paper};
  --accent: {accent};
  --muted: {muted};
}}

* {{ box-sizing: border-box; }}

body {{
  margin: 0;
  padding: 3rem 1.5rem 4rem;
  background: var(--paper);
  color: var(--ink);
  font-family: {font};
  line-height: 1.65;
}}

main {{ max-width: {max_width}; margin: 0 auto; }}

h1 {{ font-size: 2rem; margin: 0 0 .25rem; letter-spacing: -.01em; }}

h2 {{ font-size: 1.05rem; margin: 2.25rem 0 .4rem; color: var(--accent); }}

p {{ margin: 0 0 .8rem; }}

.tagline {{ color: var(--muted); margin-bottom: 2.5rem; }}

nav {{ margin-top: 3rem; border-top: 1px solid var(--muted); padding-top: 1rem; }}

nav a {{
  color: var(--accent);
  margin-right: 1rem;
  text-decoration: none;
  border-radius: {radius};
}}

nav a:hover {{ text-decoration: underline; }}

footer {{ margin-top: 2rem; color: var(--muted); font-size: .85rem; }}

@media (prefers-color-scheme: dark) {{
  body {{ background: var(--ink); color: var(--paper); }}
}}
"""

    def page(title, inner):
        return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<link rel="stylesheet" href="/styles.css">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
</head>
<body>
  <main>
{inner}
    <nav><a href="/">Home</a><a href="/about.html">About</a></nav>
    <footer>{_esc(name)}</footer>
  </main>
</body>
</html>
"""

    index_inner = (f"    <h1>{_esc(name)}</h1>\n"
                   + (f'    <p class="tagline">{_esc(tagline)}</p>\n' if tagline else "")
                   + "\n".join(body))
    about_inner = ("    <h1>About</h1>\n"
                   + "\n".join(f"    <p>{_esc(line)}</p>" for line in rng.sample(_ABOUT_LINES, 3)))
    notfound_inner = "    <h1>Not found</h1>\n    <p>That page is not here.</p>"

    glyph = _esc(name[0].upper() if name else 'W')
    favicon = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
               f'<rect width="64" height="64" rx="{rng.choice([0, 6, 12, 32])}" fill="{accent}"/>'
               f'<text x="32" y="43" font-size="34" font-family="serif" text-anchor="middle" '
               f'fill="{paper}">{glyph}</text></svg>\n')

    return {
        'index.html': page(name, index_inner),
        'about.html': page(f"About - {name}", about_inner),
        '404.html': page("Not found", notfound_inner),
        'styles.css': styles,
        'favicon.svg': favicon,
        'robots.txt': "User-agent: *\nDisallow:\n",
    }


def _esc(text):
    return (str(text).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))
