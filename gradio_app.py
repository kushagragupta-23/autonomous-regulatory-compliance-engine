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
            "⚠️ Please enter or select a circular text.",
            "",
            "",
            None
        )

    profile = TaxpayerProfile(
        entity_name=entity_name or "Acme Corp Ltd",
        entity_type=entity_type,
        annual_turnover=float(turnover) if turnover else 50000000.0,
        annual_income=12000000.0,
        gst_registered=(is_gst == "Yes"),
        opted_new_tax_regime=True
    )

    report = orchestrator.run_pipeline(circular_text, profile)

    # Status & KPI Banner
    status_color = "#10B981" if "COMPLIANT" in report.overall_compliance_status else ("#F59E0B" if "ACTION" in report.overall_compliance_status else "#EF4444")
    status_md = f"""
### ⚖️ Overall Status: <span style='color:{status_color}; font-weight:bold;'>{report.overall_compliance_status.replace('_', ' ')}</span>
**Report ID**: `{report.report_id}` | **Authority**: `{report.circular_meta.issuing_authority}` | **Hallucination Risk**: `< {report.audit_report.hallucination_risk_score * 100:.1f}%`
"""

    # Sectors, Topics & Urgency (Integrated from Tax Feed Intelligence)
    sectors_html = " ".join([f"<span style='background:#1E293B;color:#38BDF8;padding:3px 8px;border-radius:4px;font-size:12px;'>{s}</span>" for s in report.circular_meta.applicable_sectors])
    topics_html = " ".join([f"<span style='background:#1E293B;color:#A7F3D0;padding:3px 8px;border-radius:4px;font-size:12px;'>{t}</span>" for t in report.circular_meta.tax_topics])

    meta_md = f"""
**Applicable Enterprise Sectors**: {sectors_html}  
**Tax Topics**: {topics_html}  
**Timeline Directive**: `{report.circular_meta.urgency_status}`
"""

    # Impact assessment breakdown
    impact_rows = []
    for imp in report.impact_assessment:
        badge = f"<b style='color:{'#EF4444' if imp.risk_level=='CRITICAL' else ('#F59E0B' if imp.risk_level=='HIGH' else '#10B981')}'>{imp.risk_level}</b>"
        impact_rows.append(f"""
#### {imp.rule_section} [{badge}]
- **Operational Finding**: {imp.description}
- **Action Required**: {imp.action_required}
- **Statutory Deadline**: `{imp.deadline}` | **Exposure**: `{imp.financial_exposure}`
---
""")
    impacts_md = "\n".join(impact_rows)

    # Generate PDF audit memorandum
    temp_pdf = os.path.join(tempfile.gettempdir(), f"{report.report_id}_compliance_memo.pdf")
    CompliancePdfExporter.generate_pdf(report, temp_pdf)

    return status_md, meta_md, impacts_md, temp_pdf

def load_sample(sample_name):
    return SAMPLES.get(sample_name, "")

def auto_scrape_portals():
    global SAMPLES
    res = scraper.run_live_scrape()
    SAMPLES = get_sample_texts()
    new_choices = list(SAMPLES.keys())
    first_text = SAMPLES[new_choices[0]] if new_choices else ""
    status = f"✅ Scraped {res['items_scraped']} latest regulatory gazettes via BeautifulSoup4! Re-indexed into Hybrid RAG."
    return gr.update(choices=new_choices, value=new_choices[0] if new_choices else None), first_text, status

with gr.Blocks(title="ReguTax AI | Compliance Intelligence") as demo:
    gr.Markdown("""
    # ⚖️ Autonomous Regulatory & Tax Compliance Agent
    ### Enterprise Multi-Agent Regulatory Auditing & Zero-Hallucination Risk Evaluation
    *Powered by multi-agent reasoning, BM25 retrieval, and Personalised Tax Feed Domain Intelligence.*
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🏢 Taxpayer Profile")
            entity_name = gr.Textbox(value="Kushagra Enterprises Ltd", label="Entity Name")
            entity_type = gr.Dropdown(
                choices=["Private_Limited", "Public_Limited", "Partnership", "Individual", "HUF"],
                value="Private_Limited",
                label="Entity Legal Structure"
            )
            turnover = gr.Number(value=65000000, label="Annual Turnover (INR)")
            is_gst = gr.Radio(choices=["Yes", "No"], value="Yes", label="GST Registered?")

            gr.Markdown("### 📄 Preloaded Samples")
            sample_dropdown = gr.Dropdown(choices=list(SAMPLES.keys()), label="Choose Sample Gazette", value=list(SAMPLES.keys())[0] if SAMPLES else None)
            load_btn = gr.Button("Load Sample Content")

        with gr.Column(scale=2):
            gr.Markdown("### 📜 Circular / Statutory Gazette Text")
            circular_text = gr.Textbox(
                value=list(SAMPLES.values())[0] if SAMPLES else "",
                lines=12,
                label="Input Regulatory Text"
            )
            audit_btn = gr.Button("⚡ Execute Multi-Agent Audit", variant="primary")

    load_btn.click(fn=load_sample, inputs=[sample_dropdown], outputs=[circular_text])

    gr.Markdown("---")
    gr.Markdown("## 📊 Executive Audit Findings & Exposure")

    with gr.Row():
        with gr.Column():
            status_output = gr.Markdown("Click 'Execute Multi-Agent Audit' above to run analysis.")
            meta_output = gr.Markdown()
            pdf_download = gr.File(label="📥 Download Executive PDF Audit Memo")
        with gr.Column():
            impacts_output = gr.Markdown()

    audit_btn.click(
        fn=run_audit,
        inputs=[circular_text, entity_name, entity_type, turnover, is_gst],
        outputs=[status_output, meta_output, impacts_output, pdf_download]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7861)

