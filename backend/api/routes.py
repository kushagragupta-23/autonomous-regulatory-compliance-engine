import os
import hashlib
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body
from fastapi.responses import FileResponse
from backend.models.schemas import (
    AnalyzeRequest,
    ComplianceReport,
    TaxpayerProfile
)
from backend.models.clients import PRESET_CLIENTS
from backend.agents.orchestrator import ComplianceOrchestrator
from backend.services.document_service import DocumentService
from backend.services.vector_store import HybridRuleStore
from backend.services.pdf_exporter import CompliancePdfExporter
from backend.services.auto_scraper import RegulatoryScraperEngine
from backend.services.tax_feed_integration import TaxFeedIntelligence
from backend.services.scoring_engine import TenSignalHybridScorer

router = APIRouter(prefix="/api/v1", tags=["Compliance Intelligence"])

orchestrator = ComplianceOrchestrator()
rule_store = HybridRuleStore()
scraper = RegulatoryScraperEngine()
hybrid_scorer = TenSignalHybridScorer()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORTS_DIR, exist_ok=True)

REPORTS_CACHE: Dict[str, ComplianceReport] = {}
TASKS_STORE: Dict[str, Dict[str, Any]] = {}

def init_store():
    sample_docs = []
    if os.path.exists(DATA_DIR):
        for f in os.listdir(DATA_DIR):
            if f.endswith(".txt"):
                path = os.path.join(DATA_DIR, f)
                with open(path, "r", encoding="utf-8") as fl:
                    content = fl.read()
                    sample_docs.append({
                        "id": f,
                        "text": content,
                        "source": f
                    })
    if sample_docs:
        rule_store.index_documents(sample_docs)

# Initial scrape and index
scraper.run_live_scrape()
init_store()

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Regulatory & Tax Compliance Engine",
        "version": "2.0.0",
        "scoring_architecture": "10-Signal Hybrid Composite (BM25 + TF-IDF Cosine + Exponential Half-Life)",
        "indexed_documents": len(rule_store.documents),
        "scraped_feed_count": len(scraper.scraped_history),
        "authorities_supported": ["CBIC", "CBDT", "DGFT", "RBI", "SEBI", "PIB"],
        "clients_available": len(PRESET_CLIENTS),
        "active_tasks_count": len(TASKS_STORE)
    }

@router.get("/clients")
def list_clients():
    """Returns curated enterprise client profiles with GSTIN, PAN, and tax desks."""
    return PRESET_CLIENTS

@router.get("/feed")
def get_personalized_feed(
    client_id: Optional[str] = Query("client_kushagra_tech", description="Selected client ID"),
    statute: Optional[str] = Query(None, description="Filter by statute (GST, Income Tax, etc.)"),
    urgency: Optional[str] = Query(None, description="Filter by urgency"),
    q: Optional[str] = Query(None, description="Search query string")
):
    """
    Returns live scraped regulatory circulars ranked with the 10-Signal Hybrid Scoring Engine.
    Includes transparent explainability badges and actionable compliance task suggestions.
    """
    # Select client
    client = next((c for c in PRESET_CLIENTS if c["id"] == client_id), PRESET_CLIENTS[0])
    assigned_lead = client.get("assigned_lead")

    # Ensure feed is populated
    if not scraper.scraped_history:
        scraper.run_live_scrape()

    feed_items = []
    for item in scraper.scraped_history:
        # Apply filters
        if statute and statute.lower() != "all" and statute.lower() not in item.get("statute", "").lower():
            continue
        if urgency and urgency.lower() != "all" and urgency.lower() != item.get("urgency", "").lower():
            continue
        if q and q.strip():
            query_lower = q.lower()
            if query_lower not in item.get("title", "").lower() and query_lower not in item.get("summary", "").lower():
                continue

        # 10-Signal Hybrid Scoring & Explainability
        score_data = hybrid_scorer.score(item, client, assigned_lead)
        score_100 = score_data["score_100"]

        # Ensure task is registered in TASKS_STORE
        task = score_data["suggested_task"]
        t_id = task["task_id"]
        if t_id not in TASKS_STORE:
            TASKS_STORE[t_id] = {
                **task,
                "client_id": client["id"],
                "client_name": client["name"],
                "circular_id": item["id"],
                "circular_title": item["title"],
                "created_at": item["scraped_at"]
            }

        feed_items.append({
            **item,
            # Dual-compatible fields
            "relevance_score": score_100,
            "score_100": score_100,
            "rule_score": score_data["rule_score"],
            "semantic_score": score_data["semantic_score"],
            "sem_client": score_data["sem_client"],
            "sem_user": score_data["sem_user"],
            "signals": score_data["signals"],
            "reasons": score_data["reasons"],
            "explanation": score_data["explanation"],
            "client_impact": score_data["explanation"],
            "suggested_task": TASKS_STORE[t_id],
            "urgency_tier": score_data["urgency_tier"],
            "for_client": client["name"]
        })

    # Sort descending by 10-signal relevance score
    feed_items.sort(key=lambda x: x["score_100"], reverse=True)

    return {
        "client": client,
        "total_items": len(feed_items),
        "engine": "10-Signal Hybrid Scorer with Explainability Engine",
        "feed": feed_items
    }

@router.get("/tasks")
def list_compliance_tasks(client_id: Optional[str] = Query(None)):
    """Returns compliance action tasks generated from regulatory feeds."""
    tasks = list(TASKS_STORE.values())
    if client_id and client_id != "all":
        tasks = [t for t in tasks if t.get("client_id") == client_id]
    return {
        "total_tasks": len(tasks),
        "tasks": tasks
    }

@router.post("/tasks/{task_id}/action")
def update_task_action(task_id: str, payload: Dict[str, Any] = Body(...)):
    """Updates the workflow state of a client compliance task (APPROVE, DECLINE, GENERATE_MEMO)."""
    if task_id not in TASKS_STORE:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    action = payload.get("action", "APPROVE").upper()
    task = TASKS_STORE[task_id]

    if action == "APPROVE":
        task["status"] = "APPROVED_SCHEDULED"
        task["resolution_notes"] = f"Approved by Lead Practitioner. Added to client workplan. Due: {task.get('due_date')}."
    elif action == "DECLINE":
        task["status"] = "DECLINED_ARCHIVED"
        task["resolution_notes"] = "Declined by practitioner: Non-material impact for current audit cycle."
    elif action == "GENERATE_MEMO":
        task["status"] = "MEMO_GENERATED"
        task["resolution_notes"] = "Executive statutory advisory drafted and queued for client dispatch."
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action '{action}'. Use APPROVE, DECLINE, or GENERATE_MEMO.")

    return {
        "status": "success",
        "task_id": task_id,
        "action_taken": action,
        "updated_task": task
    }

@router.get("/samples")
def list_samples() -> List[Dict[str, str]]:
    samples = []
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".txt"):
                samples.append({
                    "id": filename,
                    "title": filename.replace(".txt", "").replace("_", " ").title()
                })
    return samples

@router.get("/samples/{sample_id}")
def get_sample_content(sample_id: str):
    file_path = os.path.join(DATA_DIR, sample_id)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Sample '{sample_id}' not found.")
    with open(file_path, "r", encoding="utf-8") as f:
        return {"id": sample_id, "content": f.read()}

@router.post("/analyze", response_model=ComplianceReport)
def analyze_compliance(request: AnalyzeRequest):
    content = ""
    if request.sample_id:
        file_path = os.path.join(DATA_DIR, request.sample_id)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            # Check if it matches an in-memory scraped feed item
            for item in scraper.scraped_history:
                if item["id"] == request.sample_id:
                    content = item["full_text"]
                    break
    elif request.circular_text:
        content = request.circular_text

    if not content:
        raise HTTPException(status_code=400, detail="Either 'circular_text' or valid 'sample_id' must be provided.")

    profile = request.taxpayer_profile or TaxpayerProfile()
    report = orchestrator.run_pipeline(content, profile)
    REPORTS_CACHE[report.report_id] = report

    # Pre-generate corporate PDF memo
    pdf_path = os.path.join(EXPORTS_DIR, f"{report.report_id}_compliance_memo.pdf")
    CompliancePdfExporter.generate_pdf(report, pdf_path)

    return report

@router.get("/export-pdf/{report_id}")
def download_pdf_memorandum(report_id: str):
    pdf_path = os.path.join(EXPORTS_DIR, f"{report_id}_compliance_memo.pdf")
    if not os.path.exists(pdf_path):
        if report_id in REPORTS_CACHE:
            CompliancePdfExporter.generate_pdf(REPORTS_CACHE[report_id], pdf_path)
        else:
            raise HTTPException(status_code=404, detail=f"Compliance report '{report_id}' not found.")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"Compliance_Memorandum_{report_id}.pdf"
    )

@router.post("/upload-pdf")
async def upload_pdf_and_analyze(file: UploadFile = File(...)):
    filename = file.filename.lower()
    content = ""
    pages_count = 1

    temp_path = os.path.join(DATA_DIR, f"temp_{file.filename}")
    try:
        raw_bytes = await file.read()
        with open(temp_path, "wb") as f:
            f.write(raw_bytes)

        if filename.endswith(".pdf"):
            parsed_pdf = DocumentService.parse_pdf(temp_path)
            content = parsed_pdf["full_text"]
            pages_count = parsed_pdf["pages"]
        elif filename.endswith(".txt"):
            content = raw_bytes.decode("utf-8", errors="replace")
        elif filename.endswith(".docx"):
            import docx
            doc = docx.Document(temp_path)
            content = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
        else:
            raise HTTPException(status_code=400, detail="Supported formats: .pdf, .txt, .docx")

        if not content.strip():
            raise HTTPException(status_code=400, detail="Extracted text is empty.")

        report = orchestrator.run_pipeline(content, TaxpayerProfile())
        REPORTS_CACHE[report.report_id] = report
        pdf_path = os.path.join(EXPORTS_DIR, f"{report.report_id}_compliance_memo.pdf")
        CompliancePdfExporter.generate_pdf(report, pdf_path)

        return {
            "document_metadata": {
                "source": file.filename,
                "pages": pages_count,
                "checksum": hashlib.sha256(raw_bytes).hexdigest()[:12]
            },
            "compliance_report": report
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/search")
def search_regulations(q: str, top_k: int = 2):
    if not q:
        raise HTTPException(status_code=400, detail="Search query 'q' cannot be empty.")
    results = rule_store.query(q, top_k=top_k)
    return {"query": q, "results_count": len(results), "matches": results}

@router.post("/scraper/trigger")
def trigger_auto_scrape():
    """Triggers live web scraping with BeautifulSoup4 and re-indexes into Hybrid RAG store."""
    scrape_res = scraper.run_live_scrape()
    init_store()
    return scrape_res

@router.get("/scraper/status")
def get_scraper_status():
    return {
        "engine": "BeautifulSoup4 Multi-Regulator Parser",
        "authorities": ["CBIC", "CBDT", "DGFT", "RBI", "SEBI", "PIB"],
        "last_scraped_count": len(scraper.scraped_history),
        "recent_records": scraper.scraped_history
    }
