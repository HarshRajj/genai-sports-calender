"""
Step 4: Tournament Data Extraction with LLM
Simple, fully functional, and production-ready implementation.
"""

import json
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TournamentExtractor:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.min_confidence_score = 0.7  # Minimum confidence threshold
        
    def validate_api_key(self) -> bool:
        """Validate OpenAI API key"""
        if not os.getenv('OPENAI_API_KEY'):
            print("❌ OPENAI_API_KEY not found in environment variables")
            return False
        print("✅ OpenAI API key found")
        return True
    
    def load_scraped_content(self, filename: str = "scraped_content.json") -> Optional[Dict]:
        """Load scraped content from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('scraped_data', {})
        except Exception as e:
            print(f"❌ Error loading scraped content: {e}")
            return None
    
    def _extract_relevant_content(self, content: str, max_length: int = 8000) -> str:
        """Extract the most relevant parts of content for tournament extraction"""
        if len(content) <= max_length:
            return content
        
        # Keywords that indicate tournament information
        tournament_keywords = [
            'tournament', 'championship', 'competition', 'league', 'cup', 'open',
            'registration', 'entry', 'participate', 'eligibility', 'venue', 'date',
            'prize', 'award', 'fee', 'contact', 'schedule', 'format', 'rules'
        ]
        
        # Split content into paragraphs
        paragraphs = content.split('\n')
        
        # Score paragraphs based on keyword relevance
        scored_paragraphs = []
        for para in paragraphs:
            if len(para.strip()) < 20:  # Skip very short paragraphs
                continue
                
            score = 0
            para_lower = para.lower()
            for keyword in tournament_keywords:
                score += para_lower.count(keyword)
            
            scored_paragraphs.append((score, para))
        
        # Sort by score and take the most relevant paragraphs
        scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
        
        # Build content from highest scoring paragraphs until we reach max_length
        selected_content = []
        current_length = 0
        
        for score, para in scored_paragraphs:
            if current_length + len(para) > max_length:
                break
            selected_content.append(para)
            current_length += len(para)
        
        result = '\n'.join(selected_content)
        if len(result) < max_length // 2:  # If we got too little content, add some from the beginning
            remaining_space = max_length - len(result)
            beginning_content = content[:remaining_space]
            result = beginning_content + '\n' + result
        
        return result[:max_length]

    def extract_tournaments_with_llm(self, content: Dict) -> List[Dict]:
        """Extract tournament data using LLM with confidence scoring"""
        print("🤖 Extracting tournament data with LLM...")
        
        # Get the raw content
        tournament_info = content.get('tournament_info', {})
        raw_content = tournament_info.get('raw_content', '')
        title = tournament_info.get('title', '')
        url = tournament_info.get('url', '')
        
        # Extract relevant content intelligently to avoid token limit
        max_content_length = 6000  # Conservative limit for content
        relevant_content = self._extract_relevant_content(raw_content, max_content_length)
        
        print(f"📝 Content reduced from {len(raw_content)} to {len(relevant_content)} characters")
        
        # Create simple prompt for better JSON response
        prompt = f"""Extract tournament details from this content. Return only valid JSON.

Content: {relevant_content}

Find tournaments and return JSON array with format:
[{{"name": "Tournament Name", "tournament_date": "Date", "registration_deadline": "Deadline", "level": "Level", "venue": "Venue", "summary": "Description", "confidence_score": 0.8}}]

Look for registration deadlines with keywords: deadline, last date, closing date, apply by, registration closes.

Return only JSON array or [] if no tournaments found."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # Lower temperature for more consistent JSON
                max_tokens=1500   # Increased for more detailed responses
            )
            
            # Parse LLM response
            llm_response = response.choices[0].message.content.strip()
            print(f"🔍 LLM Response length: {len(llm_response)} characters")
            print(f"📄 LLM Response: '{llm_response}'")  # Debug: show actual response
            
            # Clean JSON response
            if llm_response.startswith('```json'):
                llm_response = llm_response.replace('```json', '').replace('```', '').strip()
            elif llm_response.startswith('```'):
                llm_response = llm_response.replace('```', '').strip()
            
            # Try to find JSON array in the response
            start_idx = llm_response.find('[')
            end_idx = llm_response.rfind(']')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = llm_response[start_idx:end_idx + 1]
            else:
                json_str = llm_response
            
            # Attempt to fix common JSON issues
            json_str = self._fix_json_string(json_str)
            
            try:
                tournaments = json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parse error: {e}")
                print(f"📄 Problematic JSON snippet: {json_str[:500]}...")
                # Try to extract any valid tournament info manually
                tournaments = self._fallback_parse(llm_response)
            
            if not isinstance(tournaments, list):
                tournaments = [tournaments] if tournaments else []
            
            print(f"✅ LLM extracted {len(tournaments)} tournaments")
            return tournaments
            
        except Exception as e:
            print(f"❌ Error extracting tournaments with LLM: {e}")
            return []
    
    def _fix_json_string(self, json_str: str) -> str:
        """Attempt to fix common JSON formatting issues"""
        # Remove any trailing commas before closing brackets
        json_str = json_str.replace(',]', ']').replace(',}', '}')
        
        # Try to fix unterminated strings by finding unmatched quotes
        lines = json_str.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Count quotes in the line
            quote_count = line.count('"')
            if quote_count % 2 != 0:  # Odd number of quotes indicates unterminated string
                # Try to close the string
                if line.rstrip().endswith(','):
                    line = line.rstrip()[:-1] + '",'
                else:
                    line = line.rstrip() + '"'
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)
    
    def _fallback_parse(self, response: str) -> List[Dict]:
        """Fallback parsing when JSON parsing fails"""
        print("🔧 Attempting fallback parsing...")
        
        # Simple extraction based on keywords
        tournaments = []
        
        # Look for tournament names (very basic extraction)
        import re
        
        # Try to find tournament names
        name_patterns = [
            r'["\']name["\']:\s*["\']([^"\']+)["\']',
            r'Tournament[:\s]+([^\n,]+)',
            r'Championship[:\s]+([^\n,]+)'
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            for match in matches:
                if len(match.strip()) > 3:  # Basic validation
                    tournaments.append({
                        "name": match.strip(),
                        "confidence_score": 0.5,  # Low confidence for fallback
                        "summary": "Extracted via fallback parsing"
                    })
                    break  # Only take the first valid match
        
        print(f"🔧 Fallback extracted {len(tournaments)} tournaments")
        return tournaments

    def enhance_tournament_data(self, tournaments: List[Dict], context: Dict) -> List[Dict]:
        """Enhance tournament data with context information"""
        print("🔧 Enhancing tournament data...")
        
        search_context = context.get('search_context', {})
        
        enhanced_tournaments = []
        for tournament in tournaments:
            # Add context information
            enhanced_tournament = tournament.copy()
            
            # Map new field names to existing database schema
            if 'tournament_date' in enhanced_tournament:
                enhanced_tournament['date'] = enhanced_tournament.pop('tournament_date')
            
            enhanced_tournament.update({
                'source_url': search_context.get('original_query', ''),
                'source_sport': search_context.get('sport', ''),
                'source_level': search_context.get('level', ''),
                'extraction_timestamp': '2025-08-16T00:00:00Z',
                'data_source': 'llm_extracted'
            })
            
            # Validate confidence score
            confidence = enhanced_tournament.get('confidence_score', 0.0)
            if isinstance(confidence, str):
                try:
                    confidence = float(confidence)
                except:
                    confidence = 0.5
            
            enhanced_tournament['confidence_score'] = min(max(confidence, 0.0), 1.0)
            
            # Clean empty fields
            for key, value in enhanced_tournament.items():
                if value in ['N/A', 'Not available', 'Not specified', '', None]:
                    enhanced_tournament[key] = None
            
            enhanced_tournaments.append(enhanced_tournament)
        
        print(f"✅ Enhanced {len(enhanced_tournaments)} tournaments")
        return enhanced_tournaments
    
    def filter_by_confidence(self, tournaments: List[Dict]) -> List[Dict]:
        """Filter tournaments by confidence score"""
        print(f"🎯 Filtering tournaments by confidence (min: {self.min_confidence_score})...")
        
        high_confidence_tournaments = []
        for tournament in tournaments:
            confidence = tournament.get('confidence_score', 0.0)
            if confidence >= self.min_confidence_score:
                high_confidence_tournaments.append(tournament)
        
        filtered_count = len(tournaments) - len(high_confidence_tournaments)
        if filtered_count > 0:
            print(f"🗑️  Filtered out {filtered_count} low-confidence tournaments")
        
        print(f"✅ {len(high_confidence_tournaments)} high-confidence tournaments remaining")
        return high_confidence_tournaments
    
    def validate_tournament_data(self, tournaments: List[Dict]) -> List[Dict]:
        """Validate and clean tournament data"""
        print("🔍 Validating tournament data...")
        
        valid_tournaments = []
        
        for tournament in tournaments:
            # Check required fields
            has_name = bool(tournament.get('name', '').strip())
            has_date_or_venue = bool(tournament.get('date', '').strip()) or bool(tournament.get('venue', '').strip())
            
            if has_name and has_date_or_venue:
                # Clean and format data
                cleaned_tournament = self._clean_tournament_data(tournament)
                valid_tournaments.append(cleaned_tournament)
            else:
                print(f"⚠️  Skipping invalid tournament: {tournament.get('name', 'Unknown')}")
        
        print(f"✅ {len(valid_tournaments)} valid tournaments")
        return valid_tournaments
    
    def _clean_tournament_data(self, tournament: Dict) -> Dict:
        """Clean and format individual tournament data"""
        cleaned = {}
        
        for key, value in tournament.items():
            if value is None:
                cleaned[key] = None
            elif isinstance(value, str):
                # Clean string values
                cleaned_value = value.strip()
                if cleaned_value and cleaned_value not in ['N/A', 'Not available', 'Not specified']:
                    cleaned[key] = cleaned_value[:500]  # Limit length
                else:
                    cleaned[key] = None
            else:
                cleaned[key] = value
        
        return cleaned
    
    def save_tournament_data(self, tournaments: List[Dict], filename: str = "tournament_data.json") -> str:
        """Save tournament data with comprehensive metadata"""
        
        # Calculate statistics
        total_tournaments = len(tournaments)
        avg_confidence = sum(t.get('confidence_score', 0) for t in tournaments) / max(total_tournaments, 1)
        
        confidence_distribution = {
            'high_confidence': len([t for t in tournaments if t.get('confidence_score', 0) >= 0.8]),
            'medium_confidence': len([t for t in tournaments if 0.6 <= t.get('confidence_score', 0) < 0.8]),
            'low_confidence': len([t for t in tournaments if t.get('confidence_score', 0) < 0.6])
        }
        
        # Group by sport and level
        by_sport = {}
        by_level = {}
        
        for tournament in tournaments:
            sport = tournament.get('source_sport', 'Unknown')
            level = tournament.get('source_level', 'Unknown')
            
            by_sport[sport] = by_sport.get(sport, 0) + 1
            by_level[level] = by_level.get(level, 0) + 1
        
        # Create comprehensive output
        output_data = {
            "metadata": {
                "total_tournaments": total_tournaments,
                "average_confidence": round(avg_confidence, 3),
                "confidence_distribution": confidence_distribution,
                "extraction_timestamp": "2025-08-16T00:00:00Z",
                "extractor_version": "1.0",
                "min_confidence_threshold": self.min_confidence_score
            },
            "statistics": {
                "by_sport": by_sport,
                "by_level": by_level,
                "data_quality": {
                    "tournaments_with_dates": len([t for t in tournaments if t.get('date')]),
                    "tournaments_with_venues": len([t for t in tournaments if t.get('venue')]),
                    "tournaments_with_contact": len([t for t in tournaments if t.get('contact_information')]),
                    "tournaments_with_prizes": len([t for t in tournaments if t.get('prizes')])
                }
            },
            "tournaments": tournaments
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {total_tournaments} tournaments to {filename}")
        return filename
    
    def run_complete_extraction(self) -> List[Dict]:
        """Run the complete tournament extraction pipeline"""
        print("=" * 60)
        print("🏆 Starting Tournament Data Extraction Pipeline")
        print("=" * 60)
        
        # Step 1: Validate API
        print("🔑 Step 1: Validating OpenAI API...")
        if not self.validate_api_key():
            return []
        
        # Step 2: Load scraped content
        print("\n📋 Step 2: Loading scraped content...")
        content = self.load_scraped_content()
        if not content:
            print("❌ No scraped content found")
            return []
        print("✅ Scraped content loaded successfully")
        
        # Step 3: Extract tournaments with LLM
        print("\n🤖 Step 3: Extracting tournaments with LLM...")
        raw_tournaments = self.extract_tournaments_with_llm(content)
        if not raw_tournaments:
            print("❌ No tournaments extracted")
            return []
        
        # Step 4: Enhance tournament data
        print("\n🔧 Step 4: Enhancing tournament data...")
        enhanced_tournaments = self.enhance_tournament_data(raw_tournaments, content)
        
        # Step 5: Filter by confidence
        print("\n🎯 Step 5: Filtering by confidence...")
        confident_tournaments = self.filter_by_confidence(enhanced_tournaments)
        
        # Step 6: Validate tournament data
        print("\n🔍 Step 6: Validating tournament data...")
        valid_tournaments = self.validate_tournament_data(confident_tournaments)
        
        if not valid_tournaments:
            print("❌ No valid tournaments found")
            return []
        
        # Step 7: Save tournament data
        print("\n💾 Step 7: Saving tournament data...")
        filename = self.save_tournament_data(valid_tournaments)
        
        print("\n" + "=" * 60)
        print("✅ Tournament Data Extraction Complete!")
        print(f"📁 Data saved to: {filename}")
        print(f"🏆 Found {len(valid_tournaments)} valid tournaments")
        print("🎯 Ready for Step 5: Database Storage")
        
        return valid_tournaments

def main():
    """Main function to run tournament extraction"""
    extractor = TournamentExtractor()
    
    # Run extraction pipeline
    tournaments = extractor.run_complete_extraction()
    
    # Display extracted tournaments
    if tournaments:
        print("\n📋 Extracted Tournament Summary:")
        for i, tournament in enumerate(tournaments, 1):
            print(f"\n{i}. {tournament.get('name', 'Unknown Tournament')}")
            print(f"   Date: {tournament.get('date', 'Not specified')}")
            print(f"   Level: {tournament.get('level', 'Not specified')}")
            print(f"   Venue: {tournament.get('venue', 'Not specified')}")
            print(f"   Confidence: {tournament.get('confidence_score', 0):.2f}")

if __name__ == "__main__":
    main()
