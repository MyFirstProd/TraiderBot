from app.schemas.llm import StructuredEventAssessment


def test_llm_schema_validation():
    payload = StructuredEventAssessment(
        event_type="news",
        sentiment=0.2,
        confidence=0.7,
        novelty=0.4,
        source_reliability=0.8,
        market_relevance=0.9,
        contradiction_flag=False,
        summary="sample",
        affected_symbols=["BTCUSDT"],
    )
    assert payload.market_relevance == 0.9
