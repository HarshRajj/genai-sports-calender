"""
Step 2: Search Results Collection
Simple and fully functional implementation for collecting search results.
"""

import json
import requests
import os
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SearchResultsCollector:
    def __init__(self):
        self.api_key = os.getenv('SERPER_API_KEY')
        self.base_url = "https://google.serper.dev/search"
        
    def validate_api_key(self) -> bool:
        """Validate Serper API key"""
        if not self.api_key:
            print("❌ SERPER_API_KEY not found in environment variables")
            return False
        
        # Test API with a simple query
        try:
            response = requests.post(
                self.base_url,
                headers={'X-API-KEY': self.api_key, 'Content-Type': 'application/json'},
                json={"q": "test", "num": 1}
            )
            if response.status_code == 200:
                print("✅ Serper API key validated successfully")
                return True
            else:
                print(f"❌ API validation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API validation error: {e}")
            return False
    
    def search_query(self, query: str) -> Dict[str, Any]:
        """Search a single query using Serper API"""
        try:
            payload = {
                "q": query,
                "num": 5,  # Limit to 5 results per query for testing
                "hl": "en",
                "gl": "in"  # India location
            }
            
            response = requests.post(
                self.base_url,
                headers={'X-API-KEY': self.api_key, 'Content-Type': 'application/json'},
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Search failed for query: {query[:50]}... (Status: {response.status_code})")
                return {}
                
        except Exception as e:
            print(f"❌ Error searching query: {query[:50]}... Error: {e}")
            return {}
    
    def search_queries(self, queries: List[Dict], limit: int = 10) -> List[Dict]:
        """Search multiple queries with rate limiting"""
        print(f"🔍 Searching {min(limit, len(queries))} queries for testing...")
        
        all_results = []
        search_count = 0
        
        for query_data in queries[:limit]:  # Limit for testing
            query = query_data['query']
            sport = query_data['sport']
            level = query_data['level']
            
            print(f"Searching: {sport} - {level} ({search_count + 1}/{limit})")
            
            # Search the query
            search_result = self.search_query(query)
            
            if search_result and 'organic' in search_result:
                # Process organic results
                for result in search_result['organic']:
                    all_results.append({
                        'sport': sport,
                        'level': level,
                        'query': query,
                        'title': result.get('title', ''),
                        'link': result.get('link', ''),
                        'snippet': result.get('snippet', ''),
                        'position': result.get('position', 0)
                    })
            
            search_count += 1
            
            # Rate limiting - 1 request per second
            time.sleep(1)
        
        print(f"✅ Collected {len(all_results)} search results")
        return all_results
    
    def filter_relevant_results(self, results: List[Dict]) -> List[Dict]:
        """Filter results for tournament relevance"""
        print("🎯 Filtering relevant results...")
        
        # Keywords that indicate tournament/competition relevance
        tournament_keywords = [
            'tournament', 'championship', 'competition', 'league', 'cup',
            'series', 'match', 'fixtures', 'schedule', 'registration',
            'entry', 'participate', 'event', 'contest', 'trophy'
        ]
        
        # Keywords that indicate official/reliable sources
        official_keywords = [
            'official', 'federation', 'association', 'board', 'council',
            'organization', 'govt', 'government', 'ministry', 'sports',
            'academy', 'club', 'university', 'college', 'school'
        ]
        
        filtered_results = []
        
        for result in results:
            title = result['title'].lower()
            snippet = result['snippet'].lower()
            link = result['link'].lower()
            
            # Check for tournament relevance
            tournament_score = sum(1 for keyword in tournament_keywords 
                                 if keyword in title or keyword in snippet)
            
            # Check for official source indicators
            official_score = sum(1 for keyword in official_keywords 
                               if keyword in title or keyword in snippet or keyword in link)
            
            # Calculate relevance score
            relevance_score = tournament_score + (official_score * 0.5)
            
            if relevance_score > 0:
                result['relevance_score'] = relevance_score
                filtered_results.append(result)
        
        print(f"✅ Filtered to {len(filtered_results)} relevant results")
        return filtered_results
    
    def prioritize_results(self, results: List[Dict]) -> List[Dict]:
        """Prioritize results by relevance score and position"""
        print("📊 Prioritizing results...")
        
        # Sort by relevance score (desc) then by search position (asc)
        prioritized = sorted(results, 
                           key=lambda x: (-x.get('relevance_score', 0), x.get('position', 999)))
        
        # Add priority rank
        for i, result in enumerate(prioritized):
            result['priority_rank'] = i + 1
        
        print("✅ Results prioritized by relevance")
        return prioritized
    
    def remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate results based on URL"""
        print("🧹 Removing duplicate results...")
        
        seen_links = set()
        unique_results = []
        
        for result in results:
            link = result['link']
            if link not in seen_links:
                seen_links.add(link)
                unique_results.append(result)
        
        removed_count = len(results) - len(unique_results)
        if removed_count > 0:
            print(f"✅ Removed {removed_count} duplicate results")
        
        return unique_results
    
    def save_results(self, results: List[Dict], filename: str = "search_results.json") -> str:
        """Save search results with metadata"""
        
        # Group results by sport and level
        by_sport = {}
        by_level = {}
        
        for result in results:
            sport = result['sport']
            level = result['level']
            
            if sport not in by_sport:
                by_sport[sport] = []
            by_sport[sport].append(result)
            
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(result)
        
        # Create output data
        output_data = {
            "metadata": {
                "total_results": len(results),
                "sports_covered": len(by_sport),
                "levels_covered": len(by_level),
                "top_domains": self._get_top_domains(results),
                "generated_at": "2025-08-16T00:00:00Z"
            },
            "summary": {
                "by_sport": {sport: len(results) for sport, results in by_sport.items()},
                "by_level": {level: len(results) for level, results in by_level.items()}
            },
            "results": results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(results)} results to {filename}")
        return filename
    
    def _get_top_domains(self, results: List[Dict], top_n: int = 5) -> List[Dict]:
        """Get top domains from results"""
        from urllib.parse import urlparse
        
        domain_counts = {}
        for result in results:
            try:
                domain = urlparse(result['link']).netloc
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            except:
                continue
        
        top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return [{"domain": domain, "count": count} for domain, count in top_domains]
    
    def load_queries(self, filename: str = "simple_queries.json") -> List[Dict]:
        """Load queries from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data['queries']
        except Exception as e:
            print(f"❌ Error loading queries: {e}")
            return []
    
    def run_complete_search(self, query_limit: int = 10) -> List[Dict]:
        """Run the complete search pipeline"""
        print("=" * 60)
        print("🔍 Starting Search Results Collection Pipeline")
        print("=" * 60)
        
        # Step 1: Validate API
        print("🔑 Step 1: Validating API key...")
        if not self.validate_api_key():
            return []
        
        # Step 2: Load queries
        print("\n📋 Step 2: Loading queries...")
        queries = self.load_queries()
        if not queries:
            print("❌ No queries found")
            return []
        print(f"✅ Loaded {len(queries)} queries")
        
        # Step 3: Search queries (limited for testing)
        print(f"\n🔍 Step 3: Searching queries (limit: {query_limit})...")
        raw_results = self.search_queries(queries, limit=query_limit)
        if not raw_results:
            print("❌ No search results obtained")
            return []
        
        # Step 4: Filter relevant results
        print("\n🎯 Step 4: Filtering relevant results...")
        filtered_results = self.filter_relevant_results(raw_results)
        
        # Step 5: Prioritize results
        print("\n📊 Step 5: Prioritizing results...")
        prioritized_results = self.prioritize_results(filtered_results)
        
        # Step 6: Remove duplicates
        print("\n🧹 Step 6: Removing duplicates...")
        final_results = self.remove_duplicates(prioritized_results)
        
        # Step 7: Save results
        print("\n💾 Step 7: Saving results...")
        filename = self.save_results(final_results)
        
        print("\n" + "=" * 60)
        print("✅ Search Results Collection Complete!")
        print(f"📁 Results saved to: {filename}")
        print(f"📊 Final count: {len(final_results)} unique results")
        print("🎯 Ready for Step 3: Content Scraping")
        
        return final_results

def main():
    """Main function to run search results collection"""
    collector = SearchResultsCollector()
    
    # Run with limited queries for testing
    results = collector.run_complete_search(query_limit=15)  # Test with 15 queries
    
    # Display sample results
    if results:
        print("\n📋 Sample Results:")
        for i, result in enumerate(results[:5]):  # Show top 5
            print(f"\n{i+1}. {result['sport']} - {result['level']}")
            print(f"   Title: {result['title'][:80]}...")
            print(f"   Score: {result.get('relevance_score', 0)}")
            print(f"   URL: {result['link'][:60]}...")

if __name__ == "__main__":
    main()
