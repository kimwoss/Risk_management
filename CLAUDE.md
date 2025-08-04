# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a risk management communication system for POSCO International that analyzes crisis communication data using AI. The system consists of:

1. **Crisis Response Analysis**: Processes journalist inquiries and provides strategic advice using GPT
2. **Semantic Search**: Uses FAISS and Korean sentence transformers to find similar past incidents
3. **Data Processing**: Handles Korean CSV data with proper encoding for crisis communication cases

## Environment Setup

The project uses Python 3.11+ with a virtual environment located at `.venv/`.

**Activate environment:**
- Windows: `start_project.bat` or run `.venv\Scripts\activate`
- PowerShell: `activate_env.ps1`

**Required environment file:**
- `.env` file must contain `OPENAI_API_KEY=your_api_key_here`

## Key Dependencies

Install these dependencies in the virtual environment:
- `pandas` - CSV data processing
- `openai` - GPT API integration  
- `python-dotenv` - Environment variable management
- `sentence-transformers` - Korean text embeddings (`jhgan/ko-sroberta-multitask`)
- `faiss-cpu` - Vector similarity search
- `pickle` - Data serialization

## Core Architecture

### Data Layer (`data/`)
- `최신 언론대응내역(GPT용).csv` - Main crisis communication dataset
- Contains columns: `순번`, `발생 일시`, `발생 유형`, `이슈 발생 보고`
- Filters for `기자문의` and `기자 문의` types only

### Application Layer (`app/`)

**main.py** - Primary GPT integration and data analysis
- Loads CSV data with CP949 encoding (fallback to UTF-8-sig)  
- Filters journalist inquiry data
- Provides GPT-powered crisis response advice
- Run with: `python app/main.py`

**embedding.py** - FAISS index creation
- Creates embeddings using Korean SentenceTransformer
- Builds FAISS L2 distance index
- Saves index and mappings to `app/index/`
- Run with: `python app/embedding.py`

**faiss_search.py** - Semantic similarity search  
- Loads pre-built FAISS index
- Performs similarity search with date-based ranking
- Returns top-k most relevant recent cases
- Run with: `python app/faiss_search.py`

### Index Storage (`app/index/`)
- `faiss_index.bin` - FAISS vector index file
- `index_mapping.pkl` - Mapping between vectors and original data

## Common Development Workflows

### Running the System
1. Activate environment: `start_project.bat`
2. Test environment: `python test_env.py`
3. **Main analysis system**: `python main.py`
4. **Build FAISS index**: `python build_index.py` 
5. **Search functionality**: `python search.py` or `python search.py "검색어"`

### New Project Structure
```
ai_commsystem/
├── config/                 # Configuration files
│   ├── settings.py         # Centralized settings
├── src/                    # Source code
│   ├── core/              # Core business logic
│   │   └── risk_analyzer.py
│   ├── services/          # Service layer
│   │   ├── openai_service.py
│   │   ├── embedding_service.py
│   │   └── search_service.py
│   └── utils/             # Utility modules
│       ├── data_loader.py
│       └── logger.py
├── data/                  # Data files and index
│   └── index/            # FAISS index storage
├── logs/                 # Application logs
├── tests/                # Test files
├── main.py              # Main application entry
├── build_index.py       # Index building script
├── search.py            # Search functionality script
└── requirements.txt     # Python dependencies
```

### Data Processing Pipeline
1. Load CSV with proper Korean encoding (CP949 primary, UTF-8-sig fallback)
2. Filter for journalist inquiry types (`기자문의`, `기자 문의`)
3. Clean null values in required columns
4. Generate embeddings using Korean transformer model
5. Build and save FAISS index for similarity search

### Key Configuration Constants
- `DEFAULT_MODEL = "gpt-3.5-turbo"`
- `MODEL_NAME = "jhgan/ko-sroberta-multitask"`
- `QUERY_TYPES = ["기자문의", "기자 문의"]`
- `DEFAULT_TOP_K = 3` (search results)

## Error Handling Patterns

The codebase implements comprehensive error handling for:
- File encoding issues (Korean text processing)
- Missing required columns in CSV data
- OpenAI API failures
- FAISS index loading/saving errors
- Date parsing for various Korean date formats

## File Path Conventions

Uses absolute paths with proper Windows path handling:
- Data files referenced from project root
- Index files stored in `app/index/` directory
- Environment activation scripts in project root