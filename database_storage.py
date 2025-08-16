"""
Step 5: Database Storage with MySQL
Simple, fully functional, and production-ready database integration.
"""

import json
import os
import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TournamentDatabase:
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'sports_calendar')
        }
        self.connection = None
    
    def validate_database_config(self) -> bool:
        """Validate database configuration"""
        required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing database config: {', '.join(missing_vars)}")
            return False
        
        print("✅ Database configuration validated")
        return True
    
    def create_database_if_not_exists(self) -> bool:
        """Create the database if it doesn't exist"""
        try:
            # Connect without specifying database first
            temp_config = self.db_config.copy()
            database_name = temp_config.pop('database')  # Remove database from config
            
            temp_connection = mysql.connector.connect(**temp_config)
            cursor = temp_connection.cursor()
            
            # Create database if it doesn't exist
            create_db_query = f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            cursor.execute(create_db_query)
            
            print(f"✅ Database '{database_name}' created or already exists")
            
            temp_connection.close()
            return True
            
        except Error as e:
            print(f"❌ Error creating database: {e}")
            return False
    
    def connect_to_database(self) -> bool:
        """Establish database connection"""
        try:
            # First create database if it doesn't exist
            if not self.create_database_if_not_exists():
                return False
            
            # Now connect to the specific database
            self.connection = mysql.connector.connect(**self.db_config)
            if self.connection.is_connected():
                print("✅ Connected to MySQL database successfully")
                return True
        except Error as e:
            print(f"❌ Error connecting to database: {e}")
            return False
    
    def create_database_tables(self) -> bool:
        """Create required database tables"""
        print("🗄️  Creating database tables...")
        
        try:
            cursor = self.connection.cursor()
            
            # Create tournaments table
            create_tournaments_table = """
            CREATE TABLE IF NOT EXISTS tournaments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                sport VARCHAR(100) NOT NULL,
                level VARCHAR(100) NOT NULL,
                date_info TEXT,
                venue TEXT,
                link VARCHAR(500),
                streaming_links TEXT,
                summary TEXT,
                entry_fees VARCHAR(255),
                contact_information TEXT,
                eligibility TEXT,
                prizes TEXT,
                confidence_score DECIMAL(3,2),
                source_url VARCHAR(500),
                source_sport VARCHAR(100),
                source_level VARCHAR(100),
                extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_sport (sport),
                INDEX idx_level (level),
                INDEX idx_confidence (confidence_score),
                INDEX idx_created (created_at),
                UNIQUE KEY unique_tournament (name, sport, level)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            # Create search_logs table for tracking
            create_logs_table = """
            CREATE TABLE IF NOT EXISTS search_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                query TEXT NOT NULL,
                sport VARCHAR(100),
                level VARCHAR(100),
                results_found INT DEFAULT 0,
                execution_time DECIMAL(10,3),
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_sport_level (sport, level),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            # Create statistics table
            create_stats_table = """
            CREATE TABLE IF NOT EXISTS pipeline_statistics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                total_queries INT DEFAULT 0,
                total_search_results INT DEFAULT 0,
                total_scraped_pages INT DEFAULT 0,
                total_tournaments_extracted INT DEFAULT 0,
                average_confidence_score DECIMAL(3,2),
                pipeline_run_date DATE,
                execution_time_seconds INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_run_date (pipeline_run_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
            # Execute table creation
            cursor.execute(create_tournaments_table)
            cursor.execute(create_logs_table)
            cursor.execute(create_stats_table)
            
            self.connection.commit()
            print("✅ Database tables created successfully")
            return True
            
        except Error as e:
            print(f"❌ Error creating tables: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def load_tournament_data(self, filename: str = "tournament_data.json") -> Optional[Dict]:
        """Load tournament data from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading tournament data: {e}")
            return None
    
    def check_tournament_exists(self, tournament: Dict) -> Optional[int]:
        """Check if tournament already exists in database"""
        try:
            cursor = self.connection.cursor()
            
            # Check for duplicates based on name, sport, and level
            check_query = """
            SELECT id FROM tournaments 
            WHERE name = %s AND sport = %s AND level = %s
            """
            
            check_data = (
                tournament.get('name', '')[:255],
                tournament.get('source_sport', '')[:100],
                tournament.get('source_level', '')[:100]
            )
            
            cursor.execute(check_query, check_data)
            result = cursor.fetchone()
            
            return result[0] if result else None
            
        except Error as e:
            print(f"❌ Error checking for duplicates: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def insert_tournament(self, tournament: Dict) -> Optional[int]:
        """Insert a single tournament into database"""
        try:
            cursor = self.connection.cursor()
            
            insert_query = """
            INSERT INTO tournaments (
                name, sport, level, date_info, registration_deadline, venue, link, streaming_links,
                summary, entry_fees, contact_information, eligibility, prizes,
                confidence_score, source_url, source_sport, source_level, extraction_timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Prepare tournament data with proper null handling
            def safe_string(value, max_length=None):
                """Safely handle string values that might be None"""
                if value is None:
                    return ''
                str_value = str(value)
                return str_value[:max_length] if max_length else str_value
            
            tournament_data = (
                safe_string(tournament.get('name', ''), 255),
                safe_string(tournament.get('sport', ''), 100),  # Use 'sport' not 'source_sport'
                safe_string(tournament.get('level', ''), 100),  # Use 'level' not 'source_level'
                json.dumps(tournament.get('date', [])) if tournament.get('date') else None,
                safe_string(tournament.get('registration_deadline', '')),  # New field
                json.dumps(tournament.get('venue', [])) if tournament.get('venue') else None,
                safe_string(tournament.get('link', ''), 500),
                safe_string(tournament.get('streaming_links', '')),
                safe_string(tournament.get('summary', '')),
                safe_string(tournament.get('entry_fees', '')),
                json.dumps(tournament.get('contact_information', [])) if tournament.get('contact_information') else None,
                json.dumps(tournament.get('eligibility', [])) if tournament.get('eligibility') else None,
                json.dumps(tournament.get('prizes', [])) if tournament.get('prizes') else None,
                float(tournament.get('confidence_score', 0.0)),
                safe_string(tournament.get('source_url', ''), 500),
                safe_string(tournament.get('sport', ''), 100),  # source_sport
                safe_string(tournament.get('level', ''), 100),  # source_level
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # MySQL datetime format
            )
            
            cursor.execute(insert_query, tournament_data)
            self.connection.commit()
            
            tournament_id = cursor.lastrowid
            return tournament_id
            
        except Error as e:
            print(f"❌ Error inserting tournament: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def insert_tournaments_batch(self, tournaments: List[Dict]) -> Dict:
        """Insert multiple tournaments in batch with duplicate tracking"""
        print(f"💾 Inserting {len(tournaments)} tournaments into database...")
        
        successful_inserts = 0
        duplicates_found = 0
        failed_inserts = 0
        
        for i, tournament in enumerate(tournaments, 1):
            # Check for duplicates first
            existing_id = self.check_tournament_exists(tournament)
            if existing_id:
                duplicates_found += 1
                print(f"🔄 Duplicate found {i}/{len(tournaments)}: {tournament.get('name', 'Unknown')} (ID: {existing_id})")
                continue
            
            # Insert new tournament
            tournament_id = self.insert_tournament(tournament)
            if tournament_id:
                successful_inserts += 1
                print(f"✅ Inserted tournament {i}/{len(tournaments)}: {tournament.get('name', 'Unknown')} (ID: {tournament_id})")
            else:
                failed_inserts += 1
                print(f"❌ Failed to insert tournament {i}/{len(tournaments)}: {tournament.get('name', 'Unknown')}")
        
        result_stats = {
            'total_processed': len(tournaments),
            'successful_inserts': successful_inserts,
            'duplicates_found': duplicates_found,
            'failed_inserts': failed_inserts
        }
        
        print(f"✅ Batch insert complete:")
        print(f"   📝 New tournaments: {successful_inserts}")
        print(f"   🔄 Duplicates skipped: {duplicates_found}")
        print(f"   ❌ Failed inserts: {failed_inserts}")
        
        return result_stats
    
    def get_tournaments(self, sport: str = None, level: str = None, limit: int = 100) -> List[Dict]:
        """Retrieve tournaments with optional filtering"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            query = "SELECT * FROM tournaments WHERE 1=1"
            params = []
            
            if sport:
                query += " AND sport = %s"
                params.append(sport)
            
            if level:
                query += " AND level = %s"
                params.append(level)
            
            query += " ORDER BY confidence_score DESC, created_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            tournaments = cursor.fetchall()
            
            # Convert datetime objects to strings for JSON serialization
            for tournament in tournaments:
                for key, value in tournament.items():
                    if isinstance(value, datetime):
                        tournament[key] = value.isoformat()
            
            return tournaments
            
        except Error as e:
            print(f"❌ Error retrieving tournaments: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    def get_database_statistics(self) -> Dict:
        """Get comprehensive database statistics"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Tournament counts
            cursor.execute("SELECT COUNT(*) as total_tournaments FROM tournaments")
            total_tournaments = cursor.fetchone()['total_tournaments']
            
            # Sport distribution
            cursor.execute("""
                SELECT sport, COUNT(*) as count 
                FROM tournaments 
                GROUP BY sport 
                ORDER BY count DESC
            """)
            sport_distribution = cursor.fetchall()
            
            # Level distribution
            cursor.execute("""
                SELECT level, COUNT(*) as count 
                FROM tournaments 
                GROUP BY level 
                ORDER BY count DESC
            """)
            level_distribution = cursor.fetchall()
            
            # Confidence statistics
            cursor.execute("""
                SELECT 
                    AVG(confidence_score) as avg_confidence,
                    MIN(confidence_score) as min_confidence,
                    MAX(confidence_score) as max_confidence
                FROM tournaments
            """)
            confidence_stats = cursor.fetchone()
            
            # Recent tournaments
            cursor.execute("""
                SELECT COUNT(*) as recent_count 
                FROM tournaments 
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
            """)
            recent_tournaments = cursor.fetchone()['recent_count']
            
            return {
                'total_tournaments': total_tournaments,
                'sport_distribution': sport_distribution,
                'level_distribution': level_distribution,
                'confidence_statistics': confidence_stats,
                'recent_tournaments': recent_tournaments,
                'generated_at': datetime.now().isoformat()
            }
            
        except Error as e:
            print(f"❌ Error getting statistics: {e}")
            return {}
        finally:
            if cursor:
                cursor.close()
    
    def save_pipeline_statistics(self, stats: Dict) -> bool:
        """Save pipeline execution statistics"""
        try:
            cursor = self.connection.cursor()
            
            insert_query = """
            INSERT INTO pipeline_statistics (
                total_queries, total_search_results, total_scraped_pages,
                total_tournaments_extracted, average_confidence_score,
                pipeline_run_date, execution_time_seconds
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            stats_data = (
                stats.get('total_queries', 0),
                stats.get('total_search_results', 0),
                stats.get('total_scraped_pages', 0),
                stats.get('total_tournaments_extracted', 0),
                float(stats.get('average_confidence_score', 0.0)),
                datetime.now().date(),
                stats.get('execution_time_seconds', 0)
            )
            
            cursor.execute(insert_query, stats_data)
            self.connection.commit()
            
            print("✅ Pipeline statistics saved to database")
            return True
            
        except Error as e:
            print(f"❌ Error saving pipeline statistics: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
    
    def close_connection(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("🔌 Database connection closed")
    
    def run_complete_database_storage(self) -> bool:
        """Run the complete database storage pipeline"""
        print("=" * 60)
        print("🗄️  Starting Database Storage Pipeline")
        print("=" * 60)
        
        # Step 1: Validate config
        print("🔑 Step 1: Validating database configuration...")
        if not self.validate_database_config():
            return False
        
        # Step 2: Connect to database
        print("\n🔌 Step 2: Connecting to database...")
        if not self.connect_to_database():
            return False
        
        # Step 3: Create tables
        print("\n🗄️  Step 3: Creating database tables...")
        if not self.create_database_tables():
            return False
        
        # Step 4: Load tournament data
        print("\n📋 Step 4: Loading tournament data...")
        tournament_data = self.load_tournament_data()
        if not tournament_data:
            print("❌ No tournament data found")
            return False
        
        tournaments = tournament_data.get('tournaments', [])
        if not tournaments:
            print("❌ No tournaments in data file")
            return False
        
        print(f"✅ Loaded {len(tournaments)} tournaments")
        
        # Step 5: Insert tournaments
        print("\n💾 Step 5: Inserting tournaments into database...")
        insertion_stats = self.insert_tournaments_batch(tournaments)
        
        # Step 6: Save pipeline statistics
        print("\n📊 Step 6: Saving pipeline statistics...")
        pipeline_stats = {
            'total_tournaments_extracted': len(tournaments),
            'average_confidence_score': tournament_data.get('metadata', {}).get('average_confidence', 0.0),
            'execution_time_seconds': 0  # This would be calculated in a real scenario
        }
        self.save_pipeline_statistics(pipeline_stats)
        
        # Step 7: Generate database statistics
        print("\n📈 Step 7: Generating database statistics...")
        db_stats = self.get_database_statistics()
        
        print("\n" + "=" * 60)
        print("✅ Database Storage Complete!")
        print(f"📁 New tournaments stored: {insertion_stats.get('successful_inserts', 0)}")
        print(f"🔄 Duplicates skipped: {insertion_stats.get('duplicates_found', 0)}")
        print(f"📊 Total in database: {db_stats.get('total_tournaments', 0)}")
        print("🎯 Ready for Step 6: API Integration")
        
        return True

def main():
    """Main function to run database storage"""
    db = TournamentDatabase()
    
    try:
        # Run database storage pipeline
        success = db.run_complete_database_storage()
        
        if success:
            # Display sample tournaments
            print("\n📋 Sample Tournaments in Database:")
            tournaments = db.get_tournaments(limit=5)
            for i, tournament in enumerate(tournaments, 1):
                print(f"\n{i}. {tournament.get('name', 'Unknown')}")
                print(f"   Sport: {tournament.get('sport', 'N/A')}")
                print(f"   Level: {tournament.get('level', 'N/A')}")
                print(f"   Confidence: {tournament.get('confidence_score', 0):.2f}")
        
    finally:
        db.close_connection()

if __name__ == "__main__":
    main()
