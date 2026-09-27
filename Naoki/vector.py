import orjson
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from config import (
    CHAT_FILE,
    COLLECTION,
    DB_DIR,
    EMBED_MODEL,
    RETRIEVER_K,
    RETRIEVER_SCORE,
)

DB_DIR.mkdir(parents=True, exist_ok=True)
if not CHAT_FILE.exists():
    CHAT_FILE.touch()


embeddings = OllamaEmbeddings(
    model=EMBED_MODEL
)  # we are declaring the embeding model, hope i dont forget it
store = Chroma(
    collection_name=COLLECTION,
    persist_directory=str(DB_DIR),
    embedding_function=embeddings,
)


def _to_document(c: dict) -> Document:
    return Document(
        page_content=c["summary"],
        metadata={
            "project": c["project"],
            "ts": c["ts"],
            "topic": c["topic"],
            "text": c["text"],
        },
    )


def ingest_missing() -> int:
    """Embed any chats in chats.jsonl not yet in Chroma. Returns count added."""
    existing = set(store.get()["ids"])
    docs, ids = [], []
    for line in CHAT_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            c = orjson.loads(line)
        except ValueError:
            continue  # skip truncated/corrupt lines (e.g. killed mid-write)
        cid = str(c["id"])
        if cid in existing:
            continue
        docs.append(_to_document(c))
        ids.append(cid)
    if docs:
        store.add_documents(documents=docs, ids=ids)
    return len(ids)


def add_chat(rec: dict) -> str:
    """Append one chat to chats.jsonl AND embed it immediately. Returns str id."""
    cid = str(rec["id"])
    with open(CHAT_FILE, "ab") as f:
        f.write(orjson.dumps(rec) + b"\n")
    try:
        found = store.get(ids=[cid])
        if found and found.get("ids"):
            return cid
    except (ValueError, OSError):
        pass
    store.add_documents(documents=[_to_document(rec)], ids=[cid])
    return cid


def bootstrap() -> int:
    """One-time startup ingest. Called explicitly so importing this module has
    no side effects beyond opening the (lazy) Chroma handle."""
    return ingest_missing()


def search_relevant(query: str, k: int = RETRIEVER_K, floor: float = RETRIEVER_SCORE):
    """Return docs whose relevance score clears `floor`.

    Chroma's raw score is a distance (lower = closer); we go through
    similarity_search_with_relevance_scores so the threshold is a 0-1
    relevance (higher = more relevant), which is what RETRIEVER_SCORE means.
    """
    if not query.strip():
        return []
    pairs = store.similarity_search_with_relevance_scores(query, k=k)
    return [doc for doc, score in pairs if score >= floor]
