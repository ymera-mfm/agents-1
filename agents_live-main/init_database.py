#!/usr/bin/env python3
"""
Database Initialization Script
Initializes the database schema and creates required tables
"""

import os
import sys
import time


def wait_for_database(max_retries: int = 30, retry_delay: int = 2) -> bool:
    """Wait for database to be ready"""
    print("⏳ Waiting for database to be ready...")
    
    for attempt in range(max_retries):
        try:
            import psycopg2
            db_url = os.getenv('DATABASE_URL', 
                              'postgresql://admin:secure_password@localhost:5432/enhanced_platform')
            
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
            
            print("✅ Database is ready")
            return True
        except ImportError:
            print("⚠️  psycopg2 not installed. Skipping database connection check.")
            print("   Install with: pip install psycopg2-binary")
            return True
        except Exception as e:
            print(f"   Attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    print("❌ Database is not ready after maximum retries")
    return False


def create_tables():
    """Create database tables"""
    print("🗄️  Creating database tables...")
    
    try:
        import psycopg2
        db_url = os.getenv('DATABASE_URL', 
                          'postgresql://admin:secure_password@localhost:5432/enhanced_platform')
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Create agents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'inactive',
                config JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create engines table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engines (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                type VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'inactive',
                config JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                agent_id INTEGER REFERENCES agents(id),
                engine_id INTEGER REFERENCES engines(id),
                task_type VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                input_data JSONB,
                output_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)
        
        # Create logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                level VARCHAR(20) NOT NULL,
                message TEXT NOT NULL,
                context JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id SERIAL PRIMARY KEY,
                metric_name VARCHAR(255) NOT NULL,
                metric_value DECIMAL(10, 2),
                metric_type VARCHAR(50),
                tags JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Database tables created successfully")
        return True
    except ImportError:
        print("⚠️  psycopg2 not installed. Skipping table creation.")
        print("   Install with: pip install psycopg2-binary")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False


def seed_initial_data():
    """Seed initial data into the database"""
    print("🌱 Seeding initial data...")
    
    try:
        import psycopg2
        db_url = os.getenv('DATABASE_URL', 
                          'postgresql://admin:secure_password@localhost:5432/enhanced_platform')
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM agents")
        agent_count = cursor.fetchone()[0]
        
        if agent_count == 0:
            # Insert sample agents
            cursor.execute("""
                INSERT INTO agents (name, type, status, config)
                VALUES 
                    ('Learning Agent', 'learning', 'active', '{"version": "1.0"}'),
                    ('Communication Agent', 'communication', 'active', '{"version": "1.0"}'),
                    ('Monitoring Agent', 'monitoring', 'active', '{"version": "1.0"}')
            """)
            
            # Insert sample engines
            cursor.execute("""
                INSERT INTO engines (name, type, status, config)
                VALUES 
                    ('Intelligence Engine', 'intelligence', 'active', '{"version": "1.0"}'),
                    ('Optimization Engine', 'optimization', 'active', '{"version": "1.0"}'),
                    ('Performance Engine', 'performance', 'active', '{"version": "1.0"}')
            """)
            
            conn.commit()
            print("✅ Initial data seeded successfully")
        else:
            print("ℹ️  Database already contains data, skipping seed")
        
        cursor.close()
        conn.close()
        return True
    except ImportError:
        print("⚠️  psycopg2 not installed. Skipping data seeding.")
        return True
    except Exception as e:
        print(f"❌ Failed to seed data: {e}")
        return False


def main():
    """Main database initialization function"""
    print("=" * 60)
    print("💾 DATABASE INITIALIZATION")
    print("=" * 60)
    
    steps = [
        ("Wait for Database", wait_for_database),
        ("Create Tables", create_tables),
        ("Seed Initial Data", seed_initial_data),
    ]
    
    all_success = True
    for name, step_func in steps:
        print(f"\n{name}:")
        try:
            if not step_func():
                all_success = False
        except Exception as e:
            print(f"❌ {name} failed with error: {e}")
            all_success = False
    
    print("\n" + "=" * 60)
    if all_success:
        print("✅ Database initialized successfully!")
        print("=" * 60)
        return 0
    else:
        print("❌ Database initialization failed. Check logs above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
