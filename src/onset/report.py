
"""Self-contained HTML report for an onset Finding."""

from datetime import datetime
from html import escape
from pathlib import Path


def _sample_block(label, sample, color):
    rate_pct = round(sample.rate * 100)
    return (
        '<div style="flex:1;background:white;border:1px solid #e5e7eb;'
        'border-radius:8px;padding:16px 20px;">'
        '<div style="font-size:11px;color:#666;text-transform:uppercase;'
        'letter-spacing:0.5px;font-weight:600;">' + escape(label) + '</div>'
        '<div style="font-size:28px;font-weight:700;color:' + color
        + ';margin-top:6px;">' + str(rate_pct) + '%</div>'
        '<div style="font-size:12px;color:#666;margin-top:4px;">'
        + str(sample.failures) + ' / ' + str(sample.runs) + ' failed</div>'
        '</div>'
    )


def render_report(finding, output_path=None):
    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if finding.status == "found":
        c = finding.culprit
        title_color = "#15803d"
        headline = "ONSET FOUND"
        body = (
            '<div style="background:white;border:1px solid #e5e7eb;'
            'border-radius:8px;padding:20px;margin-bottom:16px;">'
            '<div style="font-family:ui-monospace,Menlo,monospace;font-size:13px;">'
            + '<div style="margin-bottom:8px;"><strong>Commit:</strong> '
            + escape(c.sha) + '</div>'
            + '<div style="margin-bottom:8px;"><strong>Author:</strong> '
            + escape(c.author) + '</div>'
            + '<div style="margin-bottom:8px;"><strong>Date:</strong> '
            + escape(c.date) + '</div>'
            + '<div><strong>Message:</strong> ' + escape(c.message) + '</div>'
            + '</div></div>'
            + '<div style="display:flex;gap:12px;margin-bottom:16px;">'
            + _sample_block("Before (parent)", finding.before, "#15803d")
            + _sample_block("After (culprit)", finding.after, "#b91c1c")
            + '</div>'
            + '<div style="background:white;border:1px solid #e5e7eb;'
            'border-radius:8px;padding:16px 20px;">'
            + '<div style="font-size:11px;color:#666;text-transform:uppercase;'
            'letter-spacing:0.5px;font-weight:600;margin-bottom:8px;">'
            'Statistically verified</div>'
            + '<div style="font-size:14px;">p-value: <strong>'
            + str(round(finding.p_value, 4)) + '</strong> '
            '(threshold &lt; 0.05)</div>'
            + '</div>'
        )
        if c.files:
            body += (
                '<div style="background:white;border:1px solid #e5e7eb;'
                'border-radius:8px;padding:16px 20px;margin-top:16px;">'
                '<div style="font-size:11px;color:#666;text-transform:uppercase;'
                'letter-spacing:0.5px;font-weight:600;margin-bottom:8px;">'
                'Changed files</div>'
                '<div style="font-family:ui-monospace,Menlo,monospace;font-size:13px;">'
                + "".join('<div>' + escape(f) + '</div>' for f in c.files[:15])
                + '</div></div>'
            )
    elif finding.status == "not_found":
        title_color = "#b45309"
        headline = "NO SINGLE CULPRIT"
        body = (
            '<div style="background:white;border:1px solid #e5e7eb;'
            'border-radius:8px;padding:20px;font-size:15px;">'
            + escape(finding.message)
            + '<div style="margin-top:12px;font-family:ui-monospace,Menlo,monospace;'
            'font-size:13px;color:#666;">Range: '
            + escape(finding.range_from) + ' .. ' + escape(finding.range_to)
            + '</div></div>'
        )
    elif finding.status == "no_flake":
        title_color = "#4b5563"
        headline = "NOT FLAKY"
        body = (
            '<div style="background:white;border:1px solid #e5e7eb;'
            'border-radius:8px;padding:20px;font-size:15px;">'
            + escape(finding.message) + '</div>'
        )
    else:
        title_color = "#b91c1c"
        headline = "ERROR"
        body = (
            '<div style="background:white;border:1px solid #e5e7eb;'
            'border-radius:8px;padding:20px;font-size:15px;">'
            + escape(finding.message) + '</div>'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>onset report - {escape(finding.test_id)}</title>
</head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
             margin:0;padding:32px;background:#f9fafb;color:#111827;line-height:1.5;">
<h1 style="margin:0 0 4px 0;font-size:22px;">onset report</h1>
<div style="color:#666;font-size:14px;margin-bottom:24px;">
  Test: <strong>{escape(finding.test_id)}</strong> &nbsp;&middot;&nbsp;
  Generated: <strong>{escape(generated)}</strong>
</div>
<h2 style="color:{title_color};font-size:18px;margin:0 0 16px 0;">{headline}</h2>
{body}
<footer style="margin-top:48px;padding-top:16px;border-top:1px solid #e5e7eb;
               color:#9ca3af;font-size:12px;text-align:center;">
  Generated by onset &middot; {escape(generated)}
</footer>
</body>
</html>
"""

    if output_path is None:
        Path("reports").mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = "reports/onset-" + ts + ".html"

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return str(out)
