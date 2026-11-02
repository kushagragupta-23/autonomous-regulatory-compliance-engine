import pytest
from backend.services.hybrid_rag_engine import AdvancedHybridRAGEngine

SAMPLE_DOC_1 = """
Section 194R: Benefit or perquisite in business.
Any person providing to a resident any benefit or perquisite arising from business or profession
shall withhold tax at ten per cent (10%) where value exceeds twenty thousand rupees (INR 20,000).
"""

SAMPLE_DOC_2 = """
Rule 48(4) E-Invoicing Mandate:
Every GST registered person with turnover exceeding 5 Crore rupees must generate an IRN
and dynamic QR code through the Invoice Registration Portal for B2B transactions.
"""

def test_hybrid_rag_indexing_and_rrf():
    engine = AdvancedHybridRAGEngine(rrf_k=60)
    engine.index_parent_and_children("DOC_194R", "Section 194R Circular", SAMPLE_DOC_1)
    engine.index_parent_and_children("DOC_GST", "E-Invoicing Circular", SAMPLE_DOC_2)

    assert len(engine.child_chunks) >= 2
    assert len(engine.parent_docs) == 2

    # Query with synonym "withholding tax" (should hit Section 194R through synonym expansion & RRF)
    results = engine.hybrid_search("withholding tax on perquisites", top_k=1)
    assert len(results) >= 1
    assert "194R" in results[0]["parent_context"]
    assert results[0]["rrf_score"] > 0.0

    # Query for E-Invoicing
    gst_results = engine.hybrid_search("E-Invoicing and IRN generation", top_k=1)
    assert len(gst_results) >= 1
    assert "Rule 48(4)" in gst_results[0]["parent_context"]

