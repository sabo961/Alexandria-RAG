workspace "Alexandria RAG System" "Semantic search and knowledge synthesis across 9,000 books" {

    model {
        # People
        user = person "Developer/Researcher" "Uses Alexandria to search and analyze books for insights and knowledge synthesis"

        # Software Systems
        alexandriaSystem = softwareSystem "Alexandria RAG System" "Retrieval-Augmented Generation system for multi-disciplinary book library" {

            # Containers
            gui = container "Streamlit GUI" "Web-based interface for browsing, ingesting, and querying books" "Python 3.14, Streamlit" "Web Browser"

            scripts = container "Scripts Package" "Core business logic for ingestion, chunking, querying, and management" "Python 3.14" {
                
                # --- INGESTION COMPONENTS ---
                textExtractor = component "Text Extractor" "Parses EPUB/PDF/TXT files into raw text with metadata" "ingest_books.py (extract_text)" {
                    tags "Ingestion"
                }
                
                chunkingRouter = component "Chunking Router" "Determines optimal chunking strategy based on Domain and Content Type" "ingest_books.py (calculate_params)" {
                    tags "Ingestion" "Logic"
                }

                chunker = component "Chunking Engine" "Executes the selected splitting strategy (Fixed Window or Semantic)" "ingest_books.py (chunk_text), philosophical_chunking.py" {
                    tags "Ingestion" "Core"
                }

                embedder = component "Embedder" "Converts text chunks into 384-dim vectors" "SentenceTransformer (all-MiniLM-L6-v2)" {
                    tags "Ingestion" "AI"
                }

                qdrantUploader = component "Qdrant Uploader" "Batches and uploads vectors + payloads to Qdrant" "ingest_books.py (upload_to_qdrant)" {
                    tags "Ingestion"
                }

                # --- QUERY COMPONENTS ---
                ragQueryEngine = component "RAG Query Engine" "Semantic search via Qdrant with similarity filtering, fetch multiplier, and LLM answer generation" "rag_query.py" {
                    tags "Query"
                }

                # --- MANAGEMENT COMPONENTS ---
                collectionManagement = component "Collection Management" "Tracks ingested books via per-collection manifests, CSV exports, and Qdrant statistics" "collection_manifest.py, qdrant_utils.py" {
                    tags "Management"
                }

                calibreIntegration = component "Calibre Integration" "Direct SQLite access to Calibre library for metadata and direct ingestion" "calibre_db.py" {
                    tags "Integration"
                }

                # Internal Data Flow (Ingestion)
                calibreIntegration -> textExtractor "Provides file path & metadata"
                textExtractor -> chunkingRouter "Passes raw text & domain"
                chunkingRouter -> chunker "Configures strategy (Size/Overlap/Method)"
                chunker -> embedder "Yields text chunks"
                embedder -> qdrantUploader "Yields vectors"
                qdrantUploader -> collectionManagement "Logs success"

                # Internal Data Flow (Query)
                ragQueryEngine -> collectionManagement "Checks collection status"
                ragQueryEngine -> embedder "Embeds query string"
            }

            filesystem = container "File System" "Book storage (ingest/, ingested/) and logs (logs/)" "File System" "Storage"
            calibreDb = container "Calibre Database" "Book metadata (title, author, series, tags, languages)" "SQLite (metadata.db)" "Database"
        }

        # External Systems
        qdrant = softwareSystem "Qdrant Vector DB" "Vector search engine storing 384-dim embeddings with domain/book/author metadata" "External System" {
            tags "External"
        }

        openrouter = softwareSystem "OpenRouter API" "LLM inference for answer generation (multiple models supported)" "External System" {
            tags "External"
        }

        # System Context Relationships
        user -> alexandriaSystem "Browses library, ingests books, queries for knowledge"
        alexandriaSystem -> qdrant "Stores/retrieves book chunk embeddings"
        alexandriaSystem -> openrouter "Generates natural language answers from retrieved chunks"

        # Container Relationships
        user -> gui "Uses web interface"
        gui -> scripts "Calls business logic functions"
        scripts -> filesystem "Reads/writes books and manifests"
        scripts -> calibreDb "Queries book metadata"
        scripts -> qdrant "Stores embeddings, retrieves semantic matches"
        scripts -> openrouter "Sends context + query for answer generation"

        # Component Relationships (from GUI)
        gui -> textExtractor "Initiates ingestion"
        gui -> ragQueryEngine "Executes query"
        gui -> collectionManagement "Displays stats"
        gui -> calibreIntegration "Browses library"
        
        # Backend to External
        qdrantUploader -> qdrant "Upserts vectors"
        ragQueryEngine -> qdrant "Searches vectors"
        ragQueryEngine -> openrouter "Generates answers"
    }

    views {
        systemContext alexandriaSystem "SystemContext" {
            include *
            autolayout lr
        }

        container alexandriaSystem "Containers" {
            include *
            autolayout lr
        }

        component scripts "Components" {
            include *
            autolayout lr
            description "Detailed breakdown of the Scripts Package"
        }

        # DETAILED INGESTION FLOW
        dynamic scripts "DetailedIngestionFlow" "The lifecycle of a book from file to vector" {
            calibreIntegration -> textExtractor "1. Get file path"
            textExtractor -> chunkingRouter "2. Analyze text structure"
            chunkingRouter -> chunker "3. Select & Execute Strategy (e.g., Argument vs Fixed)"
            chunker -> embedder "4. Generate Embeddings"
            embedder -> qdrantUploader "5. Prepare Batch"
            qdrantUploader -> collectionManagement "6. Log to Manifest"
            autolayout lr
        }

        styles {
            element "Software System" {
                background #1168bd
                color #ffffff
                shape RoundedBox
            }
            element "External System" {
                background #999999
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
                shape RoundedBox
            }
            element "Component" {
                background #85bbf0
                color #000000
                shape Component
            }
            element "Ingestion" {
                background #2d8a5f
            }
            element "Query" {
                background #8a2d58
            }
            element "AI" {
                background #5c2d8a
            }
        }
    }
}