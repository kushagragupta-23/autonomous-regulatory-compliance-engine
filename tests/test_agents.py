import pytest
from backend.agents.parser_agent import ParserAgent
from backend.agents.tax_diff_agent import TaxDiffAgent
from backend.agents.audit_agent import AuditAgent
from backend.agents.orchestrator import ComplianceOrchestrator
from backend.models.schemas import TaxpayerProfile

SAMPLE_CIRCULAR_194R = """
CENTRAL BOARD OF DIRECT TAXES
Circular No. 12 of 2022
Guidelines under Section 194R of the Income-tax Act, 1961.
Mandates withholding tax at 10% on benefits and perquisites exceeding INR 20,000 provided to residents.
"""

def test_parser_agent():
    parser = ParserAgent()
    output = parser.process(SAMPLE_CIRCULAR_194R)
    assert output.issuing_authority == "CBDT (Direct Taxes)"
    assert len(output.extracted_rules) >= 1
    assert any("194R" in r.section for r in output.extracted_rules)

def test_tax_diff_agent_corporate():
    parser = ParserAgent()
    parsed = parser.process(SAMPLE_CIRCULAR_194R)
    diff_agent = TaxDiffAgent()

    corp_profile = TaxpayerProfile(entity_type="Private_Limited", annual_turnover=50000000.0)
    impacts = diff_agent.evaluate(parsed, corp_profile)

    assert len(impacts) >= 1
    high_risks = [i for i in impacts if i.risk_level == "HIGH"]
    assert len(high_risks) >= 1
    assert "Section 194R" in high_risks[0].rule_section

def test_audit_agent_zero_hallucination():
    parser = ParserAgent()
    parsed = parser.process(SAMPLE_CIRCULAR_194R)
    diff_agent = TaxDiffAgent()
    profile = TaxpayerProfile()
    impacts = diff_agent.evaluate(parsed, profile)

    auditor = AuditAgent()
    verification = auditor.verify(parsed, impacts, SAMPLE_CIRCULAR_194R)

    assert verification.citation_valid is True
    assert verification.validation_status == "PASSED"
    assert verification.hallucination_risk_score <= 0.05

def test_orchestrator_end_to_end():
    orchestrator = ComplianceOrchestrator()
    report = orchestrator.run_pipeline(SAMPLE_CIRCULAR_194R)

    assert report.report_id.startswith("REP-")
    assert report.overall_compliance_status in ["COMPLIANT", "ACTION_REQUIRED", "HIGH_RISK_DEFICIT"]
    assert len(report.impact_assessment) > 0
    assert report.audit_report.citation_valid is True

