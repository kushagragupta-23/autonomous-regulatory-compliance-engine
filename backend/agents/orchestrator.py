import uuid
from datetime import datetime, timezone
from typing import Optional
from backend.models.schemas import (
    TaxpayerProfile,
    ComplianceReport,
    ParsingAgentOutput,
    ImpactItem,
    AuditVerification
)
from .parser_agent import ParserAgent
from .tax_diff_agent import TaxDiffAgent
from .audit_agent import AuditAgent

class ComplianceOrchestrator:
    """Orchestrates the multi-agent pipeline for regulatory compliance auditing."""

    def __init__(self):
        self.parser = ParserAgent()
        self.diff_agent = TaxDiffAgent()
        self.auditor = AuditAgent()

    def run_pipeline(self, circular_text: str, profile: Optional[TaxpayerProfile] = None) -> ComplianceReport:
        if profile is None:
            profile = TaxpayerProfile()

        # Step 1: Parsing Agent extracts regulatory clauses
        parsed_output: ParsingAgentOutput = self.parser.process(circular_text)

        # Step 2: Tax Diff Agent determines corporate/individual impact
        impacts: list[ImpactItem] = self.diff_agent.evaluate(parsed_output, profile)

        # Step 3: Auditor Agent validates citations & checks for hallucinations
        audit_res: AuditVerification = self.auditor.verify(parsed_output, impacts, circular_text)

        # Determine overall compliance rating
        has_critical = any(i.risk_level == "CRITICAL" for i in impacts)
        has_high = any(i.risk_level == "HIGH" for i in impacts)

        if has_critical:
            overall_status = "HIGH_RISK_DEFICIT"
        elif has_high:
            overall_status = "ACTION_REQUIRED"
        else:
            overall_status = "COMPLIANT"

        # Actionable next steps
        next_steps = []
        for imp in impacts:
            if imp.risk_level in ["CRITICAL", "HIGH"]:
                next_steps.append(f"[{imp.rule_section}] {imp.action_required} (Deadline: {imp.deadline})")

        if not next_steps:
            next_steps.append("Archive circular in annual tax audit compliance binder. No immediate operational changes needed.")

        report = ComplianceReport(
            report_id=f"REP-{uuid.uuid4().hex[:8].upper()}",
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            taxpayer_profile=profile,
            circular_meta=parsed_output,
            impact_assessment=impacts,
            audit_report=audit_res,
            overall_compliance_status=overall_status,
            recommended_next_steps=next_steps
        )

        return report
