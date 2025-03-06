# Standard library imports
import os  # Operating system interfaces
import tempfile  # Generate temporary files and directories
import uuid  # Generate unique identifiers

# Third-party imports
import pytest  # Testing framework
import numpy as np  # Numerical operations for vector manipulation

# Internal module imports
from src.backend.app.vector_store.faiss_store import FAISSStore  # Import the FAISS vector store implementation
from src.backend.app.utils.vector_utils import normalize_vector  # Import utility function to normalize vectors
from src.backend.app.utils.vector_utils import validate_vector_dimensions  # Import utility function to validate vector dimensions
from src.backend.app.services.embedding_service import generate_embedding  # Import function to generate vector embeddings
from src.backend.app.services.vector_search import search_by_vector  # Import function to search for similar vectors
from src.backend.tests.conftest import sample_vector_embeddings  # Import fixture for sample vector embeddings

# Define a constant for the test vector dimension
TEST_VECTOR_DIMENSION = 768

@pytest.mark.integration
def test_faiss_store_initialization():
    """Tests that the FAISSStore initializes correctly"""
    # Create a FAISSStore instance
    faiss_store = FAISSStore(vector_dimension=TEST_VECTOR_DIMENSION)

    # Verify that the store is initialized with the correct vector dimension
    assert faiss_store.vector_dimension == TEST_VECTOR_DIMENSION

    # Verify that the store is empty (count returns 0)
    assert faiss_store.count() == 0

    # Verify that the index is properly created
    assert faiss_store._index is not None

@pytest.mark.integration
def test_add_vectors():
    """Tests adding vectors to the FAISS store"""
    # Create a FAISSStore instance
    faiss_store = FAISSStore(vector_dimension=TEST_VECTOR_DIMENSION)

    # Create test vectors with numpy
    num_vectors = 5
    test_vectors = [np.random.rand(TEST_VECTOR_DIMENSION).astype(np.float32) for _ in range(num_vectors)]

    # Generate unique IDs for the vectors
    test_ids = [str(uuid.uuid4()) for _ in range(num_vectors)]

    # Add vectors to the store
    success = faiss_store.add_vectors(test_vectors, test_ids)
    assert success is True

    # Verify that the vectors were added (count returns correct number)
    assert faiss_store.count() == num_vectors

    # Verify that the store contains the added vector IDs
    for test_id in test_ids:
        assert faiss_store.contains(test_id)

@pytest.mark.integration
def test_search_vectors(sample_vector_embeddings: dict):
    """Tests searching for similar vectors in the FAISS store"""
    # Create a FAISSStore instance
    faiss_store = FAISSStore(vector_dimension=TEST_VECTOR_DIMENSION)

    # Extract vectors and IDs from sample_vector_embeddings
    test_vectors = sample_vector_embeddings["vectors"]
    test_ids = sample_vector_embeddings["ids"]

    # Add vectors to the store
    success = faiss_store.add_vectors(test_vectors, test_ids)
    assert success is True

    # Create a query vector similar to one of the added vectors
    query_vector = test_vectors[0]

    # Search for similar vectors
    results = faiss_store.search(query_vector, top_k=3)

    # Verify that the search returns the expected results
    assert len(results) > 0
    assert results[0]["id"] == test_ids[0]

    # Verify that the similarity scores are within expected range
    assert 0 <= results[0]["score"] <= 1

    # Test search with different top_k values
    results_top_k = faiss_store.search(query_vector, top_k=1)
    assert len(results_top_k) == 1

    # Test search with similarity threshold
    results_threshold = faiss_store.search(query_vector, threshold=0.9)
    assert all(result["score"] >= 0.9 for result in results_threshold)

@pytest.mark.integration
def test_get_vector():
    """Tests retrieving a vector from the FAISS store by ID"""
    # Create a FAISSStore instance
    faiss_store = FAISSStore(vector_dimension=TEST_VECTOR_DIMENSION)

    # Create test vectors with numpy
    num_vectors = 3
    test_vectors = [np.random.rand(TEST_VECTOR_DIMENSION).astype(np.float32) for _ in range(num_vectors)]

    # Generate unique IDs for the vectors
    test_ids = [str(uuid.uuid4()) for _ in range(num_vectors)]

    # Add vectors to the store
    success = faiss_store.add_vectors(test_vectors, test_ids)
    assert success is True

    # Retrieve a vector by ID
    retrieved_vector = faiss_store.get_vector(test_ids[0])

    # Verify that the retrieved vector matches the original
    assert np.allclose(retrieved_vector, test_vectors[0])

    # Test retrieving a non-existent vector ID
    non_existent_vector = faiss_store.get_vector("non_existent_id")
    assert non_existent_vector is None

@pytest.mark.integration
def test_delete_vectors():
    """Tests deleting vectors from the FAISS store"""
    # Create a FAISSStore instance
    faiss_store = FAISSStore(vector_dimension=TEST_VECTOR_DIMENSION)

    # Create test vectors with numpy
    num_vectors = 5
    test_vectors = [np.random.rand(TEST_VECTOR_DIMENSION).astype(np.float32) for _ in range(num_vectors)]

    # Generate unique IDs for the vectors
    test_ids = [str(uuid.uuid4()) for _ in range(num_vectors)]

    # Add vectors to the store
    success = faiss_store.add_vectors(test_vectors, test_ids)
    assert success is True

    # Delete one of the vectors
    deleted_id = test_ids[0]
    success = faiss_store.delete_vectors([deleted_id])
    assert success is True

    # Verify that the vector was deleted (count decreases)
    assert faiss_store.count() == num_vectors - 1

    # Verify that the store no longer contains the deleted vector ID
    assert not faiss_store.contains(deleted_id)

    # Verify that other vectors are still accessible
    for test_id in test_ids[1:]:
        assert faiss_store.contains(test_id)

    # Test deleting multiple vectors at once
    ids_to_delete = test_ids[1:3]
    success = faiss_store.delete_vectors(ids_to_delete)
    assert success is True
    assert faiss_store.count() == num_vectors - 3
    for id_val in ids_to_delete:
        assert not faiss_store.contains(id_val)

    # Test deleting a non-existent vector ID
    success = faiss_store.delete_vectors(["non_existent_id"])
    assert success is False

@pytest.mark.integration
def test_save_and_load():
    """Tests saving and loading the FAISS index to/from disk"""
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a FAISSStore instance
        faiss_store = FAISSStore(index_path=temp_dir, vector_dimension=TEST_VECTOR_DIMENSION)

        # Create test vectors with numpy
        num_vectors = 3
        test_vectors = [np.random.rand(TEST_VECTOR_DIMENSION).astype(np.float32) for _ in range(num_vectors)]

        # Generate unique IDs for the vectors
        test_ids = [str(uuid.uuid4()) for _ in range(num_vectors)]

        # Add vectors to the store
        success = faiss_store.add_vectors(test_vectors, test_ids)
        assert success is True

        # Save the index to the temporary directory
        success = faiss_store.save()
        assert success is True

        # Create a new FAISSStore instance
        new_faiss_store = FAISSStore(index_path=temp_dir, vector_dimension=TEST_VECTOR_DIMENSION)

        # Load the index from the temporary directory
        success = new_faiss_store.load()
        assert success is True

        # Verify that the loaded store has the same count as the original
        assert new_faiss_store.count() == num_vectors

        # Verify that the loaded store contains the same vector IDs
        for test_id in test_ids:
            assert new_faiss_store.contains(test_id)

        # Verify that the vectors can be retrieved and are the same as the originals
        for i, test_id in enumerate(test_ids):
            retrieved_vector = new_faiss_store.get_vector(test_id)
            assert np.allclose(retrieved_vector, test_vectors[i])

@pytest.mark.integration
def test_clear():
    """Tests clearing all vectors from the FAISS store"""
    # Create a FAISSStore instance
    faiss_store = FAISSStore(vector_dimension=TEST_VECTOR_DIMENSION)

    # Create test vectors with numpy
    num_vectors = 3
    test_vectors = [np.random.rand(TEST_VECTOR_DIMENSION).astype(np.float32) for _ in range(num_vectors)]

    # Generate unique IDs for the vectors
    test_ids = [str(uuid.uuid4()) for _ in range(num_vectors)]

    # Add vectors to the store
    success = faiss_store.add_vectors(test_vectors, test_ids)
    assert success is True

    # Verify that vectors were added (count > 0)
    assert faiss_store.count() > 0

    # Clear the store
    success = faiss_store.clear()
    assert success is True

    # Verify that the store is empty (count = 0)
    assert faiss_store.count() == 0

    # Verify that previously added vector IDs are no longer present
    for test_id in test_ids:
        assert not faiss_store.contains(test_id)

@pytest.mark.integration
def test_integration_with_embedding_service():
    """Tests integration between FAISSStore and embedding service"""
    # Create a FAISSStore instance
    faiss_store = FAISSStore(vector_dimension=TEST_VECTOR_DIMENSION)

    # Generate embeddings for test text using generate_embedding function
    test_text = "This is a test document for vector search."
    test_embedding = generate_embedding(test_text)

    # Add the embeddings to the store
    test_id = str(uuid.uuid4())
    success = faiss_store.add_vectors([test_embedding], [test_id])
    assert success is True

    # Generate a similar query embedding
    query_text = "vector search test"
    query_embedding = generate_embedding(query_text)

    # Search for similar vectors
    results = faiss_store.search(query_embedding, top_k=1)

    # Verify that the search returns the expected results
    assert len(results) == 1
    assert results[0]["id"] == test_id

@pytest.mark.integration
def test_integration_with_vector_search(sample_vector_embeddings: dict):
    """Tests integration between FAISSStore and vector search service"""
    # Create a FAISSStore instance
    faiss_store = FAISSStore(vector_dimension=TEST_VECTOR_DIMENSION)

    # Extract vectors and IDs from sample_vector_embeddings
    test_vectors = sample_vector_embeddings["vectors"]
    test_ids = sample_vector_embeddings["ids"]

    # Add vectors to the store
    success = faiss_store.add_vectors(test_vectors, test_ids)
    assert success is True

    # Create a mock database session
    class MockSession:
        def __init__(self):
            self.data = {}

        def execute(self, statement):
            class MockResult:
                def scalars(self):
                    class MockScalarResult:
                        def first(self):
                            return None
                    return MockScalarResult()
            return MockResult()

    mock_db_session = MockSession()

    # Create a query vector
    query_vector = test_vectors[0]

    # Use search_by_vector function to search for similar vectors
    results = search_by_vector(query_vector, mock_db_session)

    # Verify that the search returns the expected results
    assert isinstance(results, list)

@pytest.mark.integration
def test_vector_normalization():
    """Tests that vectors are properly normalized in the FAISS store"""
    # Create a FAISSStore instance
    faiss_store = FAISSStore(vector_dimension=TEST_VECTOR_DIMENSION)

    # Create a test vector with numpy
    vector1 = np.random.rand(TEST_VECTOR_DIMENSION).astype(np.float32)

    # Create the same vector but with different magnitude
    vector2 = vector1 * 2

    # Add both vectors to the store
    id1 = str(uuid.uuid4())
    id2 = str(uuid.uuid4())
    success = faiss_store.add_vectors([vector1, vector2], [id1, id2])
    assert success is True

    # Search using a third vector similar to the first two
    query_vector = normalize_vector(vector1 + (np.random.rand(TEST_VECTOR_DIMENSION) * 0.1))
    results = faiss_store.search(query_vector, top_k=2)

    # Verify that both vectors are found with similar similarity scores despite different magnitudes
    assert len(results) == 2
    assert results[0]["id"] == id1 or results[0]["id"] == id2
    assert results[1]["id"] == id1 or results[1]["id"] == id2
    assert abs(results[0]["score"] - results[1]["score"]) < 0.1

@pytest.mark.integration
@pytest.mark.slow
def test_large_vector_collection():
    """Tests FAISS performance with a larger collection of vectors"""
    # Create a FAISSStore instance
    faiss_store = FAISSStore(vector_dimension=TEST_VECTOR_DIMENSION)

    # Generate a large number of random vectors (e.g., 1000)
    num_vectors = 1000
    test_vectors = [np.random.rand(TEST_VECTOR_DIMENSION).astype(np.float32) for _ in range(num_vectors)]

    # Generate unique IDs for the vectors
    test_ids = [str(uuid.uuid4()) for _ in range(num_vectors)]

    # Add vectors to the store in batches
    batch_size = 100
    for i in range(0, num_vectors, batch_size):
        batch_vectors = test_vectors[i:i + batch_size]
        batch_ids = test_ids[i:i + batch_size]
        success = faiss_store.add_vectors(batch_vectors, batch_ids)
        assert success is True

    # Verify that all vectors were added (count matches)
    assert faiss_store.count() == num_vectors

    # Perform multiple search operations
    num_searches = 10
    search_times = []
    for _ in range(num_searches):
        query_vector = np.random.rand(TEST_VECTOR_DIMENSION).astype(np.float32)
        start_time = time.time()
        faiss_store.search(query_vector, top_k=10)
        search_time = time.time() - start_time
        search_times.append(search_time)

    # Verify search performance is within acceptable limits
    average_search_time = sum(search_times) / num_searches
    assert average_search_time < 0.1  # Adjust threshold as needed

@pytest.mark.integration
class TestFAISSIntegration:
    """Test class for FAISS integration tests"""
    def setup_method(self, method):
        """Set up method that runs before each test"""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()

        # Initialize a FAISSStore instance with the temporary directory
        self.faiss_store = FAISSStore(index_path=self.temp_dir, vector_dimension=TEST_VECTOR_DIMENSION)

        # Create sample vectors and IDs for testing
        self.sample_vectors = [np.random.rand(TEST_VECTOR_DIMENSION).astype(np.float32) for _ in range(3)]
        self.sample_ids = [str(uuid.uuid4()) for _ in range(3)]

    def teardown_method(self, method):
        """Tear down method that runs after each test"""
        # Clean up the temporary directory
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

        # Reset the FAISSStore instance
        self.faiss_store = None

    def test_add_and_search(self):
        """Tests adding vectors and searching for similar ones"""
        # Add sample vectors to the store
        success = self.faiss_store.add_vectors(self.sample_vectors, self.sample_ids)
        assert success is True

        # Search for similar vectors
        query_vector = self.sample_vectors[0]
        results = self.faiss_store.search(query_vector, top_k=1)

        # Verify search results
        assert len(results) == 1
        assert results[0]["id"] == self.sample_ids[0]

    def test_delete_and_contains(self):
        """Tests deleting vectors and checking if they exist"""
        # Add sample vectors to the store
        success = self.faiss_store.add_vectors(self.sample_vectors, self.sample_ids)
        assert success is True

        # Verify vectors exist using contains method
        for sample_id in self.sample_ids:
            assert self.faiss_store.contains(sample_id)

        # Delete vectors
        success = self.faiss_store.delete_vectors(self.sample_ids)
        assert success is True

        # Verify vectors no longer exist
        for sample_id in self.sample_ids:
            assert not self.faiss_store.contains(sample_id)

    def test_save_and_load(self):
        """Tests saving and loading the index"""
        # Add sample vectors to the store
        success = self.faiss_store.add_vectors(self.sample_vectors, self.sample_ids)
        assert success is True

        # Save the index
        success = self.faiss_store.save()
        assert success is True

        # Create a new store instance
        new_faiss_store = FAISSStore(index_path=self.temp_dir, vector_dimension=TEST_VECTOR_DIMENSION)

        # Load the index
        success = new_faiss_store.load()
        assert success is True

        # Verify loaded index contains the same vectors
        for sample_id in self.sample_ids:
            assert new_faiss_store.contains(sample_id)