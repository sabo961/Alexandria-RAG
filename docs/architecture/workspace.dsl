workspace "Alexandria RAG System" "Semantic search and knowledge synthesis across 9,000 books" {

    model {
        # People
        user = person "Developer/Researcher" "Uses Alexandria via Claude Code for semantic search and knowledge synthesis"

        # External AI Agent
        claudeCode = softwareSystem "Claude Code" "AI coding assistant that connects to Alexandria via MCP" {
            tags "External" "AI"
        }

        # Software Systems
        alexandriaSystem = softwareSystem "Alexandria RAG System" "Retrieval-Augmented Generation system for multi-disciplinary book library" {

            # ============================================
            # MCP SERVER - Primary Interface
            # ============================================
            mcpServer = container "MCP Server" "Model Context Protocol server exposing Alexandria tools to AI agents" "Python 3.14, FastMCP" {
                tags "Interface"

                # Query Tools
                queryTool = component "alexandria_query" "Semantic search + LLM answer generation with context modes" "Tool" {
                    tags "Tool" "Query"
                }
                searchTool = component "alexandria_search" "Pure vector search without LLM" "Tool" {
                    tags "Tool" "Query"
                }
                bookTool = component "alexandria_book" "Get full book metadata and chunks" "Tool" {
                    tags "Tool" "Query"
                }
                statsTool = component "alexandria_stats" "Collection statistics and health" "Tool" {
                    tags "Tool" "Management"
                }

                # Ingest Tools
                ingestTool = component "alexandria_ingest" "Ingest single book by Calibre ID" "Tool" {
                    tags "Tool" "Ingestion"
                }
                batchIngestTool = component "alexandria_batch_ingest" "Batch ingest by author/tag/list" "Tool" {
                    tags "Tool" "Ingestion"
                }
                fileIngestTool = component "alexandria_ingest_file" "Ingest local file directly" "Tool" {
                    tags "Tool" "Ingestion"
                }
                testChunkingTool = component "alexandria_test_chunking_file" "Preview chunking without ingesting" "Tool" {
                    tags "Tool" "Ingestion"
                }
            }

            # ============================================
            # SCRIPTS PACKAGE - Business Logic
            # ============================================
            scripts = container "Scripts Package" "Core business logic for ingestion, chunking, querying" "Python 3.14" {

                # --- INGESTION COMPONENTS ---
                textExtractor = component "Text Extractor" "Parses EPUB/PDF/TXT into raw text with metadata" "ingest_books.py" {
                    tags "Ingestion"
                }

                chapterDetector = component "Chapter Detector" "Detects chapter boundaries from EPUB NCX/NAV, PDF outline, or heuristics" "chapter_detection.py" {
                    tags "Ingestion"
                }

                universalChunker = component "Universal Semantic Chunker" "Splits text by semantic similarity using sentence embeddings" "universal_chunking.py" {
                    tags "Ingestion" "Core" "AI"
                }

                embedder = component "Embedder" "Converts text to 384-dim vectors" "SentenceTransformer" {
                    tags "Ingestion" "Query" "AI"
                }

                hierarchicalIngester = component "Hierarchical Ingester" "Creates parent (chapter) + child (semantic) chunk structure" "ingest_books.py" {
                    tags "Ingestion"
                }

                qdrantUploader = component "Qdrant Uploader" "Batches and uploads vectors + payloads" "ingest_books.py" {
                    tags "Ingestion"
                }

                # --- QUERY COMPONENTS ---
                ragQueryEngine = component "RAG Query Engine" "Semantic search with context modes (precise/contextual/comprehensive)" "rag_query.py" {
                    tags "Query"
                }

                parentFetcher = component "Parent Chunk Fetcher" "Retrieves parent context for hierarchical results" "rag_query.py" {
                    tags "Query"
                }

                responsePatterns = component "Response Patterns" "RAG discipline templates (direct, synthesis, critical...)" "prompts/patterns.json" {
                    tags "Query"
                }

                # --- MANAGEMENT COMPONENTS ---
                collectionManifest = component "Collection Manifest" "Tracks ingested books per collection with CSV export" "collection_manifest.py" {
                    tags "Management"
                }

                calibreDB = component "Calibre Integration" "SQLite access to Calibre library metadata" "calibre_db.py" {
                    tags "Integration"
                }

                # Internal Flow - Ingestion
                calibreDB -> textExtractor "File path + metadata"
                textExtractor -> chapterDetector "Raw text"
                chapterDetector -> universalChunker "Chapters + text"
                universalChunker -> embedder "Sentences for similarity"
                universalChunker -> hierarchicalIngester "Semantic chunks"
                hierarchicalIngester -> embedder "Chunks for embedding"
                hierarchicalIngester -> qdrantUploader "Parent + child chunks"
                qdrantUploader -> collectionManifest "Log success"

                # Internal Flow - Query
                ragQueryEngine -> embedder "Embed query"
                ragQueryEngine -> parentFetcher "Fetch context"
                ragQueryEngine -> responsePatterns "Apply template"
            }

            # ============================================
            # STORAGE
            # ============================================
            filesystem = container "File System" "Book files (ingest/, ingested/) and logs" "Local FS" "Storage"
            calibreLibrary = container "Calibre Library" "9,000 books with metadata" "SQLite + Files" "Database"
        }

        # External Systems
        qdrant = softwareSystem "Qdrant Vector DB" "Vector search engine (192.168.0.151:6333)" {
            tags "External" "Database"
        }

        openrouter = softwareSystem "OpenRouter API" "LLM inference (Claude, GPT-4, etc.)" {
            tags "External" "AI"
        }

        # ============================================
        # RELATIONSHIPS - System Context
        # ============================================
        user -> claudeCode "Asks questions, requests ingestion"
        claudeCode -> alexandriaSystem "Calls MCP tools"
        alexandriaSystem -> qdrant "Stores/retrieves vectors"
        alexandriaSystem -> openrouter "Generates answers"

        # ============================================
        # RELATIONSHIPS - Container Level
        # ============================================
        claudeCode -> mcpServer "stdio (MCP protocol)"
        mcpServer -> scripts "Calls business logic"
        scripts -> filesystem "Reads books, writes logs"
        scripts -> calibreLibrary "Queries metadata"
        scripts -> qdrant "Vector operations"
        scripts -> openrouter "LLM calls"

        # ============================================
        # RELATIONSHIPS - MCP Tools to Components
        # ============================================
        # Query tools
        queryTool -> ragQueryEngine "Executes search + LLM"
        searchTool -> ragQueryEngine "Executes search only"
        bookTool -> calibreDB "Gets metadata"
        bookTool -> qdrantUploader "Gets chunks"
        statsTool -> collectionManifest "Gets stats"

        # Ingest tools
        ingestTool -> calibreDB "Gets book path"
        ingestTool -> textExtractor "Starts pipeline"
        batchIngestTool -> calibreDB "Queries books"
        batchIngestTool -> textExtractor "Batch pipeline"
        fileIngestTool -> textExtractor "Direct file"
        testChunkingTool -> universalChunker "Preview only"

        # Backend to External
        qdrantUploader -> qdrant "Upserts vectors"
        ragQueryEngine -> qdrant "Searches vectors"
        ragQueryEngine -> openrouter "Generates answers"
    }

    views {
        # ============================================
        # SYSTEM CONTEXT - Bird's eye view
        # ============================================
        systemContext alexandriaSystem "SystemContext" {
            include *
            autolayout lr
            description "How Alexandria fits in the ecosystem"
        }

        # ============================================
        # CONTAINERS - Major building blocks
        # ============================================
        container alexandriaSystem "Containers" {
            include *
            autolayout lr
            description "Alexandria's main containers and external dependencies"
        }

        # ============================================
        # MCP SERVER - Tool breakdown
        # ============================================
        component mcpServer "MCPServerTools" {
            include *
            autolayout tb
            description "MCP Server tools exposed to Claude Code"
        }

        # ============================================
        # SCRIPTS - Business logic components
        # ============================================
        component scripts "ScriptsComponents" {
            include *
            autolayout lr
            description "Core business logic in scripts/ package"
        }

        # ============================================
        # DYNAMIC - Query Flow
        # ============================================
        dynamic alexandriaSystem "RAGQueryFlow" "How a query flows through the system" {
            queryTool -> ragQueryEngine "1. Execute search"
            ragQueryEngine -> embedder "2. Embed query"
            ragQueryEngine -> qdrant "3. Vector search"
            ragQueryEngine -> parentFetcher "4. Fetch parent context"
            ragQueryEngine -> responsePatterns "5. Apply RAG template"
            ragQueryEngine -> openrouter "6. Generate answer"
            autolayout lr
        }

        # ============================================
        # DYNAMIC - Ingestion Flow
        # ============================================
        dynamic alexandriaSystem "BookIngestionFlow" "How a book gets ingested" {
            ingestTool -> calibreDB "1. Get book info"
            ingestTool -> textExtractor "2. Start extraction"
            calibreDB -> textExtractor "3. File path + metadata"
            textExtractor -> chapterDetector "4. Raw text"
            chapterDetector -> universalChunker "5. Chapters"
            universalChunker -> embedder "6. Similarities"
            universalChunker -> hierarchicalIngester "7. Chunks"
            hierarchicalIngester -> qdrantUploader "8. Batch"
            qdrantUploader -> qdrant "9. Upsert"
            qdrantUploader -> collectionManifest "10. Log"
            autolayout lr
        }

        styles {
            element "Software System" {
                background #1168bd
                color #ffffff
                shape RoundedBox
            }
            element "External" {
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
            element "Interface" {
                background #d4a017
                color #000000
            }
            element "Tool" {
                background #f5d742
                color #000000
                shape Hexagon
            }
            element "Ingestion" {
                background #2d8a5f
                color #ffffff
            }
            element "Query" {
                background #8a2d58
                color #ffffff
            }
            element "AI" {
                background #5c2d8a
                color #ffffff
            }
            element "Management" {
                background #2d5c8a
                color #ffffff
            }
            element "Database" {
                shape Cylinder
            }
            element "Storage" {
                shape Folder
            }
        }
    }

    !docs README.md
    !docs c4
    !docs technical
}
