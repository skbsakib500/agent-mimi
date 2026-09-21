from mimi.database import get_db

def add_goal(title, description="", deadline=None, priority="medium", progress=0):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO goals (title, description, deadline, priority, progress, status) VALUES (?, ?, ?, ?, ?, 'active')",
        (title, description, deadline, priority, progress)
    )
    conn.commit()
    conn.close()

def list_goals(sort_by="id"):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT id, title, priority, progress, status, deadline, description FROM goals"
    if sort_by == "priority":
        query += " ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END"
    elif sort_by == "progress":
        query += " ORDER BY progress DESC"
    else:
        query += " ORDER BY id DESC"

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return rows

def edit_goal(goal_id, title=None, priority=None, deadline=None):
    conn = get_db()
    cursor = conn.cursor()
    if title:
        cursor.execute("UPDATE goals SET title = ? WHERE id = ?", (title, goal_id))
    if priority:
        cursor.execute("UPDATE goals SET priority = ? WHERE id = ?", (priority, goal_id))
    if deadline:
        cursor.execute("UPDATE goals SET deadline = ? WHERE id = ?", (deadline, goal_id))
    conn.commit()
    conn.close()

def delete_goal(goal_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()

def update_goal_progress(goal_id, progress):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE goals SET progress = ? WHERE id = ?", (progress, goal_id))
    conn.commit()
    conn.close()
