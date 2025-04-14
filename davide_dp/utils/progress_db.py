import sqlite3
import os

NUMBER_OF_STEPS = 8
DP_STEPS = [f'step_{i}' for i in range(1, NUMBER_OF_STEPS + 1)]


def create_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table 1: event / history of changes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS DAVIDE_DataSynthesis_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_name TEXT NOT NULL,
        step INTEGER NOT NULL,
        status INTEGER NOT NULL,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Table 2: summary of each video's current status
    table = f"""
    CREATE TABLE IF NOT EXISTS DAVIDE_DataSynthesis_summary (
        video_name TEXT PRIMARY KEY
    """
    for step in DP_STEPS:
        table += f", {step} INTEGER DEFAULT 0"
    table += ")"
    cursor.execute(table)
    conn.commit()
    conn.close()


def initialize_summary_from_raw_list(raw_list:list, db_path:str):
    """
    Read a list of video names (one per line) from `file_path`.
    For each video name, insert a row with all steps set to False (0),
    but only if it doesn't already exist in the database.
    """
    assert isinstance(raw_list, list), "raw_list must be a list of video names."
    assert isinstance(db_path, str), "db_path must be a string."
    assert os.path.exists(db_path), f"Database path {db_path} does not exist."
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for video_name in raw_list:            
        # Insert a row if not existing. By using INSERT OR IGNORE,
        # we won't overwrite existing rows.
        cursor.execute("""
            INSERT OR IGNORE INTO DAVIDE_DataSynthesis_summary (
                video_name
            ) VALUES (?)
        """, (video_name,))
    
    conn.commit()
    conn.close()


def log_step_event(video_name, dp_step, new_status, db_path):
    """
    Log a new event that step_number (and optionally substep_id) for a video
    has changed to new_status (0 or 1).
    """
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO DAVIDE_DataSynthesis_events (video_name, step, status)
        VALUES (?, ?, ?)
    """, (video_name, dp_step, new_status))
    
    conn.commit()
    conn.close()


def update_summary_for_video(video_name, db_path):
    """
    Recompute the current status of steps 1..8 for the given video
    by looking at the latest events in DAVIDE_DataSynthesis_events.
    """
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Check if we have a row in summary. If not, create one.
    cursor.execute("""
        INSERT OR IGNORE INTO DAVIDE_DataSynthesis_summary (video_name)
        VALUES (?)
    """, (video_name,))
    
    # For each step, we can look at the latest event or just see if there's any event with status=1.
    # EXACT logic depends on your use-case. We'll do a simplified approach:
    for step in DP_STEPS:
        # Check if there's *any* event for this step with status=1
        cursor.execute("""
            SELECT COUNT(*) 
            FROM DAVIDE_DataSynthesis_events
            WHERE video_name = ? AND step = ? AND status = 1
        """, (video_name, step))
        
        count = cursor.fetchone()[0]
        # If there's at least one record with status=1, we consider the step "complete"
        step_complete = 1 if count > 0 else 0
        
        # Update the summary
        cursor.execute(f"""
            UPDATE DAVIDE_DataSynthesis_summary
               SET {step} = ?
             WHERE video_name = ?
        """, (step_complete, video_name))
    
    conn.commit()
    conn.close()


def is_step_complete(dp_step, db_path, videos):
    """
    Returns True if the specified step is marked as complete (1)
    in the summary table for the given video_name. Otherwise, returns False.
    """
    assert dp_step in DP_STEPS, f"Step must be one of {DP_STEPS}"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if isinstance(videos, str):
        videos = [videos]
    results = []
    
    for video in videos:
        query = f"""
            SELECT {dp_step}
            FROM DAVIDE_DataSynthesis_summary
            WHERE video_name = ?
        """
        cursor.execute(query, (video,))
        row = cursor.fetchone()
        
        # If no row is found for this video, return False (not in table).
        if row is None:
            print(f"No row found for video {video}.")
            return False
        
        # row is a tuple like (step_value,)
        step_value = row[0]
        if not step_value:
            print(f"Step {dp_step} is not complete for video {video}.")
        results.append(bool(step_value))
    
    conn.close()
    return all(results)
