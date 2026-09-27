# Source documents for the local RAG demo

Place UTF-8 `.txt` or `.md` files in this directory. The RAG script recursively
loads them, splits them into overlapping chunks, embeds them with Ollama, and
stores the resulting index in `rag_tuto/.faiss_index/`.

For example, you can add notes about a project, a book, or a subject you want
to ask questions about. Keep the files reasonably sized and remove the sample
content below when you add your own material.

## Example

This project demonstrates a local Retrieval-Augmented Generation workflow. FAISS
stores embeddings and retrieves similar chunks. Ollama creates the embeddings
and generates an answer using only the retrieved context.
