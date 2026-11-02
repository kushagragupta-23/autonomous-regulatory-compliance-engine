from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class TaxpayerProfile(BaseModel):
    entity_name: str = Field(default="Acme Corp Ltd")
    entity_type: Literal["Individual", "HUF", "Partnership", "Private_Limited", "Public_Limited"] = "Private_Limited"
    annual_turnover: float = Field(default=50000000.0, description="Annual turnover in local currency")
    annual_income: float = Field(default=12000000.0, description="Net taxable income")
    industry_sector: str = Field(default="Information Technology")
    gst_registered: bool = Field(default=True)
    opted_new_tax_regime: bool = Field(default=True)
    employees_count: int = Field(default=45)

class ExtractedRule(BaseModel):
    section: str
    topic: str
    statutory_rate: Optional[str] = None
    threshold_limit: Optional[str] = None
    effective_date: str = "Immediate"
    raw_clause: str
    confidence_score: float = 0.95

class ParsingAgentOutput(BaseModel):
    circular_id: str
    issuing_authority: str
    notification_date: str
    title: str
    summary: str
    extracted_rules: List[ExtractedRule] = []
    applicable_sectors: List[str] = ["General Business / Commercial"]
    tax_topics: List[str] = ["Statutory Compliance"]
    urgency_status: str = "Standard filing schedule applicable."

class ImpactItem(BaseModel):
    rule_section: str
    risk_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]
    description: str
    action_required: str
    deadline: Optional[str] = "Next Filing Cycle"
    financial_exposure: Optional[str] = "Moderate"

class AuditVerification(BaseModel):
    citation_valid: bool = True
    official_gazette_ref: str
    hallucination_risk_score: float = Field(default=0.02, description="Calculated hallucination probability")
    verified_clauses_count: int
    validation_status: Literal["PASSED", "WARNING", "FAILED"] = "PASSED"
    remarks: str

class ComplianceReport(BaseModel):
    report_id: str
    generated_at: str
    taxpayer_profile: TaxpayerProfile
    circular_meta: ParsingAgentOutput
    impact_assessment: List[ImpactItem]
    audit_report: AuditVerification
    overall_compliance_status: Literal["COMPLIANT", "ACTION_REQUIRED", "HIGH_RISK_DEFICIT"]
    recommended_next_steps: List[str]

class AnalyzeRequest(BaseModel):
    circular_text: Optional[str] = None
    sample_id: Optional[str] = None
    taxpayer_profile: Optional[TaxpayerProfile] = None

