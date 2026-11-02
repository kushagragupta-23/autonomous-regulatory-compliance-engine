import os
import sys
import tempfile
import gradio as gr

# Ensure backend can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.agents.orchestrator import ComplianceOrchestrator
from backend.models.schemas import TaxpayerProfile
from backend.services.pdf_exporter import CompliancePdfExporter
from backend.services.auto_scraper import RegulatoryScraperEngine

orchestrator = ComplianceOrchestrator()
scraper = RegulatoryScraperEngine()

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def get_sample_texts():
    samples = {}
    if os.path.exists(DATA_DIR):
        for f in os.listdir(DATA_DIR):
            if f.endswith(".txt"):
                name = f.replace(".txt", "").replace("_", " ").title()
                with open(os.path.join(DATA_DIR, f), "r", encoding="utf-8") as fl:
                    samples[name] = fl.read()
    return samples

SAMPLES = get_sample_texts()

def run_audit(circular_text, entity_name, entity_type, turnover, is_gst):
    if not circular_text or not circular_text.strip():
        return (
            "⚠️ **Please enter or select a circular text.**",
            "",
            "No circular provided for auditing.",
            None
        )

    profile = TaxpayerProfile(
        entity_name=entity_name or "Kushagra Enterprises Ltd",
        entity_type=entity_type or "Private_Limited",
        annual_turnover=float(turnover) if turnover else 65000000.0,
        annual_income=12000000.0,
        gst_registered=(is_gst == "Yes"),
        opted_new_tax_regime=True
    )

    report = orchestrator.run_pipeline(circular_text, profile)

    # Status & KPI Banner
    status_color = "#10B981" if "COMPLIANT" in report.overall_compliance_status else ("#F59E0B" if "ACTION" in report.overall_compliance_status else "#EF4444")
    status_md = f"""
## ⚖️ Overall Status: <span style='color:{status_color}; font-weight:800;'>{report.overall_compliance_status.replace('_', ' ')}</span>
**Report ID**: `{report.report_id}` | **Issuing Authority**: `{report.circular_meta.issuing_authority}`  
**Calculated Hallucination Risk**: `< {report.audit_report.hallucination_risk_score * 100:.1f}% (Zero-Hallucination Verified)`
"""

    # Sectors, Topics & Urgency
    sectors_html = " ".join([f"<span style='background:#1E293B;color:#38BDF8;padding:3px 8px;border-radius:4px;font-size:12px;'>{s}</span>" for s in report.circular_meta.applicable_sectors])
    topics_html = " ".join([f"<span style='background:#1E293B;color:#A7F3D0;padding:3px 8px;border-radius:4px;font-size:12px;'>{t}</span>" for t in report.circular_meta.tax_topics])

    meta_md = f"""
**Applicable Enterprise Sectors**: {sectors_html}  
**Tax Topics**: {topics_html}  
**Statutory Directive**: `{report.circular_meta.urgency_status}`
"""

    # Impact assessment breakdown
    impact_rows = []
    for imp in report.impact_assessment:
        badge = f"<b style='color:{'#EF4444' if imp.risk_level=='CRITICAL' else ('#F59E0B' if imp.risk_level=='HIGH' else '#10B981')}'>{imp.risk_level}</b>"
        impact_rows.append(f"""
#### {imp.rule_section} [{badge}]
- **Operational Finding**: {imp.description}
- **Action Required**: {imp.action_required}
- **Statutory Deadline**: `{imp.deadline}` | **Financial Exposure**: `{imp.financial_exposure}`
---
""")
    impacts_md = "\n".join(impact_rows) if impact_rows else "✅ No adverse exposures identified for this entity profile."

    # Generate PDF audit memorandum in exports directory for safe Gradio file serving
    exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
    os.makedirs(exports_dir, exist_ok=True)
    pdf_path = os.path.join(exports_dir, f"{report.report_id}_compliance_memo.pdf")
    CompliancePdfExporter.generate_pdf(report, pdf_path)

    return status_md, meta_md, impacts_md, pdf_path

def load_sample(sample_name):
    return SAMPLES.get(sample_name, "")

with gr.Blocks(title="ReguTax AI | Compliance Intelligence") as demo:
    gr.Markdown("""
    # ⚖️ Autonomous Regulatory & Tax Compliance Agent
    > **Enterprise Multi-Agent Intelligence System for Continuous Statutory Auditing & Zero-Hallucination Risk Evaluation**  
    *Author: Kushagra Gupta · [GitHub Code](https://github.com/kushagragupta-23/autonomous-regulatory-compliance-engine) · [Portfolio](https://kushagragupta-23.github.io)*
    """)

    with gr.Row():
        # LEFT COLUMN: INPUTS & CONTROLS
        with gr.Column(scale=5):
            gr.Markdown("### 🏢 1. Taxpayer Profile")
            with gr.Row():
                entity_name = gr.Textbox(value="Kushagra Enterprises Ltd", label="Entity Name", scale=2)
                entity_type = gr.Dropdown(
                    choices=["Private_Limited", "Public_Limited", "Partnership", "Individual", "HUF"],
                    value="Private_Limited",
                    label="Entity Structure",
                    scale=1
                )
            with gr.Row():
                turnover = gr.Number(value=65000000, label="Annual Turnover (INR)", scale=2)
                is_gst = gr.Radio(choices=["Yes", "No"], value="Yes", label="GST Registered?", scale=1)

            gr.Markdown("### 📜 2. Regulatory Gazette / Circular")
            sample_dropdown = gr.Dropdown(
                choices=list(SAMPLES.keys()),
                label="Choose Preloaded Statutory Gazette",
                value=list(SAMPLES.keys())[0] if SAMPLES else None
            )
            circular_text = gr.Textbox(
                value=list(SAMPLES.values())[0] if SAMPLES else "",
                lines=8,
                label="Input Regulatory Text (Auto-fills from dropdown above)"
            )
            audit_btn = gr.Button("⚡ Execute Multi-Agent Audit", variant="primary", size="lg")

        # RIGHT COLUMN: REAL-TIME AUDIT DASHBOARD
        with gr.Column(scale=6):
            gr.Markdown("### 📊 Executive Findings & Exposure")
            status_output = gr.Markdown("👉 Select a gazette on the left and click **'⚡ Execute Multi-Agent Audit'**.")
            meta_output = gr.Markdown()
            with gr.Accordion("📋 Detailed Statutory Findings & Action Plan", open=True):
                impacts_output = gr.Markdown("Audit findings and exposure breakdowns will render here.")
            pdf_download = gr.File(label="📥 Download Executive PDF Audit Memo")

    sample_dropdown.change(fn=load_sample, inputs=[sample_dropdown], outputs=[circular_text])

    audit_btn.click(
        fn=run_audit,
        inputs=[circular_text, entity_name, entity_type, turnover, is_gst],
        outputs=[status_output, meta_output, impacts_output, pdf_download]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7861)
