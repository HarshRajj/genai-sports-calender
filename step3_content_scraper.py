"""
Step 3: Content Scraping with Firecrawl
Simple and fully functional implementation for scraping tournament content.
"""

import json
import requests
import os
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ContentScraper:
    def __init__(self):
        self.api_key = os.getenv('FIRECRAWL_API_KEY')
        self.base_url = "https://api.firecrawl.dev/v0"
        
    def validate_api_key(self) -> bool:
        """Validate Firecrawl API key"""
        if not self.api_key:
            print("❌ FIRECRAWL_API_KEY not found in environment variables")
            return False
        
        # Simply check if API key exists and is not empty
        if len(self.api_key.strip()) > 10:  # Basic validation
            print("✅ Firecrawl API key found and appears valid")
            return True
        else:
            print("❌ API key appears to be invalid (too short)")
            return False
    
    def load_search_results(self, filename: str = "search_results.json") -> List[Dict]:
        """Load search results from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data['results']
        except Exception as e:
            print(f"❌ Error loading search results: {e}")
            return []
    
    def extract_page_content(self, url: str) -> Optional[Dict]:
        """Extract content from a single page using Firecrawl"""
        try:
            print(f"🔍 Scraping: {url[:60]}...")
            
            payload = {
                "url": url,
                "formats": ["markdown", "html"],
                "onlyMainContent": True,
                "includeTags": ["title", "meta", "h1", "h2", "h3", "p", "div", "table", "ul", "ol"],
                "excludeTags": ["script", "style", "nav", "footer", "header", "aside"],
                "waitFor": 2000
            }
            
            response = requests.post(
                f"{self.base_url}/scrape",
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                },
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return {
                        'url': url,
                        'title': data.get('data', {}).get('metadata', {}).get('title', ''),
                        'description': data.get('data', {}).get('metadata', {}).get('description', ''),
                        'markdown': data.get('data', {}).get('markdown', ''),
                        'html': data.get('data', {}).get('html', ''),
                        'metadata': data.get('data', {}).get('metadata', {}),
                        'success': True
                    }
                else:
                    print(f"❌ Scraping failed: {data.get('error', 'Unknown error')}")
                    return None
            else:
                print(f"❌ Request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return None
    
    def check_content_quality(self, content: Dict) -> Dict:
        """Check quality and relevance of scraped content"""
        print("🎯 Checking content quality...")
        
        title = content.get('title', '').lower()
        description = content.get('description', '').lower()
        markdown = content.get('markdown', '').lower()
        
        # Tournament-related keywords
        tournament_keywords = [
            'tournament', 'championship', 'competition', 'league', 'cup',
            'series', 'match', 'fixtures', 'schedule', 'registration',
            'entry', 'participate', 'event', 'contest', 'trophy', 'games'
        ]
        
        # Date/time keywords
        date_keywords = [
            '2025', '2024', 'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'date', 'time', 'when', 'schedule', 'calendar'
        ]
        
        # Location keywords (India-specific)
        location_keywords = [
            'india', 'indian', 'delhi', 'mumbai', 'bangalore', 'chennai', 'kolkata',
            'hyderabad', 'pune', 'ahmedabad', 'venue', 'location', 'where'
        ]
        
        # Calculate quality scores
        tournament_score = sum(1 for keyword in tournament_keywords 
                             if keyword in title or keyword in description or keyword in markdown)
        
        date_score = sum(1 for keyword in date_keywords 
                        if keyword in title or keyword in description or keyword in markdown)
        
        location_score = sum(1 for keyword in location_keywords 
                           if keyword in title or keyword in description or keyword in markdown)
        
        # Content length score
        content_length = len(markdown)
        length_score = min(content_length / 1000, 10)  # Max score of 10
        
        # Calculate overall quality
        total_score = tournament_score + date_score + location_score + length_score
        
        quality_assessment = {
            'tournament_relevance': tournament_score,
            'date_information': date_score,
            'location_information': location_score,
            'content_length_score': length_score,
            'total_quality_score': total_score,
            'is_relevant': total_score >= 3,  # Minimum threshold
            'content_length': content_length
        }
        
        print(f"✅ Quality Score: {total_score:.1f} (Relevant: {quality_assessment['is_relevant']})")
        return quality_assessment
    
    def extract_tournament_data(self, content: Dict) -> Dict:
        """Extract specific tournament data from content"""
        print("📊 Extracting tournament data...")
        
        markdown = content.get('markdown', '')
        title = content.get('title', '')
        
        # Simple extraction patterns
        tournament_data = {
            'title': title,
            'url': content.get('url', ''),
            'tournament_name': self._extract_tournament_name(title, markdown),
            'dates': self._extract_dates(markdown),
            'location': self._extract_location(markdown),
            'registration_info': self._extract_registration_info(markdown),
            'contact_info': self._extract_contact_info(markdown),
            'eligibility': self._extract_eligibility(markdown),
            'prize_info': self._extract_prize_info(markdown),
            'raw_content': markdown[:2000]  # First 2000 chars for reference
        }
        
        print("✅ Tournament data extracted")
        return tournament_data
    
    def _extract_tournament_name(self, title: str, content: str) -> str:
        """Extract tournament name from title and content"""
        # Use title as primary source, clean it up
        tournament_name = title.replace(' - ', ' ').replace('|', ' ').split('•')[0].strip()
        return tournament_name[:100]  # Limit length
    
    def _extract_dates(self, content: str) -> List[str]:
        """Extract dates from content"""
        import re
        
        # Simple date patterns
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',  # DD/MM/YYYY or DD-MM-YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD or YYYY-MM-DD
            r'\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            dates.extend(matches)
        
        return list(set(dates))[:5]  # Return unique dates, max 5
    
    def _extract_location(self, content: str) -> List[str]:
        """Extract location information"""
        import re
        
        # Simple location patterns
        location_keywords = ['venue', 'location', 'place', 'address', 'city', 'state']
        locations = []
        
        lines = content.split('\n')
        for line in lines:
            for keyword in location_keywords:
                if keyword in line.lower():
                    locations.append(line.strip()[:100])
                    break
        
        return list(set(locations))[:3]  # Max 3 unique locations
    
    def _extract_registration_info(self, content: str) -> List[str]:
        """Extract registration information"""
        registration_keywords = ['registration', 'register', 'entry', 'application', 'form', 'deadline']
        registration_info = []
        
        lines = content.split('\n')
        for line in lines:
            for keyword in registration_keywords:
                if keyword in line.lower():
                    registration_info.append(line.strip()[:150])
                    break
        
        return list(set(registration_info))[:3]
    
    def _extract_contact_info(self, content: str) -> List[str]:
        """Extract contact information"""
        import re
        
        # Email pattern
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        
        # Phone pattern (Indian numbers)
        phones = re.findall(r'(\+91|91)?[\s-]?[6-9]\d{9}', content)
        
        contact_info = []
        contact_info.extend([f"Email: {email}" for email in emails[:2]])
        contact_info.extend([f"Phone: {phone}" for phone in phones[:2]])
        
        return contact_info
    
    def _extract_eligibility(self, content: str) -> List[str]:
        """Extract eligibility criteria"""
        eligibility_keywords = ['eligibility', 'eligible', 'criteria', 'qualification', 'age', 'category']
        eligibility_info = []
        
        lines = content.split('\n')
        for line in lines:
            for keyword in eligibility_keywords:
                if keyword in line.lower():
                    eligibility_info.append(line.strip()[:150])
                    break
        
        return list(set(eligibility_info))[:3]
    
    def _extract_prize_info(self, content: str) -> List[str]:
        """Extract prize information"""
        prize_keywords = ['prize', 'award', 'reward', 'cash', 'trophy', 'medal', 'certificate']
        prize_info = []
        
        lines = content.split('\n')
        for line in lines:
            for keyword in prize_keywords:
                if keyword in line.lower():
                    prize_info.append(line.strip()[:150])
                    break
        
        return list(set(prize_info))[:3]
    
    def filter_relevant_content(self, tournament_data: Dict, quality_assessment: Dict) -> Optional[Dict]:
        """Filter and validate extracted content"""
        print("🔍 Filtering relevant content...")
        
        # Check if content meets minimum quality threshold
        if not quality_assessment.get('is_relevant', False):
            print("❌ Content not relevant enough")
            return None
        
        # Check if we have minimum required data
        has_tournament_name = bool(tournament_data.get('tournament_name', '').strip())
        has_dates = bool(tournament_data.get('dates'))
        has_location = bool(tournament_data.get('location'))
        
        if not (has_tournament_name or has_dates or has_location):
            print("❌ Insufficient tournament data extracted")
            return None
        
        # Create filtered result
        filtered_data = {
            'tournament_info': tournament_data,
            'quality_metrics': quality_assessment,
            'extraction_timestamp': '2025-08-16T00:00:00Z',
            'is_valid': True
        }
        
        print("✅ Content successfully filtered and validated")
        return filtered_data
    
    def save_scraped_data(self, data: Dict, filename: str = "scraped_content.json") -> str:
        """Save scraped data with metadata"""
        
        output_data = {
            "metadata": {
                "scraped_at": "2025-08-16T00:00:00Z",
                "scraper_version": "1.0",
                "total_pages_scraped": 1,
                "successful_extractions": 1 if data else 0
            },
            "scraped_data": data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved scraped data to {filename}")
        return filename
    
    def run_complete_scraping(self) -> Optional[Dict]:
        """Run the complete scraping pipeline"""
        print("=" * 60)
        print("🕷️  Starting Content Scraping Pipeline")
        print("=" * 60)
        
        # Step 1: Validate API
        print("🔑 Step 1: Validating Firecrawl API...")
        if not self.validate_api_key():
            return None
        
        # Step 2: Load search results
        print("\n📋 Step 2: Loading search results...")
        search_results = self.load_search_results()
        if not search_results:
            print("❌ No search results found")
            return None
        print(f"✅ Loaded {len(search_results)} search results")
        
        # Step 3: Extract content from one page (highest priority)
        print("\n🔍 Step 3: Extracting content from top result...")
        top_result = search_results[0]  # Get the highest priority result
        url = top_result['link']
        
        scraped_content = self.extract_page_content(url)
        if not scraped_content:
            print("❌ Failed to scrape content")
            return None
        
        # Step 4: Check content quality
        print("\n🎯 Step 4: Checking content quality...")
        quality_assessment = self.check_content_quality(scraped_content)
        
        # Step 5: Extract tournament data
        print("\n📊 Step 5: Extracting tournament data...")
        tournament_data = self.extract_tournament_data(scraped_content)
        
        # Step 6: Filter relevant content
        print("\n🔍 Step 6: Filtering relevant content...")
        filtered_data = self.filter_relevant_content(tournament_data, quality_assessment)
        
        if not filtered_data:
            print("❌ Content not relevant enough")
            return None
        
        # Add search context
        filtered_data['search_context'] = {
            'sport': top_result['sport'],
            'level': top_result['level'],
            'original_query': top_result['query'],
            'search_rank': top_result.get('priority_rank', 1)
        }
        
        # Step 7: Save data
        print("\n💾 Step 7: Saving scraped data...")
        filename = self.save_scraped_data(filtered_data)
        
        print("\n" + "=" * 60)
        print("✅ Content Scraping Complete!")
        print(f"📁 Data saved to: {filename}")
        print(f"🎯 Sport: {top_result['sport']} - Level: {top_result['level']}")
        print("🎯 Ready for Step 4: LLM Processing")
        
        return filtered_data

def main():
    """Main function to run content scraping"""
    scraper = ContentScraper()
    
    # Run scraping pipeline
    result = scraper.run_complete_scraping()
    
    # Display extracted data summary
    if result:
        tournament_info = result.get('tournament_info', {})
        print("\n📋 Extracted Tournament Information:")
        print(f"   Name: {tournament_info.get('tournament_name', 'N/A')}")
        print(f"   Dates: {', '.join(tournament_info.get('dates', ['N/A']))}")
        print(f"   Locations: {', '.join(tournament_info.get('location', ['N/A']))}")
        print(f"   Quality Score: {result.get('quality_metrics', {}).get('total_quality_score', 0):.1f}")

if __name__ == "__main__":
    main()
