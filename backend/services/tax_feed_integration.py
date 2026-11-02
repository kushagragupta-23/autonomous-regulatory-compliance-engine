"""
Tax Feed Integration Module.
Leverages domain classification algorithms and taxonomy from Personalised_Tax_Intelligence_Feed-main:
1. Multi-sector keyword matching (18 distinct enterprise sectors)
2. Topic tagging (Transfer Pricing, ITC, GST Refund, TDS/TCS, etc.)
3. Statutory Section regular expression extraction
4. Urgency and deadline indicators
"""

import re
from typing import List, Dict, Any, Tuple

# Domain taxonomies from Personalised_Tax_Intelligence_Feed-main
SECTOR_TAXONOMY = {
    "Power & Energy": ["power", "electricity", "thermal", "discom", "generation", "transmission"],
    "Renewable Energy": ["renewable", "solar", "wind", "green energy", "green hydrogen", "80ia"],
    "Ports & Logistics": ["port", "logistics", "shipping", "freight", "warehous", "cargo"],
    "Mining & Metals": ["mining", "mineral", "coal", "ore", "steel", "metal", "smelter"],
    "Infrastructure": ["infrastructure", "highway", "road project", "epc", "construction", "80ia"],
    "FMCG": ["fmcg", "consumer goods", "packaged", "retail", "distributor", "msp"],
    "Banking & Financial Services": ["bank", "nbfc", "financial service", "lending", "deposit", "rbi", "interest income"],
    "Insurance": ["insurance", "insurer", "irdai", "policyholder", "premium"],
    "IT / Software Services": ["software", "it/ites", "ites", "saas", "technology service", "computer", "information technology"],
    "Real Estate": ["real estate", "developer", "housing", "construction", "rera", "joint development", "tdr"],
    "Manufacturing": ["manufactur", "factory", "plant", "production", "capital goods"],
    "Pharma & Healthcare": ["pharma", "drug", "healthcare", "hospital", "medical", "api "],
    "Telecom": ["telecom", "spectrum", "telecommunication", "5g"],
    "E-commerce": ["e-commerce", "ecommerce", "online platform", "marketplace", "aggregator"],
    "Automobile & EV": ["automobile", "automotive", "vehicle", "ev ", "electric vehicle", "auto component"],
    "Oil & Gas": ["oil", "gas", "petroleum", "refinery", "lng", "hydrocarbon"],
    "Online Gaming": ["gaming", "betting", "wager", "online game", "gameskraft"],
    "Exports / SEZ": ["export", "sez", "lut", "deemed export", "fob", "epcg", "advance authorisation"]
}

TOPIC_TAXONOMY = {
    "Transfer Pricing": ["transfer pricing", "arm's length", "arms length", "associated enterprise", "alp"],
    "International Tax": ["dtaa", "double taxation", "permanent establishment", "foreign enterprise", "treaty", "non-resident", "royalty"],
    "TDS / TCS Withholding": ["tds", "tcs", "withholding", "deduction at source", "194", "206c"],
    "GST Refund & Exemption": ["gst refund", "refund", "inverted duty", "unutilised credit"],
    "Input Tax Credit (ITC)": ["input tax credit", "itc", "credit on capital goods", "blocked credit"],
    "Search & Seizure": ["search and seizure", "search & seizure", "raid", "section 132"],
    "Reassessment": ["reassessment", "reopening", "section 147", "section 148", "escaped assessment"],
    "Faceless Assessment": ["faceless", "drp", "dispute resolution panel"],
    "Capital Gains": ["capital gain", "capital asset", "long term capital", "short term capital", "54f", "54ec"],
    "Corporate Compliance": ["roc", "companies act", "mca", "annual return", "director", "csr"],
    "Tax Audit": ["tax audit", "audit report", "44ab", "statutory audit"]
}

SECTION_REGEX = re.compile(r"\bsection\s+([0-9]{1,3}[A-Za-z]{0,3}(?:\([0-9a-zA-Z]+\))?)", re.IGNORECASE)

URGENCY_KEYWORDS = [
    "due date", "last date", "deadline", "extended", "extension", "with effect from",
    "w.e.f", "effective immediately", "comes into force", "compliance", "last day",
    "before 31", "before 30", "filing date", "amnesty", "waiver"
]

class TaxFeedIntelligence:
    """Provides advanced signal extraction adapted from the Personalised Tax Intelligence Feed."""

    @classmethod
    def match_sectors(cls, text: str) -> List[str]:
        text_lower = text.lower()
        matched = []
        for sector, keywords in SECTOR_TAXONOMY.items():
            if any(kw in text_lower for kw in keywords):
                matched.append(sector)
        return matched or ["General Business / Commercial"]

    @classmethod
    def match_topics(cls, text: str) -> List[str]:
        text_lower = text.lower()
        matched = []
        for topic, keywords in TOPIC_TAXONOMY.items():
            if any(kw in text_lower for kw in keywords):
                matched.append(topic)
        return matched or ["Statutory Compliance"]

    @classmethod
    def extract_sections(cls, text: str) -> List[str]:
        matches = SECTION_REGEX.findall(text)
        return sorted(list(set(f"Section {m.upper()}" for m in matches)))

    @classmethod
    def check_urgency(cls, text: str) -> Tuple[bool, str]:
        text_lower = text.lower()
        for kw in URGENCY_KEYWORDS:
            if kw in text_lower:
                return True, f"Statutory timeline triggered by keyword: '{kw}'"
        return False, "Standard filing schedule applicable."

