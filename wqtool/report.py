"""FR-4, FR-7, FR-8 display helpers. Build HTML from results; calculate nothing new."""
from __future__ import annotations

from html import escape

from wqtool.classifier import COLOR_NOTICE, NOT_PROVIDED, Result
from wqtool.recommender import NO_SUGGESTION_MESSAGE, Assessment
from wqtool.validation import TestEntry

LAB_WARNING = (
    "This tool does not test for lead, arsenic, nitrates, bacteria, or PFAS "
    "and cannot confirm that water is safe to drink. Use a certified laboratory "
    "to test for these contaminants."
)
TITLE = "Water Quality Decision Support Tool"
# Background and text color for each status. The written label always appears with it.
STATUS_COLORS = {
    "green": ("#2e7d32", "#ffffff"),
    "yellow": ("#f9c513", "#1a1a1a"),
    "red": ("#c62828", "#ffffff"),
}


def format_value(result: Result) -> str:
    if result.value is None:
        return "Not provided"
    number = f"{result.value:g}"
    return number if result.unit == "pH" else f"{number} {result.unit.split(' (')[0]}"


def status_chip(result: Result) -> str:
    """Colored chip with a written label. A blank reading gets plain text and no color."""
    if result.status == NOT_PROVIDED:
        return escape(result.status_label)
    background, text = STATUS_COLORS[result.status]
    return (
        f'<span style="background:{background};color:{text};padding:2px 8px;'
        f'border-radius:4px;font-weight:600;white-space:nowrap;'
        f'-webkit-print-color-adjust:exact;print-color-adjust:exact;">'
        f"{escape(result.status.capitalize())}: {escape(result.status_label)}</span>"
    )


def results_table_html(results: tuple[Result, ...]) -> str:
    cell = 'style="padding:6px 8px;border-bottom:1px solid #bbb;vertical-align:top;text-align:left;"'
    rows = []
    for r in results:
        detail = "" if r.status == NOT_PROVIDED else (
            f"{escape(r.comparison_text)}<br>{escape(r.explanation)}"
        )
        rows.append(
            f"<tr><td {cell}><strong>{escape(r.display_name)}</strong></td>"
            f"<td {cell}>{escape(format_value(r))}</td>"
            f"<td {cell}>{status_chip(r)}</td>"
            f"<td {cell}>{detail}</td></tr>"
        )
    head = "".join(f"<th {cell}>{name}</th>" for name in
                   ("Measurement", "Your result", "Status", "What it means"))
    return (
        '<table style="width:100%;border-collapse:collapse;">'
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
    )


def suggestions_html(assessment: Assessment) -> str:
    if not assessment.suggestions:
        return f"<p>{escape(NO_SUGGESTION_MESSAGE)}</p>"
    names = {r.parameter_id: r.display_name for r in assessment.results}
    items = []
    for s in assessment.suggestions:
        cause = names.get(s.parameter_id)
        label = f"<strong>{escape(cause)}:</strong> " if cause else ""
        items.append(
            f'<li style="margin-bottom:6px;">{label}{escape(s.suggestion_text)}<br>'
            f"<em>Why: {escape(s.reason_text)}</em></li>"
        )
    return f'<ul style="margin:0;padding-left:20px;">{"".join(items)}</ul>'


def sources_text(results: tuple[Result, ...]) -> str:
    seen = []
    for r in results:
        if r.reference_source not in seen:
            seen.append(r.reference_source)
    return "Reference sources: " + "; ".join(seen) + "."


def household_text(entry: TestEntry) -> str:
    people = "person" if entry.household_size == 1 else "people"
    return f"Household: {entry.household_size} {people}. Water source: {entry.water_source}."


def summary_body_html(entry: TestEntry, assessment: Assessment) -> str:
    """The one-page summary (FR-7). Uses the same results and suggestions as the screen."""
    return (
        f'<h1 style="font-size:16pt;margin:0 0 2pt 0;">{TITLE}</h1>'
        '<p style="margin:0 0 8pt 0;">Water test summary</p>'
        f'<p style="margin:0 0 8pt 0;">{escape(household_text(entry))}</p>'
        f"{results_table_html(assessment.results)}"
        f'<p style="margin:6pt 0;font-size:9pt;">{escape(COLOR_NOTICE)}</p>'
        '<h2 style="font-size:12pt;margin:10pt 0 4pt 0;">Suggestions to discuss with a professional</h2>'
        f"{suggestions_html(assessment)}"
        f'<p style="margin:8pt 0;font-size:9pt;">{escape(sources_text(assessment.results))}</p>'
        '<p style="margin:8pt 0 0 0;padding:6pt;border:1.5pt solid #000;">'
        f"<strong>Important:</strong> {escape(LAB_WARNING)}</p>"
    )


def print_component_html(entry: TestEntry, assessment: Assessment) -> str:
    """A 'Print summary' button plus the summary, which is shown only when printing.

    One click opens the browser print dialog. Nothing is sent to a server or saved.
    """
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
  @page {{ size: letter; margin: 0.6in; }}
  body {{ margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 9.5pt; line-height: 1.25; color: #000; }}
  #summary td, #summary th {{ padding: 3px 6px !important; }}
  #summary li {{ margin-bottom: 3px !important; }}
  #summary {{ display: none; }}
  button {{ font: 600 15px Arial, Helvetica, sans-serif; padding: 8px 18px; cursor: pointer;
           border: 1px solid #888; border-radius: 8px; background: #fff; color: #1a1a1a; }}
  @media print {{ #controls {{ display: none; }} #summary {{ display: block; }} }}
</style></head><body>
<div id="controls"><button type="button" onclick="window.print()">Print summary</button></div>
<div id="summary">{summary_body_html(entry, assessment)}</div>
</body></html>"""
