from __future__ import annotations

import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://junkejiang.com"
TODAY = "2026-04-27"
CURRENT_TITLE = "Research Associate"
CURRENT_EMAIL = "junke.jiang@york.ac.uk"
OLD_EMAIL = "junke.jiang@" + "insa-rennes.fr"
OLD_TITLE = "Associate " + "Research " + "Fellow"


NAV_ITEMS = [
    ("Home", "/"),
    ("Research", "/research/"),
    ("Publications", "/publication/"),
    ("CV", "/experience/"),
    ("Teaching", "/teaching/"),
    ("Contact", "/#contact"),
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def active_for(path: str, href: str) -> bool:
    if href == "/":
        return path == "index.html"
    if href == "/research/":
        return path.startswith("research/") or path.startswith("projects/")
    if href == "/publication/":
        return path.startswith("publication/") or path.startswith("publication_types/")
    if href == "/experience/":
        return path.startswith("experience/")
    if href == "/teaching/":
        return path.startswith("teaching/")
    return False


def nav_html(path: str) -> str:
    items = []
    for label, href in NAV_ITEMS:
        klass = "nav-link active" if active_for(path, href) else "nav-link"
        items.append(f'<li class=nav-item><a class="{klass}" href={href}>{label}</a></li>')
    return (
        '<ul id=nav-menu class="navbar-nav order-3 hidden lg:flex w-full pb-6 '
        'lg:order-1 lg:w-auto lg:space-x-2 lg:pb-0 xl:space-x-8 justify-left">'
        + "".join(items)
        + "</ul>"
    )


def update_nav_and_shared_head(s: str, path: str) -> str:
    s = re.sub(r"<ul id=nav-menu\b.*?</ul>", nav_html(path), s, count=1, flags=re.S)
    if "/css/profile-polish.css" not in s:
        s = s.replace("</head>", "<link rel=stylesheet href=/css/profile-polish.css></head>", 1)
    s = s.replace('@GetResearchDev', '@junke_jiang')
    s = s.replace("© 2025 Junke Jiang", "© 2026 Junke Jiang")
    s = s.replace(OLD_TITLE, CURRENT_TITLE)
    s = s.replace(OLD_EMAIL, CURRENT_EMAIL)
    s = remove_public_citation_links(s)
    return s


def remove_public_citation_links(s: str) -> str:
    bib_link = re.compile(
        r'<a\b(?=[^>]*href=(?:"[^"]*(?:cite\.bib|junkejiang\.bib)"|[^\s>]*(?:cite\.bib|junkejiang\.bib)))[^>]*>.*?</a>',
        flags=re.S | re.I,
    )
    s = bib_link.sub("", s)
    s = re.sub(r"<div class=mt-3><div>\s*</div></div>", "", s)
    s = re.sub(r'<div class="flex flex-wrap space-x-3">\s*</div>', "", s)
    return s


def update_meta(s: str, title: str, description: str, url_path: str) -> str:
    url = f"{SITE_URL}{url_path}"
    esc_desc = html.escape(description, quote=True)
    esc_title = html.escape(title, quote=True)
    s = re.sub(r"<title>.*?</title>", f"<title>{esc_title}</title>", s, count=1, flags=re.S)
    s = re.sub(
        r'<meta name=description content(?:="[^"]*")?>',
        f'<meta name=description content="{esc_desc}">',
        s,
        count=1,
    )
    s = re.sub(r'<link rel=alternate hreflang=en-us href=[^>]+>', f'<link rel=alternate hreflang=en-us href={url}>', s, count=1)
    s = re.sub(r'<link rel=canonical href=[^>]+>', f'<link rel=canonical href={url}>', s, count=1)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', s, count=1)
    s = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc_title}">', s, count=1)
    s = re.sub(r'<meta property="og:description" content(?:="[^"]*")?>', f'<meta property="og:description" content="{esc_desc}">', s, count=1)
    s = re.sub(r'<meta property="og:updated_time" content="[^"]*">', f'<meta property="og:updated_time" content="{TODAY}T00:00:00+00:00">', s, count=1)
    return s


def replace_body(s: str, body: str) -> str:
    pattern = re.compile(r'<div class=(?:"page-body[^"]*"|page-body)>.*?(?=<div class=page-footer>)', re.S)
    if not pattern.search(s):
        raise ValueError("Could not find page body")
    return pattern.sub(body, s, count=1)


def publication_html(pub: dict[str, str]) -> str:
    title = html.escape(pub["title"])
    authors = html.escape(pub["authors"])
    venue = html.escape(pub["venue"])
    note = html.escape(pub.get("note", ""))
    doi = pub.get("doi", "")
    link = f'<a href="{doi}" target="_blank" rel="noopener">DOI</a>' if doi else ""
    note_html = f"<p>{note}</p>" if note else ""
    return (
        '<div class="jp-publication">'
        f"<h3>{title}</h3>"
        f"<p>{authors}</p>"
        f"<p><em>{venue}</em>{(' · ' + link) if link else ''}</p>"
        f"{note_html}</div>"
    )


SELECTED_PUBLICATIONS = [
    {
        "title": "Structure and device-operando photostability of quasi-2D Ruddlesden-Popper perovskites: engineering the spacer cation matters",
        "authors": "J. Duan#, J. Jiang#, U. Kim, J. W. Lee, Y. Yang, M. Choi, Z. Wu, J. Xi",
        "venue": "ACS Energy Letters, 2026, 11, 1714-1723",
        "doi": "https://doi.org/10.1021/acsenergylett.5c03228",
    },
    {
        "title": "Bidentate pyridine passivators attaching trifluoromethyl substitute groups in varied positions for efficient carbon-based perovskite solar cells",
        "authors": "M. Geng#, J. Jiang#, X. Ma, J. Li, K. Wang, L. Jiang, D. Lu, B. Li, Y. Gu, T. Xu",
        "venue": "ACS Applied Materials & Interfaces, 2025, 17, 64645-64654",
        "doi": "https://doi.org/10.1021/acsami.5c18690",
    },
    {
        "title": "Flexible and efficient semiempirical DFTB parameters for electronic structure prediction of 3D, 2D iodide perovskites and heterostructures",
        "authors": "J. Jiang, T. van der Heide, S. Thébaud, C. R. Lien-Medrano, A. Fihey, L. Pedesseau, C. Quarti, M. Zacharias, G. Volonakis, M. Kepenekian, B. Aradi, M. A. Sentef, J. Even, C. Katan",
        "venue": "Physical Review Materials, 2025, 9, 023803",
        "doi": "https://doi.org/10.1103/PhysRevMaterials.9.023803",
        "note": "Develops efficient DFTB parameters for electronic-structure prediction in 3D and 2D iodide perovskites.",
    },
    {
        "title": "Scale-up solutions of 2D perovskite photovoltaics: insights of multiscale structures",
        "authors": "J. Jiang#, J. You#, S. (Frank) Liu, J. Xi",
        "venue": "ACS Energy Letters, 2024, 9, 17-29",
        "doi": "https://doi.org/10.1021/acsenergylett.3c02009",
    },
    {
        "title": "On the mechanism of solvents catalyzed structural transformation in metal halide perovskites",
        "authors": "J. Xi#, J. Jiang#, H. Duim, L. Chen, J. You, G. Portale, S. (Frank) Liu, S. Tao, M. A. Loi",
        "venue": "Advanced Materials, 2023, 35, 2302896",
        "doi": "https://doi.org/10.1002/adma.202302896",
    },
    {
        "title": "Electronic coupling between perovskite nanocrystal and fullerene modulates hot carrier capture",
        "authors": "Y. Li#, J. Jiang#, D. Wang#, D. Liu, S. Yajima, H. Li, A. Fuchimoto, H. Li, G. Shi, S. Hayase, S. Tao, J. Shi, Q. Meng, C. Ding, Q. Shen",
        "venue": "Advanced Functional Materials, 2024, 2415735",
        "doi": "https://doi.org/10.1002/adfm.202415735",
    },
    {
        "title": "Multifunctional additive CdAc2 for efficient perovskite-based solar cells",
        "authors": "N. Ren#, P. Wang#, J. Jiang#, R. Li, W. Han, J. Liu, Z. Zhu, B. Chen, Q. Xu, T. Li, B. Shi, Q. Huang, D. Zhang, S. Apergi, G. Brocks, C. Zhu, S. Tao, Y. Zhao, X. Zhang",
        "venue": "Advanced Materials, 2023, 35, 2211806",
        "doi": "https://doi.org/10.1002/adma.202211806",
    },
    {
        "title": "Colloidal synthesis of size-confined CsAgCl2 nanocrystals: implications for electroluminescence applications",
        "authors": "S. Ji, X. Meng, X. Wang, T. Bai, R. Zhang, B. Yang, K. Han, J. Jiang*, F. Liu",
        "venue": "Materials Chemistry Frontiers, 2022, 6, 3669-3677",
        "doi": "https://doi.org/10.1039/D2QM00997H",
    },
    {
        "title": "The role of solvents in the formation of methylammonium lead triiodide perovskite",
        "authors": "J. Jiang, J. M. Vicent-Luna, S. Tao",
        "venue": "Journal of Energy Chemistry, 2022, 68, 393-400",
        "doi": "https://doi.org/10.1016/j.jechem.2021.12.030",
    },
    {
        "title": "Atomistic and electronic origin of phase instability of metal halide perovskites",
        "authors": "J. Jiang, F. Liu, I. Tranca, Q. Shen, S. Tao",
        "venue": "ACS Applied Energy Materials, 2020, 3, 11548-11558",
        "doi": "https://doi.org/10.1021/acsaem.0c00791",
    },
]


def selected_publications(limit: int | None = None) -> str:
    pubs = SELECTED_PUBLICATIONS[:limit] if limit else SELECTED_PUBLICATIONS
    return "".join(publication_html(pub) for pub in pubs)


def social_links_html() -> str:
    links = [
        (
            "ORCID",
            "https://orcid.org/0000-0003-2962-766X",
            '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11"></circle><text x="12" y="15" text-anchor="middle" font-size="8" fill="white" font-family="Arial, sans-serif">iD</text></svg>',
        ),
        (
            "Google Scholar",
            "https://scholar.google.com/citations?user=PoVXBKUAAAAJ&amp;hl=en",
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 1.8 8.8 12 14.6 22.2 8.8 12 3Zm-6.2 9.7V17l6.2 3.5 6.2-3.5v-4.3L12 16.2 5.8 12.7Z"></path></svg>',
        ),
        (
            "GitHub",
            "https://github.com/JunkeJiang",
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.5c-5.25 0-9.5 4.36-9.5 9.72 0 4.29 2.72 7.93 6.49 9.21.48.09.65-.21.65-.47 0-.23-.01-1-.01-1.82-2.64.59-3.2-1.15-3.2-1.15-.43-1.12-1.06-1.42-1.06-1.42-.87-.61.07-.6.07-.6.96.07 1.47 1.01 1.47 1.01.86 1.5 2.25 1.07 2.8.82.09-.64.34-1.07.61-1.32-2.11-.25-4.33-1.08-4.33-4.8 0-1.06.37-1.93.98-2.61-.1-.25-.43-1.24.09-2.58 0 0 .8-.26 2.61 1a8.82 8.82 0 0 1 4.76 0c1.81-1.26 2.61-1 2.61-1 .52 1.34.19 2.33.09 2.58.61.68.98 1.55.98 2.61 0 3.73-2.22 4.55-4.34 4.8.35.31.66.92.66 1.85 0 1.33-.01 2.4-.01 2.73 0 .26.17.57.66.47a9.73 9.73 0 0 0 6.48-9.21c0-5.36-4.25-9.72-9.5-9.72Z"></path></svg>',
        ),
        (
            "LinkedIn",
            "https://www.linkedin.com/in/junke-jiang-051289197/",
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.45 3H3.55A1.55 1.55 0 0 0 2 4.55v14.9A1.55 1.55 0 0 0 3.55 21h16.9A1.55 1.55 0 0 0 22 19.45V4.55A1.55 1.55 0 0 0 20.45 3ZM8.15 18.2H5.5V9.75h2.65v8.45ZM6.82 8.58a1.54 1.54 0 1 1 0-3.08 1.54 1.54 0 0 1 0 3.08Zm11.88 9.62h-2.65v-4.11c0-.98-.02-2.24-1.37-2.24-1.37 0-1.58 1.07-1.58 2.17v4.18h-2.64V9.75h2.53v1.15h.04c.35-.66 1.21-1.36 2.5-1.36 2.67 0 3.17 1.76 3.17 4.05v4.61Z"></path></svg>',
        ),
    ]
    return '<div class="jp-social-links" aria-label="Academic profiles">' + "".join(
        f'<a class="jp-social-link" href="{url}" target="_blank" rel="noopener" aria-label="{label} profile">{icon}<span>{label}</span></a>'
        for label, url, icon in links
    ) + "</div>"


def home_body() -> str:
    return f'''<div class="page-body jp-page">
<section class="jp-hero">
  <div class="jp-container jp-hero-grid">
    <div>
      <p class="jp-kicker">Computational materials science · Hybrid semiconductors</p>
      <h1 class="jp-title">Junke Jiang</h1>
      <p class="jp-subtitle">I develop quantum-mechanical and data-driven simulations to understand defects, phase stability, crystallization, and optoelectronic response in hybrid semiconductors and metal-halide perovskites.</p>
      <div class="jp-actions">
        <a class="jp-button" href="/research/">Research</a>
        <a class="jp-button jp-button--ghost" href="/publication/">Publications</a>
        <a class="jp-button jp-button--ghost" href="/experience/">CV</a>
      </div>
      {social_links_html()}
    </div>
    <aside class="jp-profile-card">
      <img src="/author/junke-jiang/avatar_hu_fcf3637ab42ba40b.jpg" alt="Junke Jiang">
      <h2>{CURRENT_TITLE}</h2>
      <p><a href="https://www.york.ac.uk/physics-engineering-technology/" target="_blank" rel="noopener">School of Physics, Engineering and Technology</a><br>University of York, United Kingdom</p>
      {social_links_html()}
      <ul class="jp-meta-list">
        <li>Current project: grain-boundary defect dynamics and machine-learning force-field development for hybrid semiconductors.</li>
        <li>Methods: DFT, DFTB, ab initio molecular dynamics, molecular dynamics, Python, Bash.</li>
      </ul>
    </aside>
  </div>
</section>
<section class="jp-section">
  <div class="jp-container jp-grid jp-grid--two">
    <div>
      <h2 class="jp-heading">Research Vision</h2>
      <p class="jp-lead">My research connects atomic-scale mechanisms to materials and device performance. I use first-principles theory, semiempirical electronic-structure methods, molecular dynamics, and emerging machine-learning potentials to model hybrid semiconductor materials across length and time scales that are difficult to access experimentally.</p>
    </div>
    <div class="jp-card">
      <h3>Current Direction</h3>
      <p>At York, I am focusing on defect dynamics at grain boundaries in hybrid semiconductors and on developing machine-learning force fields that can extend accurate simulations to larger, more realistic structures.</p>
      <div class="jp-tag-row">
        <span class="jp-tag">Hybrid semiconductors</span><span class="jp-tag">Defect dynamics</span><span class="jp-tag">ML force fields</span>
      </div>
    </div>
  </div>
</section>
<section class="jp-section jp-section--soft">
  <div class="jp-container">
    <h2 class="jp-heading">Research Areas</h2>
    <p class="jp-lead">These themes form the basis of an independent research program that can later expand into project, resource, and team pages as opportunities grow.</p>
    <div class="jp-grid">
      <article class="jp-card"><img src="/media/research/energy-materials.png" alt="Perovskite materials"><h3>Perovskite Stability and Formation</h3><p>Phase transitions, crystallization pathways, solvent-precursor coordination, and the atomistic origins of instability in lead-halide and lead-free perovskites.</p></article>
      <article class="jp-card"><img src="/media/research/electronic-structure.png" alt="Electronic structure modelling"><h3>Electronic-Structure Methods</h3><p>Efficient DFTB parameterization and electronic-structure prediction for 3D, 2D, and heterostructured iodide perovskites.</p></article>
      <article class="jp-card"><img src="/media/research/materials-design.png" alt="Materials design"><h3>Defects, Dopants, and Interfaces</h3><p>Surface engineering, ligand interactions, dopant effects, and grain-boundary defect dynamics in quantum dots and hybrid semiconductor materials.</p></article>
    </div>
  </div>
</section>
<section class="jp-section" id="papers">
  <div class="jp-container">
    <h2 class="jp-heading">Selected Publications</h2>
    <p class="jp-lead">Representative publications from the latest CV are shown below. For the complete and most current publication record, please see the publications page and Google Scholar.</p>
    {selected_publications(5)}
    <div class="jp-link-list">
      <a class="jp-button" href="/publication/">All publications</a>
      <a class="jp-button jp-button--ghost" href="https://scholar.google.com/citations?user=PoVXBKUAAAAJ&amp;hl=en" target="_blank" rel="noopener">Google Scholar</a>
    </div>
    <p class="jp-note"># Equal contribution. Citation counts and indices are intentionally not repeated here so they remain current through Google Scholar.</p>
  </div>
</section>
<section class="jp-section jp-section--soft" id="news">
  <div class="jp-container">
    <h2 class="jp-heading">Recent Highlights</h2>
    <ul class="jp-list">
      <li><h3>March 2026</h3><p>Joined the School of Physics, Engineering and Technology at the University of York as a Research Associate.</p></li>
      <li><h3>2026</h3><p>Co-first-author paper on device-operando photostability of quasi-2D Ruddlesden-Popper perovskites published in <em>ACS Energy Letters</em>.</p></li>
      <li><h3>2025</h3><p>Published DFTB parameters for electronic-structure prediction of iodide perovskites and heterostructures in <em>Physical Review Materials</em>.</p></li>
      <li><h3>2024-2025</h3><p>Presented work at MATSUS, E-MRS, and French national meetings on metal-halide perovskites and nanomaterials for energy.</p></li>
    </ul>
  </div>
</section>
<section class="jp-section" id="contact">
  <div class="jp-container jp-grid jp-grid--two">
    <div>
      <h2 class="jp-heading">Contact</h2>
      <p class="jp-lead">I welcome conversations on computational materials science, hybrid semiconductors, perovskite stability, DFTB methods, and machine-learning potentials.</p>
    </div>
    <div class="jp-card">
      <h3>Junke Jiang</h3>
      <p>School of Physics, Engineering and Technology<br>University of York, Heslington, York YO10 5DD, United Kingdom</p>
      <p>Email: <a href="mailto:{CURRENT_EMAIL}">{CURRENT_EMAIL}</a></p>
      {social_links_html()}
    </div>
  </div>
</section>
</div>'''


def research_body() -> str:
    return '''<div class="page-body jp-page">
<section class="jp-hero">
  <div class="jp-container">
    <p class="jp-kicker">Research</p>
    <h1 class="jp-title">Predictive simulations for hybrid semiconductors and perovskites</h1>
    <p class="jp-subtitle">My research program combines first-principles electronic-structure theory, semiempirical methods, molecular dynamics, and machine-learning force fields to connect atomic mechanisms with optoelectronic materials performance.</p>
  </div>
</section>
<section class="jp-section">
  <div class="jp-container jp-grid jp-grid--two">
    <article class="jp-card"><img src="/media/research/materials-design.png" alt="Hybrid semiconductor models"><h3>Grain-Boundary Defects and Machine-Learning Force Fields</h3><p>At York, I work on defect dynamics at grain boundaries in hybrid semiconductors and on developing machine-learning force fields for realistic, large-scale simulations.</p><div class="jp-tag-row"><span class="jp-tag">Defect dynamics</span><span class="jp-tag">ML potentials</span><span class="jp-tag">Hybrid semiconductors</span></div></article>
    <article class="jp-card"><img src="/media/research/energy-materials.png" alt="Perovskite stability"><h3>Perovskite Stability, Phase Transitions, and Formation</h3><p>I study the mechanisms that control phase stability, crystallization, solvent effects, and morphology in metal-halide perovskites using DFT and ab initio molecular dynamics.</p><div class="jp-tag-row"><span class="jp-tag">DFT</span><span class="jp-tag">AIMD</span><span class="jp-tag">Crystallization</span></div></article>
    <article class="jp-card"><img src="/media/research/electronic-structure.png" alt="Electronic structure methods"><h3>Efficient Electronic-Structure Methods</h3><p>A major direction is the development and validation of DFTB parameters for large periodic and non-periodic perovskite systems, including 3D, 2D, and heterostructured iodide perovskites.</p><div class="jp-tag-row"><span class="jp-tag">DFTB</span><span class="jp-tag">Electronic structure</span><span class="jp-tag">Large-scale simulation</span></div></article>
    <article class="jp-card"><img src="/media/research/semiconductor-devices.png" alt="Semiconductor device modelling"><h3>Optoelectronic and Dielectric Properties</h3><p>I use atomistic modelling to understand layered perovskites, quantum dots, dopants, surfaces, interfaces, and device-relevant behavior for photovoltaics and light-emitting applications.</p><div class="jp-tag-row"><span class="jp-tag">PV</span><span class="jp-tag">LED</span><span class="jp-tag">Interfaces</span></div></article>
  </div>
</section>
<section class="jp-section jp-section--soft">
  <div class="jp-container">
    <h2 class="jp-heading">Methodological Scope</h2>
    <ul class="jp-list">
      <li><h3>Quantum-mechanical modelling</h3><p>Density functional theory, DFT-1/2, semiempirical DFTB, and electronic-structure analysis for semiconductor materials.</p></li>
      <li><h3>Atomistic dynamics</h3><p>Molecular dynamics and ab initio molecular dynamics to follow phase transitions, surface processes, ligand interactions, and solvent-assisted transformations.</p></li>
      <li><h3>Data-driven simulation</h3><p>Machine-learning force-field development to reach larger structural models and longer timescales while retaining a physically grounded link to quantum-mechanical data.</p></li>
    </ul>
  </div>
</section>
</div>'''


def cv_body() -> str:
    return f'''<div class="page-body jp-page">
<section class="jp-hero">
  <div class="jp-container">
    <p class="jp-kicker">Academic CV</p>
    <h1 class="jp-title">Experience, Education, and Service</h1>
    <p class="jp-subtitle">Selected CV details are adapted into concise English for an international academic audience. Dates and roles are preserved from the latest source CV.</p>
    <div class="jp-actions"><a class="jp-button" href="/uploads/resume.pdf" target="_blank" rel="noopener">PDF CV (2026)</a><a class="jp-button jp-button--ghost" href="/#contact">Contact</a></div>
    {social_links_html()}
    <p class="jp-hero-contact">Email: <a href="mailto:{CURRENT_EMAIL}">{CURRENT_EMAIL}</a></p>
  </div>
</section>
<section class="jp-section">
  <div class="jp-container">
    <h2 class="jp-heading">Appointments</h2>
    <div class="jp-timeline">
      <div class="jp-timeline-item"><div class="jp-date">Mar 2026-present</div><div><h3>Research Associate · University of York</h3><p>School of Physics, Engineering and Technology, York, United Kingdom. Project: grain-boundary defect dynamics and machine-learning force-field development for hybrid semiconductors. Mentor: Prof. Keith McKenna.</p></div></div>
      <div class="jp-timeline-item"><div class="jp-date">Nov 2022-present</div><div><h3>Guest Researcher · Institut FOTON, INSA Rennes / University of Rennes</h3><p>Continuing collaboration on theory and simulation of layered perovskites, perovskite materials and devices, and semiempirical simulation methods for semiconductor optoelectronic materials.</p></div></div>
      <div class="jp-timeline-item"><div class="jp-date">Nov 2022-Sep 2025</div><div><h3>Postdoctoral Researcher · Institut FOTON, INSA Rennes / University of Rennes</h3><p>Theoretical studies of optoelectronic and dielectric properties of layered perovskites; theory-guided optimization of perovskite materials and devices; development of semiempirical methods for large-scale simulations. Mentors: Prof. Jacky Even and Dr. Claudine Katan.</p></div></div>
      <div class="jp-timeline-item"><div class="jp-date">Apr-May 2023</div><div><h3>Guest Researcher · University of Bremen</h3><p>Bremen Center for Computational Materials Science, Germany. Developed DFTB methods and parameters for large-scale simulations of metal-halide perovskites. Mentors: Dr. Bálint Aradi and Prof. Thomas Frauenheim.</p></div></div>
      <div class="jp-timeline-item"><div class="jp-date">Nov 2021-Nov 2022</div><div><h3>Postdoctoral Researcher · Institut des Sciences Chimiques de Rennes</h3><p>Theoretical description and optimization of perovskite materials and devices, including photovoltaics and light-emitting diodes. Mentors: Dr. Claudine Katan and Prof. Jacky Even.</p></div></div>
      <div class="jp-timeline-item"><div class="jp-date">Oct-Nov 2021</div><div><h3>Visiting Scholar · Institut des Sciences Chimiques de Rennes</h3><p>Simulation-guided design and optimization of perovskite materials and devices.</p></div></div>
      <div class="jp-timeline-item"><div class="jp-date">Sep 2017-Aug 2021</div><div><h3>Junior Researcher · Netherlands Organisation for Scientific Research</h3><p>Project work associated with computational science for energy research.</p></div></div>
      <div class="jp-timeline-item"><div class="jp-date">Sep 2017-Oct 2021</div><div><h3>Doctoral Researcher · Eindhoven University of Technology</h3><p>Used DFT and ab initio molecular dynamics to understand phase stability in lead-halide and lead-free perovskites.</p></div></div>
    </div>
  </div>
</section>
<section class="jp-section jp-section--soft">
  <div class="jp-container jp-grid jp-grid--two">
    <div>
      <h2 class="jp-heading">Education</h2>
      <div class="jp-timeline">
        <div class="jp-timeline-item"><div class="jp-date">2017-2021</div><div><h3>PhD in Applied Physics · Eindhoven University of Technology</h3><p>Supervisors: Dr. Shuxia Tao and Prof. Peter A. Bobbert.</p></div></div>
        <div class="jp-timeline-item"><div class="jp-date">2014-2017</div><div><h3>MEng in Mechatronic Engineering · Guilin University of Electronic Technology</h3></div></div>
        <div class="jp-timeline-item"><div class="jp-date">2010-2014</div><div><h3>BEng in Microelectronics Manufacturing Engineering · Guilin University of Electronic Technology</h3></div></div>
      </div>
    </div>
    <div>
      <h2 class="jp-heading">Skills</h2>
      <div class="jp-card">
        <h3>Theory and Simulation</h3>
        <p>DFT, DFTB, molecular dynamics, DFT-1/2, solid-state physics, semiconductor physics.</p>
        <h3>Programming and Software</h3>
        <p>Python, Bash; DFTB+, SIESTA, VASP, CP2K, AMS, Materials Studio, Hefei-NAMD, Gaussian, QuantumATK, GNUplot, Chemdraw, ChemOffice, VMD.</p>
      </div>
    </div>
  </div>
</section>
<section class="jp-section">
  <div class="jp-container jp-grid jp-grid--two">
    <div>
      <h2 class="jp-heading">Awards</h2>
      <ul class="jp-list">
        <li><h3>2019</h3><p>Science China Materials Annual Excellent Paper Award.</p></li>
        <li><h3>2017</h3><p>Outstanding Master's Thesis, Guilin University of Electronic Technology.</p></li>
        <li><h3>2017</h3><p>Outstanding Master's Graduate, Guangxi Zhuang Autonomous Region.</p></li>
        <li><h3>2016</h3><p>National Scholarship, Ministry of Education of China.</p></li>
        <li><h3>2014-2017</h3><p>First-Class Graduate Scholarship, Guilin University of Electronic Technology.</p></li>
        <li><h3>2015</h3><p>Third Prize, National Multimedia Courseware Design Competition.</p></li>
      </ul>
    </div>
    <div>
      <h2 class="jp-heading">Projects and Service</h2>
      <ul class="jp-list">
        <li><h3>Collaborative projects</h3><p>Contributed to Horizon 2020 PeroCUBE, Horizon 2020 POLLOC, M-ERA.NET PHANTASTIC, and NWO CSER projects; led a Guangxi graduate innovation project.</p></li>
        <li><h3>Editorial and reviewing</h3><p>Young Editorial Board Member for <em>Nanomaterials</em>; Guest Editor for <em>Nanomaterials</em> and <em>Micromachines</em>; reviewer for more than 40 journals, including <em>Advanced Materials</em>, <em>Physical Review Letters</em>, and <em>Nano Letters</em>.</p></li>
      </ul>
    </div>
  </div>
</section>
</div>'''


def teaching_body() -> str:
    return '''<div class="page-body jp-page">
<section class="jp-hero">
  <div class="jp-container">
    <p class="jp-kicker">Teaching and Mentoring</p>
    <h1 class="jp-title">Computational materials teaching and research training</h1>
    <p class="jp-subtitle">Teaching experience from the latest CV, together with supervision interests for future students and collaborators.</p>
  </div>
</section>
<section class="jp-section">
  <div class="jp-container jp-grid jp-grid--two">
    <article class="jp-card">
      <h3>Computational Materials Science</h3>
      <p>Teaching Assistant, Autumn 2018.</p>
      <p>Supported instruction in computational approaches for materials modelling and simulation.</p>
    </article>
    <article class="jp-card">
      <h3>Finite Element Simulation</h3>
      <p>Lecturer, Spring 2019.</p>
      <p>Delivered teaching related to finite-element methods and simulation workflows.</p>
    </article>
  </div>
</section>
<section class="jp-section jp-section--soft">
  <div class="jp-container">
    <h2 class="jp-heading">Future Supervision Interests</h2>
    <p class="jp-lead">I am interested in mentoring students and collaborators working at the intersection of computational materials science, semiconductor physics, perovskite materials, and data-driven atomistic simulation.</p>
    <div class="jp-tag-row"><span class="jp-tag">DFT and DFTB</span><span class="jp-tag">Perovskite stability</span><span class="jp-tag">Machine-learning potentials</span><span class="jp-tag">Hybrid semiconductors</span><span class="jp-tag">PV and LED materials</span></div>
  </div>
</section>
</div>'''


def bib_field(text: str, name: str) -> str:
    match = re.search(rf"\b{name}\s*=\s*(?:\{{(.*?)\}}|\"(.*?)\"|([^,\n]+))", text, flags=re.S | re.I)
    if not match:
        return ""
    value = next(group for group in match.groups() if group is not None)
    value = value.replace("\n", " ")
    value = value.replace("--", "-")
    value = re.sub(r"\s+", " ", value).strip()
    return value.strip("{} ")


def archive_items() -> list[tuple[str, str, str]]:
    items: list[tuple[str, str, str]] = []
    excluded_slugs = {"conference-paper", "journal-article", "jiangsupplementary", "wangsupporting"}
    for bib_path in sorted((ROOT / "publication").glob("*/" + "cite" + ".bib")):
        slug = bib_path.parent.name
        if slug in excluded_slugs:
            continue
        text = bib_path.read_text(encoding="utf-8", errors="ignore")
        title = bib_field(text, "title")
        year = bib_field(text, "year")
        if not title or title.lower().startswith("an example"):
            continue
        items.append((f"/publication/{slug}/", title, year or ""))
    return sorted(items, key=lambda item: (item[2], item[1].lower()), reverse=True)


def publication_body() -> str:
    archive = archive_items()
    archive_html = "".join(
        f'<a href="{html.escape(href)}"><strong>{html.escape(title)}</strong><br><span>{html.escape(date)}</span></a>'
        for href, title, date in archive
    )
    return f'''<div class="page-body jp-page">
<section class="jp-hero">
  <div class="jp-container">
    <p class="jp-kicker">Publications</p>
    <h1 class="jp-title">Selected and complete publication record</h1>
    <p class="jp-subtitle">Selected publications are curated from the latest CV. The archive below preserves the existing generated publication pages and DOI metadata where available.</p>
    <div class="jp-actions"><a class="jp-button" href="https://scholar.google.com/citations?user=PoVXBKUAAAAJ&amp;hl=en" target="_blank" rel="noopener">Google Scholar</a></div>
  </div>
</section>
<section class="jp-section">
  <div class="jp-container">
    <h2 class="jp-heading">Selected Publications</h2>
    {selected_publications()}
    <p class="jp-note"># Equal contribution. * Corresponding author. For current citation metrics, please consult Google Scholar.</p>
  </div>
</section>
<section class="jp-section jp-section--soft">
  <div class="jp-container">
    <h2 class="jp-heading">Publication Archive</h2>
    <p class="jp-lead">This archive keeps the original generated publication pages available for detailed metadata, citations, and DOI links.</p>
    <div class="jp-archive-list">{archive_html}</div>
  </div>
</section>
</div>'''


def update_page(path: str, title: str, description: str, url_path: str, body: str) -> None:
    s = read(path)
    s = update_nav_and_shared_head(s, path)
    s = update_meta(s, title, description, url_path)
    s = replace_body(s, body)
    write(path, s)


def make_page_from_template(template_path: str, output_path: str, title: str, description: str, url_path: str, body: str) -> None:
    s = read(template_path)
    s = update_nav_and_shared_head(s, output_path)
    s = update_meta(s, title, description, url_path)
    s = replace_body(s, body)
    write(output_path, s)


def update_sitemap() -> None:
    path = ROOT / "sitemap.xml"
    if not path.exists():
        return
    s = path.read_text(encoding="utf-8")
    if "<loc>https://junkejiang.github.io/research/</loc>" in s or "<loc>https://junkejiang.com/research/</loc>" in s:
        return
    entry = (
        "<url><loc>https://junkejiang.com/research/</loc>"
        f"<lastmod>{TODAY}T00:00:00+00:00</lastmod></url>"
    )
    s = s.replace("</urlset>", entry + "</urlset>")
    s = s.replace("https://junkejiang.github.io/", "https://junkejiang.com/")
    path.write_text(s, encoding="utf-8")


def cleanup_generated_outputs() -> None:
    text_suffixes = {".html", ".xml", ".md"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        s = path.read_text(encoding="utf-8", errors="ignore")
        s = remove_public_citation_links(s)
        s = re.sub(r'<script src="/livereload\.js\?[^"]*"[^>]*></script>\s*', "", s)
        s = s.replace('href="/uploads/resume.pdf"', 'href="/uploads/resume.pdf"')
        s = s.replace(OLD_TITLE, CURRENT_TITLE)
        s = s.replace(OLD_EMAIL, CURRENT_EMAIL)
        s = s.replace("https://junkejiang.github.io/", "https://junkejiang.com/")
        s = re.sub(
            r'(<div class="text-sm font-bold text-neutral-700 dark:text-neutral-300">)Postdoctoral Researcher(</div>)',
            rf"\1{CURRENT_TITLE}\2",
            s,
        )
        s = s.replace("Bib" + "TeX", "citation metadata")
        s = s.replace("bib" + "tex", "citation metadata")
        s = s.replace("&lt;em>" + "Cite" + "&lt;/em>", "citation metadata")
        s = s.replace("<em>" + "Cite" + "</em>", "citation metadata")
        s = s.replace(">" + "Cite" + "</a>", "></a>")
        if path.suffix.lower() == ".html" and "/publication/" in s:
            if path.parent.name in {"jiangsupplementary", "wangsupporting"}:
                s = remove_publication_last_updated_block(s)
            s = normalize_publication_date_placeholders(s)
        if path.suffix.lower() == ".html" and path.relative_to(ROOT).as_posix().startswith("publication_types/"):
            s = remove_placeholder_publication_type_metadata(s)
        if path.suffix.lower() == ".xml" and "/publication/" in s:
            s = normalize_publication_feed_date_placeholders(s)
        if path.name == "sitemap.xml":
            s = normalize_publication_sitemap_date_placeholders(s)
        path.write_text(s, encoding="utf-8")


def normalize_publication_date_placeholders(s: str) -> str:
    """Remove misleading Jan. 1 placeholder dates from public publication pages."""
    modified = re.search(r'article:modified_time" content="(\d{4}-\d{2}-\d{2})T00:00:00\+00:00"', s)
    month_names = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
    if modified:
        iso = modified.group(1)
        year, month, day = iso.split("-")
        exact_display = f"{month_names[int(month) - 1]} {int(day)}, {year}"
        s = re.sub(
            r'article:published_time" content="[^"]+"',
            f'article:published_time" content="{iso}T00:00:00+00:00"',
            s,
        )
        s = re.sub(
            r'article:modified_time" content="[^"]+"',
            f'article:modified_time" content="{iso}T00:00:00+00:00"',
            s,
        )
        s = re.sub(r'"datePublished":"[^"]+"', f'"datePublished":"{iso}T00:00:00Z"', s)
        s = re.sub(r'"dateModified":"[^"]+"', f'"dateModified":"{iso}T00:00:00Z"', s)
        if not iso.endswith("-01-01"):
            s = re.sub(rf"Jan 1, {year}", exact_display, s)
            s = re.sub(rf"(<span class=mr-1>){year}(</span>)", rf"\1{exact_display}\2", s)
            s = re.sub(
                rf"datetime={year}-01-01T00:00:00\.000Z",
                f"datetime={iso}T00:00:00.000Z",
                s,
            )
            s = re.sub(
                r'(<time[^>]*><span>)(Last updated on|Publication year)(</span>)',
                r"\1Publication date\3",
                s,
            )
            s = re.sub(rf"(Publication date</span>\s*){year}", rf"\1{exact_display}", s)
            return s
        s = remove_placeholder_publication_metadata(s, year)
    s = re.sub(
        r'(<time[^>]*datetime=\d{4}-01-01T00:00:00\.000Z><span>)Last updated on(</span>)',
        r"\1Publication year\2",
        s,
    )
    s = re.sub(r"Jan 1, ((?:19|20)\d{2})", r"\1", s)
    return s


def remove_placeholder_publication_metadata(s: str, year: str) -> str:
    s = re.sub(
        rf'<meta property="article:(?:published|modified)_time" content="{year}-01-01T00:00:00\+00:00">',
        "",
        s,
    )
    s = re.sub(rf'"datePublished":"{year}-01-01T00:00:00Z"', f'"datePublished":"{year}"', s)
    s = re.sub(rf'"dateModified":"{year}-01-01T00:00:00Z"', f'"dateModified":"{year}"', s)
    s = re.sub(rf'datetime="?{year}-01-01T00:00:00\.000Z"?', f'datetime="{year}"', s)
    return s


def normalize_publication_feed_date_placeholders(s: str) -> str:
    def clean_item(match: re.Match[str]) -> str:
        item = match.group(0)
        if "/publication/" not in item:
            return item
        return re.sub(
            r"<pubDate>\w{3}, 01 Jan (?:19|20)\d{2} 00:00:00 \+0000</pubDate>",
            "",
            item,
        )

    return re.sub(r"<item>.*?</item>", clean_item, s)


def normalize_publication_sitemap_date_placeholders(s: str) -> str:
    def clean_url(match: re.Match[str]) -> str:
        url = match.group(0)
        if "/publication/" not in url and "/publication_types/" not in url:
            return url
        return re.sub(
            r"<lastmod>(?:19|20)\d{2}-01-01T00:00:00\+00:00</lastmod>",
            "",
            url,
        )

    return re.sub(r"<url>.*?</url>", clean_url, s)


def remove_placeholder_publication_type_metadata(s: str) -> str:
    return re.sub(
        r'<meta property="og:updated_time" content="(?:19|20)\d{2}-01-01T00:00:00\+00:00">',
        "",
        s,
    )


def remove_publication_last_updated_block(s: str) -> str:
    return re.sub(
        r'\s*<time class="mt-12 mb-8 block text-xs text-gray-500 ltr:text-right rtl:text-left dark:text-gray-400" datetime="[^"]+">\s*'
        r"<span>Last updated on</span>\s*[^<]+</time>",
        "",
        s,
    )


def main() -> None:
    for html_path in ROOT.rglob("*.html"):
        rel = html_path.relative_to(ROOT).as_posix()
        s = html_path.read_text(encoding="utf-8")
        s = update_nav_and_shared_head(s, rel)
        html_path.write_text(s, encoding="utf-8")

    update_page(
        "index.html",
        "Junke Jiang | Computational Materials Scientist",
        "Junke Jiang is a Research Associate at the University of York working on computational materials science, hybrid semiconductors, perovskites, DFTB, and machine-learning force fields.",
        "/",
        home_body(),
    )
    make_page_from_template(
        "projects/index.html",
        "research/index.html",
        "Research | Junke Jiang",
        "Research themes in computational materials science, hybrid semiconductors, perovskite stability, DFTB methods, and machine-learning force fields.",
        "/research/",
        research_body(),
    )
    update_page(
        "projects/index.html",
        "Research | Junke Jiang",
        "Research themes in computational materials science, hybrid semiconductors, perovskite stability, DFTB methods, and machine-learning force fields.",
        "/research/",
        research_body(),
    )
    update_page(
        "experience/index.html",
        "CV | Junke Jiang",
        "Academic appointments, education, skills, awards, projects, and service for Junke Jiang.",
        "/experience/",
        cv_body(),
    )
    update_page(
        "teaching/index.html",
        "Teaching | Junke Jiang",
        "Teaching and mentoring experience in computational materials science and finite element simulation.",
        "/teaching/",
        teaching_body(),
    )
    update_page(
        "publication/index.html",
        "Publications | Junke Jiang",
        "Selected and complete publication record for Junke Jiang, including representative perovskite and computational materials papers.",
        "/publication/",
        publication_body(),
    )
    cleanup_generated_outputs()
    update_sitemap()


if __name__ == "__main__":
    main()
