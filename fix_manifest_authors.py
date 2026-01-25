"""
Fix duplicate authors in alexandria_manifest.csv
"""
import csv
from pathlib import Path

manifest_path = Path("logs/alexandria_manifest.csv")

# Read manifest
with open(manifest_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Found {len(rows)} books in manifest")

# Fix duplicate authors
fixed_count = 0
for row in rows:
    author = row['Author']

    # Check if author has duplicates like "Name & Name & Name"
    if ' & ' in author:
        parts = author.split(' & ')
        # Remove duplicates while preserving order
        unique_authors = []
        seen = set()
        for part in parts:
            part_clean = part.strip()
            if part_clean not in seen:
                unique_authors.append(part_clean)
                seen.add(part_clean)

        new_author = ' & '.join(unique_authors)

        if new_author != author:
            print(f"  Fixing: {row['Book Title']}")
            print(f"    OLD: {author}")
            print(f"    NEW: {new_author}")
            row['Author'] = new_author
            fixed_count += 1

print(f"\nFixed {fixed_count} books")

# Write back
with open(manifest_path, 'w', encoding='utf-8', newline='') as f:
    fieldnames = ['Collection', 'Book Title', 'Author', 'Language', 'Domain', 'File Type', 'Chunks', 'Size (MB)', 'File Name', 'Ingested At']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

    # Write TOTAL row
    total_chunks = sum(int(row['Chunks']) for row in rows)
    total_size = sum(float(row['Size (MB)']) for row in rows)
    f.write(f"\nTOTAL,,,,,,{total_chunks},{total_size},,\n")

print(f"✅ Manifest updated: {manifest_path}")
