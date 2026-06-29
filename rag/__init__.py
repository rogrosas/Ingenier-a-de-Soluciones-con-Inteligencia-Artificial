"""Pipeline RAG del agente bancario (RA1/IL1.3 integrado en el proyecto)."""

from .rag_pipeline import RAGRetriever, responder_con_rag

__all__ = ["RAGRetriever", "responder_con_rag"]
