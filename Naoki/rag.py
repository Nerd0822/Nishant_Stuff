"""Searchable memory: notes, facts, and this project's own code.

Why RAG instead of pasting everything into the prompt: about_me.json and
notes.txt grow forever, and full-prompt injection wastes context on
irrelevant history. The retriever hands the agent only the chunks matching
this turn's message.

Embeddings run locally (nomic-embed-text), vectors live in FAISS on disk
under ./index.faiss. Rebuild after anything that changes the sources --
add_fact and save_note already trigger it; code edits just need a manual
rebuild. history.json-style unbounded chat logs are never indexed: old
tool outputs make terrible retrieval material.
"""

from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

BASE = Path(__file__).resolve().parent
INDEX_DIR = BASE / "index.faiss"
EMBED_MODEL = "nomic-embed-text"
NOTES_FILE = Path.home() / "notes.txt"


def _load_documents() -> list[Document]:
    docs: list[Document] = []
    if NOTES_FILE.is_file():
        text = NOTES_FILE.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            docs.append(
                Document(page_content=text, metadata={"source": str(NOTES_FILE)})
            )
    about = BASE / "about_me.json"
    if about.is_file():
        import json

        try:
            facts = json.loads(about.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            facts = []
        if isinstance(facts, list):
            for fact in facts:
                docs.append(
                    Document(
                        page_content=f"User fact: {fact}",
                        metadata={"source": str(about)},
                    )
                )
    for path in sorted(BASE.glob("*.py")):
        docs.append(
            Document(
                page_content=path.read_text(encoding="utf-8", errors="replace"),
                metadata={"source": str(path)},
            )
        )
    # 800 chars with overlap: a fact or function rarely splits mid-thought.
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    return splitter.split_documents(docs)


def build_index() -> FAISS:
    """Rebuild the on-disk index from current sources. Returns it."""
    index = FAISS.from_documents(_load_documents(), OllamaEmbeddings(model=EMBED_MODEL))
    index.save_local(str(INDEX_DIR))
    return index


def load_retriever(k: int = 4):
    """Load the saved index as a top-k retriever. Raises if never built."""
    index = FAISS.load_local(
        str(INDEX_DIR),
        OllamaEmbeddings(model=EMBED_MODEL),
        allow_dangerous_deserialization=True,
    )
    return index.as_retriever(search_kwargs={"k": k})
