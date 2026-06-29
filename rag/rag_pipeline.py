"""
Pipeline RAG — Banco Digital Chile (IL1.3 / EFT IE2)
=====================================================
Recuperación aumentada que combina fuentes internas (productos y políticas del
banco) y externas (normativa CMF/SERNAC/Ley 19.628) para enriquecer la respuesta
del modelo.

Backend de recuperación: TF-IDF + similitud coseno implementado con numpy. Se
eligió un recuperador léxico para que el pipeline sea 100% reproducible y no
dependa de credenciales de API; en producción el `RAGRetriever` se sustituye por
embeddings densos (p. ej. text-embedding-3) manteniendo la misma interfaz.

Flujo: documentos → chunking → vectorización TF-IDF → recuperación top-k →
ensamblado de contexto → (opcional) generación con el LLM.
"""

from __future__ import annotations

import math
import re
import sys
from collections import Counter

import numpy as np

from rag.knowledge_base import DOCUMENTOS

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

_TOKEN_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)
# Palabras vacías frecuentes en español (lista compacta).
_STOP = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "y", "o",
    "a", "en", "que", "se", "su", "sus", "por", "con", "para", "es", "al", "lo",
    "como", "mas", "más", "le", "ya", "tiene", "ser", "son", "the",
}


def _tokenizar(texto: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(texto) if t.lower() not in _STOP and len(t) > 2]


def _chunk(texto: str, max_palabras: int = 60) -> list[str]:
    """Divide por oraciones agrupando hasta ~max_palabras (chunking simple)."""
    oraciones = re.split(r"(?<=[.])\s+", texto.strip())
    chunks, actual, n = [], [], 0
    for o in oraciones:
        p = len(o.split())
        if n + p > max_palabras and actual:
            chunks.append(" ".join(actual)); actual, n = [], 0
        actual.append(o); n += p
    if actual:
        chunks.append(" ".join(actual))
    return chunks


class RAGRetriever:
    """Recuperador TF-IDF sobre la base de conocimiento (interna + externa)."""

    def __init__(self, documentos: list[dict] | None = None, max_palabras_chunk: int = 60):
        docs = documentos if documentos is not None else DOCUMENTOS
        # Expandir documentos a chunks conservando metadatos.
        self.chunks: list[dict] = []
        for d in docs:
            for i, c in enumerate(_chunk(d["texto"], max_palabras_chunk)):
                self.chunks.append({
                    "doc_id": d["id"], "origen": d["origen"],
                    "fuente": d["fuente"], "chunk_id": f"{d['id']}#{i}", "texto": c,
                })
        self._construir_indice()

    def _construir_indice(self):
        tokenizados = [_tokenizar(c["texto"]) for c in self.chunks]
        vocab = sorted({t for toks in tokenizados for t in toks})
        self.vocab = {t: i for i, t in enumerate(vocab)}
        n_docs = len(self.chunks)
        # IDF
        df = Counter()
        for toks in tokenizados:
            for t in set(toks):
                df[t] += 1
        self.idf = np.zeros(len(vocab))
        for t, i in self.vocab.items():
            self.idf[i] = math.log((1 + n_docs) / (1 + df[t])) + 1
        # Matriz TF-IDF normalizada
        self.matriz = np.zeros((n_docs, len(vocab)))
        for r, toks in enumerate(tokenizados):
            tf = Counter(toks)
            for t, c in tf.items():
                j = self.vocab[t]
                self.matriz[r, j] = (c / len(toks)) * self.idf[j]
            norma = np.linalg.norm(self.matriz[r])
            if norma:
                self.matriz[r] /= norma

    def _vectorizar(self, consulta: str) -> np.ndarray:
        toks = _tokenizar(consulta)
        v = np.zeros(len(self.vocab))
        tf = Counter(toks)
        for t, c in tf.items():
            if t in self.vocab:
                j = self.vocab[t]
                v[j] = (c / max(1, len(toks))) * self.idf[j]
        norma = np.linalg.norm(v)
        return v / norma if norma else v

    def recuperar(self, consulta: str, k: int = 3) -> list[dict]:
        """Devuelve los k chunks más relevantes con su score de similitud."""
        v = self._vectorizar(consulta)
        scores = self.matriz @ v
        idx = np.argsort(scores)[::-1][:k]
        resultados = []
        for i in idx:
            if scores[i] <= 0:
                continue
            r = dict(self.chunks[i]); r["score"] = round(float(scores[i]), 3)
            resultados.append(r)
        return resultados

    def construir_contexto(self, consulta: str, k: int = 3) -> tuple[str, list[dict]]:
        """Ensambla el contexto recuperado para inyectarlo en el prompt del LLM."""
        recuperados = self.recuperar(consulta, k)
        lineas = []
        for r in recuperados:
            etiqueta = "INTERNA" if r["origen"] == "interna" else "EXTERNA"
            lineas.append(f"[{etiqueta} · {r['fuente']}] {r['texto']}")
        return "\n".join(lineas), recuperados


# Recuperador compartido (singleton perezoso)
_retriever: RAGRetriever | None = None


def _get_retriever() -> RAGRetriever:
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever


def responder_con_rag(pregunta: str, k: int = 3, llm=None) -> dict:
    """
    Responde una pregunta usando RAG. Si se entrega un `llm` (LangChain), genera
    la respuesta condicionada al contexto recuperado; en caso contrario devuelve
    el contexto recuperado (modo reproducible sin API).
    """
    contexto, fuentes = _get_retriever().construir_contexto(pregunta, k)
    origenes = sorted({f["origen"] for f in fuentes})
    if llm is not None:
        prompt = (
            "Responde la pregunta del cliente usando EXCLUSIVAMENTE el siguiente contexto "
            "recuperado. Si el contexto no alcanza, indícalo.\n\n"
            f"CONTEXTO:\n{contexto}\n\nPREGUNTA: {pregunta}\nRESPUESTA:"
        )
        respuesta = llm.invoke(prompt).content
    else:
        respuesta = ("(Modo reproducible sin LLM) Contexto recuperado para fundamentar la "
                     "respuesta:\n" + contexto)
    return {
        "pregunta": pregunta,
        "respuesta": respuesta,
        "fuentes": fuentes,
        "origenes_combinados": origenes,
    }


# ── Demostración ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    consultas = [
        "¿Qué requisitos y tasa tiene el crédito hipotecario?",
        "¿Qué derechos tengo como consumidor y cómo se protege mi RUT?",
        "¿Pueden transferir dinero de mi cuenta sin que yo confirme?",
    ]
    r = _get_retriever()
    print(f"Base: {len(r.chunks)} chunks · "
          f"{sum(1 for c in r.chunks if c['origen']=='interna')} internos / "
          f"{sum(1 for c in r.chunks if c['origen']=='externa')} externos\n")
    for q in consultas:
        out = responder_con_rag(q, k=2)
        print("=" * 64)
        print("PREGUNTA:", q)
        print("Fuentes combinadas:", out["origenes_combinados"])
        for f in out["fuentes"]:
            print(f"  · [{f['origen']}] {f['fuente']} (score {f['score']})")
