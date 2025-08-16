"""
Step 6: API & Endpoints with FastAPI
Simple, fully functional, and production-ready REST API for tournament data.
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import mysql.connector
from mysql.connector import Error
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from config import SPORTS_LIST, LEVELS_LIST, LOCAL_LEVELS_LIST
import asyncio
import sys
sys.path.append('.')

# Import pipeline components
from step1_simple_query_generator import SimpleQueryGenerator
from step2_search_results import SearchResultsCollector  
from step3_content_scraper import ContentScraper
from step4_tournament_extractor import TournamentExtractor
from step5_database_storage import TournamentDatabase

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="GenAI Sports Calendar API",
    description="REST API for accessing sports tournament data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API responses
class Tournament(BaseModel):
    id: int
    name: str
    sport: str
    level: str
    date_info: Optional[List[str]] = None
    registration_deadline: Optional[str] = None
    venue: Optional[List[str]] = None
    link: Optional[str] = None
    streaming_links: Optional[str] = None
    summary: Optional[str] = None
    entry_fees: Optional[str] = None
    contact_information: Optional[List[str]] = None
    eligibility: Optional[List[str]] = None
    prizes: Optional[List[str]] = None
    confidence_score: float
    source_url: Optional[str] = None
    source_sport: Optional[str] = None
    source_level: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class TournamentSummary(BaseModel):
    id: int
    name: str
    sport: str
    level: str
    confidence_score: float
    created_at: datetime

class DatabaseStats(BaseModel):
    total_tournaments: int
    average_confidence: float
    by_sport: Dict[str, int]
    by_level: Dict[str, int]
    recent_tournaments: int

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Any = None
    total_count: Optional[int] = None

# Database connection dependency
def get_db_connection():
    """Get database connection"""
    try:
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'sports_calendar')
        }
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

def parse_json_field(field_value: str) -> List[str]:
    """Safely parse JSON field or return as single item list"""
    if not field_value:
        return []
    
    # First try to parse as JSON
    try:
        parsed = json.loads(field_value)
        return parsed if isinstance(parsed, list) else [str(parsed)]
    except:
        # If not JSON, treat as string and return as single item list
        # Remove quotes if present
        cleaned = field_value.strip(' "\'')
        return [cleaned] if cleaned else []

def is_current_or_future_tournament(date_info: str) -> bool:
    """Check if tournament is current or future based on date information"""
    if not date_info:
        return True  # Include tournaments without date info
    
    import re
    from datetime import datetime
    
    # Current date
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    
    # Clean the date string
    date_str = date_info.lower().strip(' "')
    
    # Check for specific patterns
    if any(word in date_str for word in ['tbd', 'to be decided', 'coming soon', 'upcoming']):
        return True
    
    # Extract year
    year_match = re.search(r'\b(20\d{2})\b', date_str)
    if year_match:
        year = int(year_match.group(1))
        if year > current_year:
            return True
        elif year < current_year:
            return False
        # Same year, check month if available
        
    # Check for month names in current year
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    for month_name, month_num in months.items():
        if month_name in date_str:
            if year_match:
                year = int(year_match.group(1))
                if year == current_year and month_num >= current_month:
                    return True
                elif year > current_year:
                    return True
                else:
                    return False
    
    # If we can't determine, include by default (better to show than hide)
    return True

# API Endpoints

@app.get("/", response_model=APIResponse)
async def root():
    """API root endpoint with basic information"""
    return APIResponse(
        success=True,
        message="GenAI Sports Calendar API is running",
        data={
            "version": "1.0.0",
            "description": "REST API for sports tournament data",
            "endpoints": {
                "tournaments": "/tournaments",
                "tournament_by_id": "/tournaments/{id}",
                "search": "/tournaments/search",
                "sports": "/sports",
                "levels": "/levels", 
                "statistics": "/statistics",
                "documentation": "/docs"
            }
        }
    )

@app.get("/tournaments", response_model=APIResponse)
async def get_tournaments(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    sport: Optional[str] = Query(None, description="Filter by sport"),
    level: Optional[str] = Query(None, description="Filter by level"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    show_past: bool = Query(False, description="Include past tournaments"),
    connection = Depends(get_db_connection)
):
    """Get tournaments with optional filtering and pagination"""
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Build query with filters
        query = "SELECT * FROM tournaments WHERE 1=1"
        params = []
        
        if sport:
            query += " AND sport = %s"
            params.append(sport)
        
        if level:
            query += " AND level = %s"
            params.append(level)
        
        if min_confidence is not None:
            query += " AND confidence_score >= %s"
            params.append(min_confidence)
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['COUNT(*)']
        
        # Add pagination and ordering
        query += " ORDER BY confidence_score DESC, created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])
        
        cursor.execute(query, params)
        tournaments = cursor.fetchall()
        
        # Process tournaments and filter by date if needed
        processed_tournaments = []
        for tournament in tournaments:
            # Apply date filtering if show_past is False
            if not show_past and not is_current_or_future_tournament(tournament['date_info']):
                continue
                
            tournament_data = {
                'id': tournament['id'],
                'name': tournament['name'],
                'sport': tournament['sport'],
                'level': tournament['level'],
                'date_info': parse_json_field(tournament['date_info']),
                'registration_deadline': tournament.get('registration_deadline', ''),
                'venue': parse_json_field(tournament['venue']),
                'link': tournament['link'],
                'streaming_links': tournament['streaming_links'],
                'summary': tournament['summary'],
                'entry_fees': tournament['entry_fees'],
                'contact_information': parse_json_field(tournament['contact_information']),
                'eligibility': parse_json_field(tournament['eligibility']),
                'prizes': parse_json_field(tournament['prizes']),
                'confidence_score': float(tournament['confidence_score']),
                'source_url': tournament['source_url'],
                'source_sport': tournament['source_sport'],
                'source_level': tournament['source_level'],
                'created_at': tournament['created_at'],
                'updated_at': tournament['updated_at']
            }
            processed_tournaments.append(tournament_data)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(processed_tournaments)} tournaments",
            data=processed_tournaments,
            total_count=total_count
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tournaments: {e}")
    finally:
        if connection.is_connected():
            connection.close()

@app.get("/tournaments/search", response_model=APIResponse)
async def search_tournaments(
    q: str = Query(..., min_length=2, description="Search query (minimum 2 characters)"),
    limit: int = Query(20, ge=1, le=50, description="Number of results"),
    connection = Depends(get_db_connection)
):
    """Search tournaments by name, summary, or venue"""
    try:
        cursor = connection.cursor(dictionary=True)
        
        search_query = """
        SELECT * FROM tournaments 
        WHERE name LIKE %s OR summary LIKE %s OR venue LIKE %s
        ORDER BY confidence_score DESC, created_at DESC
        LIMIT %s
        """
        
        search_term = f"%{q}%"
        cursor.execute(search_query, (search_term, search_term, search_term, limit))
        tournaments = cursor.fetchall()
        
        # Process tournaments (simplified for search)
        processed_tournaments = []
        for tournament in tournaments:
            tournament_data = {
                'id': tournament['id'],
                'name': tournament['name'],
                'sport': tournament['sport'],
                'level': tournament['level'],
                'confidence_score': float(tournament['confidence_score']),
                'created_at': tournament['created_at']
            }
            processed_tournaments.append(tournament_data)
        
        return APIResponse(
            success=True,
            message=f"Found {len(processed_tournaments)} tournaments matching '{q}'",
            data=processed_tournaments,
            total_count=len(processed_tournaments)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {e}")
    finally:
        if connection.is_connected():
            connection.close()

@app.get("/tournaments/{tournament_id}", response_model=APIResponse)
async def get_tournament_by_id(
    tournament_id: int,
    connection = Depends(get_db_connection)
):
    """Get a specific tournament by ID"""
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM tournaments WHERE id = %s"
        cursor.execute(query, (tournament_id,))
        tournament = cursor.fetchone()
        
        if not tournament:
            raise HTTPException(status_code=404, detail="Tournament not found")
        
        # Process tournament data
        tournament_data = {
            'id': tournament['id'],
            'name': tournament['name'],
            'sport': tournament['sport'],
            'level': tournament['level'],
            'date_info': parse_json_field(tournament['date_info']),
            'venue': parse_json_field(tournament['venue']),
            'link': tournament['link'],
            'streaming_links': tournament['streaming_links'],
            'summary': tournament['summary'],
            'entry_fees': tournament['entry_fees'],
            'contact_information': parse_json_field(tournament['contact_information']),
            'eligibility': parse_json_field(tournament['eligibility']),
            'prizes': parse_json_field(tournament['prizes']),
            'confidence_score': float(tournament['confidence_score']),
            'source_url': tournament['source_url'],
            'source_sport': tournament['source_sport'],
            'source_level': tournament['source_level'],
            'created_at': tournament['created_at'],
            'updated_at': tournament['updated_at']
        }
        
        return APIResponse(
            success=True,
            message="Tournament retrieved successfully",
            data=tournament_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving tournament: {e}")
    finally:
        if connection.is_connected():
            connection.close()

@app.get("/sports", response_model=APIResponse)
async def get_sports(connection = Depends(get_db_connection)):
    """Get list of all sports with tournament counts"""
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get sports from database with tournament counts
        query = """
        SELECT sport, COUNT(*) as tournament_count, AVG(confidence_score) as avg_confidence
        FROM tournaments 
        GROUP BY sport 
        ORDER BY tournament_count DESC
        """
        
        cursor.execute(query)
        db_sports = cursor.fetchall()
        
        # Create a set of sports from database for quick lookup
        db_sports_dict = {sport['sport']: sport for sport in db_sports}
        
        # Combine configured sports with database sports
        sports_data = []
        
        # Add all configured sports
        for sport in SPORTS_LIST:
            if sport in db_sports_dict:
                # Sport exists in database
                db_sport = db_sports_dict[sport]
                sports_data.append({
                    'sport': sport,
                    'tournament_count': db_sport['tournament_count'],
                    'avg_confidence': round(float(db_sport['avg_confidence']), 2)
                })
            else:
                # Sport not in database yet
                sports_data.append({
                    'sport': sport,
                    'tournament_count': 0,
                    'avg_confidence': 0.0
                })
        
        # Add any sports from database that aren't in our configured list
        for sport in db_sports:
            if sport['sport'] not in SPORTS_LIST:
                sports_data.append({
                    'sport': sport['sport'],
                    'tournament_count': sport['tournament_count'],
                    'avg_confidence': round(float(sport['avg_confidence']), 2)
                })
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(sports_data)} sports",
            data=sports_data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving sports: {e}")
    finally:
        if connection.is_connected():
            connection.close()

@app.get("/levels", response_model=APIResponse)
async def get_levels(connection = Depends(get_db_connection)):
    """Get list of all competition levels with tournament counts"""
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get levels from database with tournament counts
        query = """
        SELECT level, COUNT(*) as tournament_count, AVG(confidence_score) as avg_confidence
        FROM tournaments 
        GROUP BY level 
        ORDER BY tournament_count DESC
        """
        
        cursor.execute(query)
        db_levels = cursor.fetchall()
        
        # Create a set of levels from database for quick lookup
        db_levels_dict = {level['level']: level for level in db_levels}
        
        # Combine configured levels with database levels
        levels_data = []
        all_levels = LEVELS_LIST + LOCAL_LEVELS_LIST
        
        # Add all configured levels
        for level in all_levels:
            if level in db_levels_dict:
                # Level exists in database
                db_level = db_levels_dict[level]
                levels_data.append({
                    'level': level,
                    'tournament_count': db_level['tournament_count'],
                    'avg_confidence': round(float(db_level['avg_confidence']), 2)
                })
            else:
                # Level not in database yet
                levels_data.append({
                    'level': level,
                    'tournament_count': 0,
                    'avg_confidence': 0.0
                })
        
        # Add any levels from database that aren't in our configured list
        for level in db_levels:
            if level['level'] not in all_levels:
                levels_data.append({
                    'level': level['level'],
                    'tournament_count': level['tournament_count'],
                    'avg_confidence': round(float(level['avg_confidence']), 2)
                })
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(levels_data)} levels",
            data=levels_data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving levels: {e}")
    finally:
        if connection.is_connected():
            connection.close()
        if connection.is_connected():
            connection.close()

@app.get("/statistics", response_model=APIResponse)
async def get_statistics(connection = Depends(get_db_connection)):
    """Get comprehensive database statistics"""
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Total tournaments
        cursor.execute("SELECT COUNT(*) as total FROM tournaments")
        total_tournaments = cursor.fetchone()['total']
        
        # Average confidence
        cursor.execute("SELECT AVG(confidence_score) as avg_confidence FROM tournaments")
        avg_confidence_result = cursor.fetchone()
        avg_confidence = float(avg_confidence_result['avg_confidence']) if avg_confidence_result['avg_confidence'] else 0.0
        
        # By sport
        cursor.execute("SELECT sport, COUNT(*) as count FROM tournaments GROUP BY sport ORDER BY count DESC")
        by_sport = {row['sport']: row['count'] for row in cursor.fetchall()}
        
        # By level
        cursor.execute("SELECT level, COUNT(*) as count FROM tournaments GROUP BY level ORDER BY count DESC")
        by_level = {row['level']: row['count'] for row in cursor.fetchall()}
        
        # Recent tournaments (last 7 days)
        cursor.execute("SELECT COUNT(*) as recent FROM tournaments WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
        recent_tournaments = cursor.fetchone()['recent']
        
        stats_data = {
            'total_tournaments': total_tournaments,
            'average_confidence': round(avg_confidence, 2),
            'by_sport': by_sport,
            'by_level': by_level,
            'recent_tournaments': recent_tournaments,
            'generated_at': datetime.now().isoformat()
        }
        
        return APIResponse(
            success=True,
            message="Statistics retrieved successfully",
            data=stats_data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving statistics: {e}")
    finally:
        if connection.is_connected():
            connection.close()

@app.post("/tournaments/intelligent-search", response_model=APIResponse)
async def intelligent_search(
    sport: str = Query(..., description="Sport name"),
    level: str = Query(..., description="Competition level"),
    force_refresh: bool = Query(False, description="Force refresh even if data exists"),
    connection = Depends(get_db_connection)
):
    """
    Intelligent search that checks database first, then runs pipeline if needed
    """
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Step 1: Check if tournaments exist for this sport-level combination
        check_query = """
        SELECT COUNT(*) as count, MAX(created_at) as latest_update
        FROM tournaments 
        WHERE sport = %s AND level = %s
        """
        cursor.execute(check_query, (sport, level))
        result = cursor.fetchone()
        
        existing_count = result['count']
        latest_update = result['latest_update']
        
        if existing_count > 0 and not force_refresh:
            # Data exists, return existing tournaments
            tournaments_query = """
            SELECT * FROM tournaments 
            WHERE sport = %s AND level = %s
            ORDER BY confidence_score DESC, created_at DESC
            LIMIT 20
            """
            cursor.execute(tournaments_query, (sport, level))
            tournaments = cursor.fetchall()
            
            processed_tournaments = []
            for tournament in tournaments:
                tournament_data = process_tournament_data(tournament)
                processed_tournaments.append(tournament_data)
            
            return APIResponse(
                success=True,
                message=f"Found {len(processed_tournaments)} existing tournaments for {sport} - {level}",
                data=processed_tournaments,
                total_count=len(processed_tournaments),
                metadata={
                    "source": "database",
                    "last_updated": latest_update.isoformat() if latest_update else None,
                    "sport": sport,
                    "level": level
                }
            )
        
        else:
            # No data exists or force refresh requested - run the pipeline
            try:
                pipeline_result = await run_pipeline_for_sport_level(sport, level)
                
                if pipeline_result["success"]:
                    # Fetch the newly added tournaments
                    tournaments_query = """
                    SELECT * FROM tournaments 
                    WHERE sport = %s AND level = %s
                    ORDER BY confidence_score DESC, created_at DESC
                    LIMIT 20
                    """
                    cursor.execute(tournaments_query, (sport, level))
                    tournaments = cursor.fetchall()
                    
                    processed_tournaments = []
                    for tournament in tournaments:
                        tournament_data = process_tournament_data(tournament)
                        processed_tournaments.append(tournament_data)
                    
                    return APIResponse(
                        success=True,
                        message=f"Pipeline completed! Found {len(processed_tournaments)} new tournaments for {sport} - {level}",
                        data=processed_tournaments,
                        total_count=len(processed_tournaments),
                        metadata={
                            "source": "pipeline",
                            "pipeline_stats": pipeline_result["stats"],
                            "sport": sport,
                            "level": level,
                            "generated_at": datetime.now().isoformat()
                        }
                    )
                else:
                    return APIResponse(
                        success=False,
                        message=f"Pipeline failed for {sport} - {level}: {pipeline_result['error']}",
                        data=[],
                        metadata={
                            "source": "pipeline",
                            "sport": sport,
                            "level": level,
                            "error": pipeline_result["error"]
                        }
                    )
                    
            except Exception as pipeline_error:
                return APIResponse(
                    success=False,
                    message=f"Pipeline execution failed: {str(pipeline_error)}",
                    data=[],
                    metadata={
                        "source": "pipeline",
                        "sport": sport,
                        "level": level,
                        "error": str(pipeline_error)
                    }
                )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligent search error: {e}")
    finally:
        if connection.is_connected():
            connection.close()

async def run_pipeline_for_sport_level(sport: str, level: str) -> dict:
    """
    Run the complete extraction pipeline for a specific sport-level combination
    """
    try:
        stats = {
            "queries_generated": 0,
            "search_results": 0,
            "content_scraped": 0,
            "tournaments_extracted": 0,
            "tournaments_stored": 0
        }
        
        # Step 1: Generate queries for this specific sport-level combination
        query_generator = SimpleQueryGenerator()
        
        # Create specific queries for this sport-level
        if level in LOCAL_LEVELS_LIST:
            templates = query_generator.local_templates
        else:
            templates = query_generator.templates
            
        specific_queries = []
        for template in templates:
            query = template.format(sport=sport, level=level)
            specific_queries.append({
                "sport": sport,
                "level": level,
                "query": query,
                "source": "template"
            })
        
        stats["queries_generated"] = len(specific_queries)
        
        # Step 2: Search for results
        search_collector = SearchResultsCollector()
        search_results = []
        
        for query_data in specific_queries:
            result = search_collector.search_query(query_data["query"])
            if result and result.get("organic", []):
                for organic_result in result["organic"]:
                    search_results.append({
                        "sport": sport,
                        "level": level,
                        "title": organic_result.get("title", ""),
                        "link": organic_result.get("link", ""),
                        "snippet": organic_result.get("snippet", ""),
                        "source": "search"
                    })
        
        stats["search_results"] = len(search_results)
        
        if not search_results:
            return {
                "success": False,
                "error": f"No search results found for {sport} - {level}",
                "stats": stats
            }
        
        # Step 3: Scrape content (limit to top 5 results for speed)
        content_scraper = ContentScraper()
        scraped_content = []
        
        for result in search_results[:5]:  # Limit for faster processing
            content = content_scraper.extract_page_content(result["link"])
            if content and content.get("success"):
                scraped_content.append({
                    "sport": sport,
                    "level": level,
                    "url": result["link"],
                    "title": result["title"],
                    "content": content.get("markdown", ""),
                    "source": "scraping"
                })
        
        stats["content_scraped"] = len(scraped_content)
        
        if not scraped_content:
            return {
                "success": False,
                "error": f"No content could be scraped for {sport} - {level}",
                "stats": stats
            }
        
        # Step 4: Extract tournament information
        tournament_extractor = TournamentExtractor()
        extracted_tournaments = []
        
        for content in scraped_content:
            # Format content for tournament extractor
            formatted_content = {
                "tournament_info": {
                    "raw_content": content["content"],
                    "title": content["title"],
                    "url": content["url"]
                }
            }
            
            tournaments = tournament_extractor.extract_tournaments_with_llm(formatted_content)
            if tournaments:
                # Add sport and level information to each tournament
                for tournament in tournaments:
                    tournament["sport"] = sport
                    tournament["level"] = level
                    tournament["source_url"] = content["url"]
                extracted_tournaments.extend(tournaments)
        
        stats["tournaments_extracted"] = len(extracted_tournaments)
        
        if not extracted_tournaments:
            return {
                "success": False,
                "error": f"No tournaments could be extracted for {sport} - {level}",
                "stats": stats
            }
        
        # Step 5: Store in database
        print(f"💾 Step 5: Storing tournaments in database...")
        db_storage = TournamentDatabase()
        
        # Initialize database connection
        if not db_storage.connect_to_database():
            return {
                "success": False,
                "error": "Failed to connect to database",
                "stats": stats
            }
        
        stored_count = 0
        
        for tournament in extracted_tournaments:
            try:
                tournament_id = db_storage.insert_tournament(tournament)
                if tournament_id:
                    stored_count += 1
                    print(f"✅ Stored tournament: {tournament.get('name', 'Unknown')}")
                else:
                    print(f"⚠️ Failed to store tournament: {tournament.get('name', 'Unknown')}")
            except Exception as e:
                print(f"❌ Error storing tournament: {e}")
        
        # Close database connection
        db_storage.close_connection()
        
        stats["tournaments_stored"] = stored_count
        
        return {
            "success": True,
            "stats": stats,
            "message": f"Pipeline completed successfully for {sport} - {level}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "stats": stats
        }

def process_tournament_data(tournament):
    """Helper function to process tournament data for API response"""
    return {
        'id': tournament['id'],
        'name': tournament['name'],
        'sport': tournament['sport'],
        'level': tournament['level'],
        'date_info': json.loads(tournament['date_info']) if tournament['date_info'] else [],
        'venue': json.loads(tournament['venue']) if tournament['venue'] else [],
        'link': tournament['link'],
        'streaming_links': tournament['streaming_links'],
        'summary': tournament['summary'],
        'confidence_score': float(tournament['confidence_score']),
        'created_at': tournament['created_at'].isoformat() if tournament['created_at'] else None
    }

@app.get("/frontend")
async def serve_frontend():
    """Serve the frontend HTML file"""
    return FileResponse("step7_frontend.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        connection = get_db_connection()
        connection.close()
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting GenAI Sports Calendar API...")
    print("📋 API Documentation: http://localhost:8000/docs")
    print("🔍 Alternative Docs: http://localhost:8000/redoc")
    print("💻 API Base URL: http://localhost:8000")
    
    uvicorn.run(
        "step6_api_endpoints:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
