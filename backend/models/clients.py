"""
Client Profiles for Personalised Tax & Regulatory Intelligence.
Enriched with corporate GSTIN, PAN, statutory sections, recurring issue tags,
and assigned tax practitioner desks.
"""

from typing import List, Dict, Any

PRESET_CLIENTS: List[Dict[str, Any]] = [
    {
        "id": "client_kushagra_tech",
        "name": "Kushagra Technologies Pvt Ltd",
        "entity_type": "Private_Limited",
        "gstin": "27AABCK1234F1Z5",
        "pan": "AABCK1234F",
        "sector": "IT / Software Services",
        "secondary_sectors": ["E-commerce", "Exports / SEZ"],
        "turnover": 75000000.0,
        "income": 15000000.0,
        "gst_registered": True,
        "opted_new_tax_regime": True,
        "focus_topics": ["TDS / TCS Withholding", "Input Tax Credit (ITC)", "Transfer Pricing", "Exports / SEZ"],
        "sections": ["Section 194R", "Section 194Q", "Section 16(4)", "Section 17(5)", "Section 92CA", "Section 10AA"],
        "issue_tags": ["Export LUT", "Vendor Withholding", "Perquisite Taxation", "Software Royalties", "Arm's Length Margin"],
        "assigned_lead": {
            "name": "Kushagra Gupta",
            "title": "Lead Enterprise AI Architect",
            "desk": "Corporate Tech & Cross-Border Desk",
            "topics": ["Transfer Pricing", "TDS / TCS Withholding", "Input Tax Credit (ITC)"]
        }
    },
    {
        "id": "client_solaris_energy",
        "name": "Solaris Clean Energy Corp",
        "entity_type": "Public_Limited",
        "gstin": "24AAACS5678B1Z2",
        "pan": "AAACS5678B",
        "sector": "Renewable Energy",
        "secondary_sectors": ["Power & Energy", "Infrastructure"],
        "turnover": 450000000.0,
        "income": 65000000.0,
        "gst_registered": True,
        "opted_new_tax_regime": False,
        "focus_topics": ["Section 80IA Deductions", "Customs Valuation", "Corporate Compliance", "Input Tax Credit (ITC)"],
        "sections": ["Section 80IA", "Section 16(2)", "Heading 9801", "Section 115JB"],
        "issue_tags": ["Project Import Concessions", "Inverted Duty Structure", "Solar Cell Tariffs", "EPC Contracting"],
        "assigned_lead": {
            "name": "Advisory Desk",
            "title": "Partner - Energy & Infra",
            "desk": "Renewables & Infrastructure Desk",
            "topics": ["Section 80IA Deductions", "Customs Valuation", "Corporate Compliance"]
        }
    },
    {
        "id": "client_apex_realty",
        "name": "Apex Prime Real Estate Developers",
        "entity_type": "Partnership",
        "gstin": "27AAHFA9012C1Z8",
        "pan": "AAHFA9012C",
        "sector": "Real Estate",
        "secondary_sectors": ["Infrastructure", "Construction"],
        "turnover": 120000000.0,
        "income": 22000000.0,
        "gst_registered": True,
        "opted_new_tax_regime": False,
        "focus_topics": ["Capital Gains", "Search & Seizure", "GST Litigation", "TDS / TCS Withholding"],
        "sections": ["Section 194-IA", "Section 54F", "Section 50C", "Section 148", "Rule 42"],
        "issue_tags": ["Joint Development Agreements (JDA)", "TDR Withholding", "ITC Reversal on Completion Certificate", "RERA Escrow"],
        "assigned_lead": {
            "name": "Real Estate Practice Group",
            "title": "Senior Tax Counsel",
            "desk": "Real Estate & Construction Desk",
            "topics": ["Capital Gains", "GST Litigation", "Search & Seizure"]
        }
    },
    {
        "id": "client_medlife_pharma",
        "name": "MedLife Global Pharma Ltd",
        "entity_type": "Public_Limited",
        "gstin": "29AABCM3456D1Z1",
        "pan": "AABCM3456D",
        "sector": "Pharma & Healthcare",
        "secondary_sectors": ["Exports / SEZ", "Manufacturing"],
        "turnover": 850000000.0,
        "income": 110000000.0,
        "gst_registered": True,
        "opted_new_tax_regime": True,
        "focus_topics": ["Exports / SEZ", "TDS / TCS Withholding", "Tax Audit", "Transfer Pricing"],
        "sections": ["Section 10AA", "Section 194R", "Section 44AB", "Section 92C"],
        "issue_tags": ["API Bulk Drug Export", "Doctor Freebie Withholding", "SEZ De-bonding", "R&D Weighted Deduction"],
        "assigned_lead": {
            "name": "Life Sciences Practice",
            "title": "Partner - Pharma & Lifesciences",
            "desk": "Pharma & International Trade Desk",
            "topics": ["Exports / SEZ", "TDS / TCS Withholding", "Tax Audit"]
        }
    },
    {
        "id": "client_verma_individual",
        "name": "Rajesh Verma (Senior Consultant)",
        "entity_type": "Individual",
        "gstin": "27AAAPV7890E1Z4",
        "pan": "AAAPV7890E",
        "sector": "Banking & Financial Services",
        "secondary_sectors": ["IT / Software Services"],
        "turnover": 18000000.0,
        "income": 12500000.0,
        "gst_registered": True,
        "opted_new_tax_regime": True,
        "focus_topics": ["Section 115BAC Slabs", "Capital Gains", "TDS / TCS Withholding"],
        "sections": ["Section 115BAC", "Section 194J", "Section 112A", "Section 87A"],
        "issue_tags": ["Professional Consultancy TDS", "Presumptive Taxation 44ADA", "Long-Term Capital Gains", "New Tax Slabs"],
        "assigned_lead": {
            "name": "HNWI & Private Client Desk",
            "title": "Principal Advisor",
            "desk": "Executive & Wealth Advisory",
            "topics": ["Section 115BAC Slabs", "Capital Gains", "TDS / TCS Withholding"]
        }
    }
]
