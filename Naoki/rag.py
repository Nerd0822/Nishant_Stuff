import orjson
from functools import lru_cache
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from config import EMBED_MODEL, CHAT_LOG, DB_DIR

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
TOP_K = 3
SCORE_MIN = 0.4
SKIP_ROLES = {"tool"}

# load the document first
def load_doc(file):
    messages = []
    with open(file, encoding="utf-8") as f:
        for line in f:
            lines = [
                f"{m['role']}: {m['content']}"
                for m in ex
                if m["content"].strip() and m["role"] not in SKIP_ROLES
            ]
            if line:
                messages.append(orjson.loads(line))

    exchanges, current = [], []
    for m in messages:
        if m["role"] == "human" and current:
            exchanges.append(current)
            current = []
        current.append(m)
    if current:
        exchanges.append(current)

    docs = []
    for i, ex in enumerate(exchanges):
        lines = [
            f"{m['role']}: {m['content']}"
            for m in ex
            if m["content"].strip() and m["role"] not in SKIP_ROLES
        ]
        if not lines:
            continue
        docs.append(
            Document(
                page_content="\n".join(lines),
                metadata={"source": str(file), "turn": i, "num_messages": len(ex)},
            )
        )
    return docs


# chunk the doc
def chunk_doc(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_documents(docs)


# store on the db
@lru_cache(maxsize=1)
def get_store():
    return Chroma(
        collection_name="chat_memory",
        embedding_function=OllamaEmbeddings(model=EMBED_MODEL,keep_alive=30),
        persist_directory=str(DB_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )


# index the vector
def index(file=CHAT_LOG):
    chunks = chunk_doc(load_doc(file))

    seen, ids = {}, []
    for c in chunks:
        turn = c.metadata["turn"]
        n = seen.get(turn, 0)
        seen[turn] = n + 1
        ids.append(f"{c.metadata['source']}-{turn}-{n}")

    store = get_store()
    have = set(store.get(ids=ids, include=[])["ids"])
    todo = [(c, i) for c, i in zip(chunks, ids) if i not in have]
    if not todo:
        return 0
    store.add_documents([c for c, _ in todo], ids=[i for _, i in todo])
    return len(todo)


# retrive
def get_retriever(k=TOP_K):
    return get_store().as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": k, "score_threshold": SCORE_MIN},
    )
