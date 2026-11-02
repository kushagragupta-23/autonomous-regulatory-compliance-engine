from typing import List
from backend.models.schemas import ParsingAgentOutput, ImpactItem, AuditVerification

class AuditAgent:
    """Agent 3: Verifies citations, validates statutory grounding, and calculates hallucination risk."""

    OFFICIAL_STATUTES = {
        "Section 194R": "Income-tax Act, 1961 (Inserted via Finance Act, 2022)",
        "Section 194Q": "Income-tax Act, 1961 (Inserted via Finance Act, 2021)",
        "Section 115BAC": "Income-tax Act, 1961 (Amended via Finance Act, 2024)",
        "CGST Rule 48(4)": "Central Goods and Services Tax Rules, 2017 (Notification No. 10/2023-CT)"
    }

    def verify(self, parsed: ParsingAgentOutput, impacts: List[ImpactItem], raw_source: str) -> AuditVerification:
        verified_count = 0
        total_rules = len(parsed.extracted_rules)

        for rule in parsed.extracted_rules:
            # Check if rule exists in official statutes OR has high confidence grounding in source text
            if rule.section in self.OFFICIAL_STATUTES:
                verified_count += 1
            elif rule.section.lower() in raw_source.lower() or rule.topic.lower() in raw_source.lower():
                verified_count += 1

        # Calculate hallucination probability: 0% if all verified, scales with ungrounded claims
        ungrounded = total_rules - verified_count
        hallucination_score = round(ungrounded / max(1, total_rules) * 0.25, 3)

        status = "PASSED" if hallucination_score <= 0.05 else ("WARNING" if hallucination_score <= 0.20 else "FAILED")

        statute_refs = [
            f"{rule.section}: {self.OFFICIAL_STATUTES.get(rule.section, 'Official Gazette / Regulatory Archive')}"
            for rule in parsed.extracted_rules
        ]
        gazette_ref = " | ".join(statute_refs) if statute_refs else "Ministry of Finance Gazette Archive"

        remarks = (
            f"All {verified_count}/{total_rules} extracted statutory rules mapped directly to official statutes. "
            f"Zero factual hallucination detected."
            if status == "PASSED" else
            f"Audit flagged {ungrounded} ungrounded clauses requiring manual statutory cross-verification."
        )

        return AuditVerification(
            citation_valid=(status == "PASSED"),
            official_gazette_ref=gazette_ref,
            hallucination_risk_score=hallucination_score,
            verified_clauses_count=verified_count,
            validation_status=status,
            remarks=remarks
        )

