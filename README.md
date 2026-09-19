# Yash Kaushik portfolio

Static HTML and CSS portfolio for yashkaushik.dev. No build step.
Updated from `D:/Lab/Git/port` on 2026-09-19. The repository's `CNAME`
and Git configuration were preserved; the old ZIP snapshot was excluded.

## Preview and verify

Requires Python 3.13 for the development tools; the website requires no Python.

```powershell
python -m http.server 8899 --bind 127.0.0.1
# Open http://127.0.0.1:8899/
```

```powershell
python verify.py
python -m compileall .
```

Verification checks page structure, local file links, navigation, metadata,
sitemap coverage, CSS class coverage and the social image dimensions.
It does not validate external links, browser layout or full accessibility.

`make_assets.py` optionally regenerates the raster assets. It requires Pillow
and the Windows Georgia/Calibri fonts. Existing assets are ready to use.

## Publishing

Publish the seven HTML pages, style.css, favicon.svg, favicon.ico,
apple-touch-icon.png, og.png, robots.txt, sitemap.xml and CNAME.
Include `_redirects` for Netlify. Keep development scripts and archives out
of the public upload. Hosting configuration is unchanged by this merge.
Local previews use `.html` URLs; the supplied clean-URL rewrites are specific
to Netlify. Nothing has been deployed by this merge.

## Review follow-ups

- Add a public code sample when available. Contact contains an inactive GitHub
  placeholder; enable it only when its target exists.
- Focus the contact-page role list around your primary Developer Experience
  positioning; it currently ranges from SRE to Engineering Program Manager.
- Visually test all pages at mobile and desktop widths, including keyboard
  operation of the mobile menu, before publishing.

The merge adds skip links, current-page navigation semantics, larger mobile
menu targets and semantic project headings without changing career claims.

The portfolio serves as the resume; no downloadable resume is planned.
Project summaries lead with outcomes and separate validation evidence from
user impact, with prototype and rollout limitations stated explicitly.
