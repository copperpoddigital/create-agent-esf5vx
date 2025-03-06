#!/usr/bin/env python3
"""
Benchmark script for vector search operations in the Document Management and AI Chatbot System.

This script measures and reports on the efficiency, accuracy, and scalability of the
FAISS vector search implementation under various conditions and workloads.
"""

import numpy as np  # version 1.24.0+
import time
import argparse
import logging
import matplotlib.pyplot as plt  # version 3.7.0+
import pandas as pd  # version 2.0.0+
from tqdm import tqdm  # version 4.65.0+
import os
import json
import sys
import platform
from typing import List, Dict, Any, Optional

# Import from our application
from ..app.vector_store.faiss_store import FAISSStore
from ..app.services.vector_search import VectorSearchService
from ..app.services.embedding_service import generate_embedding
from ..app.utils.vector_utils import normalize_vector, calculate_similarity
from ..app.core.settings import VectorSearchSettings

# Set up logger
logger = logging.getLogger(__name__)

# Define results directory
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '../../benchmark_results')

class BenchmarkConfig:
    """Configuration class for benchmark parameters"""
    
    def __init__(self, config_dict: Optional[dict] = None):
        """
        Initialize benchmark configuration with default or provided values
        
        Args:
            config_dict: Optional dictionary with configuration values
        """
        # Default configuration values
        self.num_vectors = 10000
        self.dimension = VectorSearchSettings.VECTOR_DIMENSION
        self.num_queries = 10
        self.num_runs = 5
        self.top_k = 5
        self.threshold = 0.7
        self.output_dir = RESULTS_DIR
        self.index_types = ["Flat", "IVFFlat", "HNSW"]
        self.batch_size = 1000
        self.nlist_values = [50, 100, 200]
        self.nprobe_values = [1, 5, 10, 20]
        self.scale_vector_counts = [100, 1000, 10000, 100000]
        
        # Override defaults with provided values
        if config_dict:
            for key, value in config_dict.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        
        # Validate configuration
        self.validate()
    
    def to_dict(self) -> dict:
        """
        Converts configuration to a dictionary
        
        Returns:
            Dictionary representation of the configuration
        """
        return {
            "num_vectors": self.num_vectors,
            "dimension": self.dimension,
            "num_queries": self.num_queries,
            "num_runs": self.num_runs,
            "top_k": self.top_k,
            "threshold": self.threshold,
            "output_dir": self.output_dir,
            "index_types": self.index_types,
            "batch_size": self.batch_size,
            "nlist_values": self.nlist_values,
            "nprobe_values": self.nprobe_values,
            "scale_vector_counts": self.scale_vector_counts
        }
    
    @classmethod
    def from_args(cls, args: argparse.Namespace) -> 'BenchmarkConfig':
        """
        Creates configuration from command-line arguments
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            Configuration object
        """
        config_dict = {
            "num_vectors": args.num_vectors,
            "dimension": args.dimension,
            "num_queries": args.num_queries,
            "num_runs": args.num_runs,
            "top_k": args.top_k,
            "threshold": args.threshold,
            "output_dir": args.output_dir,
            "index_types": args.index_types.split(","),
            "batch_size": args.batch_size
        }
        return cls(config_dict)
    
    def validate(self) -> bool:
        """
        Validates configuration values
        
        Returns:
            True if configuration is valid
        """
        # Check that numeric values are positive
        assert self.num_vectors > 0, "Number of vectors must be positive"
        assert self.dimension > 0, "Vector dimension must be positive"
        assert self.num_queries > 0, "Number of queries must be positive"
        assert self.num_runs > 0, "Number of runs must be positive"
        assert self.top_k > 0, "Top-k must be positive"
        assert self.batch_size > 0, "Batch size must be positive"
        
        # Check that threshold is between 0 and 1
        assert 0 <= self.threshold <= 1, "Threshold must be between 0 and 1"
        
        # Check that lists are not empty
        assert self.index_types, "Index types list cannot be empty"
        assert self.nlist_values, "nlist values list cannot be empty"
        assert self.nprobe_values, "nprobe values list cannot be empty"
        assert self.scale_vector_counts, "Scale vector counts list cannot be empty"
        
        return True

# Mock database session for testing
class MockSession:
    """Mock database session for testing the VectorSearchService"""
    
    def __init__(self):
        """Initialize the mock session"""
        pass
    
    def query(self):
        """
        Mock query method that returns a query object
        
        Returns:
            Self for method chaining
        """
        return self
    
    def filter(self, condition):
        """
        Mock filter method
        
        Args:
            condition: Any filter condition
            
        Returns:
            Self for method chaining
        """
        return self
    
    def all(self):
        """
        Mock all method that returns an empty list
        
        Returns:
            Empty list
        """
        return []

def setup_logging(verbose: bool):
    """
    Configures logging for the benchmark script
    
    Args:
        verbose: Whether to enable verbose logging
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(level=log_level, format=log_format)
    
    # Set up file handler for saving logs
    os.makedirs(RESULTS_DIR, exist_ok=True)
    file_handler = logging.FileHandler(os.path.join(RESULTS_DIR, "benchmark.log"))
    file_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(file_handler)

def generate_random_vectors(num_vectors: int, dimension: int) -> List[np.ndarray]:
    """
    Generates random vectors for benchmark testing
    
    Args:
        num_vectors: Number of vectors to generate
        dimension: Dimension of each vector
        
    Returns:
        List of random vectors
    """
    # Generate random vectors
    vectors = []
    for _ in range(num_vectors):
        # Generate random vector and normalize
        vector = np.random.rand(dimension).astype(np.float32)
        vector = normalize_vector(vector)
        vectors.append(vector)
    
    return vectors

def generate_test_queries(query_texts: List[str]) -> List[np.ndarray]:
    """
    Generates test queries for benchmarking
    
    Args:
        query_texts: List of query text strings
        
    Returns:
        List of query vector embeddings
    """
    # Generate embeddings for query texts
    query_vectors = []
    for text in query_texts:
        vector = generate_embedding(text)
        query_vectors.append(vector)
    
    return query_vectors

def benchmark_vector_addition(
    vector_store: FAISSStore,
    vectors: List[np.ndarray],
    ids: List[str],
    batch_size: int
) -> dict:
    """
    Benchmarks the performance of adding vectors to the FAISS index
    
    Args:
        vector_store: FAISS vector store instance
        vectors: List of vectors to add
        ids: List of vector IDs
        batch_size: Size of batches for adding vectors
        
    Returns:
        Dictionary with benchmark results
    """
    results = {
        "total_time": 0.0,
        "vectors_per_second": 0.0,
        "batch_times": []
    }
    
    start_time = time.time()
    
    # Process vectors in batches
    for i in range(0, len(vectors), batch_size):
        batch_start = time.time()
        batch_vectors = vectors[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        # Add vectors to FAISS index
        vector_store.add_vectors(batch_vectors, batch_ids)
        
        batch_time = time.time() - batch_start
        results["batch_times"].append(batch_time)
    
    total_time = time.time() - start_time
    vectors_per_second = len(vectors) / total_time
    
    results["total_time"] = total_time
    results["vectors_per_second"] = vectors_per_second
    
    logger.info(f"Added {len(vectors)} vectors in {total_time:.2f}s ({vectors_per_second:.2f} vectors/s)")
    
    return results

def benchmark_vector_search(
    vector_store: FAISSStore,
    query_vectors: List[np.ndarray],
    top_k: int,
    threshold: float,
    num_runs: int
) -> dict:
    """
    Benchmarks the performance of vector similarity search
    
    Args:
        vector_store: FAISS vector store instance
        query_vectors: List of query vectors
        top_k: Number of results to return
        threshold: Similarity threshold
        num_runs: Number of times to run each query
        
    Returns:
        Dictionary with benchmark results
    """
    results = {
        "search_times": [],
        "avg_search_time": 0.0,
        "result_counts": []
    }
    
    # Run searches for each query vector
    for query_vector in query_vectors:
        query_times = []
        
        # Run each query multiple times
        for _ in range(num_runs):
            start_time = time.time()
            
            # Perform search
            search_results = vector_store.search(query_vector, top_k, threshold)
            
            search_time = time.time() - start_time
            query_times.append(search_time)
            
            # Record number of results
            results["result_counts"].append(len(search_results))
        
        # Average search time for this query
        avg_query_time = sum(query_times) / len(query_times)
        results["search_times"].append(avg_query_time)
    
    # Calculate overall average search time
    results["avg_search_time"] = sum(results["search_times"]) / len(results["search_times"])
    
    logger.info(f"Average search time: {results['avg_search_time']:.4f}s")
    
    return results

def benchmark_service_search(
    search_service: VectorSearchService,
    query_texts: List[str],
    top_k: int,
    threshold: float,
    num_runs: int
) -> dict:
    """
    Benchmarks the performance of the VectorSearchService
    
    Args:
        search_service: Vector search service instance
        query_texts: List of query text strings
        top_k: Number of results to return
        threshold: Similarity threshold
        num_runs: Number of times to run each query
        
    Returns:
        Dictionary with benchmark results
    """
    results = {
        "search_times": [],
        "avg_search_time": 0.0,
        "result_counts": []
    }
    
    # Create a mock session for testing
    mock_session = MockSession()
    
    # Run searches for each query
    for query_text in query_texts:
        query_times = []
        
        # Run each query multiple times
        for _ in range(num_runs):
            start_time = time.time()
            
            # Perform search using the service
            search_results = search_service.search(query_text, mock_session, top_k, threshold)
            
            search_time = time.time() - start_time
            query_times.append(search_time)
            
            # Record number of results
            results["result_counts"].append(len(search_results))
        
        # Average search time for this query
        avg_query_time = sum(query_times) / len(query_times)
        results["search_times"].append(avg_query_time)
    
    # Calculate overall average search time
    results["avg_search_time"] = sum(results["search_times"]) / len(results["search_times"])
    
    logger.info(f"Average service search time: {results['avg_search_time']:.4f}s")
    
    return results

def benchmark_index_types(
    index_types: List[str],
    vectors: List[np.ndarray],
    ids: List[str],
    query_vectors: List[np.ndarray],
    top_k: int
) -> dict:
    """
    Benchmarks different FAISS index types
    
    Args:
        index_types: List of FAISS index types to benchmark
        vectors: List of vectors to add to each index
        ids: List of vector IDs
        query_vectors: List of query vectors
        top_k: Number of results to return
        
    Returns:
        Dictionary with benchmark results for different index types
    """
    results = {}
    
    for index_type in index_types:
        logger.info(f"Benchmarking index type: {index_type}")
        
        # Create vector store with this index type
        with open("/tmp/faiss_benchmark_index", "w") as f:
            pass  # Create empty file
        
        # Override settings for this benchmark
        VectorSearchSettings.INDEX_TYPE = index_type
        
        # Create new vector store
        vector_store = FAISSStore(index_path="/tmp/faiss_benchmark_index")
        
        # Benchmark vector addition
        addition_results = benchmark_vector_addition(
            vector_store=vector_store,
            vectors=vectors,
            ids=ids,
            batch_size=1000
        )
        
        # Benchmark vector search
        search_results = benchmark_vector_search(
            vector_store=vector_store,
            query_vectors=query_vectors,
            top_k=top_k,
            threshold=0.7,
            num_runs=5
        )
        
        # Combine results
        results[index_type] = {
            "addition": addition_results,
            "search": search_results
        }
    
    return results

def benchmark_index_parameters(
    index_type: str,
    nlist_values: List[int],
    nprobe_values: List[int],
    vectors: List[np.ndarray],
    ids: List[str],
    query_vectors: List[np.ndarray],
    top_k: int
) -> dict:
    """
    Benchmarks FAISS index with different parameter values
    
    Args:
        index_type: FAISS index type
        nlist_values: List of nlist values to test
        nprobe_values: List of nprobe values to test
        vectors: List of vectors to add to each index
        ids: List of vector IDs
        query_vectors: List of query vectors
        top_k: Number of results to return
        
    Returns:
        Dictionary with benchmark results for different parameter combinations
    """
    # Only meaningful for IVFFlat index
    if index_type != "IVFFlat":
        logger.warning(f"Parameter tuning only meaningful for IVFFlat index, not {index_type}")
        return {}
    
    results = {}
    
    for nlist in nlist_values:
        for nprobe in nprobe_values:
            logger.info(f"Benchmarking parameters: nlist={nlist}, nprobe={nprobe}")
            
            # Create vector store with these parameters
            with open("/tmp/faiss_benchmark_index", "w") as f:
                pass  # Create empty file
            
            # Override settings for this benchmark
            VectorSearchSettings.INDEX_TYPE = index_type
            VectorSearchSettings.NLIST = nlist
            VectorSearchSettings.NPROBE = nprobe
            
            # Create new vector store
            vector_store = FAISSStore(index_path="/tmp/faiss_benchmark_index")
            
            # Add vectors
            vector_store.add_vectors(vectors, ids)
            
            # Benchmark vector search
            search_results = benchmark_vector_search(
                vector_store=vector_store,
                query_vectors=query_vectors,
                top_k=top_k,
                threshold=0.7,
                num_runs=5
            )
            
            # Record results
            param_key = f"nlist={nlist},nprobe={nprobe}"
            results[param_key] = search_results
    
    return results

def benchmark_scale(
    vector_counts: List[int],
    dimension: int,
    query_vectors: List[np.ndarray],
    top_k: int
) -> dict:
    """
    Benchmarks vector search performance at different scales
    
    Args:
        vector_counts: List of vector counts to benchmark
        dimension: Vector dimension
        query_vectors: List of query vectors
        top_k: Number of results to return
        
    Returns:
        Dictionary with benchmark results at different scales
    """
    results = {}
    
    for count in vector_counts:
        logger.info(f"Benchmarking scale: {count} vectors")
        
        # Generate vectors for this scale
        vectors = generate_random_vectors(count, dimension)
        ids = [f"vec_{i}" for i in range(count)]
        
        # Create vector store for this scale
        with open("/tmp/faiss_benchmark_index", "w") as f:
            pass  # Create empty file
        
        vector_store = FAISSStore(index_path="/tmp/faiss_benchmark_index")
        
        # Add vectors
        addition_results = benchmark_vector_addition(
            vector_store=vector_store,
            vectors=vectors,
            ids=ids,
            batch_size=1000
        )
        
        # Benchmark vector search
        search_results = benchmark_vector_search(
            vector_store=vector_store,
            query_vectors=query_vectors,
            top_k=top_k,
            threshold=0.7,
            num_runs=5
        )
        
        # Record results
        results[count] = {
            "addition": addition_results,
            "search": search_results
        }
    
    return results

def plot_results(results: dict, output_dir: str):
    """
    Generates plots from benchmark results
    
    Args:
        results: Dictionary with benchmark results
        output_dir: Directory to save plots
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Plot time vs. scale
    if "scale" in results:
        scales = list(results["scale"].keys())
        search_times = [results["scale"][s]["search"]["avg_search_time"] for s in scales]
        
        plt.figure(figsize=(10, 6))
        plt.plot(scales, search_times, marker='o')
        plt.xscale('log')
        plt.yscale('log')
        plt.xlabel('Number of Vectors')
        plt.ylabel('Average Search Time (s)')
        plt.title('Search Performance vs. Scale')
        plt.grid(True, which="both", ls="-")
        plt.savefig(os.path.join(output_dir, 'scale_performance.png'))
        plt.close()
    
    # Plot index type comparison
    if "index_types" in results:
        index_types = list(results["index_types"].keys())
        search_times = [results["index_types"][t]["search"]["avg_search_time"] for t in index_types]
        
        plt.figure(figsize=(10, 6))
        bars = plt.bar(index_types, search_times)
        plt.xlabel('Index Type')
        plt.ylabel('Average Search Time (s)')
        plt.title('Search Performance by Index Type')
        
        # Add time labels above bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.4f}s',
                    ha='center', va='bottom')
        
        plt.savefig(os.path.join(output_dir, 'index_type_comparison.png'))
        plt.close()
    
    # Plot parameter tuning heatmap
    if "parameters" in results and results["parameters"]:
        # Extract parameters and search times
        params = list(results["parameters"].keys())
        search_times = [results["parameters"][p]["avg_search_time"] for p in params]
        
        # Parse parameters into nlist and nprobe values
        param_dict = {}
        for param in params:
            nlist_val = int(param.split(",")[0].split("=")[1])
            nprobe_val = int(param.split(",")[1].split("=")[1])
            param_dict[(nlist_val, nprobe_val)] = results["parameters"][param]["avg_search_time"]
        
        # Get unique nlist and nprobe values
        nlist_vals = sorted(set(k[0] for k in param_dict.keys()))
        nprobe_vals = sorted(set(k[1] for k in param_dict.keys()))
        
        # Create DataFrame for heatmap
        data = np.zeros((len(nlist_vals), len(nprobe_vals)))
        for i, nlist in enumerate(nlist_vals):
            for j, nprobe in enumerate(nprobe_vals):
                if (nlist, nprobe) in param_dict:
                    data[i, j] = param_dict[(nlist, nprobe)]
        
        df = pd.DataFrame(data, index=nlist_vals, columns=nprobe_vals)
        
        plt.figure(figsize=(10, 8))
        plt.pcolormesh(df.columns, df.index, df.values)
        plt.colorbar(label='Average Search Time (s)')
        plt.xlabel('nprobe')
        plt.ylabel('nlist')
        plt.title('Search Performance by Index Parameters')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'parameter_tuning.png'))
        plt.close()

def save_results(results: dict, output_dir: str, filename: str) -> str:
    """
    Saves benchmark results to a file
    
    Args:
        results: Dictionary with benchmark results
        output_dir: Directory to save results
        filename: Filename for the results
        
    Returns:
        Path to saved results file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert numpy arrays to lists for JSON serialization
    def convert_numpy(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(v) for v in obj]
        else:
            return obj
    
    converted_results = convert_numpy(results)
    
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w') as f:
        json.dump(converted_results, f, indent=2)
    
    logger.info(f"Saved results to {filepath}")
    
    return filepath

def load_results(filepath: str) -> dict:
    """
    Loads benchmark results from a file
    
    Args:
        filepath: Path to results file
        
    Returns:
        Loaded benchmark results
    """
    if not os.path.exists(filepath):
        logger.error(f"Results file not found: {filepath}")
        return {}
    
    with open(filepath, 'r') as f:
        results = json.load(f)
    
    logger.info(f"Loaded results from {filepath}")
    
    return results

def run_comprehensive_benchmark(config: dict) -> dict:
    """
    Runs a comprehensive benchmark suite
    
    Args:
        config: Benchmark configuration dictionary
        
    Returns:
        Dictionary with all benchmark results
    """
    # Initialize benchmark configuration
    benchmark_config = BenchmarkConfig(config)
    
    # Initialize results dictionary
    results = {
        "config": benchmark_config.to_dict(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "system_info": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
    }
    
    # Generate random vectors for benchmarking
    logger.info(f"Generating {benchmark_config.num_vectors} random vectors with dimension {benchmark_config.dimension}")
    vectors = generate_random_vectors(benchmark_config.num_vectors, benchmark_config.dimension)
    ids = [f"vec_{i}" for i in range(benchmark_config.num_vectors)]
    
    # Generate test queries
    sample_texts = [
        "machine learning algorithms",
        "document management system",
        "natural language processing",
        "vector similarity search",
        "artificial intelligence applications",
        "neural network architecture",
        "data science techniques",
        "information retrieval systems",
        "semantic text analysis",
        "content recommendation engine"
    ]
    sample_texts = sample_texts[:benchmark_config.num_queries]
    
    logger.info(f"Generating {len(sample_texts)} test queries")
    query_vectors = generate_test_queries(sample_texts)
    
    # Create vector store for basic benchmarks
    logger.info("Creating vector store for basic benchmarks")
    with open("/tmp/faiss_benchmark_index", "w") as f:
        pass  # Create empty file
    
    vector_store = FAISSStore(index_path="/tmp/faiss_benchmark_index")
    
    # Benchmark vector addition
    logger.info("Benchmarking vector addition performance")
    addition_results = benchmark_vector_addition(
        vector_store=vector_store,
        vectors=vectors,
        ids=ids,
        batch_size=benchmark_config.batch_size
    )
    results["vector_addition"] = addition_results
    
    # Benchmark vector search
    logger.info("Benchmarking vector search performance")
    search_results = benchmark_vector_search(
        vector_store=vector_store,
        query_vectors=query_vectors,
        top_k=benchmark_config.top_k,
        threshold=benchmark_config.threshold,
        num_runs=benchmark_config.num_runs
    )
    results["vector_search"] = search_results
    
    # Benchmark search service
    logger.info("Benchmarking vector search service")
    search_service = VectorSearchService(vector_store)
    service_results = benchmark_service_search(
        search_service=search_service,
        query_texts=sample_texts,
        top_k=benchmark_config.top_k,
        threshold=benchmark_config.threshold,
        num_runs=benchmark_config.num_runs
    )
    results["service_search"] = service_results
    
    # Benchmark different index types
    logger.info("Benchmarking different index types")
    index_type_results = benchmark_index_types(
        index_types=benchmark_config.index_types,
        vectors=vectors[:min(10000, len(vectors))],  # Limit vectors for index type comparison
        ids=ids[:min(10000, len(ids))],
        query_vectors=query_vectors,
        top_k=benchmark_config.top_k
    )
    results["index_types"] = index_type_results
    
    # Benchmark index parameters (only for IVFFlat)
    logger.info("Benchmarking index parameters")
    parameter_results = benchmark_index_parameters(
        index_type="IVFFlat",
        nlist_values=benchmark_config.nlist_values,
        nprobe_values=benchmark_config.nprobe_values,
        vectors=vectors[:min(10000, len(vectors))],  # Limit vectors for parameter tuning
        ids=ids[:min(10000, len(ids))],
        query_vectors=query_vectors,
        top_k=benchmark_config.top_k
    )
    results["parameters"] = parameter_results
    
    # Benchmark scalability
    logger.info("Benchmarking scalability")
    scale_results = benchmark_scale(
        vector_counts=benchmark_config.scale_vector_counts,
        dimension=benchmark_config.dimension,
        query_vectors=query_vectors,
        top_k=benchmark_config.top_k
    )
    results["scale"] = scale_results
    
    # Save results and generate plots
    save_results(results, benchmark_config.output_dir, "comprehensive_benchmark_results.json")
    plot_results(results, benchmark_config.output_dir)
    
    return results

def parse_args():
    """
    Parses command-line arguments for the benchmark script
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Benchmark vector search operations")
    
    parser.add_argument("--num-vectors", type=int, default=10000,
                        help="Number of vectors to generate (default: 10000)")
    parser.add_argument("--dimension", type=int, default=VectorSearchSettings.VECTOR_DIMENSION,
                        help=f"Vector dimension (default: {VectorSearchSettings.VECTOR_DIMENSION})")
    parser.add_argument("--num-queries", type=int, default=10,
                        help="Number of queries to run (default: 10)")
    parser.add_argument("--num-runs", type=int, default=5,
                        help="Number of runs per query (default: 5)")
    parser.add_argument("--top-k", type=int, default=5,
                        help="Number of results to retrieve (default: 5)")
    parser.add_argument("--threshold", type=float, default=0.7,
                        help="Similarity threshold (default: 0.7)")
    parser.add_argument("--output-dir", type=str, default=RESULTS_DIR,
                        help=f"Output directory for results (default: {RESULTS_DIR})")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--index-types", type=str, default="Flat,IVFFlat,HNSW",
                        help="Comma-separated list of index types to test (default: Flat,IVFFlat,HNSW)")
    parser.add_argument("--batch-size", type=int, default=1000,
                        help="Batch size for adding vectors (default: 1000)")
    
    return parser.parse_args()

def main():
    """
    Main function that runs the benchmark script
    
    Returns:
        Exit code (0 for success)
    """
    # Parse command-line arguments
    args = parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Log the start of the benchmark
    logger.info("Starting vector search benchmark")
    logger.info(f"Configuration: {vars(args)}")
    
    # Create configuration from arguments
    config = BenchmarkConfig.from_args(args)
    
    # Run comprehensive benchmark
    try:
        results = run_comprehensive_benchmark(config.to_dict())
        logger.info("Benchmark completed successfully")
        logger.info(f"Results saved to {config.output_dir}")
    except Exception as e:
        logger.exception(f"Benchmark failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())