"""
Configuration file for GenAI Sports Calendar
Contains all sports and competition levels covered by the system.
"""

# Sports covered by the system
SPORTS_LIST = [
    "Cricket",
    "Football", 
    "Basketball",
    "Tennis",
    "Badminton"
]

# Competition levels supported
LEVELS_LIST = [
    "School",
    "College", 
    "State",
    "National",
    "International",
    "Professional"
]

# API Configuration
DEFAULT_SEARCH_LIMIT = 15
DEFAULT_CONFIDENCE_THRESHOLD = 0.7
MAX_QUERIES_PER_SPORT = 3

# File Configuration
DEFAULT_OUTPUT_FILES = {
    "queries": "simple_queries.json",
    "search_results": "search_results.json", 
    "scraped_content": "scraped_content.json",
    "tournament_data": "tournament_data.json"
}
