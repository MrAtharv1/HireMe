"""
PDF generation via xhtml2pdf + Jinja2.

Renders a tailored resume JSON into a professional HTML template,
then converts it to a PDF file.
"""

from __future__ import annotations

import io
import logging
import uuid
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, BaseLoader
from xhtml2pdf import pisa

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────
#  Jinja2 HTML Template
# ─────────────────────────────────────────────────────────────────────────

RESUME_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <style>
        @page {
            size: A4;
            margin: 1.5cm;
        }
        body {
            font-family: Helvetica, Arial, sans-serif;
            font-size: 10pt;
            color: #1a1a1a;
            line-height: 1.45;
        }
        h1 {
            font-size: 20pt;
            margin: 0 0 2pt 0;
            color: #0d47a1;
        }
        h2 {
            font-size: 12pt;
            color: #0d47a1;
            border-bottom: 1px solid #0d47a1;
            padding-bottom: 3pt;
            margin-top: 14pt;
            margin-bottom: 6pt;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        h3 {
            font-size: 11pt;
            margin: 6pt 0 2pt 0;
            color: #333;
        }
        .contact-line {
            font-size: 9pt;
            color: #555;
            margin-bottom: 10pt;
        }
        .contact-line a {
            color: #0d47a1;
            text-decoration: none;
        }
        .summary {
            font-style: italic;
            color: #444;
            margin-bottom: 8pt;
        }
        ul {
            margin: 2pt 0 6pt 14pt;
            padding: 0;
        }
        li {
            margin-bottom: 2pt;
        }
        .date-range {
            float: right;
            font-size: 9pt;
            color: #777;
        }
        .section-item {
            margin-bottom: 8pt;
        }
        .skills-list {
            columns: 3;
            -webkit-columns: 3;
            -moz-columns: 3;
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .skills-list li {
            font-size: 9.5pt;
            padding: 1pt 0;
        }
        .clearfix::after {
            content: "";
            display: table;
            clear: both;
        }
    </style>
</head>
<body>

    {# ── Header ── #}
    {% set pi = data.get("personal_info", {}) %}
    <h1>{{ pi.get("full_name", "Candidate") }}</h1>
    <div class="contact-line">
        {% set contact_parts = [] %}
        {% if pi.get("email") %}{% set _ = contact_parts.append(pi.email) %}{% endif %}
        {% if pi.get("phone") %}{% set _ = contact_parts.append(pi.phone) %}{% endif %}
        {% if pi.get("location") %}{% set _ = contact_parts.append(pi.location) %}{% endif %}
        {% if pi.get("linkedin") %}{% set _ = contact_parts.append('<a href="' + pi.linkedin + '">LinkedIn</a>') %}{% endif %}
        {% if pi.get("github") %}{% set _ = contact_parts.append('<a href="' + pi.github + '">GitHub</a>') %}{% endif %}
        {% if pi.get("portfolio") %}{% set _ = contact_parts.append('<a href="' + pi.portfolio + '">Portfolio</a>') %}{% endif %}
        {{ contact_parts | join(" &bull; ") }}
    </div>

    {# ── Summary ── #}
    {% if pi.get("summary") %}
    <div class="summary">{{ pi.summary }}</div>
    {% endif %}

    {# ── Skills ── #}
    {% set skills = data.get("skills", []) %}
    {% if skills %}
    <h2>Skills</h2>
    <ul class="skills-list">
        {% for skill in skills %}
        <li>{{ skill }}</li>
        {% endfor %}
    </ul>
    {% endif %}

    {# ── Experience ── #}
    {% set experience = data.get("experience", []) %}
    {% if experience %}
    <h2>Experience</h2>
    {% for exp in experience %}
    <div class="section-item clearfix">
        <h3>
            {{ exp.get("title", "") }}
            {% if exp.get("company") %} — {{ exp.company }}{% endif %}
            {% if exp.get("start_date") or exp.get("end_date") %}
            <span class="date-range">
                {{ exp.get("start_date", "") }}{% if exp.get("end_date") %} – {{ exp.end_date }}{% elif exp.get("is_current") %} – Present{% endif %}
            </span>
            {% endif %}
        </h3>
        {% if exp.get("location") %}<div style="font-size:9pt;color:#777;">{{ exp.location }}</div>{% endif %}
        {% if exp.get("bullet_points") %}
        <ul>
            {% for bp in exp.bullet_points %}<li>{{ bp }}</li>{% endfor %}
        </ul>
        {% endif %}
    </div>
    {% endfor %}
    {% endif %}

    {# ── Projects ── #}
    {% set projects = data.get("projects", []) %}
    {% if projects %}
    <h2>Projects</h2>
    {% for proj in projects %}
    <div class="section-item">
        <h3>
            {{ proj.get("name", "") }}
            {% if proj.get("technologies") %}
            <span style="font-size:9pt;font-weight:normal;color:#555;"> ({{ proj.technologies | join(", ") }})</span>
            {% endif %}
        </h3>
        {% if proj.get("description") %}<div style="font-size:9.5pt;">{{ proj.description }}</div>{% endif %}
        {% if proj.get("bullet_points") %}
        <ul>
            {% for bp in proj.bullet_points %}<li>{{ bp }}</li>{% endfor %}
        </ul>
        {% endif %}
    </div>
    {% endfor %}
    {% endif %}

    {# ── Education ── #}
    {% set education = data.get("education", []) %}
    {% if education %}
    <h2>Education</h2>
    {% for edu in education %}
    <div class="section-item clearfix">
        <h3>
            {{ edu.get("degree", "") }}
            {% if edu.get("field_of_study") %} in {{ edu.field_of_study }}{% endif %}
            {% if edu.get("start_date") or edu.get("end_date") %}
            <span class="date-range">
                {{ edu.get("start_date", "") }}{% if edu.get("end_date") %} – {{ edu.end_date }}{% endif %}
            </span>
            {% endif %}
        </h3>
        {% if edu.get("institution") %}<div style="font-size:9.5pt;">{{ edu.institution }}</div>{% endif %}
        {% if edu.get("grade") %}<div style="font-size:9pt;color:#555;">Grade: {{ edu.grade }}</div>{% endif %}
    </div>
    {% endfor %}
    {% endif %}

    {# ── Certifications ── #}
    {% set certs = data.get("certifications", []) %}
    {% if certs %}
    <h2>Certifications</h2>
    <ul>
        {% for cert in certs %}
        <li>
            {{ cert.get("name", "") }}
            {% if cert.get("issuer") %} — {{ cert.issuer }}{% endif %}
            {% if cert.get("date") %} ({{ cert.date }}){% endif %}
        </li>
        {% endfor %}
    </ul>
    {% endif %}

    {# ── Achievements ── #}
    {% set achievements = data.get("achievements", []) %}
    {% if achievements %}
    <h2>Achievements</h2>
    <ul>
        {% for ach in achievements %}
        <li>{{ ach }}</li>
        {% endfor %}
    </ul>
    {% endif %}

</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────

_jinja_env = Environment(loader=BaseLoader(), autoescape=False)


def render_resume_html(data: Dict[str, Any]) -> str:
    """Render the resume JSON into an HTML string."""
    template = _jinja_env.from_string(RESUME_HTML_TEMPLATE)
    return template.render(data=data)


def generate_pdf(data: Dict[str, Any], filename_hint: str | None = None) -> str:
    """
    Generate a PDF from resume JSON and save it to the configured directory.

    Returns
    -------
    str
        Absolute path to the generated PDF.
    """
    html = render_resume_html(data)
    pdf_buffer = io.BytesIO()

    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)
    if pisa_status.err:
        logger.error("xhtml2pdf conversion errors: %s", pisa_status.err)
        raise RuntimeError("Failed to generate PDF — xhtml2pdf reported errors.")

    # Persist to disk
    out_dir = Path(settings.GENERATED_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = filename_hint or str(uuid.uuid4())
    pdf_path = out_dir / f"{stem}.pdf"
    pdf_path.write_bytes(pdf_buffer.getvalue())

    logger.info("PDF generated → %s (%d bytes)", pdf_path, pdf_path.stat().st_size)
    return str(pdf_path.resolve())
