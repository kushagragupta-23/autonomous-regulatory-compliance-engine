from typing import List
from backend.models.schemas import TaxpayerProfile, ParsingAgentOutput, ImpactItem

class TaxDiffAgent:
    """Agent 2: Evaluates the delta impact of extracted tax rules against a taxpayer's profile."""

    def evaluate(self, parsed_data: ParsingAgentOutput, profile: TaxpayerProfile) -> List[ImpactItem]:
        impacts: List[ImpactItem] = []

        for rule in parsed_data.extracted_rules:
            # Rule 1: Section 194R (Business perks TDS)
            if "194R" in rule.section:
                if profile.entity_type in ["Private_Limited", "Public_Limited", "Partnership"]:
                    impacts.append(ImpactItem(
                        rule_section="Section 194R",
                        risk_level="HIGH",
                        description=f"Applies to {profile.entity_name} for dealer conferences, gifting, and vendor perks exceeding INR 20k.",
                        action_required="Ensure accounting ERP flags non-cash benefits and withholds 10% TDS before benefit transfer.",
                        deadline="Monthly on the 7th of following month",
                        financial_exposure="10% TDS + 1.5%/month penalty on failure to withhold"
                    ))
                else:
                    impacts.append(ImpactItem(
                        rule_section="Section 194R",
                        risk_level="LOW",
                        description="Individual professional perquisites threshold not triggered unless gross turnover exceeds statutory audit limits.",
                        action_required="Maintain expense logs for client gifts.",
                        deadline="Annual Return Filing",
                        financial_exposure="Minimal"
                    ))

            # Rule 2: Section 194Q (Purchase of Goods TDS)
            elif "194Q" in rule.section:
                if profile.annual_turnover > 100000000.0:  # > 10 Cr turnover
                    impacts.append(ImpactItem(
                        rule_section="Section 194Q",
                        risk_level="CRITICAL",
                        description=f"Turnover of INR {profile.annual_turnover:,.0f} exceeds 10 Cr threshold. Mandatory 0.1% TDS on vendor purchases > 50 Lakhs.",
                        action_required="Automate AP ledger check to deduct 0.1% TDS upon crossing 50 Lakhs aggregate purchase per vendor.",
                        deadline="7th of each following month",
                        financial_exposure="30% disallowance of expenditure under Section 40(a)(ia)"
                    ))
                else:
                    impacts.append(ImpactItem(
                        rule_section="Section 194Q",
                        risk_level="INFORMATIONAL",
                        description="Entity turnover is below 10 Crore prior year threshold; Section 194Q deduction obligation not triggered.",
                        action_required="Verify vendor TCS deduction under Section 206C(1H) instead.",
                        deadline="Annual Review",
                        financial_exposure="None"
                    ))

            # Rule 3: Section 115BAC (New Tax Regime)
            elif "115BAC" in rule.section:
                if profile.entity_type in ["Individual", "HUF"]:
                    impacts.append(ImpactItem(
                        rule_section="Section 115BAC",
                        risk_level="MEDIUM",
                        description="Default regime is New Tax Regime with standard deduction of INR 75,000.",
                        action_required="Compare tax liability between Old (with 80C/80D/HRA) vs New Regime before filing ITR.",
                        deadline="31st July of Assessment Year",
                        financial_exposure="Possible tax overpayment if Old Regime deductions exceed INR 3,75,000"
                    ))
                else:
                    impacts.append(ImpactItem(
                        rule_section="Section 115BAC",
                        risk_level="INFORMATIONAL",
                        description="Section 115BAC is designated for Individuals/HUFs. Corporate entities are governed by Section 115BAA/115BAB.",
                        action_required="Review corporate concessional rate eligibility under Section 115BAA (22% effective).",
                        deadline="Filing of Form 10-IC",
                        financial_exposure="None"
                    ))

            # Rule 4: CGST Rule 48(4) E-Invoicing
            elif "Rule 48(4)" in rule.section or "e-invoice" in rule.topic.lower():
                if profile.gst_registered and profile.annual_turnover >= 50000000.0: # >= 5 Cr
                    impacts.append(ImpactItem(
                        rule_section="CGST Rule 48(4)",
                        risk_level="CRITICAL",
                        description=f"Turnover of INR {profile.annual_turnover:,.0f} crosses 5 Cr threshold. Invoices without IRN/QR code are legally invalid.",
                        action_required="Integrate ERP directly with Invoice Registration Portal (IRP) or GSP for real-time B2B IRN generation.",
                        deadline="Immediate / Next B2B Billing",
                        financial_exposure="INR 10,000 or 100% of tax evaded per invoice + recipient loss of ITC"
                    ))
                else:
                    impacts.append(ImpactItem(
                        rule_section="CGST Rule 48(4)",
                        risk_level="LOW",
                        description="Turnover currently under 5 Cr mandatory threshold or not GST registered.",
                        action_required="Monitor turnover growth as threshold approaches.",
                        deadline="Quarterly Check",
                        financial_exposure="Low"
                    ))

            # Fallback
            else:
                impacts.append(ImpactItem(
                    rule_section=rule.section,
                    risk_level="MEDIUM",
                    description=f"Regulatory advisory regarding {rule.topic}.",
                    action_required="Conduct formal tax review with chartered accountant.",
                    deadline="Next Board/Finance Review",
                    financial_exposure="Subject to audit"
                ))

        return impacts

