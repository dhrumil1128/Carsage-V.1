import sqlite3

def view_feedback():
    conn = sqlite3.connect('feedback.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM feedback")
    rows = cursor.fetchall()

    if len(rows) > 0:
        print(f"Successfully retrieved {len(rows)} feedback entries:")
        for row in rows:
            print(row)
    else:
        print("No feedback entries found.")

    conn.close()

# View the feedback entries
view_feedback()
