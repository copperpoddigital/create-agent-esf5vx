# Data Flow Architecture

This document provides detailed information about the data flows within the Document Management and AI Chatbot System, including data transformations, processing pipelines, and interactions between system components.

## 1. Introduction

The Document Management and AI Chatbot System processes data through several key components, each responsible for specific transformations and operations. Understanding these data flows is crucial for system optimization, troubleshooting, and future enhancements.

The system's data flow architecture follows these principles:

- Clear separation of concerns between components
- Well-defined data transformation points
- Efficient data routing between components
- Optimized storage patterns for different data types
- Scalable processing pipelines

The primary data flow begins with document upload, where PDFs are processed through the Document Processor to extract text. The extracted text is then passed to the Vector Engine, which generates embeddings using Sentence Transformers and stores them in the FAISS index. Document metadata is stored in PostgreSQL through the Data Store component.

For queries, user input is processed by the API Layer and passed to the Vector Engine, which generates a query embedding and performs similarity search in FAISS. The most relevant document segments are retrieved and combined with the original query to form a prompt for the LLM Connector. The LLM generates a response based on the document context, which is returned to the user along with references to the source documents.

Feedback flows from the API Layer to the Feedback Manager, which stores user ratings and uses them to periodically update the response generation process through reinforcement learning techniques.

## 2. Core Data Flow Patterns

The system implements several core data flow patterns:

### 2.1 Data Processing Patterns

```mermaid
flowchart TD
    subgraph "Data Flow Patterns"
        A[Ingestion] --> B[Transformation]
        B --> C[Storage]
        C --> D[Retrieval]
        D --> E[Processing]
        E --> F[Response Generation]
    end
    
    subgraph "Document Flow"
        D1[Document Upload] --> T1[Text Extraction]
        T1 --> T2[Text Chunking]
        T2 --> T3[Vector Embedding]
        T3 --> S1[Vector Storage]
    end
    
    subgraph "Query Flow"
        Q1[Query Input] --> QT1[Query Embedding]
        QT1 --> QT2[Vector Search]
        QT2 --> QT3[Context Preparation]
        QT3 --> QT4[Response Generation]
    end
    
    subgraph "Feedback Flow"
        F1[User Feedback] --> F2[Feedback Storage]
        F2 --> F3[Aggregation]
        F3 --> F4[Model Improvement]
    end
```

### 2.2 Component Interaction Model

```mermaid
flowchart TD
    Client[Client Applications] --> API[API Layer]
    
    API --> DocMgr[Document Manager]
    API --> QueryEngine[Query Engine]
    API --> FeedbackSys[Feedback System]
    
    DocMgr --> DocProcessor[Document Processor]
    DocMgr --> MetaStore[Metadata Store]
    
    DocProcessor --> FileStore[(File Storage)]
    DocProcessor --> VectorDB[(FAISS Vector DB)]
    MetaStore --> RelationalDB[(PostgreSQL)]
    
    QueryEngine --> VectorSearch[Vector Search Engine]
    QueryEngine --> ResponseGen[Response Generator]
    
    VectorSearch --> VectorDB
    VectorSearch --> RelationalDB
    ResponseGen --> LLMService[LLM Service]
    
    FeedbackSys --> RelationalDB
```

Data transformation occurs primarily at three points:

1. Document text extraction (PDF to plain text)
2. Vector embedding generation (text to vector embeddings)
3. Context preparation (document segments to LLM prompt)

## 3. Document Processing Flow

The document processing flow handles the transformation of uploaded PDF documents into searchable vector embeddings and stored metadata.

### 3.1 End-to-End Document Processing

```mermaid
sequenceDiagram
    participant Client
    participant API as API Layer
    participant DocMgr as Document Manager
    participant DocProc as Document Processor
    participant MetaStore as Metadata Store
    participant FileStore as File Storage
    participant VectorDB as FAISS Vector DB
    participant RelDB as PostgreSQL
    
    Client->>API: Upload Document (PDF)
    API->>DocMgr: Process Document
    
    DocMgr->>DocMgr: Validate Document
    DocMgr->>FileStore: Store Original Document
    FileStore-->>DocMgr: File Path
    
    DocMgr->>DocProc: Process Document
    DocProc->>DocProc: Extract Text
    DocProc->>DocProc: Clean Text
    DocProc->>DocProc: Chunk Document
    
    loop For Each Chunk
        DocProc->>DocProc: Generate Embedding
        DocProc->>VectorDB: Store Embedding
    end
    
    DocProc-->>DocMgr: Processing Results
    
    DocMgr->>MetaStore: Store Metadata
    MetaStore->>RelDB: Save Document Metadata
    RelDB-->>MetaStore: Confirmation
    MetaStore-->>DocMgr: Metadata Stored
    
    DocMgr-->>API: Document Processed
    API-->>Client: Upload Success Response
```

### 3.2 Document Data Transformations

The document undergoes several transformations during processing:

1. **PDF to Text**: 
   - Input: Raw PDF document
   - Process: Text extraction using PyMuPDF
   - Output: Plain text content

2. **Text to Chunks**:
   - Input: Plain text content
   - Process: Splitting into manageable chunks with optimal size
   - Output: Array of text chunks

3. **Chunks to Vectors**:
   - Input: Text chunks
   - Process: Vector embedding generation using Sentence Transformers
   - Output: High-dimensional vector embeddings (768 dimensions)

4. **Metadata Extraction**:
   - Input: PDF document and processing results
   - Process: Extraction of document properties and processing statistics
   - Output: Structured metadata record

### 3.3 Data Quality Controls

```mermaid
flowchart TD
    A[Document Input] --> B{Format Check}
    B -->|Invalid| C[Reject Document]
    B -->|Valid| D{Size Check}
    
    D -->|Too Large| E[Reject Document]
    D -->|Acceptable| F[Extract Text]
    
    F --> G{Text Extraction Successful?}
    G -->|No| H[Log Extraction Error]
    H --> I[Return 422 Unprocessable Entity]
    G -->|Yes| J[Text Processing]
    
    J --> K{Chunking Successful?}
    K -->|No| L[Log Chunking Error]
    L --> M[Return Error Status]
    K -->|Yes| N[Vector Generation]
    
    N --> O{Vectors Generated?}
    O -->|No| P[Log Vector Error]
    P --> Q[Return Error Status]
    O -->|Yes| R[Storage]
    R --> S[Return Success]
```

SLA: Document processing completes within 10 seconds for documents up to 10MB in size.

## 4. Query and Response Flow

The query and response flow handles the transformation of user queries into vector searches and AI-generated responses.

### 4.1 End-to-End Query Processing

```mermaid
sequenceDiagram
    participant Client
    participant API as API Layer
    participant QueryEng as Query Engine
    participant VectorSearch as Vector Search Engine
    participant RespGen as Response Generator
    participant VectorDB as FAISS Vector DB
    participant RelDB as PostgreSQL
    participant LLM as LLM Service
    
    Client->>API: Submit Query
    API->>QueryEng: Process Query
    
    QueryEng->>VectorSearch: Search Documents
    VectorSearch->>VectorSearch: Generate Query Embedding
    VectorSearch->>VectorDB: Perform Similarity Search
    VectorDB-->>VectorSearch: Similar Vector IDs and Scores
    
    VectorSearch->>RelDB: Retrieve Document Chunks
    RelDB-->>VectorSearch: Document Content
    VectorSearch->>VectorSearch: Rank Results
    VectorSearch-->>QueryEng: Ranked Document Chunks
    
    QueryEng->>RespGen: Generate Response
    RespGen->>RespGen: Prepare Context
    RespGen->>LLM: Send Query and Context
    LLM-->>RespGen: Generated Response
    RespGen-->>QueryEng: Formatted Response
    
    QueryEng->>RelDB: Store Query and Response
    RelDB-->>QueryEng: Storage Confirmation
    
    QueryEng-->>API: Query Results
    API-->>Client: Response with Document References
```

SLA: Query processing completes within 3 seconds for standard queries.

### 4.2 Query Data Transformations

The query undergoes several transformations during processing:

1. **Query Text to Vector**:
   - Input: Natural language query
   - Process: Vector embedding generation using the same model as documents
   - Output: Query vector representation

2. **Vector to Document Retrieval**:
   - Input: Query vector
   - Process: Similarity search in FAISS
   - Output: Ranked list of relevant document chunks with similarity scores

3. **Context Preparation**:
   - Input: Relevant document chunks
   - Process: Selection and formatting of context for LLM
   - Output: Formatted context string

4. **Response Generation**:
   - Input: Query and context
   - Process: LLM processing with prompt engineering
   - Output: Natural language response

### 4.3 Context Window Management

```mermaid
flowchart TD
    A[Relevant Documents] --> B[Score and Rank]
    B --> C[Select Top Documents]
    C --> D{Total Tokens > Max?}
    D -->|Yes| E[Truncate or Summarize]
    D -->|No| F[Format Context]
    E --> F
    F --> G[Combine with Query]
    G --> H[Send to LLM]
```

The system carefully manages the context window to ensure optimal use of the LLM's token limit:

1. Documents are ranked by relevance score
2. Top N documents are selected based on relevance
3. If the total token count exceeds the LLM's maximum context window:
   - Either truncate documents
   - Or prioritize most relevant sections
4. Context is formatted with clear section boundaries
5. The formatted context is combined with the query in a structured prompt

## 5. Feedback and Learning Flow

The feedback and learning flow handles the collection, processing, and application of user feedback for system improvement.

### 5.1 End-to-End Feedback Processing

```mermaid
sequenceDiagram
    participant Client
    participant API as API Layer
    participant FeedbackSys as Feedback System
    participant DB as PostgreSQL
    participant RL as RL Engine
    
    Client->>API: Submit Feedback
    API->>FeedbackSys: Process Feedback
    FeedbackSys->>DB: Store Feedback
    DB-->>FeedbackSys: Storage Confirmation
    FeedbackSys-->>API: Feedback Accepted
    API-->>Client: Feedback Success Response
    
    Note over RL,DB: Scheduled Process
    RL->>DB: Retrieve Accumulated Feedback
    DB-->>RL: Feedback Data
    RL->>RL: Process Feedback
    RL->>RL: Update Response Model
    RL->>DB: Store Updated Model Parameters
    DB-->>RL: Storage Confirmation
```

### 5.2 Feedback Data Transformations

The feedback undergoes several transformations during processing:

1. **User Feedback to Storage**:
   - Input: User rating (1-5) and optional comments
   - Process: Association with query and response
   - Output: Structured feedback record

2. **Feedback Aggregation**:
   - Input: Multiple feedback records
   - Process: Statistical analysis and pattern recognition
   - Output: Aggregated feedback metrics

3. **Model Improvement**:
   - Input: Aggregated feedback
   - Process: Parameter adjustment based on reinforcement learning
   - Output: Updated model parameters

### 5.3 Reinforcement Learning Cycle

```mermaid
flowchart TD
    A[Collect User Feedback] --> B[Store Feedback]
    B --> C[Aggregate Feedback]
    C --> D[Identify Patterns]
    D --> E[Generate Training Examples]
    E --> F[Update Response Parameters]
    F --> G[Deploy Updated Model]
    G --> H[Monitor Performance]
    H --> A
```

The reinforcement learning cycle operates as follows:

1. User feedback is collected on query responses
2. Feedback is stored with associated queries and responses
3. Feedback is aggregated to identify patterns
4. Successful responses are used as positive examples
5. Response parameters are updated based on learning
6. Updated model is deployed in a controlled manner
7. Performance is monitored to verify improvement
8. The cycle continues with new feedback

## 6. Data Transformations

### 6.1 Key Data Transformation Points

```mermaid
flowchart TD
    subgraph "Document Processing"
        A1[PDF Document] -->|Text Extraction| B1[Plain Text]
        B1 -->|Chunking| C1[Text Chunks]
        C1 -->|Embedding Generation| D1[Vector Embeddings]
    end
    
    subgraph "Query Processing"
        A2[Query Text] -->|Embedding Generation| B2[Query Vector]
        B2 -->|Similarity Search| C2[Relevant Documents]
        C2 -->|Context Formation| D2[Formatted Context]
        D2 -->|LLM Processing| E2[AI Response]
    end
    
    subgraph "Feedback Processing"
        A3[User Feedback] -->|Validation| B3[Validated Feedback]
        B3 -->|Aggregation| C3[Feedback Patterns]
        C3 -->|Model Training| D3[Updated Parameters]
    end
```

### 6.2 Data Transformation Details

| Transformation | Input Format | Output Format | Process | Technology | Performance Considerations |
| --- | --- | --- | --- | --- | --- |
| PDF to Text | PDF Binary | Plain Text | Text extraction | PyMuPDF | Memory usage for large documents |
| Text to Chunks | Plain Text | Text Chunks Array | Text splitting | Custom algorithm | Chunk size affects search precision |
| Text to Vector | Text | Float Array (768 dim) | Embedding generation | Sentence Transformers | CPU/GPU intensive |
| Query to Vector | Query Text | Float Array (768 dim) | Embedding generation | Sentence Transformers | Latency sensitive |
| Documents to Context | Document Chunks | Formatted String | Context preparation | Custom algorithm | Token limit management |
| Feedback to Metrics | Individual Ratings | Statistical Summary | Aggregation | Pandas/NumPy | Batch processing |

## 7. Data Storage Patterns

### 7.1 Storage Components

```mermaid
flowchart TD
    subgraph "Storage Components"
        A[File Storage] --> A1[Original Documents]
        B[Vector Database] --> B1[Document Embeddings]
        B[Vector Database] --> B2[Query Embeddings]
        C[Relational Database] --> C1[Document Metadata]
        C[Relational Database] --> C2[Query History]
        C[Relational Database] --> C3[Feedback Data]
        C[Relational Database] --> C4[User Data]
    end
```

### 7.2 Data Persistence Strategy

| Data Type | Storage | Format | Retention | Access Pattern | Backup Strategy |
| --- | --- | --- | --- | --- | --- |
| Original Documents | File System/S3 | PDF Binary | Until deletion | Write once, read many | Regular snapshots |
| Document Metadata | PostgreSQL | Relational | Until deletion | Frequent reads, occasional updates | Database backups |
| Vector Embeddings | FAISS | Binary Vector | Until document deletion | Write once, read many | Index snapshots |
| Query History | PostgreSQL | Relational | 1 year | Write once, occasional reads | Database backups |
| User Feedback | PostgreSQL | Relational | 2 years | Write once, batch reads | Database backups |
| User Data | PostgreSQL | Relational | Until account deletion | Frequent reads, occasional updates | Database backups |

### 7.3 Data Flow Between Storage Systems

```mermaid
flowchart TD
    Client[Client] --> API[API Layer]
    
    API -->|Document Upload| FS[(File Storage)]
    API -->|Document Metadata| DB[(PostgreSQL)]
    API -->|Vector Storage| VS[(FAISS)]
    
    API -->|Query| VS
    VS -->|Document IDs| DB
    DB -->|Document Content| API
    
    API -->|Feedback| DB
    
    subgraph "Data Flow"
        FS -.->|Document ID Reference| DB
        VS -.->|Vector ID Reference| DB
    end
```

## 8. Performance Considerations

### 8.1 Key Performance Metrics

| Process | Key Metric | Target | Bottleneck | Optimization Technique |
| --- | --- | --- | --- | --- |
| Document Upload | Processing Time | \< 10s for 10MB | PDF extraction | Asynchronous processing |
| Vector Generation | Embedding Time | \< 5s per document | CPU/GPU resources | Batch processing |
| Vector Search | Query Latency | \< 500ms | FAISS index size | Index optimization, sharding |
| Response Generation | Response Time | \< 2.5s | LLM API | Prompt optimization, caching |
| Feedback Processing | Processing Time | N/A (background) | Database I/O | Batch processing |

### 8.2 Performance Optimization Strategies

```mermaid
flowchart TD
    A[Performance Bottlenecks] --> B[Document Processing]
    A --> C[Vector Search]
    A --> D[Response Generation]
    
    B --> B1[Parallel Processing]
    B --> B2[Asynchronous Handling]
    B --> B3[Resource Allocation]
    
    C --> C1[Index Optimization]
    C --> C2[Caching]
    C --> C3[Query Optimization]
    
    D --> D1[Prompt Engineering]
    D --> D2[Token Management]
    D --> D3[Model Selection]
```

### 8.3 Data Volume Considerations

| Component | Current Capacity | Scaling Threshold | Scaling Strategy |
| --- | --- | --- | --- |
| Document Storage | Unlimited | N/A | Horizontal scaling |
| Vector Database | ~1M documents | When search time \> 500ms | Sharding, index optimization |
| Metadata Database | Unlimited | When query time \> 100ms | Read replicas, query optimization |
| LLM Integration | Rate limited | When queue depth \> 10 | Caching, queue management |

### 8.4 Caching Strategy

```mermaid
flowchart TD
    A[Caching Points] --> B[Query Results]
    A --> C[Document Metadata]
    A --> D[Vector Embeddings]
    A --> E[LLM Responses]
    
    B --> B1[In-memory LRU Cache]
    B --> B2[TTL: 30 minutes]
    
    C --> C1[Database Query Cache]
    C --> C2[Auto-invalidation on updates]
    
    D --> D1[FAISS in-memory]
    D --> D2[Manual invalidation]
    
    E --> E1[Response Cache]
    E --> E2[TTL: 1 hour]
```

The system implements caching at multiple levels to optimize performance:

1. **Query Results Cache**:
   - Caches results for identical queries
   - Utilizes an LRU (Least Recently Used) eviction policy
   - Time-based expiration (TTL) of 30 minutes

2. **Document Metadata Cache**:
   - Database-level query cache for document metadata
   - Automatically invalidated when documents are updated
   - Optimized for frequent read operations

3. **Vector Embeddings**:
   - FAISS index kept in memory for fast search
   - Manually invalidated when documents are updated
   - Memory-mapped for large indices

4. **LLM Responses**:
   - Caches responses for identical query/context combinations
   - Reduces LLM API costs for repeated queries
   - TTL of 1 hour to balance freshness with performance