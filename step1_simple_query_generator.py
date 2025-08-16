"""
Simple Query Generator for Tournament Calendar - Step 1
Generates exactly 3 queries per sport-level combination with LLM enhancement.
"""

import json
import os
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SimpleQueryGenerator:
    def __init__(self):
        # Simple sports and levels list
        self.sports = ["Cricket", "Football", "Basketball", "Tennis", "Badminton"]
        self.levels = ["School", "College", "Club", "State", "National"]
        
        # Only 3 simple templates per sport-level combination
        self.templates = [
            "{sport} tournament {level} India 2025",
            "{sport} championship {level} 2025 registration",
            "India {sport} {level} competition 2025 schedule"
        ]
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def step1_generate_base_queries(self) -> List[Dict]:
        """Step 1: Generate base queries (exactly 3 per sport-level combo)"""
        print("Step 1: Generating base queries...")
        queries = []
        
        for sport in self.sports:
            for level in self.levels:
                for template in self.templates:
                    query = template.format(sport=sport, level=level)
                    queries.append({
                        "sport": sport,
                        "level": level,
                        "query": query,
                        "source": "template"
                    })
        
        print(f"Generated {len(queries)} base queries")
        return queries
    
    def step2_enhance_with_llm(self, base_queries: List[Dict]) -> List[Dict]:
        """Step 2: Enhance queries using LLM"""
        print("Step 2: Enhancing queries with LLM...")
        
        if not os.getenv('OPENAI_API_KEY'):
            print("No OpenAI API key found, skipping LLM enhancement")
            return base_queries
        
        # Create a simple prompt for all sports at once
        prompt = f"""
        Generate 3 additional search queries for finding tournament information for each sport-level combination.
        Focus on finding official tournament websites, registration pages, and schedule information.
        
        Make queries specific to India and include year 2025.
        Vary the language and terms used (tournament, championship, competition, league, cup, series, etc.).
        
        Sports: {', '.join(self.sports)}
        Levels: {', '.join(self.levels)}
        
        Return only the additional queries in this exact JSON format:
        [
            {{"sport": "Cricket", "level": "School", "query": "example query", "source": "llm_generated"}},
            ...
        ]
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            llm_response = response.choices[0].message.content.strip()
            if llm_response.startswith('```json'):
                llm_response = llm_response.replace('```json', '').replace('```', '').strip()
            
            llm_queries = json.loads(llm_response)
            enhanced_queries = base_queries + llm_queries
            print(f"Added {len(llm_queries)} LLM-enhanced queries")
            
            return enhanced_queries
            
        except Exception as e:
            print(f"Error with LLM enhancement: {e}")
            return base_queries
    
    def step3_remove_duplicates(self, queries: List[Dict]) -> List[Dict]:
        """Step 3: Remove duplicate queries"""
        print("Step 3: Removing duplicates...")
        
        seen_queries = set()
        unique_queries = []
        
        for query in queries:
            query_text = query['query'].lower().strip()
            if query_text not in seen_queries:
                seen_queries.add(query_text)
                unique_queries.append(query)
        
        removed = len(queries) - len(unique_queries)
        print(f"Removed {removed} duplicate queries")
        return unique_queries
    
    def step4_save_queries(self, queries: List[Dict]) -> str:
        """Step 4: Save queries to JSON file"""
        print("Step 4: Saving queries...")
        
        data = {
            "metadata": {
                "total_queries": len(queries),
                "sports": self.sports,
                "levels": self.levels,
                "generated_at": "2025-08-16"
            },
            "queries": queries
        }
        
        filename = "simple_queries.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(queries)} queries to {filename}")
        return filename
    
    def generate_all_queries(self) -> List[Dict]:
        """Main function to generate all queries step by step"""
        print("🚀 Simple Query Generator Started")
        print("-" * 40)
        
        # Step 1: Generate base queries
        queries = self.step1_generate_base_queries()
        
        # Step 2: Enhance with LLM
        queries = self.step2_enhance_with_llm(queries)
        
        # Step 3: Remove duplicates
        queries = self.step3_remove_duplicates(queries)
        
        # Step 4: Save queries
        filename = self.step4_save_queries(queries)
        
        print("-" * 40)
        print(f"✅ Complete! Generated {len(queries)} unique queries")
        print(f"📁 Saved to: {filename}")
        
        return queries

def main():
    """Main function"""
    generator = SimpleQueryGenerator()
    queries = generator.generate_all_queries()
    
    # Show sample queries
    print("\n📋 Sample Queries:")
    for i, query in enumerate(queries[:10]):
        print(f"{i+1}. {query['sport']} - {query['level']}: {query['query']}")

if __name__ == "__main__":
    main()
