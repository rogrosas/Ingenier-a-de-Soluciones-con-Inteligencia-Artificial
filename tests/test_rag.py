"""Pruebas del pipeline RAG (rag/rag_pipeline.py)."""

from rag.rag_pipeline import RAGRetriever, responder_con_rag


def test_indice_construido():
    r = RAGRetriever()
    assert len(r.chunks) >= 8
    origenes = {c["origen"] for c in r.chunks}
    assert origenes == {"interna", "externa"}  # combina ambas fuentes


def test_recupera_relevante_interno():
    r = RAGRetriever()
    res = r.recuperar("tasa del crédito hipotecario", k=2)
    assert res and "hipotecario" in res[0]["texto"].lower()


def test_recupera_relevante_externo():
    r = RAGRetriever()
    res = r.recuperar("derechos del consumidor financiero", k=2)
    assert any(x["origen"] == "externa" for x in res)


def test_scores_ordenados_descendente():
    r = RAGRetriever()
    res = r.recuperar("crédito de consumo requisitos", k=3)
    scores = [x["score"] for x in res]
    assert scores == sorted(scores, reverse=True)


def test_responder_combina_fuentes():
    out = responder_con_rag(
        "¿Qué tasa tiene el crédito de consumo y qué información debe darme el banco?", k=4)
    assert "interna" in out["origenes_combinados"]
    assert "externa" in out["origenes_combinados"]
    assert out["fuentes"]
