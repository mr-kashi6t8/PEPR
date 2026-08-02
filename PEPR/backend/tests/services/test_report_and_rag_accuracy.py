from app.services.nlp.rag_engine import RAGEngine
from app.services.reports.generator import ReportGeneratorService


def test_rag_fallback_recommendation_uses_pide_evidence():
    rec = RAGEngine.build_research_recommendation_from_evidence(
        problem_description="High inflation",
        evidence_texts=[
            "PIDE paper highlights energy subsidy pressure and fiscal stress.",
            "The working paper recommends tariff reform and better targeting.",
        ],
        citations=[
            {"document_identifier": "PIDE-WP-2024-88", "title": "Energy Subsidies and Circular Debt", "authors": "PIDE"}
        ],
    )

    assert rec.problem_statement == "High inflation"
    assert "PIDE" in rec.suggested_solution
    assert "tariff" in rec.suggested_solution.lower() or "subsidy" in rec.suggested_solution.lower()
    assert len(rec.key_interventions) >= 2


def test_report_generator_builds_top_ten_problem_structure():
    service = ReportGeneratorService()
    payload = service.build_weekly_report_payload(
        problems=[
            {"title": "Inflation", "description": "Prices are rising", "severity": "HIGH"},
            {"title": "Fiscal pressure", "description": "Budget strain", "severity": "HIGH"},
        ],
        trends=[{"title": "Inflation", "direction": "UP", "drivers": ["energy"]}],
        gaps=[{"policy_name": "Energy subsidy reform", "gap_reasoning": "Target missed", "systemic_issues": ["governance"]}],
        papers=[{"title": "Energy Subsidies", "document_identifier": "PIDE-WP-2024-88", "authors": "PIDE"}],
        research_summaries=[{"problem": "Inflation", "solution": "Reform subsidies and strengthen targeted transfers."}],
    )

    assert len(payload.top_10_problems) == 2
    assert payload.top_10_problems[0].problem_title == "Inflation"
    assert payload.relevant_pide_research[0].problem_statement == "Inflation"
    assert len(payload.evidence_and_citations) >= 2
