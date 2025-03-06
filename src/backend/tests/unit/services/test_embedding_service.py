import pytest  # pytest 7.0.0+
from unittest.mock import MagicMock  # unittest standard library
import numpy as np  # numpy 1.20.0+
import pytest_asyncio  # pytest-asyncio 0.18.0+
from sentence_transformers import SentenceTransformer  # sentence-transformers 2.2.2+

from app.services.embedding_service import (
    generate_embedding,
    generate_embeddings_batch,
    async_generate_embedding,
    async_generate_embeddings_batch,
    store_embedding,
    store_embeddings_batch,
    process_document_chunk,
    process_document_chunks,
    async_process_document_chunks,
    search_similar,
    search_similar_by_text,
    async_search_similar_by_text,
    delete_embedding,
    delete_embeddings_batch,
    rebuild_index,
    EmbeddingService,
    get_embedding_model,
    get_vector_store,
)
from app.models.document_chunk import DocumentChunk
from app.vector_store.faiss_store import FAISSStore
from app.utils.vector_utils import normalize_vector, validate_vector_dimensions, generate_embedding_id
from tests.conftest import sample_vector_embeddings


def test_get_embedding_model():
    """Tests that get_embedding_model initializes and returns a SentenceTransformer model"""
    # Arrange
    mock_sentence_transformer = MagicMock(spec=SentenceTransformer)

    # Act
    model = get_embedding_model()

    # Assert
    assert isinstance(model, SentenceTransformer)


def test_get_vector_store():
    """Tests that get_vector_store initializes and returns a FAISSStore instance"""
    # Arrange
    mock_faiss_store = MagicMock(spec=FAISSStore)

    # Act
    store = get_vector_store()

    # Assert
    assert isinstance(store, FAISSStore)


def test_generate_embedding():
    """Tests that generate_embedding correctly generates a vector embedding for text"""
    # Arrange
    mock_model = MagicMock()
    sample_embedding = sample_vector_embeddings(1)[0]
    mock_model.encode.return_value = sample_embedding
    get_embedding_model.return_value = mock_model
    text = "sample text"

    # Act
    embedding = generate_embedding(text)

    # Assert
    mock_model.encode.assert_called_once_with(text, convert_to_numpy=True, normalize_embeddings=True)
    assert isinstance(embedding, np.ndarray)


def test_generate_embeddings_batch():
    """Tests that generate_embeddings_batch correctly generates embeddings for multiple texts"""
    # Arrange
    mock_model = MagicMock()
    sample_embeddings = sample_vector_embeddings(2)
    mock_model.encode.return_value = sample_embeddings
    get_embedding_model.return_value = mock_model
    texts = ["sample text 1", "sample text 2"]

    # Act
    embeddings = generate_embeddings_batch(texts)

    # Assert
    mock_model.encode.assert_called_once_with(texts, convert_to_numpy=True, normalize_embeddings=True)
    assert isinstance(embeddings, list)
    assert len(embeddings) == 2
    assert isinstance(embeddings[0], np.ndarray)


@pytest.mark.asyncio
async def test_async_generate_embedding():
    """Tests that async_generate_embedding correctly generates a vector embedding asynchronously"""
    # Arrange
    mock_embedding = sample_vector_embeddings(1)[0]
    generate_embedding.return_value = mock_embedding
    text = "sample text"

    # Act
    embedding = await async_generate_embedding(text)

    # Assert
    generate_embedding.assert_called_once_with(text)
    assert isinstance(embedding, np.ndarray)


@pytest.mark.asyncio
async def test_async_generate_embeddings_batch():
    """Tests that async_generate_embeddings_batch correctly generates embeddings for multiple texts asynchronously"""
    # Arrange
    mock_embeddings = sample_vector_embeddings(2)
    generate_embeddings_batch.return_value = mock_embeddings
    texts = ["sample text 1", "sample text 2"]

    # Act
    embeddings = await async_generate_embeddings_batch(texts)

    # Assert
    generate_embeddings_batch.assert_called_once_with(texts)
    assert isinstance(embeddings, list)
    assert len(embeddings) == 2
    assert isinstance(embeddings[0], np.ndarray)


def test_store_embedding():
    """Tests that store_embedding correctly stores a vector embedding in FAISS"""
    # Arrange
    mock_store = MagicMock()
    get_vector_store.return_value = mock_store
    mock_embedding_id = "test_embedding_id"
    generate_embedding_id.return_value = mock_embedding_id
    embedding = sample_vector_embeddings(1)[0]

    # Act
    embedding_id = store_embedding(embedding)

    # Assert
    mock_store.add_vectors.assert_called_once()
    mock_store.save.assert_called_once()
    assert embedding_id == mock_embedding_id


def test_store_embeddings_batch():
    """Tests that store_embeddings_batch correctly stores multiple vector embeddings in FAISS"""
    # Arrange
    mock_store = MagicMock()
    get_vector_store.return_value = mock_store
    mock_embedding_ids = ["test_embedding_id_1", "test_embedding_id_2"]
    generate_embedding_id.side_effect = mock_embedding_ids
    embeddings = sample_vector_embeddings(2)

    # Act
    embedding_ids = store_embeddings_batch(embeddings)

    # Assert
    mock_store.add_vectors.assert_called_once()
    mock_store.save.assert_called_once()
    assert embedding_ids == mock_embedding_ids


def test_process_document_chunk():
    """Tests that process_document_chunk correctly processes a document chunk"""
    # Arrange
    mock_chunk = MagicMock(spec=DocumentChunk)
    mock_chunk.content = "test content"
    mock_embedding = sample_vector_embeddings(1)[0]
    generate_embedding.return_value = mock_embedding
    mock_embedding_id = "test_embedding_id"
    store_embedding.return_value = mock_embedding_id

    # Act
    embedding_id = process_document_chunk(mock_chunk)

    # Assert
    generate_embedding.assert_called_once_with(mock_chunk.content)
    store_embedding.assert_called_once_with(mock_embedding)
    assert embedding_id == mock_embedding_id


def test_process_document_chunks():
    """Tests that process_document_chunks correctly processes multiple document chunks"""
    # Arrange
    mock_chunks = [MagicMock(spec=DocumentChunk, content=f"test content {i}") for i in range(2)]
    mock_embeddings = sample_vector_embeddings(2)
    generate_embeddings_batch.return_value = mock_embeddings
    mock_embedding_ids = ["test_embedding_id_1", "test_embedding_id_2"]
    store_embeddings_batch.return_value = mock_embedding_ids

    # Act
    embedding_ids = process_document_chunks(mock_chunks)

    # Assert
    texts = [chunk.content for chunk in mock_chunks]
    generate_embeddings_batch.assert_called_once_with(texts)
    store_embeddings_batch.assert_called_once_with(mock_embeddings)
    assert embedding_ids == mock_embedding_ids


@pytest.mark.asyncio
async def test_async_process_document_chunks():
    """Tests that async_process_document_chunks correctly processes multiple document chunks asynchronously"""
    # Arrange
    mock_chunks = [MagicMock(spec=DocumentChunk, content=f"test content {i}") for i in range(2)]
    mock_embeddings = sample_vector_embeddings(2)
    async_generate_embeddings_batch.return_value = mock_embeddings
    mock_embedding_ids = ["test_embedding_id_1", "test_embedding_id_2"]
    store_embeddings_batch.return_value = mock_embedding_ids

    # Act
    embedding_ids = await async_process_document_chunks(mock_chunks)

    # Assert
    texts = [chunk.content for chunk in mock_chunks]
    async_generate_embeddings_batch.assert_called_once_with(texts)
    store_embeddings_batch.assert_called_once_with(mock_embeddings)
    assert embedding_ids == mock_embedding_ids


def test_search_similar():
    """Tests that search_similar correctly searches for similar vectors"""
    # Arrange
    mock_store = MagicMock()
    sample_results = [{"id": "1", "score": 0.9}, {"id": "2", "score": 0.8}]
    mock_store.search.return_value = sample_results
    get_vector_store.return_value = mock_store
    query_vector = sample_vector_embeddings(1)[0]
    top_k = 5
    threshold = 0.7

    # Act
    results = search_similar(query_vector, top_k, threshold)

    # Assert
    mock_store.search.assert_called_once_with(query_vector, top_k, threshold)
    assert results == sample_results


def test_search_similar_by_text():
    """Tests that search_similar_by_text correctly searches for similar vectors by text"""
    # Arrange
    mock_embedding = sample_vector_embeddings(1)[0]
    generate_embedding.return_value = mock_embedding
    sample_results = [{"id": "1", "score": 0.9}, {"id": "2", "score": 0.8}]
    search_similar.return_value = sample_results
    query_text = "test query"
    top_k = 5
    threshold = 0.7

    # Act
    results = search_similar_by_text(query_text, top_k, threshold)

    # Assert
    generate_embedding.assert_called_once_with(query_text)
    search_similar.assert_called_once_with(mock_embedding, top_k, threshold)
    assert results == sample_results


@pytest.mark.asyncio
async def test_async_search_similar_by_text():
    """Tests that async_search_similar_by_text correctly searches for similar vectors by text asynchronously"""
    # Arrange
    mock_embedding = sample_vector_embeddings(1)[0]
    async_generate_embedding.return_value = mock_embedding
    sample_results = [{"id": "1", "score": 0.9}, {"id": "2", "score": 0.8}]
    search_similar.return_value = sample_results
    query_text = "test query"
    top_k = 5
    threshold = 0.7

    # Act
    results = await async_search_similar_by_text(query_text, top_k, threshold)

    # Assert
    async_generate_embedding.assert_called_once_with(query_text)
    search_similar.assert_called_once_with(mock_embedding, top_k, threshold)
    assert results == sample_results


def test_delete_embedding():
    """Tests that delete_embedding correctly deletes a vector embedding"""
    # Arrange
    mock_store = MagicMock()
    mock_store.delete_vectors.return_value = True
    get_vector_store.return_value = mock_store
    embedding_id = "test_embedding_id"

    # Act
    success = delete_embedding(embedding_id)

    # Assert
    mock_store.delete_vectors.assert_called_once_with([embedding_id])
    mock_store.save.assert_called_once()
    assert success is True


def test_delete_embeddings_batch():
    """Tests that delete_embeddings_batch correctly deletes multiple vector embeddings"""
    # Arrange
    mock_store = MagicMock()
    mock_store.delete_vectors.return_value = True
    get_vector_store.return_value = mock_store
    embedding_ids = ["test_embedding_id_1", "test_embedding_id_2"]

    # Act
    success = delete_embeddings_batch(embedding_ids)

    # Assert
    mock_store.delete_vectors.assert_called_once_with(embedding_ids)
    mock_store.save.assert_called_once()
    assert success is True


def test_rebuild_index():
    """Tests that rebuild_index correctly rebuilds the FAISS index"""
    # Arrange
    mock_store = MagicMock()
    mock_store.clear.return_value = True
    get_vector_store.return_value = mock_store

    # Act
    success = rebuild_index()

    # Assert
    mock_store.clear.assert_called_once()
    mock_store.save.assert_called_once()
    assert success is True


def test_embedding_service_init():
    """Tests that EmbeddingService initializes correctly"""
    # Arrange
    mock_model = MagicMock()
    get_embedding_model.return_value = mock_model
    mock_store = MagicMock()
    get_vector_store.return_value = mock_store

    # Act
    service = EmbeddingService()

    # Assert
    get_embedding_model.assert_called_once()
    get_vector_store.assert_called_once()
    assert service._model == mock_model
    assert service._vector_store == mock_store


def test_embedding_service_generate_embedding():
    """Tests that EmbeddingService.generate_embedding correctly generates a vector embedding"""
    # Arrange
    mock_model = MagicMock()
    sample_embedding = sample_vector_embeddings(1)[0]
    mock_model.encode.return_value = sample_embedding
    get_embedding_model.return_value = mock_model
    service = EmbeddingService()
    text = "sample text"

    # Act
    embedding = service.generate_embedding(text)

    # Assert
    mock_model.encode.assert_called_once_with(text, convert_to_numpy=True, normalize_embeddings=True)
    assert isinstance(embedding, np.ndarray)


def test_embedding_service_generate_embeddings_batch():
    """Tests that EmbeddingService.generate_embeddings_batch correctly generates embeddings for multiple texts"""
    # Arrange
    mock_model = MagicMock()
    sample_embeddings = sample_vector_embeddings(2)
    mock_model.encode.return_value = sample_embeddings
    get_embedding_model.return_value = mock_model
    service = EmbeddingService()
    texts = ["sample text 1", "sample text 2"]

    # Act
    embeddings = service.generate_embeddings_batch(texts)

    # Assert
    mock_model.encode.assert_called_once_with(texts, convert_to_numpy=True, normalize_embeddings=True)
    assert isinstance(embeddings, list)
    assert len(embeddings) == 2
    assert isinstance(embeddings[0], np.ndarray)


def test_embedding_service_store_embedding():
    """Tests that EmbeddingService.store_embedding correctly stores a vector embedding"""
    # Arrange
    mock_store = MagicMock()
    get_vector_store.return_value = mock_store
    mock_embedding_id = "test_embedding_id"
    generate_embedding_id.return_value = mock_embedding_id
    service = EmbeddingService()
    embedding = sample_vector_embeddings(1)[0]

    # Act
    embedding_id = service.store_embedding(embedding)

    # Assert
    mock_store.add_vectors.assert_called_once()
    mock_store.save.assert_called_once()
    assert embedding_id == mock_embedding_id


def test_embedding_service_store_embeddings_batch():
    """Tests that EmbeddingService.store_embeddings_batch correctly stores multiple vector embeddings"""
    # Arrange
    mock_store = MagicMock()
    get_vector_store.return_value = mock_store
    mock_embedding_ids = ["test_embedding_id_1", "test_embedding_id_2"]
    generate_embedding_id.side_effect = mock_embedding_ids
    service = EmbeddingService()
    embeddings = sample_vector_embeddings(2)

    # Act
    embedding_ids = service.store_embeddings_batch(embeddings)

    # Assert
    mock_store.add_vectors.assert_called_once()
    mock_store.save.assert_called_once()
    assert embedding_ids == mock_embedding_ids


def test_embedding_service_process_document_chunk():
    """Tests that EmbeddingService.process_document_chunk correctly processes a document chunk"""
    # Arrange
    mock_chunk = MagicMock(spec=DocumentChunk)
    mock_chunk.content = "test content"
    mock_embedding = sample_vector_embeddings(1)[0]
    generate_embedding.return_value = mock_embedding
    mock_embedding_id = "test_embedding_id"
    store_embedding.return_value = mock_embedding_id
    service = EmbeddingService()

    # Act
    embedding_id = service.process_document_chunk(mock_chunk)

    # Assert
    generate_embedding.assert_called_once_with(mock_chunk.content)
    store_embedding.assert_called_once_with(mock_embedding)
    assert embedding_id == mock_embedding_id


def test_embedding_service_process_document_chunks():
    """Tests that EmbeddingService.process_document_chunks correctly processes multiple document chunks"""
    # Arrange
    mock_chunks = [MagicMock(spec=DocumentChunk, content=f"test content {i}") for i in range(2)]
    mock_embeddings = sample_vector_embeddings(2)
    generate_embeddings_batch.return_value = mock_embeddings
    mock_embedding_ids = ["test_embedding_id_1", "test_embedding_id_2"]
    store_embeddings_batch.return_value = mock_embedding_ids
    service = EmbeddingService()

    # Act
    embedding_ids = service.process_document_chunks(mock_chunks)

    # Assert
    texts = [chunk.content for chunk in mock_chunks]
    generate_embeddings_batch.assert_called_once_with(texts)
    store_embeddings_batch.assert_called_once_with(mock_embeddings)
    assert embedding_ids == mock_embedding_ids


def test_embedding_service_search_similar():
    """Tests that EmbeddingService.search_similar correctly searches for similar vectors"""
    # Arrange
    mock_store = MagicMock()
    sample_results = [{"id": "1", "score": 0.9}, {"id": "2", "score": 0.8}]
    mock_store.search.return_value = sample_results
    get_vector_store.return_value = mock_store
    service = EmbeddingService()
    query_vector = sample_vector_embeddings(1)[0]
    top_k = 5
    threshold = 0.7

    # Act
    results = service.search_similar(query_vector, top_k, threshold)

    # Assert
    mock_store.search.assert_called_once_with(query_vector, top_k, threshold)
    assert results == sample_results


def test_embedding_service_search_similar_by_text():
    """Tests that EmbeddingService.search_similar_by_text correctly searches for similar vectors by text"""
    # Arrange
    mock_embedding = sample_vector_embeddings(1)[0]
    generate_embedding.return_value = mock_embedding
    sample_results = [{"id": "1", "score": 0.9}, {"id": "2", "score": 0.8}]
    search_similar.return_value = sample_results
    service = EmbeddingService()
    query_text = "test query"
    top_k = 5
    threshold = 0.7

    # Act
    results = service.search_similar_by_text(query_text, top_k, threshold)

    # Assert
    generate_embedding.assert_called_once_with(query_text)
    search_similar.assert_called_once_with(mock_embedding, top_k, threshold)
    assert results == sample_results


def test_embedding_service_delete_embedding():
    """Tests that EmbeddingService.delete_embedding correctly deletes a vector embedding"""
    # Arrange
    mock_store = MagicMock()
    mock_store.delete_vectors.return_value = True
    get_vector_store.return_value = mock_store
    service = EmbeddingService()
    embedding_id = "test_embedding_id"

    # Act
    success = service.delete_embedding(embedding_id)

    # Assert
    mock_store.delete_vectors.assert_called_once_with([embedding_id])
    mock_store.save.assert_called_once()
    assert success is True


def test_embedding_service_delete_embeddings_batch():
    """Tests that EmbeddingService.delete_embeddings_batch correctly deletes multiple vector embeddings"""
    # Arrange
    mock_store = MagicMock()
    mock_store.delete_vectors.return_value = True
    get_vector_store.return_value = mock_store
    service = EmbeddingService()
    embedding_ids = ["test_embedding_id_1", "test_embedding_id_2"]

    # Act
    success = service.delete_embeddings_batch(embedding_ids)

    # Assert
    mock_store.delete_vectors.assert_called_once_with(embedding_ids)
    mock_store.save.assert_called_once()
    assert success is True


def test_embedding_service_rebuild_index():
    """Tests that EmbeddingService.rebuild_index correctly rebuilds the FAISS index"""
    # Arrange
    mock_store = MagicMock()
    mock_store.clear.return_value = True
    get_vector_store.return_value = mock_store
    service = EmbeddingService()

    # Act
    success = service.rebuild_index()

    # Assert
    mock_store.clear.assert_called_once()
    mock_store.save.assert_called_once()
    assert success is True