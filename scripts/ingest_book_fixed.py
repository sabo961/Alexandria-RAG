def ingest_book(
    filepath: str,
    domain: str = 'technical',
    collection_name: str = 'alexandria',
    qdrant_host: str = 'localhost',
    qdrant_port: int = 6333
):
    """
    Main ingestion pipeline: Extract → Chunk → Embed → Upload

    Args:
        filepath: Path to book file (EPUB/PDF/TXT)
        domain: Domain category for chunking strategy
        collection_name: Qdrant collection name
        qdrant_host: Qdrant server host
        qdrant_port: Qdrant server port
    """
    logger.info(f"Starting ingestion pipeline for: {filepath}")
    
    # DIAGNOSTIC CHECK
    try:
        if os.path.exists(filepath):
            file_stat = os.stat(filepath)
            logger.info(f"✅ File exists. Size: {file_stat.st_size} bytes")
        else:
            logger.error(f"❌ File does not exist at path: {filepath}")
            return {'success': False, 'error': 'File not found (os.path.exists failed)'}
    except OSError as e:
        logger.error(f"❌ OS Error checking file stats: {e}")
        return {'success': False, 'error': f'OS Error: {e}'}
        
    logger.info(f"Domain: {domain} | Collection: {collection_name}")

    # Step 1: Extract text
    sections, metadata = extract_text(filepath)
    logger.info(f"Book: {metadata['title']} by {metadata['author']}")

    # Check if any content was extracted
    if not sections or all(not section.get('text', '').strip() for section in sections):
        logger.error(f"❌ No content extracted from {filepath}")
        logger.error("   The file may be encrypted, corrupted, or in an unsupported format")
        return {'success': False, 'error': 'No content extracted'}

    # Step 2: Calculate optimal chunking parameters
    optimal_params = calculate_optimal_chunk_params(sections, domain=domain)

    # Step 3: Chunk text
    # For PDFs, merge all pages before chunking (better chunk sizes)
    # For EPUBs, keep chapters separate (preserve structure)
    file_format = metadata.get('format', '')
    merge_sections = (file_format == 'PDF')

    chunks = create_chunks_from_sections(
        sections,
        metadata,
        domain=domain,
        max_tokens=optimal_params['max_tokens'],
        overlap=optimal_params['overlap'],
        merge_sections=merge_sections
    )

    actual_chunks = len(chunks)
    target_chunks = optimal_params['target_chunks']
    efficiency = (target_chunks / actual_chunks * 100) if actual_chunks > 0 else 0

    logger.info(f"Total chunks created: {actual_chunks} (target: ~{target_chunks}, efficiency: {efficiency:.0f}%)")

    # Step 4: Generate embeddings
    embedding_gen = EmbeddingGenerator()
    texts = [chunk['text'] for chunk in chunks]
    embeddings = embedding_gen.generate_embeddings(texts)

    # Step 5: Upload to Qdrant
    upload_to_qdrant(
        chunks=chunks,
        embeddings=embeddings,
        domain=domain,
        collection_name=collection_name,
        qdrant_host=qdrant_host,
        qdrant_port=qdrant_port
    )

    logger.info(f"✅ Ingestion complete for: {metadata['title']}")

    # Return success status and metadata for manifest logging
    return {
        'success': True,
        'title': metadata.get('title', 'Unknown'),
        'author': metadata.get('author', 'Unknown'),
        'chunks': len(chunks),
        'file_size_mb': os.path.getsize(filepath) / (1024 * 1024),
        'filepath': filepath
    }
