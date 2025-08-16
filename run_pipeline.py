# GenAI Sports Calendar - Complete Pipeline Runner
"""
Complete data pipeline runner for sports tournament extraction.
Runs all steps in sequence with proper error handling and logging.
"""

import sys
import os
import time
from datetime import datetime

def run_step(step_name: str, script_name: str) -> bool:
    """Run a pipeline step and return success status"""
    print(f"\n{'='*60}")
    print(f"🚀 Running {step_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Import and run the step
        result = os.system(f"python {script_name}")
        
        if result == 0:
            elapsed = time.time() - start_time
            print(f"✅ {step_name} completed successfully in {elapsed:.1f}s")
            return True
        else:
            print(f"❌ {step_name} failed with exit code {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {step_name}: {e}")
        return False

def main():
    """Run the complete pipeline"""
    print("🏆 GenAI Sports Calendar - Complete Pipeline")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    pipeline_steps = [
        ("Step 1: Query Generation", "step1_simple_query_generator.py"),
        ("Step 2: Search Results", "step2_search_results.py"),
        ("Step 3: Content Scraping", "step3_content_scraper.py"),
        ("Step 4: Tournament Extraction", "step4_tournament_extractor.py")
    ]
    
    success_count = 0
    total_start_time = time.time()
    
    for step_name, script_name in pipeline_steps:
        if run_step(step_name, script_name):
            success_count += 1
        else:
            print(f"\n❌ Pipeline failed at {step_name}")
            print("Please check the error messages above and fix any issues.")
            sys.exit(1)
    
    total_elapsed = time.time() - total_start_time
    
    print(f"\n{'='*60}")
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"{'='*60}")
    print(f"✅ All {len(pipeline_steps)} steps completed")
    print(f"⏱️  Total time: {total_elapsed:.1f} seconds")
    print(f"📁 Check the following output files:")
    print("   - simple_queries.json")
    print("   - search_results.json") 
    print("   - scraped_content.json")
    print("   - tournament_data.json")
    print(f"\n🎯 Pipeline completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
