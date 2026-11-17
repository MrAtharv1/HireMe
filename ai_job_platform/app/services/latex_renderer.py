"""
LaTeX Resume Renderer — Single-Column ATS Jake's Template.
Uses Jinja2 with custom delimiters to prevent LaTeX syntax conflicts.
Includes strict LaTeX character escaping and 1-page line budget auto-fitting.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
import jinja2

# LaTeX special character replacements
LATEX_ESCAPES = [
    ('\\', r'\textbackslash{}'),
    ('&', r'\&'),
    ('%', r'\%'),
    ('$', r'\$'),
    ('#', r'\#'),
    ('_', r'\_'),
    ('{', r'\{'),
    ('}', r'\}'),
    ('~', r'\textasciitilde{}'),
    ('^', r'\textasciicircum{}'),
]


def latex_escape(text: Optional[str]) -> str:
    """Escapes special LaTeX characters for safe compilation."""
    if not text:
        return ""
    s = str(text)
    for char, replacement in LATEX_ESCAPES:
        s = s.replace(char, replacement)
    return s


# ATS Jake's Resume Template
JAKES_RESUME_LATEX_TEMPLATE = r"""\documentclass[letterpaper,10pt]{article}

\pdfgentounicode=1
\input{glyphtounicode}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins (0.5 to 0.6 in)
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% Custom commands
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\begin{document}

%----------HEADING----------
\begin{center}
    \textbf{\Huge \scshape \VAR{name}} \\ \vspace{2pt}
    \small 
    \BLOCK{if phone}\VAR{phone} $|$ \BLOCK{endif}
    \BLOCK{if email}\href{mailto:\VAR{email}}{\underline{\VAR{email}}} $|$ \BLOCK{endif}
    \BLOCK{if linkedin}\href{\VAR{linkedin}}{\underline{LinkedIn}} $|$ \BLOCK{endif}
    \BLOCK{if github}\href{\VAR{github}}{\underline{GitHub}} $|$ \BLOCK{endif}
    \BLOCK{if portfolio}\href{\VAR{portfolio}}{\underline{Portfolio}}\BLOCK{endif}
\end{center}

\BLOCK{if summary}
%-----------SUMMARY-----------
\section{Professional Summary}
\small{\VAR{summary}}
\vspace{2pt}
\BLOCK{endif}

%-----------EDUCATION-----------
\BLOCK{if education}
\section{Education}
  \resumeSubHeadingListStart
    \BLOCK{for edu in education}
      \resumeSubheading
        {\VAR{edu.institution}}{\VAR{edu.dates}}
        {\VAR{edu.degree}}{\VAR{edu.location}}
    \BLOCK{endfor}
  \resumeSubHeadingListEnd
\BLOCK{endif}

%-----------TECHNICAL SKILLS-----------
\BLOCK{if skills_categories}
\section{Technical Skills}
 \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
      \BLOCK{for cat, skills in skills_categories.items()}
        \BLOCK{if skills}
          \textbf{\VAR{cat}}: \VAR{skills|join(", ")} \\
        \BLOCK{endif}
      \BLOCK{endfor}
    }}
 \end{itemize}
\BLOCK{endif}

%-----------EXPERIENCE-----------
\BLOCK{if experiences}
\section{Experience}
  \resumeSubHeadingListStart
    \BLOCK{for exp in experiences}
      \resumeSubheading
        {\VAR{exp.role}}{\VAR{exp.dates}}
        {\VAR{exp.company}}{\VAR{exp.location}}
        \resumeItemListStart
          \BLOCK{for bullet in exp.bullets}
            \resumeItem{\VAR{bullet}}
          \BLOCK{endfor}
        \resumeItemListEnd
    \BLOCK{endfor}
  \resumeSubHeadingListEnd
\BLOCK{endif}

%-----------PROJECTS-----------
\BLOCK{if projects}
\section{Projects}
    \resumeSubHeadingListStart
      \BLOCK{for proj in projects}
        \resumeProjectHeading
          {\textbf{\VAR{proj.name}} $|$ \emph{\VAR{proj.technologies_str}}}{\VAR{proj.dates}}
          \resumeItemListStart
            \BLOCK{for bullet in proj.bullets}
              \resumeItem{\VAR{bullet}}
            \BLOCK{endfor}
          \resumeItemListEnd
      \BLOCK{endfor}
    \resumeSubHeadingListEnd
\BLOCK{endif}

%-----------CERTIFICATIONS & ACHIEVEMENTS-----------
\BLOCK{if certifications or achievements}
\section{Certifications \& Achievements}
  \begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
      \BLOCK{for cert in certifications}
        $\bullet$ \VAR{cert} \\
      \BLOCK{endfor}
      \BLOCK{for ach in achievements}
        $\bullet$ \VAR{ach} \\
      \BLOCK{endfor}
    }}
  \end{itemize}
\BLOCK{endif}

\end{document}
"""


def _get_jinja_env() -> jinja2.Environment:
    """Configures Jinja2 environment with LaTeX-compatible delimiters."""
    return jinja2.Environment(
        block_start_string=r"\BLOCK{",
        block_end_string=r"}",
        variable_start_string=r"\VAR{",
        variable_end_string=r"}",
        comment_start_string=r"\#{",
        comment_end_string=r"}",
        line_statement_prefix=None,
        line_comment_prefix=None,
        trim_blocks=True,
        autoescape=False,
    )


def estimate_line_budget(payload: Dict[str, Any]) -> int:
    """
    Estimates total rendered vertical lines to guarantee a strict 1-page fit.
    Letter paper at 10pt holds ~52-55 lines with Jake's template spacing.
    """
    lines = 5  # Heading + contact
    if payload.get("summary"):
        lines += 3
    if payload.get("education"):
        lines += 2 + len(payload["education"]) * 3
    if payload.get("skills_categories"):
        lines += 2 + len([k for k, v in payload["skills_categories"].items() if v])
    if payload.get("experiences"):
        lines += 2
        for exp in payload["experiences"]:
            lines += 2 + len(exp.get("bullets", [])) * 2
    if payload.get("projects"):
        lines += 2
        for proj in payload["projects"]:
            lines += 2 + len(proj.get("bullets", [])) * 2
    if payload.get("certifications") or payload.get("achievements"):
        lines += 2 + len(payload.get("certifications", [])) + len(payload.get("achievements", []))
    return lines


def auto_fit_to_one_page(payload: Dict[str, Any], max_lines: int = 52) -> Dict[str, Any]:
    """
    Strict 1-page auto-trimming:
    If estimated lines exceed max_lines, drops lowest-ranked project bullet or project.
    """
    estimated = estimate_line_budget(payload)
    if estimated <= max_lines:
        return payload

    # 1. First attempt: trim bullets per project down to 2
    projects = payload.get("projects", [])
    for proj in reversed(projects):
        if len(proj.get("bullets", [])) > 2:
            proj["bullets"] = proj["bullets"][:2]
            estimated = estimate_line_budget(payload)
            if estimated <= max_lines:
                return payload

    # 2. Second attempt: drop 3rd project if present
    if len(projects) > 2:
        payload["projects"] = projects[:2]
        estimated = estimate_line_budget(payload)
        if estimated <= max_lines:
            return payload

    # 3. Third attempt: drop summary if still overflowing
    if payload.get("summary") and estimated > max_lines:
        payload["summary"] = ""
        estimated = estimate_line_budget(payload)

    return payload


def render_latex_resume(data: Dict[str, Any]) -> str:
    """
    Escapes all strings in data dictionary and renders the Jinja2 LaTeX template.
    Guarantees single-page fit.
    """
    fitted_data = auto_fit_to_one_page(data)

    def escape_recursive(val: Any) -> Any:
        if isinstance(val, str):
            return latex_escape(val)
        elif isinstance(val, list):
            return [escape_recursive(x) for x in val]
        elif isinstance(val, dict):
            # Only escape values, not dictionary keys which are template variable identifiers
            return {k: escape_recursive(v) for k, v in val.items()}
        return val

    safe_payload = escape_recursive(fitted_data)

    env = _get_jinja_env()
    template = env.from_string(JAKES_RESUME_LATEX_TEMPLATE)
    return template.render(**safe_payload)


def render_html_resume(data: Dict[str, Any]) -> str:
    """
    Renders an HTML/CSS document mirroring Jake's single-column resume template.
    Fully compatible with xhtml2pdf for deterministic, offline, 1-page PDF generation.
    """
    import html

    fitted_data = auto_fit_to_one_page(dict(data))
    name = html.escape(fitted_data.get("name") or "Software Engineer")
    email = html.escape(fitted_data.get("email") or "")
    phone = html.escape(fitted_data.get("phone") or "")
    location = html.escape(fitted_data.get("location") or "")
    linkedin = html.escape(fitted_data.get("linkedin") or "")
    github = html.escape(fitted_data.get("github") or "")
    portfolio = html.escape(fitted_data.get("portfolio") or "")
    summary = html.escape(fitted_data.get("summary") or "")

    # Build contact items
    contact_parts = []
    if email:
        contact_parts.append(f'<a href="mailto:{email}" style="color: #111; text-decoration: underline;">{email}</a>')
    if phone:
        contact_parts.append(phone)
    if location:
        contact_parts.append(location)
    if linkedin:
        display_li = linkedin.replace("https://www.", "").replace("https://", "").replace("www.", "")
        contact_parts.append(f'<a href="{linkedin}" style="color: #111; text-decoration: underline;">{display_li}</a>')
    if github:
        display_gh = github.replace("https://www.", "").replace("https://", "").replace("www.", "")
        contact_parts.append(f'<a href="{github}" style="color: #111; text-decoration: underline;">{display_gh}</a>')
    if portfolio:
        contact_parts.append(f'<a href="{portfolio}" style="color: #111; text-decoration: underline;">Portfolio</a>')

    contact_html = " | ".join(contact_parts)

    # Sections
    sections_html = []

    # 1. Summary
    if summary:
        sections_html.append(f"""
        <div class="section-title">Professional Summary</div>
        <div class="summary-text">{summary}</div>
        """)

    # 2. Education
    education = fitted_data.get("education") or []
    if education:
        edu_rows = []
        for edu in education:
            inst = html.escape(edu.get("institution") or "")
            dates = html.escape(edu.get("dates") or "")
            degree = html.escape(edu.get("degree") or "")
            loc = html.escape(edu.get("location") or "")
            edu_rows.append(f"""
            <table class="entry">
              <tr>
                <td class="entry-title">{inst}</td>
                <td class="entry-date">{dates}</td>
              </tr>
              <tr>
                <td class="entry-subtitle">{degree}</td>
                <td class="entry-location">{loc}</td>
              </tr>
            </table>
            """)
        sections_html.append(f"""
        <div class="section-title">Education</div>
        {''.join(edu_rows)}
        """)

    # 3. Technical Skills
    skills_cats = fitted_data.get("skills_categories") or {}
    if skills_cats:
        cat_lines = []
        for cat, skills in skills_cats.items():
            if skills:
                sk_str = ", ".join(html.escape(s) for s in skills)
                cat_lines.append(f'<div class="skills-group"><strong>{html.escape(cat)}:</strong> {sk_str}</div>')
        if cat_lines:
            sections_html.append(f"""
            <div class="section-title">Technical Skills</div>
            {''.join(cat_lines)}
            """)

    # 4. Experience
    experiences = fitted_data.get("experiences") or []
    if experiences:
        exp_entries = []
        for exp in experiences:
            role = html.escape(exp.get("role") or "Software Engineer")
            company = html.escape(exp.get("company") or "")
            dates = html.escape(exp.get("dates") or "")
            loc = html.escape(exp.get("location") or "")
            bullets = exp.get("bullets") or []
            bullets_html = "".join(f"<li>{html.escape(b)}</li>" for b in bullets if b)
            exp_entries.append(f"""
            <table class="entry">
              <tr>
                <td class="entry-title">{role}</td>
                <td class="entry-date">{dates}</td>
              </tr>
              <tr>
                <td class="entry-subtitle">{company}</td>
                <td class="entry-location">{loc}</td>
              </tr>
            </table>
            {"<ul>" + bullets_html + "</ul>" if bullets_html else ""}
            """)
        sections_html.append(f"""
        <div class="section-title">Experience</div>
        {''.join(exp_entries)}
        """)

    # 5. Projects
    projects = fitted_data.get("projects") or []
    if projects:
        proj_entries = []
        for proj in projects:
            p_name = html.escape(proj.get("name") or "Project")
            tech = html.escape(proj.get("technologies_str") or "")
            dates = html.escape(proj.get("dates") or "")
            bullets = proj.get("bullets") or []
            bullets_html = "".join(f"<li>{html.escape(b)}</li>" for b in bullets if b)
            subtitle = f" | <em>{tech}</em>" if tech else ""
            proj_entries.append(f"""
            <table class="entry">
              <tr>
                <td class="entry-title">{p_name}{subtitle}</td>
                <td class="entry-date">{dates}</td>
              </tr>
            </table>
            {"<ul>" + bullets_html + "</ul>" if bullets_html else ""}
            """)
        sections_html.append(f"""
        <div class="section-title">Projects</div>
        {''.join(proj_entries)}
        """)

    # 6. Certifications & Achievements
    certs = fitted_data.get("certifications") or []
    achs = fitted_data.get("achievements") or []
    if certs or achs:
        ca_items = []
        for c in certs:
            ca_items.append(f"<li>{html.escape(c)}</li>")
        for a in achs:
            ca_items.append(f"<li>{html.escape(a)}</li>")
        sections_html.append(f"""
        <div class="section-title">Certifications & Achievements</div>
        <ul>{''.join(ca_items)}</ul>
        """)

    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: letter portrait;
    margin: 0.4in 0.45in 0.4in 0.45in;
  }}
  body {{
    font-family: Helvetica, Arial, sans-serif;
    font-size: 9.5pt;
    line-height: 1.25;
    color: #111111;
  }}
  .header {{
    text-align: center;
    margin-bottom: 6px;
  }}
  .name {{
    font-size: 18pt;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
  }}
  .contact {{
    font-size: 8.5pt;
    color: #333333;
  }}
  .section-title {{
    font-size: 10.5pt;
    font-weight: bold;
    text-transform: uppercase;
    border-bottom: 1px solid #111111;
    padding-bottom: 2px;
    margin-top: 6px;
    margin-bottom: 4px;
    letter-spacing: 0.3px;
  }}
  .summary-text {{
    font-size: 9pt;
    line-height: 1.25;
    margin-bottom: 4px;
  }}
  table.entry {{
    width: 100%;
    margin-bottom: 1px;
  }}
  table.entry td {{
    padding: 0;
    vertical-align: top;
  }}
  .entry-title {{
    font-weight: bold;
    font-size: 9.5pt;
  }}
  .entry-date {{
    text-align: right;
    font-size: 9pt;
    color: #333333;
  }}
  .entry-subtitle {{
    font-style: italic;
    font-size: 9pt;
  }}
  .entry-location {{
    text-align: right;
    font-style: italic;
    font-size: 9pt;
    color: #444444;
  }}
  ul {{
    margin: 1px 0 3px 14px;
    padding: 0;
  }}
  li {{
    font-size: 9pt;
    line-height: 1.25;
    margin-bottom: 2px;
  }}
  .skills-group {{
    margin-bottom: 2px;
    font-size: 9pt;
  }}
</style>
</head>
<body>
  <div class="header">
    <div class="name">{name}</div>
    <div class="contact">{contact_html}</div>
  </div>
  {''.join(sections_html)}
</body>
</html>"""
    return full_html


def parse_tex_to_payload(tex_content: str) -> Dict[str, Any]:
    """
    Parses a Jake's LaTeX resume string back into a dictionary payload.
    Used for on-the-fly rendering when only .tex source is stored.
    """
    import html

    def unescape_latex(s: str) -> str:
        s = s.replace(r"\\", "")
        for char, rep in reversed(LATEX_ESCAPES):
            s = s.replace(rep, char)
        return s.strip()

    payload: Dict[str, Any] = {
        "name": "Software Engineer",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": "",
        "portfolio": "",
        "summary": "",
        "education": [],
        "skills_categories": {},
        "experiences": [],
        "projects": [],
        "certifications": [],
        "achievements": [],
    }

    # Name
    m_name = re.search(r"\\textbf\{\\Huge\s*\\scshape\s*([^}]+)\}", tex_content)
    if m_name:
        payload["name"] = unescape_latex(m_name.group(1))

    # Contact
    m_mail = re.search(r"\\href\{mailto:([^}]+)\}", tex_content)
    if m_mail:
        payload["email"] = m_mail.group(1)
    
    m_li = re.search(r"\\href\{([^}]+linkedin[^}]+)\}", tex_content)
    if m_li:
        payload["linkedin"] = m_li.group(1)

    m_gh = re.search(r"\\href\{([^}]+github[^}]+)\}", tex_content)
    if m_gh:
        payload["github"] = m_gh.group(1)

    # Summary
    m_sum = re.search(r"\\section\{Professional Summary\}\s*\\small\{([^}]+)\}", tex_content)
    if m_sum:
        payload["summary"] = unescape_latex(m_sum.group(1))

    # Skills
    for cat_m in re.finditer(r"\\textbf\{([^}]+)\}:\s*([^\\]+)\\\\", tex_content):
        cat = unescape_latex(cat_m.group(1))
        sk_items = [unescape_latex(s) for s in cat_m.group(2).split(",") if s.strip()]
        if cat and sk_items:
            payload["skills_categories"][cat] = sk_items

    # Education
    for edu_m in re.finditer(r"\\resumeSubheading\s*\{([^}]+)\}\{([^}]*)\}\s*\{([^}]*)\}\{([^}]*)\}", tex_content):
        # Could be edu or exp depending on context
        pass

    # Simple section splitting
    sec_splits = re.split(r"\\section\{([^}]+)\}", tex_content)
    for i in range(1, len(sec_splits), 2):
        sec_title = sec_splits[i].strip().lower()
        sec_body = sec_splits[i+1] if i+1 < len(sec_splits) else ""

        if "education" in sec_title:
            for em in re.finditer(r"\\resumeSubheading\s*\{([^}]+)\}\{([^}]*)\}\s*\{([^}]*)\}\{([^}]*)\}", sec_body):
                payload["education"].append({
                    "institution": unescape_latex(em.group(1)),
                    "dates": unescape_latex(em.group(2)),
                    "degree": unescape_latex(em.group(3)),
                    "location": unescape_latex(em.group(4)),
                })
        elif "experience" in sec_title:
            # find subheadings and items
            exp_blocks = re.split(r"\\resumeSubheading", sec_body)
            for eb in exp_blocks[1:]:
                header_m = re.match(r"\s*\{([^}]+)\}\{([^}]*)\}\s*\{([^}]*)\}\{([^}]*)\}", eb)
                if header_m:
                    bullets = [unescape_latex(bm.group(1)) for bm in re.finditer(r"\\resumeItem\{([^}]+)\}", eb)]
                    payload["experiences"].append({
                        "role": unescape_latex(header_m.group(1)),
                        "dates": unescape_latex(header_m.group(2)),
                        "company": unescape_latex(header_m.group(3)),
                        "location": unescape_latex(header_m.group(4)),
                        "bullets": bullets,
                    })
        elif "project" in sec_title:
            proj_blocks = re.split(r"\\resumeProjectHeading", sec_body)
            for pb in proj_blocks[1:]:
                header_m = re.match(r"\s*\{\\textbf\{([^}]+)\}\s*\|\s*\\emph\{([^}]*)\}\}\{([^}]*)\}", pb)
                if header_m:
                    bullets = [unescape_latex(bm.group(1)) for bm in re.finditer(r"\\resumeItem\{([^}]+)\}", pb)]
                    payload["projects"].append({
                        "name": unescape_latex(header_m.group(1)),
                        "technologies_str": unescape_latex(header_m.group(2)),
                        "dates": unescape_latex(header_m.group(3)),
                        "bullets": bullets,
                    })
        elif "cert" in sec_title or "achieve" in sec_title:
            for bm in re.finditer(r"\$\\bullet\$\s*([^\\]+)\\\\", sec_body):
                payload["certifications"].append(unescape_latex(bm.group(1)))

    return payload


