# Yash Kaushik portfolio

The portfolio at [yashkaushik.dev](https://yashkaushik.dev/) is a seven-page static HTML and CSS site hosted on GitHub Pages. There is no build step.

## Preview and verify locally

Run these commands from the repository root with Python 3.

```sh
python -m http.server 8899 --bind 127.0.0.1
```

Open `http://127.0.0.1:8899/`. In a second terminal, run:

```sh
python verify.py
python -m compileall .
```

The verifier checks page structure, navigation, local links, canonical URLs, Open Graph metadata, homepage JSON-LD, sitemap coverage, CSS classes, and social image dimensions. It also checks for superseded figures and present-tense employment claims. Preview the site at mobile and desktop widths, and use the keyboard to check the skip link and navigation.

## GitHub Pages workflow

Start changes from `main` on a feature branch. Open a pull request against `main` and include the verification results and any factual questions for review. Merge only after the owner approves publication. GitHub Pages publishes from the root of `main` and serves the site on the custom domain. Keep `CNAME`, canonical URLs, `robots.txt`, and `sitemap.xml` aligned with that domain. The site uses `.html` links for compatibility with GitHub Pages and the local server. `_redirects` is a legacy Netlify file.

The checked-in raster assets are ready to serve. To regenerate just the social image, install Pillow and run:

```sh
python -c "from make_assets import build_og_card; build_og_card().save('og.png', 'PNG', optimize=True)"
```

The asset generator uses Georgia and Calibri on Windows and Liberation Serif and Sans on Linux. The full `python make_assets.py` command also regenerates the raster favicons.

## Add a public project

Add a separate public-project section to `projects.html` when there is a completed write-up. Reuse the existing case-study layout with a stable anchor, a result, the problem, the contribution and technical approach, the validation or deployment status, and the technology stack. Include verified public links when available. Review claims and disclosure before publishing.
