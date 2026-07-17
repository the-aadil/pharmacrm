# init_db.py
import sqlite3
import os


def get_postgres_schema() -> str:
    """Return PostgreSQL-compatible CREATE TABLE statements for all CRM tables."""
    return """
    CREATE TABLE IF NOT EXISTS hcps (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        specialty VARCHAR(255)
    );

    CREATE TABLE IF NOT EXISTS interactions (
        id SERIAL PRIMARY KEY,
        hcp_name VARCHAR(255) NOT NULL,
        interaction_type VARCHAR(50),
        duration_minutes INTEGER,
        topics_discussed TEXT,
        sentiment VARCHAR(20),
        next_steps TEXT,
        ai_summary TEXT,
        compliance_flag BOOLEAN DEFAULT FALSE,
        compliance_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS interaction_products (
        id SERIAL PRIMARY KEY,
        interaction_id INTEGER REFERENCES interactions(id),
        product_name VARCHAR(255),
        samples_given INTEGER DEFAULT 0,
        lot_number VARCHAR(100)
    );

    CREATE TABLE IF NOT EXISTS interaction_edit_history (
        id SERIAL PRIMARY KEY,
        interaction_id INTEGER REFERENCES interactions(id),
        edited_field VARCHAR(100),
        old_value TEXT,
        new_value TEXT,
        edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS follow_ups (
        id SERIAL PRIMARY KEY,
        interaction_id INTEGER REFERENCES interactions(id),
        hcp_name VARCHAR(255),
        due_date VARCHAR(20),
        note TEXT,
        status VARCHAR(20) DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS chat_sessions (
        id SERIAL PRIMARY KEY,
        thread_id VARCHAR(255) UNIQUE,
        rep_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS chat_messages (
        id SERIAL PRIMARY KEY,
        session_id INTEGER REFERENCES chat_sessions(id),
        role VARCHAR(20),
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """


def initialize_database():
    """Create all tables and seed initial data for the Pharma CRM."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pharma_crm.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS hcps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialty TEXT
    );

    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hcp_name TEXT NOT NULL,
        interaction_type TEXT,
        duration_minutes INTEGER,
        topics_discussed TEXT,
        sentiment TEXT,
        next_steps TEXT,
        ai_summary TEXT,
        compliance_flag INTEGER DEFAULT 0,
        compliance_notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS interaction_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interaction_id INTEGER,
        product_name TEXT,
        samples_given INTEGER DEFAULT 0,
        lot_number TEXT,
        FOREIGN KEY (interaction_id) REFERENCES interactions(id)
    );

    CREATE TABLE IF NOT EXISTS interaction_edit_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interaction_id INTEGER,
        edited_field TEXT,
        old_value TEXT,
        new_value TEXT,
        edited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS follow_ups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        interaction_id INTEGER,
        hcp_name TEXT,
        due_date TEXT,
        note TEXT,
        status TEXT DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS chat_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        thread_id TEXT UNIQUE,
        rep_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        role TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
    );
    """)
    
    # Seed HCPs
    seed_hcps = [
        ("Dr. Smith", "Pulmonologist"),
        ("Dr. Sarah Jenkins", "Cardiologist"),
        ("Dr. Alex Kumar", "General Practice"),
        ("Dr. Robert Chen", "Neurologist"),
        ("Dr. Lisa Park", "Rheumatologist"),
        ("Dr. James Wong", "Neurologist"),
        ("Dr. Priya Sharma", "Oncologist"),
        ("Dr. Aadil Khan", "General Practice"),
        ("Dr. Aadil", "General Practice"),
    ]
    for name, specialty in seed_hcps:
        cursor.execute("SELECT COUNT(*) FROM hcps WHERE name = ?", (name,))
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO hcps (name, specialty) VALUES (?, ?)", (name, specialty))
        conn.commit()
    conn.close()
    print("Database initialized successfully with all tables and seed data.")

if __name__ == "__main__":
    initialize_database()