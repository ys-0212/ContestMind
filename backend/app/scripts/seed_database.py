import os
import sys
import json
import psycopg2
from pathlib import Path

# Add backend directory to sys.path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.config import settings

def init_problems_table(cursor):
    print("Initializing problems table if not exists...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public.problems (
            problem_id VARCHAR(50) PRIMARY KEY,
            title TEXT NOT NULL,
            rating INTEGER,
            tags TEXT[],
            url TEXT,
            statement TEXT,
            editorial TEXT,
            source VARCHAR(50) DEFAULT 'codeforces',
            examples JSONB,
            has_statement BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
        );
    """)

def seed_problems(cursor):
    input_file = settings.PROCESSED_DATA_DIR / "problems.jsonl"
    if not input_file.exists():
        print(f"File not found: {input_file}")
        return

    print("Seeding problems...")
    insert_query = """
        INSERT INTO public.problems (problem_id, title, rating, tags, url, statement, editorial, source, examples, has_statement)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (problem_id) DO UPDATE SET
            title = EXCLUDED.title,
            rating = EXCLUDED.rating,
            tags = EXCLUDED.tags,
            url = EXCLUDED.url,
            statement = EXCLUDED.statement,
            editorial = EXCLUDED.editorial,
            examples = EXCLUDED.examples,
            has_statement = EXCLUDED.has_statement;
    """

    count = 0
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            try:
                data = json.loads(line)
                problem_id = data.get("problem_id", "").strip().upper()
                if not problem_id:
                    continue
                
                tags = data.get("tags", [])
                examples = data.get("examples", [])
                
                cursor.execute(insert_query, (
                    problem_id,
                    data.get("title", f"Problem {problem_id}"),
                    data.get("rating"),
                    tags,
                    data.get("url", ""),
                    data.get("statement"),
                    data.get("editorial"),
                    data.get("source", "codeforces"),
                    json.dumps(examples),
                    bool(data.get("statement"))
                ))
                count += 1
                if count % 100 == 0:
                    print(f"Inserted {count} problems...")
            except Exception as e:
                print(f"Error inserting problem: {e}")

    print(f"Finished seeding {count} problems.")

def main():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL must be set in .env")
        sys.exit(1)

    print("Connecting to Supabase PostgreSQL...")
    conn = psycopg2.connect(database_url)
    conn.autocommit = True
    cursor = conn.cursor()

    try:
        init_problems_table(cursor)
        seed_problems(cursor)
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
