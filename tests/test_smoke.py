"""
EFFIONG AI - smoke tests
=========================
No network and no API keys required. Run with:  pytest tests/ -q
These check the parts of the system that must work completely offline (math engine, document engine,
file ingestion, evidence scoring, prediction math, heritage ledger, security shield) so a broken import
or a regression is caught before deploying.
"""
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


def test_config_defaults():
    from src import config
    assert config.get("NON_EXISTENT_KEY", "fallback") == "fallback"
    assert isinstance(config.limits(), dict)


def test_math_engine_symbolic():
    from src.services.math_utils import try_symbolic, factorial
    r = try_symbolic("solve x^2-5x+6=0")
    assert r is not None and ("2" in r["result"] and "3" in r["result"])
    r2 = try_symbolic("what is 2+2")
    assert r2 is not None and r2["result"].strip() == "4"
    assert try_symbolic("__import__('os').system('ls')") is None
    assert factorial(10) == "3628800"


def test_math_engine_rejects_injection():
    from src.services.math_utils import try_symbolic
    for bad in ["open('/etc/passwd')", "x.__class__.__bases__", "lambda: 1", "import os"]:
        assert try_symbolic(bad) is None


def test_doc_engine_pdf_and_docx():
    from src.utilities import doc_engine
    md = "# Title\n\nSome **bold** text.\n\n| A | B |\n|---|---|\n| 1 | Verified |\n"
    pdf = doc_engine.compile_pdf_bytes(md, doc_type="Test")
    assert pdf[:4] == b"%PDF"
    docx = doc_engine.compile_word_bytes(md, doc_type="Test")
    assert docx[:2] == b"PK"


def test_doc_engine_pptx():
    from src.utilities import doc_engine
    md = "# Deck\n\n## Slide one\n- point a\n- point b\n"
    pptx = doc_engine.compile_pptx_bytes(md)
    assert pptx[:2] == b"PK"


def test_doc_engine_svg_sanitizer():
    from src.utilities import doc_engine
    dirty = '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script><rect onclick="x()" /></svg>'
    clean = doc_engine.sanitize_svg(dirty)
    assert clean and "script" not in clean.lower() and "onclick" not in clean.lower()


def test_evidence_service():
    from src.services.evidence_service import EvidenceService
    ev = EvidenceService()
    sources = [{"source": "Wikipedia", "url": "https://en.wikipedia.org/wiki/X"},
               {"source": "Harvard", "url": "https://library.harvard.edu/x"}]
    matrix = ev.build_truth_matrix(sources)
    assert matrix["classification"] in {"VERIFIED FACT", "EVIDENCE SUPPORTED", "PROBABLE", "ORAL TRADITION",
                                        "COMPETING CLAIM", "SPECULATIVE", "UNVERIFIED"}


def test_predictive_engine():
    from src.services.predictive_service import PredictiveEngine, extract_series
    series = extract_series("values: 10, 12, 15, 19, 24, 30")
    assert series == [10.0, 12.0, 15.0, 19.0, 24.0, 30.0]
    result = PredictiveEngine.forecast_series(series, 3)
    assert len(result["projected_steps"]) == 3
    assert result["trend_direction"] == "UPWARD"


def test_heritage_store():
    from src.database.heritage_store import HeritageStore
    store = HeritageStore()
    node = store.create_node("Test heritage claim", "A short narrative.", "Oral Tradition Transcript")
    assert node["status"] == "Pending Verification"
    assert store.get_node(node["id"]) is not None
    stats = store.get_statistics()
    assert stats["total_nodes"] == 1


def test_file_service_ingest_text():
    from src.services.file_service import file_service
    att = file_service.ingest("note.txt", b"hello world")
    assert att.kind == "text" and "hello world" in att.text


def test_guard_rate_limit_and_ssrf():
    from src.core.guard import RateGuard, assert_public_url, UnsafeURL
    guard = RateGuard(path="/tmp/effiong_test_usage.json")
    ok, _ = guard.check("test-user", "chat")
    assert ok is True
    with pytest.raises(UnsafeURL):
        assert_public_url("http://127.0.0.1/secret")
    with pytest.raises(UnsafeURL):
        assert_public_url("ftp://example.com")


def test_knowledge_graph():
    from src.services.knowledge_graph_service import KnowledgeGraphService
    kg = KnowledgeGraphService()
    graph = kg.build_graph(["The Kingdom of Benin traded with the Kingdom of Benin's neighbours."])
    assert isinstance(graph["nodes"], list)


def test_document_type_detection():
    from src.services.document_service import detect_doc_type, detect_formats
    assert detect_doc_type("write me a cover letter for a data job") == "cover_letter"
    assert detect_doc_type("draft a business plan for my bakery") == "business_plan"
    assert "pptx" in detect_formats("make me a presentation about Benin", "presentation")


def test_intent_classifier():
    from src.services.brain_router import classify_intent
    assert classify_intent("solve x^2-4=0") == "math"
    assert classify_intent("draw a picture of a lion") == "image"
    assert classify_intent("write me a resume") == "document"
    assert classify_intent("predict bitcoin price next month") == "prediction"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
