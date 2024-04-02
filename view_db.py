import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('hgn.db')

# Create a cursor object
cur = conn.cursor()

# Execute your query
cur.execute("SELECT * FROM wallets WHERE username='test11'")

# Fetch and print all rows of the query result
rows = cur.fetchall()
for row in rows:
    print(row)

# Close the connection
conn.close()
