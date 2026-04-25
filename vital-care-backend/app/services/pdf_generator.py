import io
import logging
from datetime import datetime
from app.schemas.wellbeing import EscalationSummary

logger = logging.getLogger(__name__)

_DISCLAIMER = (
    "This document is not a medical record. Bring it to your provider "
    "to help explain how you have been feeling."
)


class WellbeingPDFGenerator:
    """Generates a 1-page student well-being summary PDF using fpdf2."""

    def generate(self, summary: EscalationSummary, session_id: str) -> bytes:
        try:
            from fpdf import FPDF
        except ImportError:
            logger.error("fpdf2 not installed. Run: pip install fpdf2")
            return b""

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Student Well-being Summary Report", ln=True, align="C")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  |  Session: {session_id[:8]}...", ln=True, align="C")
        pdf.ln(4)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        # Session overview
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Session Overview", ln=True)
        pdf.set_font("Helvetica", "", 10)

        mood_scores = [p.score for p in summary.mood_timeline]
        stress_scores = [p.score for p in summary.stress_timeline]
        severity = summary.severity_progression[-1] if summary.severity_progression else "CRITICAL"

        overview_lines = [
            f"Duration: {summary.duration_minutes} minutes",
            f"Final Severity: {severity}",
            f"Mood Range: {min(mood_scores) if mood_scores else '?'} - {max(mood_scores) if mood_scores else '?'} / 10",
            f"Stress Peak: {max(stress_scores) if stress_scores else '?'} / 10",
        ]
        for line in overview_lines:
            pdf.cell(0, 7, line, ln=True)
        pdf.ln(3)

        # Key concerns
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Key Concerns Identified", ln=True)
        pdf.set_font("Helvetica", "", 10)
        top_tags = [t.tag for t in summary.top_tags[:6]]
        pdf.multi_cell(0, 7, "  ".join(top_tags) if top_tags else "No tags recorded")
        pdf.ln(3)

        # Key moments
        if summary.key_moments:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "What You Shared", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for moment in summary.key_moments[:3]:
                safe_moment = moment[:120] + "..." if len(moment) > 120 else moment
                pdf.multi_cell(0, 7, f"• \"{safe_moment}\"")
            pdf.ln(3)

        # Recommended next steps
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Recommended Next Steps", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for i, resource in enumerate(summary.immediate_resources, 1):
            pdf.cell(0, 7, f"{i}. {resource}", ln=True)
        if summary.nearby_providers:
            for provider in summary.nearby_providers[:2]:
                line = f"• {provider.get('name', '')} | {provider.get('address', '')} | {provider.get('phone', '')}"
                pdf.multi_cell(0, 7, line)
        pdf.ln(3)

        # Severity progression
        if len(summary.severity_progression) > 1:
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Severity Progression", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 7, " → ".join(summary.severity_progression), ln=True)
            pdf.ln(3)

        # Disclaimer
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "I", 9)
        pdf.multi_cell(0, 6, f"⚠️  {_DISCLAIMER}")

        return bytes(pdf.output())


def get_pdf_generator() -> WellbeingPDFGenerator:
    return WellbeingPDFGenerator()
