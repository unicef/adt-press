"""
RAG (Retrieval-Augmented Generation) nodes for knowledge base retrieval.

This module provides Hamilton nodes for:
- Building and caching a vector index from reference documents
- Retrieving relevant context based on semantic similarity

The knowledge base is designed to complement (not replace) styleguide injection:
- Styleguides: Full injection for design consistency
- References: RAG retrieval for curriculum, entities, pedagogy, book context
"""

import hashlib
import os
import re
from dataclasses import dataclass

import structlog
import yaml
from hamilton.function_modifiers import cache, config
from omegaconf import DictConfig

from adt_press.models.config import KnowledgeBaseConfig, StyleguideConfig

log = structlog.get_logger()


@dataclass
class Document:
    """A chunk of content from the knowledge base."""

    content: str
    metadata: dict
    collection: str
    source_file: str


@dataclass
class RetrievedDocument:
    """A document retrieved from the knowledge base with similarity score."""

    document: Document
    score: float


class KnowledgeIndex:
    """Wrapper around ChromaDB for knowledge base retrieval."""

    def __init__(self, persist_directory: str, collection_name: str):
        import chromadb
        from chromadb.config import Settings

        self.client = chromadb.Client(
            Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False,
                is_persistent=True,
            )
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, documents: list[Document], embeddings: list[list[float]]) -> None:
        """Add documents with pre-computed embeddings to the index."""
        if not documents:
            return

        self.collection.add(
            ids=[f"doc_{i}" for i in range(len(documents))],
            embeddings=embeddings,
            documents=[doc.content for doc in documents],
            metadatas=[
                {
                    "collection": doc.collection,
                    "source_file": doc.source_file,
                    **doc.metadata,
                }
                for doc in documents
            ],
        )

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[RetrievedDocument]:
        """Search for similar documents using a query embedding."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        retrieved = []
        if results["documents"] and results["documents"][0]:
            for i, (content, metadata, distance) in enumerate(
                zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ):
                doc = Document(
                    content=content,
                    metadata=metadata,
                    collection=metadata.get("collection", "unknown"),
                    source_file=metadata.get("source_file", "unknown"),
                )
                # Convert distance to similarity score (cosine distance -> similarity)
                score = 1.0 - distance
                retrieved.append(RetrievedDocument(document=doc, score=score))

        return retrieved

    def clear(self) -> None:
        """Clear all documents from the collection."""
        # Delete and recreate the collection
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            metadata={"hnsw:space": "cosine"},
        )


def _chunk_markdown(content: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split markdown content into chunks by sections."""
    # Split by headers (##, ###, etc.)
    sections = re.split(r"(?=^#{1,4}\s)", content, flags=re.MULTILINE)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        # If section is small enough, keep it as one chunk
        if len(section) <= chunk_size:
            chunks.append(section)
        else:
            # Split large sections into overlapping chunks
            words = section.split()
            current_chunk = []
            current_length = 0

            for word in words:
                word_len = len(word) + 1  # +1 for space
                if current_length + word_len > chunk_size and current_chunk:
                    chunks.append(" ".join(current_chunk))
                    # Keep overlap
                    overlap_words = current_chunk[-chunk_overlap // 10 :] if chunk_overlap else []
                    current_chunk = overlap_words
                    current_length = sum(len(w) + 1 for w in current_chunk)

                current_chunk.append(word)
                current_length += word_len

            if current_chunk:
                chunks.append(" ".join(current_chunk))

    return chunks


def _chunk_yaml(content: str) -> list[str]:
    """Split YAML content into chunks by top-level entries."""
    try:
        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            return [content]

        chunks = []
        for key, value in data.items():
            if isinstance(value, list):
                # Each list item is a chunk
                for item in value:
                    chunk_content = yaml.dump({key: [item]}, default_flow_style=False)
                    chunks.append(chunk_content)
            else:
                chunk_content = yaml.dump({key: value}, default_flow_style=False)
                chunks.append(chunk_content)

        return chunks if chunks else [content]
    except yaml.YAMLError:
        return [content]


def _chunk_pdf(file_path: str, chunk_size: int, chunk_overlap: int) -> list[tuple[str, dict]]:
    """Extract and chunk text from a PDF file.

    Returns list of (chunk_text, metadata) tuples where metadata includes page numbers.
    """
    import pymupdf

    chunks = []

    try:
        doc = pymupdf.open(file_path)

        # Extract text page by page
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()

            if not text.strip():
                continue

            # Split page text into paragraphs
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

            current_chunk = []
            current_length = 0

            for para in paragraphs:
                para_len = len(para)

                # If adding this paragraph exceeds chunk_size, save current chunk
                if current_length + para_len > chunk_size and current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append((chunk_text, {"page_number": page_num + 1}))

                    # Keep overlap
                    if chunk_overlap > 0 and current_chunk:
                        # Keep last paragraph(s) for overlap
                        overlap_text = current_chunk[-1] if current_chunk else ""
                        current_chunk = [overlap_text] if len(overlap_text) < chunk_overlap else []
                        current_length = len(overlap_text) if current_chunk else 0
                    else:
                        current_chunk = []
                        current_length = 0

                current_chunk.append(para)
                current_length += para_len

            # Don't forget remaining content from this page
            if current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append((chunk_text, {"page_number": page_num + 1}))

        doc.close()

    except Exception as e:
        log.warning("failed_to_process_pdf", file=file_path, error=str(e))

    return chunks


def _load_documents(
    references_path: str,
    collections: list[str],
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    """Load and chunk all documents from the references directory."""
    documents = []

    for collection in collections:
        collection_path = os.path.join(references_path, collection)
        if not os.path.exists(collection_path):
            log.warning("collection_not_found", collection=collection, path=collection_path)
            continue

        for root, _, files in os.walk(collection_path):
            for filename in files:
                if filename.startswith(".") or filename == "README.md":
                    continue

                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, references_path)

                try:
                    # Handle PDFs separately (binary files)
                    if filename.endswith(".pdf"):
                        log.info("processing_pdf", file=filename)
                        pdf_chunks = _chunk_pdf(file_path, chunk_size, chunk_overlap)

                        for i, (chunk_text, chunk_metadata) in enumerate(pdf_chunks):
                            if chunk_text.strip():
                                documents.append(
                                    Document(
                                        content=chunk_text,
                                        metadata={
                                            "chunk_index": i,
                                            "filename": filename,
                                            **chunk_metadata,
                                        },
                                        collection=collection,
                                        source_file=rel_path,
                                    )
                                )
                        continue

                    # Handle text-based files
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    if not content.strip():
                        continue

                    # Chunk based on file type
                    if filename.endswith(".md"):
                        chunks = _chunk_markdown(content, chunk_size, chunk_overlap)
                    elif filename.endswith((".yaml", ".yml")):
                        chunks = _chunk_yaml(content)
                    else:
                        # Plain text: single chunk
                        chunks = [content]

                    for i, chunk in enumerate(chunks):
                        if chunk.strip():
                            documents.append(
                                Document(
                                    content=chunk,
                                    metadata={"chunk_index": i, "filename": filename},
                                    collection=collection,
                                    source_file=rel_path,
                                )
                            )

                except Exception as e:
                    log.warning("failed_to_load_document", file=file_path, error=str(e))

    return documents


def _compute_embeddings(
    documents: list[Document],
    model: str,
) -> list[list[float]]:
    """Compute embeddings for documents using OpenAI."""
    import openai

    if not documents:
        return []

    client = openai.OpenAI()

    # Batch embeddings (OpenAI supports up to 2048 inputs)
    batch_size = 100
    all_embeddings = []

    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        texts = [doc.content for doc in batch]

        response = client.embeddings.create(
            model=model,
            input=texts,
        )

        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)

    return all_embeddings


def _compute_query_embedding(query: str, model: str) -> list[float]:
    """Compute embedding for a query string."""
    import openai

    client = openai.OpenAI()
    response = client.embeddings.create(
        model=model,
        input=[query],
    )
    return response.data[0].embedding


# ============================================================================
# Hamilton Nodes
# ============================================================================


def knowledge_base_config(config: DictConfig) -> KnowledgeBaseConfig:
    """Load knowledge base configuration from config.yaml."""
    kb_config = config.get("knowledge_base", {})
    return KnowledgeBaseConfig.model_validate(dict(kb_config))


def knowledge_index_cache_key(
    knowledge_base_config: KnowledgeBaseConfig,
) -> str:
    """Generate cache key based on references content."""
    if not knowledge_base_config.enabled:
        return "disabled"

    # Hash the content of all reference files
    file_hashes = []

    for collection in knowledge_base_config.collections:
        collection_path = os.path.join(knowledge_base_config.references_path, collection)
        if not os.path.exists(collection_path):
            continue

        for root, _, files in os.walk(collection_path):
            for filename in sorted(files):
                if filename.startswith(".") or filename == "README.md":
                    continue

                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                        file_hashes.append(f"{file_path}:{file_hash}")
                except Exception:
                    continue

    # Include config settings that affect indexing
    config_str = f"{knowledge_base_config.embedding_model}:{knowledge_base_config.chunk_size}:{knowledge_base_config.chunk_overlap}"
    file_hashes.append(config_str)

    combined = "\n".join(sorted(file_hashes))
    return hashlib.sha256(combined.encode()).hexdigest()


@cache(behavior="disable")
@config.when(rag_strategy="enabled")
def knowledge_index__enabled(
    run_output_dir_config: str,
    knowledge_base_config: KnowledgeBaseConfig,
    knowledge_index_cache_key: str,
) -> KnowledgeIndex:
    """Build or load the knowledge base index."""
    persist_dir = os.path.join(run_output_dir_config, "knowledge_index")
    cache_key_path = os.path.join(run_output_dir_config, "knowledge_index_key.txt")

    # Check if cache is valid
    cache_valid = False
    if os.path.exists(cache_key_path) and os.path.exists(persist_dir):
        with open(cache_key_path, "r") as f:
            stored_key = f.read().strip()
        cache_valid = stored_key == knowledge_index_cache_key

    index = KnowledgeIndex(persist_dir, knowledge_base_config.collection_name)

    if cache_valid:
        log.info("knowledge_index_loaded_from_cache")
        return index

    log.info("building_knowledge_index", references_path=knowledge_base_config.references_path)

    # Clear existing and rebuild
    index.clear()

    # Load and chunk documents
    documents = _load_documents(
        knowledge_base_config.references_path,
        knowledge_base_config.collections,
        knowledge_base_config.chunk_size,
        knowledge_base_config.chunk_overlap,
    )

    if not documents:
        log.warning("no_documents_found")
    else:
        log.info("documents_loaded", count=len(documents))

        # Compute embeddings
        embeddings = _compute_embeddings(documents, knowledge_base_config.embedding_model)

        # Add to index
        index.add_documents(documents, embeddings)
        log.info("knowledge_index_built", document_count=len(documents))

    # Save cache key
    os.makedirs(os.path.dirname(cache_key_path), exist_ok=True)
    with open(cache_key_path, "w") as f:
        f.write(knowledge_index_cache_key)

    return index


@cache(behavior="disable")
@config.when(rag_strategy="disabled")
def knowledge_index__disabled(
    knowledge_base_config: KnowledgeBaseConfig,
) -> KnowledgeIndex | None:
    """Return None when RAG is disabled."""
    return None


def retrieve_context(
    knowledge_index: KnowledgeIndex | None,
    knowledge_base_config: KnowledgeBaseConfig,
    query: str,
) -> list[RetrievedDocument]:
    """Retrieve relevant documents from the knowledge base."""
    if knowledge_index is None or not knowledge_base_config.enabled:
        return []

    if not query.strip():
        return []

    query_embedding = _compute_query_embedding(query, knowledge_base_config.embedding_model)
    return knowledge_index.search(query_embedding, knowledge_base_config.top_k)


def format_retrieved_context(retrieved_docs: list[RetrievedDocument]) -> str:
    """Format retrieved documents into a string for prompt injection."""
    if not retrieved_docs:
        return ""

    sections = []
    for doc in retrieved_docs:
        header = f"[{doc.document.collection}] (relevance: {doc.score:.2f})"
        sections.append(f"{header}\n{doc.document.content}")

    return "\n\n---\n\n".join(sections)


# ============================================================================
# Styleguide Nodes (Full Injection)
# ============================================================================


def styleguide_config(config: DictConfig) -> StyleguideConfig:
    """Load styleguide configuration from config.yaml."""
    sg_config = config.get("styleguide", {})
    return StyleguideConfig.model_validate(dict(sg_config))


def styleguide_content(styleguide_config: StyleguideConfig) -> str:
    """Load the full styleguide content for injection into prompts.

    Unlike RAG-retrieved context, styleguides are injected in full to ensure
    consistent design patterns across all generated HTML.
    """
    if not styleguide_config.enabled:
        return ""

    styleguide_path = styleguide_config.get_styleguide_path()

    if not os.path.exists(styleguide_path):
        log.warning(
            "styleguide_not_found",
            path=styleguide_path,
            name=styleguide_config.name,
        )
        return ""

    try:
        with open(styleguide_path, "r", encoding="utf-8") as f:
            content = f.read()
        log.info(
            "styleguide_loaded",
            name=styleguide_config.name,
            length=len(content),
        )
        return content
    except Exception as e:
        log.warning("styleguide_load_error", path=styleguide_path, error=str(e))
        return ""
