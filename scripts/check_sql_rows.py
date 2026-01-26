import sqlite3
from pathlib import Path

# Connect to Calibre DB
db_path = Path(r"G:\My Drive\alexandria\metadata.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Run the exact same query as calibre_db.py
query = """
SELECT
    b.id,
    b.title,
    b.path,
    b.timestamp,
    b.pubdate,
    b.isbn,
    b.series_index,
    GROUP_CONCAT(DISTINCT a.name) as authors,
    GROUP_CONCAT(DISTINCT l.lang_code) as languages,
    GROUP_CONCAT(DISTINCT t.name) as tags,
    s.name as series_name,
    p.name as publisher,
    r.rating
FROM books b
LEFT JOIN books_authors_link bal ON b.id = bal.book
LEFT JOIN authors a ON bal.author = a.id
LEFT JOIN books_languages_link bll ON b.id = bll.book
LEFT JOIN languages l ON bll.lang_code = l.id
LEFT JOIN books_tags_link btl ON b.id = btl.book
LEFT JOIN tags t ON btl.tag = t.id
LEFT JOIN books_series_link bsl ON b.id = bsl.book
LEFT JOIN series s ON bsl.series = s.id
LEFT JOIN books_publishers_link bpl ON b.id = bpl.book
LEFT JOIN publishers p ON bpl.publisher = p.id
LEFT JOIN books_ratings_link brl ON b.id = brl.book
LEFT JOIN ratings r ON brl.rating = r.id
WHERE b.title LIKE '%Son of Hamas%'
GROUP BY b.id
ORDER BY b.timestamp DESC
"""

cursor.execute(query)
rows = cursor.fetchall()

print(f"Number of rows returned: {len(rows)}")
print("\nRows:")
for i, row in enumerate(rows):
    print(f"\nRow {i+1}:")
    print(f"  ID: {row[0]}")
    print(f"  Title: {row[1]}")
    print(f"  Authors: {row[7]}")

conn.close()
