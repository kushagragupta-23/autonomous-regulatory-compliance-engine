import re
from typing import Dict, Any, List
from backend.models.schemas import ParsingAgentOutput, ExtractedRule
from backend.services.tax_feed_integration import TaxFeedIntelligence

class ParserAgent:
    """Agent 1: Extracts structured tax and statutory metadata from legal text."""

    AUTHORITY_PATTERNS = [
        (r'\b(CBDT|Central Board of Direct Taxes)\b', "CBDT (Direct Taxes)"),
        (r'\b(CBIC|Central Board of Indirect Taxes and Customs)\b', "CBIC (Indirect Taxes / GST)"),
        (r'\b(MCA|Ministry of Corporate Affairs)\b', "MCA (Corporate Affairs)"),
        (r'\b(IRS|Internal Revenue Service)\b', "IRS (Federal Tax)")
    ]

    def process(self, text: str) -> ParsingAgentOutput:
        # 1. Authority extraction
        authority = "Ministry of Finance"
        for pattern, name in self.AUTHORITY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                authority = name
                break

        # 2. Circular / Notification ID extraction
        circ_match = re.search(r'(?:Circular|Notification|Order)\s*(?:No\.?|Number)?\s*[:\-]?\s*([A-Za-z0-9\/\-\.]+)', text, re.IGNORECASE)
        circular_id = circ_match.group(1) if circ_match else "CIRC-2026-GEN"

        # 3. Notification Date extraction
        date_match = re.search(r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s*,?\s*\d{4})\b', text, re.IGNORECASE)
        if not date_match:
            date_match = re.search(r'\b(\d{2}[\/\-]\d{2}[\/\-]\d{4})\b', text)
        notification_date = date_match.group(1) if date_match else "01/04/2026"

        # 4. Extract section rules
        rules: List[ExtractedRule] = []

        # Check for Section 194R (Perquisites TDS)
        if re.search(r'194R', text, re.IGNORECASE):
            rules.append(ExtractedRule(
                section="Section 194R",
                topic="TDS on Benefit or Perquisite in respect of Business or Profession",
                statutory_rate="10%",
                threshold_limit="INR 20,000 per financial year",
                effective_date="Immediate",
                raw_clause="Deduction of tax at source at the rate of ten per cent on value or aggregate value of benefit or perquisite exceeding twenty thousand rupees.",
                confidence_score=0.98
            ))

        # Check for Section 194Q / 206C(1H) (TDS/TCS on Goods)
        if re.search(r'194Q', text, re.IGNORECASE):
            rules.append(ExtractedRule(
                section="Section 194Q",
                topic="TDS on Purchase of Goods exceeding Threshold",
                statutory_rate="0.10%",
                threshold_limit="INR 50,00,000 turnover/purchase",
                effective_date="Immediate",
                raw_clause="Buyer responsible for paying sum exceeding 50 lakh rupees to a resident seller shall deduct tax equal to 0.1%.",
                confidence_score=0.97
            ))

        # Check for Section 115BAC (New Concessional Tax Regime)
        if re.search(r'115BAC', text, re.IGNORECASE):
            rules.append(ExtractedRule(
                section="Section 115BAC",
                topic="Default Concessional Tax Regime for Individuals and HUF",
                statutory_rate="Slab rates up to 30%",
                threshold_limit="Standard Deduction INR 75,000",
                effective_date="FY 2025-26 Onwards",
                raw_clause="Revised tax slabs applicable with standard deduction enhanced to INR 75,000 for salaried taxpayers.",
                confidence_score=0.99
            ))

        # Check for GST E-Invoicing / Rule 48(4)
        if re.search(r'(?:e-invoice|Rule 48\(4\)|IRN)', text, re.IGNORECASE):
            rules.append(ExtractedRule(
                section="CGST Rule 48(4)",
                topic="Mandatory E-Invoicing and IRN Generation",
                statutory_rate="N/A",
                threshold_limit="INR 5 Crore Aggregate Turnover",
                effective_date="Phase VI Rollout",
                raw_clause="Mandatory generation of Invoice Reference Number (IRN) through Invoice Registration Portal for B2B supplies.",
                confidence_score=0.96
            ))

        # If no specific recognized regex hit, create fallback general rule
        if not rules:
            first_clause = text.split("\n")[0][:120] if text else "General Statutory Directive"
            rules.append(ExtractedRule(
                section="Statutory Guideline",
                topic="General Regulatory Compliance Directive",
                statutory_rate="Subject to Assessment",
                threshold_limit="As stipulated in Gazette",
                effective_date="Immediate",
                raw_clause=first_clause,
                confidence_score=0.85
            ))

        # Title and Summary
        first_line = text.strip().split("\n")[0]
        title = first_line[:100] if len(first_line) > 10 else f"Regulatory Circular {circular_id}"
        summary = f"Issued by {authority}. Governs {len(rules)} specific statutory rule provisions effective from {notification_date}."

        # Integration with Personalised Tax Intelligence Feed taxonomy
        matched_sectors = TaxFeedIntelligence.match_sectors(text)
        matched_topics = TaxFeedIntelligence.match_topics(text)
        is_urgent, urgency_msg = TaxFeedIntelligence.check_urgency(text)

        return ParsingAgentOutput(
            circular_id=circular_id,
            issuing_authority=authority,
            notification_date=notification_date,
            title=title,
            summary=summary,
            extracted_rules=rules,
            applicable_sectors=matched_sectors,
            tax_topics=matched_topics,
            urgency_status=urgency_msg
        )

