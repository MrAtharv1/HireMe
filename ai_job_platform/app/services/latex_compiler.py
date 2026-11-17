"""
LaTeX Compiler Service.
Compiles generated .tex files to .pdf using Tectonic or pdflatex via asyncio subprocess.
Includes automatic, high-fidelity fallback rendering via xhtml2pdf to guarantee
that a visual, 1-page ATS-compliant PDF is ALWAYS generated even without host LaTeX toolchains.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class LaTeXCompilerNotFoundError(Exception):
    """Raised when neither tectonic nor pdflatex is installed on the host and fallback fails."""
    pass


class LaTeXCompilationFailedError(Exception):
    """Raised when LaTeX compilation and fallback both fail."""
    pass


def find_latex_compiler() -> Optional[str]:
    """Checks for tectonic first, then pdflatex."""
    # Check bin directory inside project first if packaged
    local_tectonic = Path(__file__).resolve().parent.parent.parent / "bin" / "tectonic.exe"
    if local_tectonic.is_file():
        return str(local_tectonic)
    tectonic_bin = shutil.which("tectonic")
    if tectonic_bin:
        return "tectonic"
    pdflatex_bin = shutil.which("pdflatex")
    if pdflatex_bin:
        return "pdflatex"
    return None


def render_pdf_fallback(
    output_pdf_path: str,
    render_payload: Optional[Dict[str, Any]] = None,
    tex_content: Optional[str] = None
) -> str:
    """
    Renders high-fidelity Jake's Resume directly to PDF using xhtml2pdf.
    Guarantees that a valid 1-page PDF file is created even if no LaTeX binaries exist on host.
    """
    from xhtml2pdf import pisa
    from app.services.latex_renderer import render_html_resume, parse_tex_to_payload

    if render_payload is None:
        if tex_content:
            render_payload = parse_tex_to_payload(tex_content)
        else:
            render_payload = {"name": "Software Engineer"}

    html_content = render_html_resume(render_payload)
    out_p = Path(output_pdf_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "wb") as f:
        status = pisa.CreatePDF(html_content, dest=f)
        if status.err:
            logger.error("xhtml2pdf rendering error: %s", status.err)
            raise RuntimeError(f"xhtml2pdf rendering error: {status.err}")

    return str(out_p)


async def compile_latex_to_pdf(
    tex_content: str,
    output_pdf_path: str,
    timeout_seconds: float = 3.0,
    render_payload: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """
    Compiles LaTeX string into a PDF file.
    Tries Tectonic/pdflatex first if available; if not available or if compilation fails,
    seamlessly falls back to the embedded high-fidelity PDF rendering engine (xhtml2pdf)
    so the user ALWAYS gets a real, visual, 1-page PDF file.
    Returns:
        (saved_tex_path, output_pdf_path)
    """
    # 1. Save the .tex file alongside the intended .pdf destination
    tex_path = str(Path(output_pdf_path).with_suffix(".tex"))
    Path(tex_path).parent.mkdir(parents=True, exist_ok=True)
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_content)

    compiler = find_latex_compiler()

    if compiler:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_tex = Path(temp_dir) / "resume.tex"
                temp_tex.write_text(tex_content, encoding="utf-8")

                if "tectonic" in compiler:
                    cmd = [compiler, "-o", temp_dir, str(temp_tex)]
                else:  # pdflatex
                    cmd = ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, str(temp_tex)]

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                try:
                    stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
                except asyncio.TimeoutError:
                    try:
                        proc.kill()
                        await proc.wait()
                    except Exception:
                        pass
                    stdout_b, stderr_b = b"", b"timeout"

                temp_pdf = Path(temp_dir) / "resume.pdf"
                if proc.returncode == 0 and temp_pdf.is_file():
                    shutil.copyfile(str(temp_pdf), output_pdf_path)
                    logger.info("Compiled PDF successfully via %s", compiler)
                    return tex_path, output_pdf_path
                else:
                    logger.warning(
                        "LaTeX compiler %s failed (exit %s); falling back to direct PDF engine.",
                        compiler, proc.returncode
                    )
        except Exception as exc:
            logger.warning("LaTeX compiler %s execution failed (%s); falling back to direct PDF engine.", compiler, exc)

    # 2. Seamless Fallback to high-fidelity embedded PDF generator
    logger.info("Using high-fidelity embedded PDF engine for %s", output_pdf_path)
    render_pdf_fallback(output_pdf_path, render_payload=render_payload, tex_content=tex_content)
    return tex_path, output_pdf_path
