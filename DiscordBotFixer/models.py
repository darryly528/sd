import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise Exception("DATABASE_URL not found in environment variables")
        
        # Initialize database and create tables
        self._create_tables()
    
    @contextmanager
    def get_connection(self):
        # Ensure SSL mode for Railway deployment
        database_url = self.database_url
        if 'sslmode=' not in database_url and ('railway' in database_url.lower() or os.getenv('RAILWAY') == 'true'):
            if '?' in database_url:
                database_url += '&sslmode=require'
            else:
                database_url += '?sslmode=require'
        
        conn = psycopg2.connect(database_url)
        try:
            yield conn
        finally:
            conn.close()
    
    def _create_tables(self):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Create table for storing Roblox usernames
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS roblox_users (
                        discord_user_id BIGINT PRIMARY KEY,
                        roblox_username VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Create table for tracking ticket conversations
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ticket_conversations (
                        id SERIAL PRIMARY KEY,
                        discord_user_id BIGINT NOT NULL,
                        channel_id BIGINT NOT NULL,
                        conversation_state VARCHAR(50) DEFAULT 'started',
                        is_reporting_member BOOLEAN DEFAULT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                conn.commit()
    
    def save_roblox_username(self, discord_user_id, roblox_username):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO roblox_users (discord_user_id, roblox_username, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (discord_user_id)
                    DO UPDATE SET roblox_username = EXCLUDED.roblox_username, updated_at = CURRENT_TIMESTAMP
                """, (discord_user_id, roblox_username))
                conn.commit()
    
    def get_roblox_username(self, discord_user_id):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT roblox_username FROM roblox_users WHERE discord_user_id = %s", (discord_user_id,))
                result = cur.fetchone()
                return result['roblox_username'] if result else None
    
    def save_ticket_conversation(self, discord_user_id, channel_id, conversation_state='started'):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ticket_conversations (discord_user_id, channel_id, conversation_state, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                """, (discord_user_id, channel_id, conversation_state))
                conn.commit()
    
    def update_ticket_conversation(self, channel_id, conversation_state=None, is_reporting_member=None):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                updates = []
                params = []
                
                if conversation_state is not None:
                    updates.append("conversation_state = %s")
                    params.append(conversation_state)
                
                if is_reporting_member is not None:
                    updates.append("is_reporting_member = %s")
                    params.append(is_reporting_member)
                
                if updates:
                    updates.append("updated_at = CURRENT_TIMESTAMP")
                    params.append(channel_id)
                    
                    query = f"UPDATE ticket_conversations SET {', '.join(updates)} WHERE channel_id = %s"
                    cur.execute(query, params)
                    conn.commit()
    
    def get_ticket_conversation(self, channel_id):
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM ticket_conversations WHERE channel_id = %s", (channel_id,))
                return cur.fetchone()