import os  # File system operations and path manipulation
import uuid  # Generate unique identifiers for test documents
from unittest.mock import patch  # Mocking library for isolating components during testing

import pytest  # Testing framework for writing and running tests
from fastapi import HTTPException  # version: 0.95.0+
from fastapi import UploadFile  # version: 0.95.0+

from app.models.document import DocumentStatus  # Import document status enum for testing status updates
from app.services.document_processor import (  # Import the DocumentProcessor class for testing
    DocumentProcessor,
    create_document_chunks,
    process_document,
    process_document_from_path,
)
from tests.conftest import sample_pdf_path  # Import fixture for sample PDF file path


def test_document_processor_init():
    """Tests the initialization of the DocumentProcessor class"""
    # Create a DocumentProcessor instance
    processor = DocumentProcessor()

    # Verify that the instance has the correct default chunk size and overlap
    assert processor._chunk_size is not None
    assert processor._chunk_overlap is not None

    # Create a DocumentProcessor with custom chunk size and overlap
    custom_processor = DocumentProcessor(chunk_size=500, chunk_overlap=100)

    # Verify that the instance has the correct custom values
    assert custom_processor._chunk_size == 500
    assert custom_processor._chunk_overlap == 100


@patch("app.services.document_processor.is_pdf_file", return_value=True)
@patch("app.services.document_processor.extract_text_from_pdf_bytes", return_value="Sample text content")
@patch("app.services.document_processor.extract_pdf_metadata", return_value={"title": "Test Document"})
@patch("app.services.document_processor.chunk_text", return_value=["Chunk 1", "Chunk 2"])
@patch("app.services.document_processor.count_tokens", return_value=10)
@patch("app.services.document_processor.process_document_chunks", return_value=["embedding_id_1", "embedding_id_2"])
@patch("app.services.file_storage.FileStorage.store_document", return_value="test_file_path.pdf")
def test_process_document_valid_pdf(
    mock_store_document,
    mock_process_document_chunks,
    mock_count_tokens,
    mock_chunk_text,
    mock_extract_pdf_metadata,
    mock_extract_text_from_pdf_bytes,
    mock_is_pdf_file,
):
    """Tests processing a valid PDF document"""
    # Create mock document content and filename
    document_content = b"Mock PDF Content"
    filename = "test.pdf"

    # Create a mock Document object
    class MockDocument:
        id = uuid.uuid4()

        def update_status(self, status):
            self.status = status

    mock_document = MockDocument()

    # Call process_document with the test data
    result = process_document(document_content, filename, db_document=mock_document)

    # Verify that is_pdf_file was called with the document content
    mock_is_pdf_file.assert_called_once_with(document_content)

    # Verify that store_document was called with the document content and filename
    mock_store_document.assert_called_once_with(document_content, filename)

    # Verify that extract_text_from_pdf_bytes was called with the document content
    mock_extract_text_from_pdf_bytes.assert_called_once_with(document_content)

    # Verify that extract_pdf_metadata was called
    mock_extract_pdf_metadata.assert_called_once()

    # Verify that chunk_text was called with the extracted text
    mock_chunk_text.assert_called_once_with("Sample text content", None, None)

    # Verify that count_tokens was called for each chunk
    assert mock_count_tokens.call_count == 2

    # Verify that process_document_chunks was called with the document chunks
    mock_process_document_chunks.assert_called_once()

    # Verify that the document status was updated to available
    assert mock_document.status == DocumentStatus.available

    # Verify that the result contains the expected data
    assert "document_path" in result
    assert "metadata" in result
    assert "chunks" in result
    assert "text_chunks" in result
    assert "token_counts" in result
    assert "embedding_ids" in result
    assert result["status"] == "success"


@patch("app.services.document_processor.is_pdf_file", return_value=False)
def test_process_document_invalid_pdf(mock_is_pdf_file):
    """Tests processing an invalid PDF document"""
    # Create mock document content and filename
    document_content = b"Mock Invalid PDF Content"
    filename = "test.pdf"

    # Create a mock Document object
    class MockDocument:
        def update_status(self, status):
            self.status = status

    mock_document = MockDocument()

    # Call process_document with the test data and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        process_document(document_content, filename, db_document=mock_document)

    # Verify that is_pdf_file was called with the document content
    mock_is_pdf_file.assert_called_once_with(document_content)

    # Verify that the document status was updated to error if a document object was provided
    assert mock_document.status == DocumentStatus.error
    assert exc_info.value.status_code == 400


@patch("app.services.document_processor.is_pdf_file", return_value=True)
@patch("app.services.document_processor.extract_text_from_pdf_bytes", side_effect=Exception("Extraction error"))
@patch("app.services.file_storage.FileStorage.store_document", return_value="test_file_path.pdf")
def test_process_document_extraction_error(mock_store_document, mock_extract_text_from_pdf_bytes, mock_is_pdf_file):
    """Tests handling of text extraction errors during document processing"""
    # Create mock document content and filename
    document_content = b"Mock PDF Content"
    filename = "test.pdf"

    # Create a mock Document object
    class MockDocument:
        def update_status(self, status):
            self.status = status

    mock_document = MockDocument()

    # Call process_document with the test data and expect Exception
    with pytest.raises(HTTPException) as exc_info:
        process_document(document_content, filename, db_document=mock_document)

    # Verify that is_pdf_file was called with the document content
    mock_is_pdf_file.assert_called_once_with(document_content)

    # Verify that store_document was called
    mock_store_document.assert_called_once()

    # Verify that extract_text_from_pdf_bytes was called and raised an exception
    mock_extract_text_from_pdf_bytes.assert_called_once_with(document_content)

    # Verify that the document status was updated to error
    assert mock_document.status == DocumentStatus.error
    assert exc_info.value.status_code == 500


@patch("app.services.document_processor.is_pdf_file", return_value=True)
@patch("app.services.document_processor.extract_text_from_pdf", return_value="Sample text content")
@patch("app.services.document_processor.extract_pdf_metadata", return_value={"title": "Test Document"})
@patch("app.services.document_processor.chunk_text", return_value=["Chunk 1", "Chunk 2"])
@patch("app.services.document_processor.count_tokens", return_value=10)
@patch("app.services.document_processor.process_document_chunks", return_value=["embedding_id_1", "embedding_id_2"])
@patch("app.services.file_storage.FileStorage.get_full_path", return_value="/full/path/to/test_file.pdf")
def test_process_document_from_path_valid_pdf(
    mock_get_full_path,
    mock_process_document_chunks,
    mock_count_tokens,
    mock_chunk_text,
    mock_extract_pdf_metadata,
    mock_extract_text_from_pdf,
    mock_is_pdf_file,
    sample_pdf_path,
):
    """Tests processing a valid PDF document from a file path"""
    # Create a mock Document object
    class MockDocument:
        id = uuid.uuid4()

        def update_status(self, status):
            self.status = status

    mock_document = MockDocument()

    # Call process_document_from_path with the sample PDF path
    result = process_document_from_path(sample_pdf_path, db_document=mock_document)

    # Verify that get_full_path was called with the file path
    mock_get_full_path.assert_called_once_with(sample_pdf_path)

    # Verify that is_pdf_file was called with the full path
    mock_is_pdf_file.assert_called_once_with("/full/path/to/test_file.pdf")

    # Verify that extract_text_from_pdf was called with the full path
    mock_extract_text_from_pdf.assert_called_once_with("/full/path/to/test_file.pdf")

    # Verify that extract_pdf_metadata was called
    mock_extract_pdf_metadata.assert_called_once_with("/full/path/to/test_file.pdf")

    # Verify that chunk_text was called with the extracted text
    mock_chunk_text.assert_called_once_with("Sample text content", None, None)

    # Verify that count_tokens was called for each chunk
    assert mock_count_tokens.call_count == 2

    # Verify that process_document_chunks was called with the document chunks
    mock_process_document_chunks.assert_called_once()

    # Verify that the document status was updated to available if a document object was provided
    assert mock_document.status == DocumentStatus.available

    # Verify that the result contains the expected data
    assert "document_path" in result
    assert "metadata" in result
    assert "chunks" in result
    assert "text_chunks" in result
    assert "token_counts" in result
    assert "embedding_ids" in result
    assert result["status"] == "success"


@patch("app.services.document_processor.is_pdf_file", return_value=False)
@patch("app.services.file_storage.FileStorage.get_full_path", return_value="/full/path/to/test_file.pdf")
def test_process_document_from_path_invalid_pdf(mock_get_full_path):
    """Tests processing an invalid PDF document from a file path"""
    # Create a mock Document object
    class MockDocument:
        def update_status(self, status):
            self.status = status

    mock_document = MockDocument()

    # Call process_document_from_path with a test file path and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        process_document_from_path("test_file.pdf", db_document=mock_document)

    # Verify that get_full_path was called with the file path
    mock_get_full_path.assert_called_once_with("test_file.pdf")

    # Verify that is_pdf_file was called with the full path
    # mock_is_pdf_file.assert_called_once_with("/full/path/to/test_file.pdf")

    # Verify that the document status was updated to error if a document object was provided
    assert mock_document.status == DocumentStatus.error
    assert exc_info.value.status_code == 400


def test_create_document_chunks():
    """Tests the creation of document chunks from text chunks"""
    # Create test text chunks and token counts
    text_chunks = ["Chunk 1", "Chunk 2", "Chunk 3"]
    token_counts = [10, 20, 15]

    # Create a test document ID
    document_id = uuid.uuid4()

    # Call create_document_chunks with the test data
    chunks = create_document_chunks(text_chunks, token_counts, document_id)

    # Verify that the correct number of chunks was created
    assert len(chunks) == 3

    # Verify that each chunk has the correct document ID, index, content, and token count
    for i, chunk in enumerate(chunks):
        assert chunk.document_id == document_id
        assert chunk.chunk_index == i
        assert chunk.content == text_chunks[i]
        assert chunk.token_count == token_counts[i]


@patch("app.services.document_processor.process_document")
def test_document_processor_process_document(mock_process_document):
    """Tests the process_document method of the DocumentProcessor class"""
    # Create a DocumentProcessor instance
    processor = DocumentProcessor()

    # Create mock document content, filename, and document object
    document_content = b"Mock PDF Content"
    filename = "test.pdf"
    mock_document = "Mock Document"

    # Call the process_document method on the DocumentProcessor instance
    processor.process_document(document_content, filename, db_document=mock_document)

    # Verify that the process_document function was called with the correct arguments including chunk settings
    mock_process_document.assert_called_once_with(
        document_content=document_content,
        filename=filename,
        db_document=mock_document,
        chunk_size=processor._chunk_size,
        chunk_overlap=processor._chunk_overlap,
    )


@patch("app.services.document_processor.process_document_from_path")
def test_document_processor_process_document_from_path(mock_process_document_from_path):
    """Tests the process_document_from_path method of the DocumentProcessor class"""
    # Create a DocumentProcessor instance
    processor = DocumentProcessor()

    # Create a test file path and document object
    file_path = "test_file.pdf"
    mock_document = "Mock Document"

    # Call the process_document_from_path method on the DocumentProcessor instance
    processor.process_document_from_path(file_path, db_document=mock_document)

    # Verify that the process_document_from_path function was called with the correct arguments including chunk settings
    mock_process_document_from_path.assert_called_once_with(
        file_path=file_path,
        db_document=mock_document,
        chunk_size=processor._chunk_size,
        chunk_overlap=processor._chunk_overlap,
    )


@patch("app.services.document_processor.process_document_from_path")
def test_document_processor_reprocess_document(mock_process_document_from_path):
    """Tests the reprocess_document method of the DocumentProcessor class"""
    # Create a DocumentProcessor instance
    processor = DocumentProcessor()

    # Create a mock Document object with a file path
    class MockDocument:
        id = uuid.uuid4()
        file_path = "test_file.pdf"

        def update_status(self, status):
            self.status = status

    mock_document = MockDocument()

    # Call the reprocess_document method on the DocumentProcessor instance
    processor.reprocess_document(mock_document)

    # Verify that the document status was updated to processing
    assert mock_document.status == DocumentStatus.processing

    # Verify that process_document_from_path was called with the document's file path
    mock_process_document_from_path.assert_called_once_with(
        file_path=mock_document.file_path,
        db_document=mock_document,
        chunk_size=processor._chunk_size,
        chunk_overlap=processor._chunk_overlap,
    )


@pytest.mark.asyncio
@patch("app.services.document_processor.is_pdf_file", return_value=True)
@patch("app.services.document_processor.extract_text_from_pdf_bytes", return_value="Sample text content")
@patch("app.services.document_processor.extract_pdf_metadata", return_value={"title": "Test Document"})
@patch("app.services.document_processor.chunk_text", return_value=["Chunk 1", "Chunk 2"])
@patch("app.services.document_processor.count_tokens", return_value=10)
@patch("app.services.document_processor.async_process_document_chunks", return_value=["embedding_id_1", "embedding_id_2"])
@patch("app.services.file_storage.FileStorage.store_document", return_value="test_file_path.pdf")
async def test_async_process_document(
    mock_store_document,
    mock_async_process_document_chunks,
    mock_count_tokens,
    mock_chunk_text,
    mock_extract_pdf_metadata,
    mock_extract_text_from_pdf_bytes,
    mock_is_pdf_file,
):
    """Tests the async_process_document function"""
    # Import async_process_document from document_processor
    from app.services.document_processor import async_process_document

    # Create mock document content and filename
    document_content = b"Mock PDF Content"
    filename = "test.pdf"

    # Create a mock Document object
    class MockDocument:
        id = uuid.uuid4()

        def update_status(self, status):
            self.status = status

    mock_document = MockDocument()

    # Call async_process_document with the test data
    result = await async_process_document(document_content, filename, db_document=mock_document)

    # Verify that is_pdf_file was called with the document content
    mock_is_pdf_file.assert_called_once_with(document_content)

    # Verify that store_document was called
    mock_store_document.assert_called_once_with(document_content, filename)

    # Verify that extract_text_from_pdf_bytes was called
    mock_extract_text_from_pdf_bytes.assert_called_once_with(document_content)

    # Verify that extract_pdf_metadata was called
    mock_extract_pdf_metadata.assert_called_once()

    # Verify that chunk_text was called
    mock_chunk_text.assert_called_once_with("Sample text content", None, None)

    # Verify that count_tokens was called
    assert mock_count_tokens.call_count == 2

    # Verify that async_process_document_chunks was called
    mock_async_process_document_chunks.assert_called_once()

    # Verify that the document status was updated to available
    assert mock_document.status == DocumentStatus.available

    # Verify that the result contains the expected data
    assert "document_path" in result
    assert "metadata" in result
    assert "chunks" in result
    assert "text_chunks" in result
    assert "token_counts" in result
    assert "embedding_ids" in result
    assert result["status"] == "success"


@pytest.mark.asyncio
@patch("app.services.document_processor.is_pdf_file", return_value=True)
@patch("app.services.document_processor.extract_text_from_pdf", return_value="Sample text content")
@patch("app.services.document_processor.extract_pdf_metadata", return_value={"title": "Test Document"})
@patch("app.services.document_processor.chunk_text", return_value=["Chunk 1", "Chunk 2"])
@patch("app.services.document_processor.count_tokens", return_value=10)
@patch("app.services.document_processor.async_process_document_chunks", return_value=["embedding_id_1", "embedding_id_2"])
@patch("app.services.file_storage.FileStorage.get_full_path", return_value="/full/path/to/test_file.pdf")
async def test_async_process_document_from_path(
    mock_get_full_path,
    mock_async_process_document_chunks,
    mock_count_tokens,
    mock_chunk_text,
    mock_extract_pdf_metadata,
    mock_extract_text_from_pdf,
    mock_is_pdf_file,
    sample_pdf_path,
):
    """Tests the async_process_document_from_path function"""
    # Import async_process_document_from_path from document_processor
    from app.services.document_processor import async_process_document_from_path

    # Create a mock Document object
    class MockDocument:
        id = uuid.uuid4()

        def update_status(self, status):
            self.status = status

    mock_document = MockDocument()

    # Call async_process_document_from_path with the sample PDF path
    result = await async_process_document_from_path(sample_pdf_path, db_document=mock_document)

    # Verify that get_full_path was called
    mock_get_full_path.assert_called_once_with(sample_pdf_path)

    # Verify that is_pdf_file was called
    mock_is_pdf_file.assert_called_once_with("/full/path/to/test_file.pdf")

    # Verify that extract_text_from_pdf was called
    mock_extract_text_from_pdf.assert_called_once_with("/full/path/to/test_file.pdf")

    # Verify that extract_pdf_metadata was called
    mock_extract_pdf_metadata.assert_called_once_with("/full/path/to/test_file.pdf")

    # Verify that chunk_text was called
    mock_chunk_text.assert_called_once_with("Sample text content", None, None)

    # Verify that count_tokens was called
    assert mock_count_tokens.call_count == 2

    # Verify that async_process_document_chunks was called
    mock_async_process_document_chunks.assert_called_once()

    # Verify that the document status was updated to available
    assert mock_document.status == DocumentStatus.available

    # Verify that the result contains the expected data
    assert "document_path" in result
    assert "metadata" in result
    assert "chunks" in result
    assert "text_chunks" in result
    assert "token_counts" in result
    assert "embedding_ids" in result
    assert result["status"] == "success"


@pytest.mark.asyncio
@patch("app.services.document_processor.async_process_document")
@patch("app.services.document_processor.async_process_document_from_path")
async def test_document_processor_async_methods(mock_async_process_document_from_path, mock_async_process_document):
    """Tests the async methods of the DocumentProcessor class"""
    # Create a DocumentProcessor instance
    processor = DocumentProcessor()

    # Create mock document content, filename, and document object
    document_content = b"Mock PDF Content"
    filename = "test.pdf"
    mock_document = "Mock Document"

    # Call the async_process_document method on the DocumentProcessor instance
    await processor.async_process_document(document_content, filename, db_document=mock_document)

    # Verify that async_process_document was called with the correct arguments
    mock_async_process_document.assert_called_once_with(
        document_content=document_content,
        filename=filename,
        db_document=mock_document,
        chunk_size=processor._chunk_size,
        chunk_overlap=processor._chunk_overlap,
    )

    # Create a test file path and document object
    file_path = "test_file.pdf"
    mock_document = "Mock Document"

    # Call the async_process_document_from_path method on the DocumentProcessor instance
    await processor.async_process_document_from_path(file_path, db_document=mock_document)

    # Verify that async_process_document_from_path was called with the correct arguments
    mock_async_process_document_from_path.assert_called_once_with(
        file_path=file_path,
        db_document=mock_document,
        chunk_size=processor._chunk_size,
        chunk_overlap=processor._chunk_overlap,
    )

    # Create a mock Document object with a file path
    class MockDocument:
        id = uuid.uuid4()
        file_path = "test_file.pdf"

        def update_status(self, status):
            self.status = status

    mock_document = MockDocument()

    # Call the async_reprocess_document method on the DocumentProcessor instance
    await processor.async_reprocess_document(mock_document)

    # Verify that the document status was updated to processing
    assert mock_document.status == DocumentStatus.processing

    # Verify that async_process_document_from_path was called with the document's file path
    mock_async_process_document_from_path.assert_called_called()


@pytest.mark.skipif(not os.path.exists("test_sample.pdf"), reason="Sample PDF file not found")
@patch("app.services.document_processor.process_document_chunks", return_value=["embedding_id_1", "embedding_id_2"])
def test_integration_with_real_pdf(mock_process_document_chunks, sample_pdf_path):
    """Integration test with a real PDF file"""
    # Skip this test if the sample PDF file doesn't exist
    if not os.path.exists(sample_pdf_path):
        pytest.skip(f"Sample PDF file not found at: {sample_pdf_path}")

    # Read the sample PDF file content
    with open(sample_pdf_path, "rb") as f:
        pdf_content = f.read()

    # Create a DocumentProcessor instance
    processor = DocumentProcessor()

    # Process the real PDF document
    result = processor.process_document(pdf_content, "real_test_document.pdf")

    # Verify that the result contains expected fields (file_path, metadata, chunks)
    assert "document_path" in result
    assert "metadata" in result
    assert "chunks" in result

    # Verify that text was extracted from the PDF
    assert result["text_chunks"] is not None

    # Verify that chunks were created
    assert len(result["chunks"]) > 0

    # Verify that each chunk has an embedding ID
    for chunk in result["chunks"]:
        assert chunk.embedding_id is not None