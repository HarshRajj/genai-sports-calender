# GenAI Sports Calendar - Tournament Data Pipeline

A comprehensive data pipeline for extracting and organizing sports tournament information using AI and web scraping.

## 🚀 Features

- **Smart Query Generation**: AI-powered search query generation for sports tournaments
- **Intelligent Search**: Automated web search using Serper API
- **Content Scraping**: Advanced web scraping with Firecrawl
- **LLM Extraction**: OpenAI-powered tournament data extraction with confidence scoring
- **Production Ready**: Clean, optimized, and fully functional pipeline

## 📋 Pipeline Steps

1. **Step 1**: Generate search queries for sport-level combinations
2. **Step 2**: Search and collect results from web sources
3. **Step 3**: Scrape content from relevant pages
4. **Step 4**: Extract tournament data using LLM with confidence scoring

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/genai-sports-calendar.git
cd genai-sports-calendar
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with your API keys:
```env
OPENAI_API_KEY=your_openai_api_key
SERPER_API_KEY=your_serper_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

## 🎯 Usage

### Run Individual Steps

```bash
# Step 1: Generate queries
python step1_simple_query_generator.py

# Step 2: Search for results
python step2_search_results.py

# Step 3: Scrape content
python step3_content_scraper.py

# Step 4: Extract tournament data
python step4_tournament_extractor.py
```

### Run Complete Pipeline

```bash
# Run all steps in sequence
python run_pipeline.py
```

## 📊 Output Files

- `simple_queries.json` - Generated search queries
- `search_results.json` - Web search results
- `scraped_content.json` - Scraped page content
- `tournament_data.json` - Final tournament information

## 🔧 Configuration

### Sports Covered
- Cricket
- Football
- Basketball
- Tennis
- Badminton

### Competition Levels
- School
- College
- State
- National
- International
- Professional

## 📁 Project Structure

```
genai-sports-calendar/
├── step1_simple_query_generator.py  # Query generation
├── step2_search_results.py          # Web search
├── step3_content_scraper.py          # Content scraping
├── step4_tournament_extractor.py     # LLM extraction
├── requirements.txt                  # Dependencies
├── .env.example                     # Environment template
├── README.md                        # This file
└── data/                           # Output files
```

## 🔑 API Requirements

1. **OpenAI API**: For LLM-based data extraction
2. **Serper API**: For web search functionality
3. **Firecrawl API**: For content scraping

## 📈 Data Quality

- **Confidence Scoring**: Each tournament gets a confidence score (0.0-1.0)
- **Quality Filtering**: Only tournaments with confidence ≥ 0.7 are saved
- **Data Validation**: Ensures required fields are present
- **Duplicate Removal**: Eliminates duplicate entries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for GPT models
- Serper for search API
- Firecrawl for web scraping
- Built as part of GenAI Internship Assignment

## 📞 Contact

For questions or support, please open an issue in the GitHub repository.
