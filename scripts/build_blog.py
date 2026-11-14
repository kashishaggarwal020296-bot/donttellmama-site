#!/usr/bin/env python3
"""
Builds the DTM blog from Markdown source files.

Reads every *.md file in blog-content/ (except files starting with "_",
which are templates/drafts, not posts), renders each into a styled static
HTML page at blog/<slug>.html using templates/layout.html, and regenerates
blog/index.html listing all published posts newest-first.

Run manually with:  python3 scripts/build_blog.py
The GitHub Action in .github/workflows/build-blog.yml runs this
automatically whenever a file under blog-content/ changes on main.
"""
import datetime as dt
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, "blog-content")
OUT_DIR = os.path.join(ROOT, "blog")
LAYOUT_PATH = os.path.join(ROOT, "templates", "layout.html")
SITEMAP_PATH = os.path.join(ROOT, "sitemap.xml")
SITE_URL = "https://donttellmama.in"


def update_sitemap(posts):
    """Rewrites the auto-generated block in sitemap.xml between the
    BLOG-URLS markers to list the blog index + every published post,
    leaving the rest of the file (static pages) untouched."""
    if not os.path.isfile(SITEMAP_PATH):
        return
    with open(SITEMAP_PATH, "r", encoding="utf-8") as f:
        sitemap = f.read()

    entries = [f"""  <url>
    <loc>{SITE_URL}/blog/</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>"""]
    for post in posts:
        entries.append(f"""  <url>
    <loc>{SITE_URL}/blog/{post['slug']}.html</loc>
    <lastmod>{post['date'].isoformat()}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>""")
    block = "\n".join(entries)

    pattern = re.compile(
        r"(<!-- BLOG-URLS-START.*?-->\n)(.*?)(\n?\s*<!-- BLOG-URLS-END -->)",
        re.DOTALL,
    )
    if not pattern.search(sitemap):
        print("WARNING: BLOG-URLS markers not found in sitemap.xml — skipping sitemap update", file=sys.stderr)
        return
    sitemap = pattern.sub(lambda m: m.group(1) + block + m.group(3), sitemap)
    with open(SITEMAP_PATH, "w", encoding="utf-8") as f:
        f.write(sitemap)
    print("updated", SITEMAP_PATH)



def parse_frontmatter(text):
    """Pulls simple "key: value" frontmatter between --- fences off the top
    of a file. Returns (dict, remaining_body_text)."""
    m = re.match(r"^---\s*\n(.*?\n)---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError("missing --- frontmatter block at top of file")
    meta = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip().lower()] = value.strip()
    return meta, m.group(2)


def inline_md(text):
    """Bold / italic / links, applied within one line or paragraph."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def markdown_to_html(body):
    """Minimal Markdown -> HTML: ## / ### headings, blank-line paragraphs,
    "- " bullet lists, "> " blockquotes, plus inline bold/italic/links."""
    lines = body.replace("\r\n", "\n").split("\n")
    out = []
    i = 0
    para = []

    def flush_para():
        if para:
            out.append("<p>" + inline_md(" ".join(para).strip()) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            flush_para()
            i += 1
            continue

        if stripped.startswith("### "):
            flush_para()
            out.append("<h3>" + inline_md(stripped[4:].strip()) + "</h3>")
            i += 1
            continue

        if stripped.startswith("## "):
            flush_para()
            out.append("<h2>" + inline_md(stripped[3:].strip()) + "</h2>")
            i += 1
            continue

        if stripped.startswith("- "):
            flush_para()
            items = []
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("## ", "### ")):
                first = lines[i].strip()
                if first.startswith("- "):
                    item_lines = [first[2:].strip()]
                    i += 1
                    # Soft-wrapped continuation lines: anything non-blank that
                    # doesn't start a new bullet, heading or quote.
                    while (i < len(lines) and lines[i].strip()
                           and not lines[i].strip().startswith(("- ", "## ", "### ", "> "))):
                        item_lines.append(lines[i].strip())
                        i += 1
                    items.append("<li>" + inline_md(" ".join(item_lines)) + "</li>")
                else:
                    break
            out.append("<ul>" + "".join(items) + "</ul>")
            continue

        if stripped.startswith("> "):
            flush_para()
            quote_lines = [stripped[2:].strip()]
            i += 1
            while (i < len(lines) and lines[i].strip()
                   and not lines[i].strip().startswith(("- ", "## ", "### "))):
                nxt = lines[i].strip()
                quote_lines.append(nxt[2:].strip() if nxt.startswith("> ") else nxt)
                i += 1
            out.append("<blockquote><p>" + inline_md(" ".join(quote_lines)) + "</p></blockquote>")
            continue

        para.append(stripped)
        i += 1

    flush_para()
    return "\n".join(out)


def slugify(name):
    name = re.sub(r"\.md$", "", name, flags=re.IGNORECASE)
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9]+", "-", name).strip("-")
    return name


def load_posts():
    posts = []
    if not os.path.isdir(CONTENT_DIR):
        return posts
    for fname in sorted(os.listdir(CONTENT_DIR)):
        if not fname.endswith(".md") or fname.startswith("_"):
            continue
        path = os.path.join(CONTENT_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        try:
            meta, body = parse_frontmatter(raw)
        except ValueError as e:
            print(f"SKIPPING {fname}: {e}", file=sys.stderr)
            continue
        for required in ("title", "description", "date"):
            if required not in meta:
                print(f"SKIPPING {fname}: missing required '{required}:' field", file=sys.stderr)
                break
        else:
            slug = meta.get("slug") or slugify(fname)
            try:
                post_date = dt.datetime.strptime(meta["date"], "%Y-%m-%d").date()
            except ValueError:
                print(f"SKIPPING {fname}: date must be YYYY-MM-DD, got '{meta['date']}'", file=sys.stderr)
                continue
            posts.append({
                "slug": slug,
                "title": meta["title"],
                "description": meta["description"],
                "date": post_date,
                "body_html": markdown_to_html(body),
            })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def render_page(layout, title, description, canonical, body_html, page_css="", page_css_960="", page_css_1000=""):
    page = layout
    page = page.replace("{{TITLE}}", html.escape(title, quote=True))
    page = page.replace("{{DESCRIPTION}}", html.escape(description, quote=True))
    page = page.replace("{{CANONICAL}}", canonical)
    page = page.replace("{{PAGE_CSS}}", page_css)
    page = page.replace("{{PAGE_CSS_960}}", page_css_960)
    page = page.replace("{{PAGE_CSS_1000}}", page_css_1000)
    page = page.replace("{{BODY}}", body_html)
    return page


BLOG_CSS = """
  /* ---- BLOG ---- */
  .bloghero{position:relative;padding:168px 0 60px;text-align:center;overflow:hidden;}
  .bloghero::before{content:"";position:absolute;inset:0;z-index:0;
    background:radial-gradient(ellipse at 50% 0%, rgba(215,162,35,.10), transparent 60%);}
  .bloghero-inner{position:relative;z-index:1;max-width:720px;margin:0 auto;padding:0 32px;}
  .bloghero .cap{display:inline-flex;align-items:center;gap:9px;font-family:var(--sans);font-size:12px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);margin-bottom:22px;}
  .bloghero h1{font-family:var(--serif);font-weight:600;color:var(--cream);font-size:clamp(38px,6vw,60px);line-height:1.04;text-transform:uppercase;letter-spacing:.01em;}
  .bloghero .sub{font-family:var(--serif);font-style:italic;font-size:clamp(17px,2vw,21px);color:var(--cream);opacity:.88;margin-top:18px;}

  .blog-list{padding:10px 0 110px;}
  .blog-grid{max-width:800px;margin:0 auto;display:flex;flex-direction:column;gap:0;}
  .blog-card{display:block;border-bottom:1px solid rgba(215,162,35,.16);padding:34px 4px;}
  .blog-card:first-child{border-top:1px solid rgba(215,162,35,.16);}
  .blog-card .meta{font-family:var(--sans);font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);}
  .blog-card h2{font-family:var(--serif);font-weight:600;font-size:clamp(22px,3vw,30px);color:var(--cream);margin-top:10px;line-height:1.2;}
  .blog-card p{font-family:var(--serif);font-style:italic;font-size:15px;color:var(--cream-dim);margin-top:10px;line-height:1.6;max-width:62ch;}
  .blog-card .more{display:inline-block;font-family:var(--sans);font-size:11.5px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--cream);opacity:.8;margin-top:14px;transition:opacity .2s,color .2s;}
  .blog-card:hover .more{opacity:1;color:var(--gold);}
  .blog-empty{text-align:center;font-family:var(--serif);font-style:italic;font-size:16px;color:var(--cream-dim);padding:40px 0;}

  .blogpost-hero{padding:150px 0 10px;text-align:center;}
  .blogpost-hero .wrap{max-width:760px;}
  .blogpost-hero .back{display:inline-block;font-family:var(--sans);font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--cream-dim);margin-bottom:28px;transition:color .2s;}
  .blogpost-hero .back:hover{color:var(--gold);}
  .blogpost-hero .meta{font-family:var(--sans);font-size:11px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);}
  .blogpost-hero h1{font-family:var(--serif);font-weight:600;font-size:clamp(30px,4.6vw,48px);color:var(--cream);line-height:1.1;margin-top:16px;text-wrap:balance;}

  .blogpost-body{max-width:680px;margin:0 auto;padding:50px 0 60px;}
  .blogpost-body p{font-family:var(--sans);font-size:16px;font-weight:300;color:var(--cream);opacity:.92;line-height:1.8;margin-bottom:22px;}
  .blogpost-body h2{font-family:var(--serif);font-weight:600;font-size:clamp(24px,3.2vw,32px);color:var(--cream);margin:40px 0 18px;line-height:1.2;}
  .blogpost-body h3{font-family:var(--serif);font-weight:600;font-size:21px;color:var(--gold-soft);margin:30px 0 14px;}
  .blogpost-body ul{margin:0 0 22px 22px;}
  .blogpost-body li{font-family:var(--sans);font-size:16px;font-weight:300;color:var(--cream);opacity:.92;line-height:1.8;margin-bottom:8px;}
  .blogpost-body a{color:var(--gold);border-bottom:1px solid rgba(215,162,35,.4);}
  .blogpost-body a:hover{color:#f0c250;}
  .blogpost-body blockquote{border-left:2px solid var(--gold);padding-left:20px;margin:28px 0;font-family:var(--serif);font-style:italic;font-size:19px;color:var(--cream);}
  .blogpost-foot{max-width:680px;margin:0 auto;padding:30px 0 90px;border-top:1px solid rgba(215,162,35,.16);text-align:center;}
  .blogpost-foot a{display:inline-block;margin-top:20px;}
"""

BLOG_CSS_960 = """
"""

BLOG_CSS_1000 = """
    .bloghero{padding:130px 0 40px;}
    .blogpost-hero{padding:120px 0 10px;}
"""


def main():
    with open(LAYOUT_PATH, "r", encoding="utf-8") as f:
        layout = f.read()

    os.makedirs(OUT_DIR, exist_ok=True)
    posts = load_posts()

    # Individual post pages
    for post in posts:
        back = '<a class="back" href="/blog/">← All Stories</a>'
        hero = f"""
<section class="blogpost-hero">
  <div class="wrap">
    {back}
    <div class="meta">{post['date'].strftime('%B %-d, %Y')}</div>
    <h1>{html.escape(post['title'])}</h1>
  </div>
</section>
<article class="blogpost-body wrap">
{post['body_html']}
</article>
<div class="blogpost-foot wrap">
  <a class="btn-gold-lg" href="/blog/">← Back to All Stories</a>
</div>
"""
        page = render_page(
            layout,
            title=f"{post['title']} — Don't Tell Mama",
            description=post["description"],
            canonical=f"{SITE_URL}/blog/{post['slug']}.html",
            body_html=hero,
            page_css=BLOG_CSS,
            page_css_960=BLOG_CSS_960,
            page_css_1000=BLOG_CSS_1000,
        )
        out_path = os.path.join(OUT_DIR, f"{post['slug']}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page)
        print("wrote", out_path)

    # Index / listing page
    if posts:
        cards = []
        for post in posts:
            cards.append(f"""
      <a class="blog-card" href="/blog/{post['slug']}.html">
        <div class="meta">{post['date'].strftime('%B %-d, %Y')}</div>
        <h2>{html.escape(post['title'])}</h2>
        <p>{html.escape(post['description'])}</p>
        <span class="more">Read the story →</span>
      </a>""")
        grid_html = "".join(cards)
    else:
        grid_html = '<p class="blog-empty">New stories are on the way — check back soon.</p>'

    index_body = f"""
<section class="bloghero">
  <div class="bloghero-inner">
    <span class="cap">Bar &amp; Resto · Est. 2010 · Bengaluru</span>
    <div class="diamond"></div>
    <h1 style="margin-top:14px;">The Blog</h1>
    <p class="sub">Stories from the rooftop, HSR Layout and beyond.</p>
  </div>
</section>
<section class="blog-list">
  <div class="wrap">
    <div class="blog-grid">{grid_html}
    </div>
  </div>
</section>
"""
    index_page = render_page(
        layout,
        title="The Blog — Don't Tell Mama",
        description="Stories, guides and ideas from Don't Tell Mama — HSR Layout's rooftop bar and restaurant.",
        canonical=f"{SITE_URL}/blog/",
        body_html=index_body,
        page_css=BLOG_CSS + "\n  .diamond{width:8px;height:8px;background:var(--gold);transform:rotate(45deg);margin:0 auto;}",
        page_css_960=BLOG_CSS_960,
        page_css_1000=BLOG_CSS_1000,
    )
    index_path = os.path.join(OUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_page)
    print("wrote", index_path, f"({len(posts)} posts)")

    update_sitemap(posts)


if __name__ == "__main__":
    main()
