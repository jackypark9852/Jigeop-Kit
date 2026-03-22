"""Jinja2 environment configured for LaTeX output.

Uses custom delimiters to avoid conflicts with LaTeX braces:
  Variables:  \\VAR{ expr }
  Blocks:     \\BLOCK{ stmt }  ...  \\BLOCK{ endstmt }
  Comments:   %# comment #%

Usage:
    from templates.jinja_env import get_env
    env = get_env()
    tmpl = env.get_template("resume.tex.j2")
    rendered = tmpl.render(context)
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

TEMPLATES_DIR = Path(__file__).parent

_LATEX_ESCAPE = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}


def _latex_escape(text: str) -> str:
    """Escape special LaTeX characters in a string."""
    if not isinstance(text, str):
        text = str(text)
    return "".join(_LATEX_ESCAPE.get(c, c) for c in text)


def get_env() -> Environment:
    """Return a Jinja2 Environment configured for LaTeX templates."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        # Custom delimiters — safe inside LaTeX source
        block_start_string=r"\BLOCK{",
        block_end_string="}",
        variable_start_string=r"\VAR{",
        variable_end_string="}",
        comment_start_string=r"%#",
        comment_end_string="#%",
        # Trim whitespace around block tags to keep LaTeX output clean
        trim_blocks=True,
        lstrip_blocks=True,
        # Catch typos in template variable names
        undefined=StrictUndefined,
        # Don't auto-escape (we handle escaping via the filter)
        autoescape=False,
    )
    env.filters["e"] = _latex_escape  # \VAR{ name | e }
    return env
