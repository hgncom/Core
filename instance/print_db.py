import sqlite3
import pprint

def print_database_contents(db_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Retrieve a list of all tables in the database
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()

    # Initialize PrettyPrinter
    pp = pprint.PrettyPrinter(indent=4)

    # Iterate over all tables and print their contents
    for table_name in tables:
        print(f"Contents of table '{table_name[0]}':")
        cur.execute(f"SELECT * FROM {table_name[0]};")
        table_contents = cur.fetchall()

        # Print the contents of each table
        pp.pprint(table_contents)
        print("\n")  # Add a newline for better readability between tables

    # Close the database connection
    conn.close()

db_path = './hgn.db'
print_database_contents(db_path)
