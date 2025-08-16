"""
Configuration file for GenAI Sports Calendar
Contains all sports and competition levels covered by the system.
"""

"""
Configuration file for GenAI Sports Calendar
Contains all sports and competition levels covered by the system.
"""

# Sports covered by the system (Updated comprehensive list)
SPORTS_LIST = [
    "Cricket",
    "Football", 
    "Badminton",
    "Running",
    "Gym",
    "Cycling",
    "Swimming",
    "Kabaddi",
    "Yoga",
    "Basketball",
    "Chess",
    "Table Tennis"
]

# Competition levels supported (Updated comprehensive list)
LEVELS_LIST = [
    "Corporate",
    "School",
    "College/University",
    "Club/Academy", 
    "District",
    "State",
    "Zonal/Regional",
    "National",
    "International"
]

# Local tournament specific levels for better coverage
LOCAL_LEVELS_LIST = [
    "Local",
    "Community",
    "Residential",
    "Municipal",
    "City",
    "Inter-Club",
    "Inter-School",
    "Inter-College",
    "Neighborhood",
    "Society"
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
