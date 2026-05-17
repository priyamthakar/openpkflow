"""Report generation module.

v0.1.x: Markdown and HTML reports.
v0.3.0+: ReportLab PDF, python-docx Word (planned).
"""
from .html import render_html_report

__all__ = ["render_html_report"]
