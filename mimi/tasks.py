from mimi.database import get_db

def add_task(title, mission_id=0, description="", due_date=None, priority="medium"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, mission_id, description, due_date, priority, status) VALUES (?, ?, ?, ?, ?, 'active')",
        (title, mission_id, description, due_date, priority)
    )
    conn.commit()
    conn.close()

def list_tasks(sort_by="id", status_filter=None):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT id, title, priority, status, due_date, description FROM tasks"
    params = []
    where_clauses = []

    if status_filter:
        where_clauses.append("status = ?")
        params.append(status_filter)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    if sort_by == "priority":
        query += " ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END"
    elif sort_by == "due_date":
        query += " ORDER BY due_date ASC"
    else:
        query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def edit_task(task_id, title=None, priority=None, due_date=None):
    conn = get_db()
    cursor = conn.cursor()
    if title:
        cursor.execute("UPDATE tasks SET title = ? WHERE id = ?", (title, task_id))
    if priority:
        cursor.execute("UPDATE tasks SET priority = ? WHERE id = ?", (priority, task_id))
    if due_date:
        cursor.execute("UPDATE tasks SET due_date = ? WHERE id = ?", (due_date, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def complete_task(task_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
