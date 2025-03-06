import pytest  # pytest 7.0.0+
import numpy as np  # numpy 1.24.0+
import uuid  # standard library
import base64  # standard library

from src.backend.app.utils.vector_utils import normalize_vector, validate_vector_dimensions, calculate_similarity, serialize_vector, deserialize_vector, generate_embedding_id, batch_normalize_vectors, convert_to_numpy_array, combine_vectors  # internal
from src.backend.tests.conftest import sample_vector_embeddings  # internal
from src.backend.app.core.settings import VECTOR_DIMENSION  # internal


@pytest.mark.parametrize("vector, expected_norm", [
    (np.array([3, 4]), 1.0),
    (np.array([1, 0, 0]), 1.0),
    (np.array([1, 1, 1, 1]), 1.0)
])
def test_normalize_vector(vector, expected_norm):
    """Tests that the normalize_vector function correctly normalizes vectors to unit length"""
    # Create test vectors with known magnitudes
    # Apply normalize_vector function to each test vector
    normalized_vector = normalize_vector(vector)
    # Calculate the L2 norm of the normalized vector
    norm = np.linalg.norm(normalized_vector)
    # Assert that the norm is approximately 1.0 (unit length)
    assert norm == pytest.approx(expected_norm)


def test_normalize_vector_zero():
    """Tests that the normalize_vector function handles zero vectors correctly"""
    # Create a zero vector
    zero_vector = np.array([0, 0, 0])
    # Apply normalize_vector function to the zero vector
    normalized_vector = normalize_vector(zero_vector)
    # Assert that the result is a zero vector with the same shape
    assert np.array_equal(normalized_vector, zero_vector)


def test_validate_vector_dimensions():
    """Tests that the validate_vector_dimensions function correctly validates vector dimensions"""
    # Create vectors with different dimensions
    valid_vector = np.array([1] * VECTOR_DIMENSION)
    invalid_vector = np.array([1, 2, 3])
    # Test validation with explicit expected dimension
    assert validate_vector_dimensions(valid_vector, VECTOR_DIMENSION) is True
    assert validate_vector_dimensions(invalid_vector, VECTOR_DIMENSION) is False
    # Test validation with default dimension from settings
    assert validate_vector_dimensions(valid_vector) is True
    # Assert that valid dimensions return True
    # Assert that invalid dimensions return False
    assert validate_vector_dimensions(np.array([1] * 100), 100) is True
    # Test that None vector returns False
    assert validate_vector_dimensions(None) is False


@pytest.mark.parametrize("vector_a, vector_b, expected_similarity", [
    (np.array([1, 0, 0]), np.array([1, 0, 0]), 1.0),
    (np.array([1, 0, 0]), np.array([0, 1, 0]), 0.0),
    (np.array([1, 1, 0]), np.array([1, 0, 0]), 0.7071),
    (np.array([1, 2, 3]), np.array([4, 5, 6]), 0.9746)
])
def test_calculate_similarity(vector_a, vector_b, expected_similarity):
    """Tests that the calculate_similarity function correctly calculates cosine similarity between vectors"""
    # Create pairs of test vectors with known similarity values
    # Calculate similarity using calculate_similarity function
    similarity = calculate_similarity(vector_a, vector_b)
    # Assert that the calculated similarity is approximately equal to the expected value
    assert similarity == pytest.approx(expected_similarity, abs=1e-4)


def test_generate_embedding_id():
    """Tests that the generate_embedding_id function creates valid unique identifiers"""
    # Generate multiple embedding IDs
    id1 = generate_embedding_id()
    id2 = generate_embedding_id()
    # Assert that each ID is a string
    assert isinstance(id1, str)
    assert isinstance(id2, str)
    # Verify that the IDs are valid UUIDs
    uuid.UUID(id1)
    uuid.UUID(id2)
    # Assert that multiple calls generate different IDs
    assert id1 != id2


def test_serialize_deserialize_vector():
    """Tests that vectors can be serialized and deserialized correctly"""
    # Create test vectors with different dimensions
    vector = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    # Serialize each vector using serialize_vector
    serialized_vector = serialize_vector(vector)
    # Assert that the serialized result is a string
    assert isinstance(serialized_vector, str)
    # Deserialize the string back to a vector using deserialize_vector
    deserialized_vector = deserialize_vector(serialized_vector)
    # Assert that the deserialized vector is equal to the original vector
    assert np.allclose(vector, deserialized_vector)


def test_batch_normalize_vectors():
    """Tests that the batch_normalize_vectors function correctly normalizes multiple vectors"""
    # Create a list of test vectors
    vectors = [np.array([3, 4]), np.array([1, 0, 0]), np.array([1, 1, 1, 1])]
    # Apply batch_normalize_vectors function to the list
    normalized_vectors = batch_normalize_vectors(vectors)
    # Assert that the result is a list of the same length
    assert len(normalized_vectors) == len(vectors)
    # Assert that each vector in the result is normalized (has unit length)
    for vector in normalized_vectors:
        assert np.linalg.norm(vector) == pytest.approx(1.0)
    # Test with empty list and verify appropriate handling
    assert batch_normalize_vectors([]) == []


@pytest.mark.parametrize("input_data, expected_shape", [
    ([1, 2, 3], (3,)),
    ([[1, 2, 3]], (1, 3)),
    (np.array([1, 2, 3]), (3,)),
    (np.array([[1, 2, 3]]), (1, 3))
])
def test_convert_to_numpy_array(input_data, expected_shape):
    """Tests that the convert_to_numpy_array function correctly converts different input types to numpy arrays"""
    # Test with different input types: list, tuple, numpy array
    # Test with different shapes: 1D, 2D
    # Apply convert_to_numpy_array to each input
    result = convert_to_numpy_array(input_data)
    # Assert that the result is a numpy array with the expected shape and dtype
    assert isinstance(result, np.ndarray)
    assert result.shape == expected_shape
    assert result.dtype == np.float32


@pytest.mark.parametrize("method, expected_result", [
    ('mean', np.array([0.5, 0.5, 0.5])),
    ('max', np.array([1, 1, 1])),
    ('sum', np.array([1, 1, 1]))
])
def test_combine_vectors(method, expected_result):
    """Tests that the combine_vectors function correctly combines multiple vectors using different methods"""
    # Create a list of test vectors
    vectors = [np.array([0, 0, 0]), np.array([1, 1, 1])]
    # Apply combine_vectors with different methods (mean, max, sum)
    combined_vector = combine_vectors(vectors, method=method)
    # Assert that the result has the expected values for each method
    assert np.allclose(combined_vector, normalize_vector(expected_result))


def test_with_sample_embeddings(sample_vector_embeddings):
    """Tests vector utility functions with real sample embeddings from fixtures"""
    # Extract sample embeddings from the fixture
    vector1 = sample_vector_embeddings[0]
    vector2 = sample_vector_embeddings[1]
    # Test normalize_vector with sample embeddings
    normalized_vector1 = normalize_vector(vector1)
    assert np.linalg.norm(normalized_vector1) == pytest.approx(1.0)
    # Test calculate_similarity between sample embeddings
    similarity = calculate_similarity(vector1, vector2)
    assert isinstance(similarity, float)
    # Test serialize_deserialize_vector with sample embeddings
    serialized_vector = serialize_vector(vector1)
    deserialized_vector = deserialize_vector(serialized_vector)
    assert np.allclose(vector1, deserialized_vector)
    # Assert that all operations produce expected results with real-world data