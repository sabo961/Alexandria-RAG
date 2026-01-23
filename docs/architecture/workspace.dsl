workspace "Alexandria RAG System" "Semantic search and knowledge synthesis across 9,000 books" {

    model {
        # People
        user = person "Developer/Researcher" "Uses Alexandria to search and analyze books for insights and knowledge synthesis"

        # Software Systems
        alexandriaSystem = softwareSystem "Alexandria RAG System" "Retrieval-Augmented Generation system for multi-disciplinary book library" {

            # Containers
            gui = container "Streamlit GUI" "Web-based interface for browsing, ingesting, and querying books" "Python 3.14, Streamlit" "Web Browser"

            scripts = container "Scripts Package" "Core business logic for ingestion, chunking, querying, and management" "Python 3.14" {
                # Components
                ingestionEngine = component "Ingestion Engine" "Processes EPUB/PDF/TXT/MD books into chunks and uploads to Qdrant" "batch_ingest.py, ingest_books.py" {
                    tags "Ingestion"
                }

                chunkingStrategies = component "Chunking Strategies" "Domain-specific chunking (technical, psychology, philosophy, history) with argument-based pre-chunking for philosophical texts" "philosophical_chunking.py" {
                    tags "Chunking"
                }

                ragQueryEngine = component "RAG Query Engine" "Semantic search via Qdrant with similarity filtering, fetch multiplier, and LLM answer generation" "rag_query.py" {
                    tags "Query"
                }

                collectionManagement = component "Collection Management" "Tracks ingested books via per-collection manifests, CSV exports, and Qdrant statistics" "collection_manifest.py, qdrant_utils.py" {
                    tags "Management"
                }

                calibreIntegration = component "Calibre Integration" "Direct SQLite access to Calibre library for metadata and direct ingestion" "calibre_db.py" {
                    tags "Integration"
                }

                # Component relationships
                ingestionEngine -> chunkingStrategies "Uses chunking strategies"
                ingestionEngine -> collectionManagement "Logs ingested books to manifest"
                ragQueryEngine -> collectionManagement "Checks collection status"
                calibreIntegration -> ingestionEngine "Provides book paths for ingestion"
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
        gui -> ingestionEngine "Triggers book ingestion with domain selection"
        gui -> ragQueryEngine "Executes RAG queries with parameters"
        gui -> collectionManagement "Displays collection statistics and manifests"
        gui -> calibreIntegration "Browses Calibre library with filters"
    }

    views {
        # System Context View
        systemContext alexandriaSystem "SystemContext" {
            include *
            autolayout lr
            description "System context diagram showing Alexandria RAG System and external dependencies"
        }

        # Container View
        container alexandriaSystem "Containers" {
            include *
            autolayout lr
            description "Container diagram showing major architectural components of Alexandria"
        }

        # Component View (Scripts Package)
        component scripts "Components" {
            include *
            autolayout lr
            description "Component diagram showing internal structure of Scripts Package"
        }

        # Dynamic View: Book Ingestion Flow (Container Level)
        dynamic alexandriaSystem "BookIngestionFlow" "Illustrates the book ingestion process from selection to Qdrant upload" {
            user -> gui "Selects books from Calibre library"
            gui -> scripts "Calls calibre_db.get_all_books()"
            scripts -> calibreDb "Queries book metadata"
            gui -> scripts "Triggers ingest_books.py with domain"
            scripts -> filesystem "Reads book file (EPUB/PDF/TXT)"
            scripts -> qdrant "Uploads chunks with embeddings"
            scripts -> filesystem "Writes manifest JSON/CSV"
            gui -> user "Displays ingestion success"
            autolayout lr
        }

        # Dynamic View: RAG Query Flow (Container Level)
        dynamic alexandriaSystem "RAGQueryFlow" "Illustrates the RAG query process from question to answer" {
            user -> gui "Enters query + parameters"
            gui -> scripts "Calls perform_rag_query()"
            scripts -> qdrant "Semantic search with fetch multiplier"
            scripts -> openrouter "Sends context + query for answer"
            openrouter -> scripts "Returns generated answer"
            scripts -> gui "Returns RAGResult (answer + sources)"
            gui -> user "Displays answer with source citations"
            autolayout lr
        }

        # Dynamic View: Component-Level Ingestion
        dynamic scripts "ComponentIngestionFlow" "Detailed component interactions during book ingestion" {
            calibreIntegration -> ingestionEngine "Provides book path and metadata"
            ingestionEngine -> chunkingStrategies "Applies domain-specific chunking"
            chunkingStrategies -> ingestionEngine "Returns chunks"
            ingestionEngine -> collectionManagement "Logs to manifest"
            autolayout lr
        }

        # Dynamic View: Component-Level Query
        dynamic scripts "ComponentQueryFlow" "Detailed component interactions during RAG query" {
            ragQueryEngine -> collectionManagement "Verifies collection exists"
            collectionManagement -> ragQueryEngine "Returns collection status"
            autolayout lr
        }

        # Styles
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
            element "Person" {
                shape person
                background #08427b
                color #ffffff
            }
            element "Database" {
                shape Cylinder
            }
            element "Storage" {
                shape Folder
            }
            element "Web Browser" {
                shape WebBrowser
            }
        }
    }

    configuration {
        scope softwaresystem
    }
}
