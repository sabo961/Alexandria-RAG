import sqlite3
from pathlib import Path

# Connect to Calibre DB
db_path = Path(r"G:\My Drive\alexandria\metadata.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find the book
cursor.execute("""
SELECT b.id, b.title, a.name, bal.author as author_id
FROM books b
LEFT JOIN books_authors_link bal ON b.id = bal.book
LEFT JOIN authors a ON bal.author = a.id
WHERE b.title LIKE '%Son of Hamas%'
ORDER BY b.id, bal.id
""")

print("Book ID | Title | Author Name | Author ID")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row[0]:7} | {row[1][:30]:30} | {row[2]:20} | {row[3]}")

# Check GROUP_CONCAT with and without DISTINCT
print("\n\nWithout DISTINCT:")
cursor.execute("""
SELECT b.id, b.title, GROUP_CONCAT(a.name, ' & ') as authors
FROM books b
LEFT JOIN books_authors_link bal ON b.id = bal.book
LEFT JOIN authors a ON bal.author = a.id
WHERE b.title LIKE '%Son of Hamas%'
GROUP BY b.id
""")
for row in cursor.fetchall():
    print(f"{row[0]:7} | {row[1][:40]:40} | {row[2]}")

print("\n\nWith DISTINCT (no separator - SQLite limitation):")
cursor.execute("""
SELECT b.id, b.title, GROUP_CONCAT(DISTINCT a.name) as authors
FROM books b
LEFT JOIN books_authors_link bal ON b.id = bal.book
LEFT JOIN authors a ON bal.author = a.id
WHERE b.title LIKE '%Son of Hamas%'
GROUP BY b.id
""")
for row in cursor.fetchall():
    print(f"{row[0]:7} | {row[1][:40]:40} | {row[2]}")
    print("Note: DISTINCT removes duplicates but separator is comma, not ' & '")

conn.close()
