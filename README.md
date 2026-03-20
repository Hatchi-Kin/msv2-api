# Music Curation & Discovery Platform

A sophisticated music discovery and playlist curation platform powered by AI agents, vector search, and intelligent recommendation systems. This FastAPI-based service provides a comprehensive music library management system with advanced AI-powered playlist generation and music discovery capabilities.

## 🎯 Overview

This platform combines music library management with AI-powered discovery, offering:

- **Inference by calling Knative APIs**: CLAP and Openl3 inference by calling "serverless" functions
- **Vector-based Music Search**: Semantic search across music libraries using vector embeddings
- **Agentic Playlist Generation**: Autonomous AI agents that curate playlists based on user preferences
- **Multi-tenant Architecture**: Support for multiple users with personalized recommendations
- **Real-time Audio Processing**: Integration with audio analysis and embedding services

## 🏗️ Architecture

### Core Components

```
msv2-api/
├── api/                    # FastAPI application
│   ├── agents/            # AI agents for music curation
│   ├── core/              # Core configurations and utilities
│   ├── handlers/          # Request handlers
│   ├── models/            # Pydantic models
│   ├── repositories/      # Database access layer
│   ├── routers/           # API endpoints
│   └── main.py           # Application entry point
├── tests/                 # Test suite
├── scripts/               # Utility scripts
└── pyproject.toml         # Dependencies and project config
```

### Key Technologies

- **Backend**: FastAPI, Python 3.12+
- **Database**: PostgreSQL with pgvector for vector similarity search
- **AI/ML**: LangGraph, LangChain, Claude/Gemini LLMs
- **Vector Search**: pgvector for music embedding similarity
- **Storage**: MinIO for audio file storage
- **Orchestration**: LangGraph for AI agent workflows

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 14+ with pgvector extension
- MinIO (or S3-compatible storage)
- LLM API keys (Anthropic Claude or Google Gemini)

### Installation

1. **Clone and setup environment:**

```bash
git clone <repository>
cd msv2-api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Database setup:**

```bash
# Install PostgreSQL with pgvector
# Create database and enable extensions:
# CREATE EXTENSION vector;
# CREATE EXTENSION pgvector;
```

4. **Run the application:**

```bash
# Development
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎵 Core Features

### 1. Music Library Management

- **Track Management**: Upload, tag, and organize music libraries
- **Audio Analysis**: BPM, key, energy, and mood analysis
- **Vector Embeddings**: Audio feature embeddings for similarity search
- **Metadata Management**: Artist, album, genre, and custom tagging

### 2. AI-Powered Playlist Curation

- **Gem Hunter Agent**: Autonomous playlist curator using LangGraph
- **Intelligent Search**: Vector similarity search with semantic understanding
- **Mood & Vibe Matching**: AI-powered mood and vibe analysis
- **Personalized Discovery**: Learns from user preferences and listening habits

### 3. Agentic Playlist Generation

The system features an intelligent agent that:

1. **Analyzes** existing playlists for musical patterns
2. **Searches** for similar tracks using vector similarity
3. **Evaluates** candidate tracks for quality and fit
4. **Presents** curated playlists with AI-generated justifications

### 4. Advanced Search Capabilities

- **Semantic Search**: Find music by mood, emotion, or vibe
- **Vector Similarity**: Find musically similar tracks using embeddings
- **Hybrid Search**: Combine metadata, tags, and audio features
- **Real-time Filtering**: BPM, key, energy, danceability, and more

## 🏗️ Architecture Details

### Database Schema

The system uses PostgreSQL with:

- **Users & Authentication**: JWT-based auth with refresh tokens
- **Music Library**: Tracks, artists, albums with vector embeddings
- **Playlists & Collections**: User-created and AI-generated playlists
- **Analytics**: Listening history, preferences, and recommendations

### AI/ML Components

- **Embedding Models**: Audio feature extraction and vectorization
- **LLM Integration**: Claude/Gemini for natural language understanding
- **LangGraph Agents**: Autonomous playlist curation workflows
- **Recommendation Engine**: Collaborative and content-based filtering

### Storage Architecture

- **PostgreSQL**: Primary data store with pgvector
- **MinIO/S3**: Audio file storage and streaming
- **Redis**: Caching and session management
- **Vector Database**: pgvector for similarity search

## 🚀 API Endpoints

### Core Endpoints

- `GET /tracks` - Search and filter tracks
- `POST /playlists` - Create AI-curated playlists
- `GET /recommendations` - Personalized recommendations
- `POST /analyze` - Audio feature analysis
- `GET /discover` - Discovery feed with AI suggestions

### Agent Endpoints

- `POST /agent/recommend/{playlist_id}` - Start playlist curation
- `POST /agent/resume` - Continue agent workflow
- `GET /agent/status/{session_id}` - Check agent status

## 🛠️ Development

### Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=api tests/

# Run specific test categories
pytest tests/test_agents.py -v
pytest tests/test_repositories.py -v
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build manually
docker build -t msv2-api .
docker run -p 8000:8000 msv2-api
```

## 📊 API Documentation

Once running, access:

- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/music_db

# AI/ML Services
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🔄 CI/CD

### GitHub Actions

Automated workflows for:

- Testing on PRs
- Docker image building
- Security scanning
- Performance benchmarking

### For local development

**you might port-forward the k3s postgres services:**

```sh
kubectl port-forward service/postgres-service 5432:5432 -n glasgow-prod
```

**and**

```sh
kubectl port-forward -n glasgow-prod svc/minio-service 9000:9000
```

**Then start the app**

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```
