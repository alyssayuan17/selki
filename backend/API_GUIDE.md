# Triple-TS Speaks API Guide

## Quick Start

### 1. Start the API Server

```bash
cd backend
uvicorn main:app --reload
```

The API will be available at: `http://localhost:8000`

Interactive API docs: `http://localhost:8000/docs`

### 2. Test the API

In a separate terminal:

```bash
cd backend
python test_api.py
```

This will create a test job, poll for completion, and retrieve results.

---

## API Endpoints

### POST /api/v1/presentations

Submit audio for analysis.

**Request:**
```json
{
  "audio_url": "file://test.wav",
  "language": "en",
  "talk_type": "presentation",
  "audience_type": "general",
  "requested_metrics": ["pace", "fillers", "intonation"],
  "user_metadata": {"user_id": "123"}
}
```

**Response (201 Created):**
```json
{
  "job_id": "pres_abc123",
  "status": "queued",
  "created_at": "2025-12-06T12:00:00Z",
  "input": {...}
}
```

### GET /api/v1/presentations/{job_id}

Get job status.

**Response while processing:**
```json
{
  "job_id": "pres_abc123",
  "status": "processing",
  "created_at": "2025-12-06T12:00:00Z",
  "updated_at": "2025-12-06T12:00:10Z"
}
```

**Response when done:**
```json
{
  "job_id": "pres_abc123",
  "status": "done",
  "created_at": "2025-12-06T12:00:00Z",
  "updated_at": "2025-12-06T12:01:00Z",
  "input": {...},
  "quality_flags": {...},
  "overall_score": {
    "score_0_100": 75,
    "label": "good",
    "confidence": 0.80
  },
  "available_metrics": ["pace", "fillers", "intonation"]
}
```

### GET /api/v1/presentations/{job_id}/full

Get full detailed results (only when status=done).

**Response:**
```json
{
  "job_id": "pres_abc123",
  "status": "done",
  "input": {...},
  "quality_flags": {...},
  "overall_score": {...},
  "metrics": {
    "pace": {
      "score_0_100": 72,
      "label": "slightly_fast",
      "confidence": 0.83,
      "abstained": false,
      "details": {...},
      "feedback": [...]
    },
    ...
  },
  "timeline": [...],
  "model_metadata": {...},
  "transcript": {
    "full_text": "...",
    "language": "en"
  }
}
```

### GET /api/v1/presentations/{job_id}/transcript

Get transcript.

**Response when done:**
```json
{
  "job_id": "pres_abc123",
  "status": "done",
  "transcript": {
    "full_text": "Hello everyone...",
    "language": "en",
    "segments": [...],
    "tokens": [...]
  }
}
```

### DELETE /api/v1/presentations/{job_id}

Delete a job.

**Response:** 204 No Content

---

## Architecture

```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────────┐
│     FastAPI Application         │
│  (main.py)                      │
├─────────────────────────────────┤
│  Routers:                       │
│  - api/v1/presentations.py      │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│     Job Manager                 │
│  (jobs/job_manager.py)          │
│  - In-memory job storage        │
│  - Background task execution    │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Analysis Pipeline              │
│  (analyzer/run_pipeline.py)     │
│  - Audio processing             │
│  - Metric computation           │
│  - Result generation            │
└─────────────────────────────────┘
```

---

## File Structure

```
backend/
├── main.py                       # FastAPI app entry point
├── api/
│   └── v1/
│       ├── schemas.py            # Pydantic models
│       ├── presentations.py      # API endpoints
│       └── errors.py             # Error handling
├── jobs/
│   ├── job_manager.py            # Job lifecycle management
│   └── storage.py                # Job persistence (TODO)
└── analyzer/
    ├── run_pipeline.py           # Main analysis pipeline
    ├── audio_to_json.py          # Audio processing
    └── metrics/                  # Individual metrics
        ├── pace.py
        ├── fillers.py
        ├── intonation.py
        ├── content_structure.py
        └── ...
```

---

## Testing with curl

```bash
# Create job
curl -X POST http://localhost:8000/api/v1/presentations \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "file://test.wav",
    "language": "en",
    "talk_type": "test",
    "audience_type": "general"
  }'

# Get status
curl http://localhost:8000/api/v1/presentations/pres_abc123

# Get full results
curl http://localhost:8000/api/v1/presentations/pres_abc123/full

# Delete job
curl -X DELETE http://localhost:8000/api/v1/presentations/pres_abc123
```

---

## Next Steps

### Immediate Enhancements:
1. **Add file upload support**  
   - Modify POST endpoint to accept `UploadFile` instead of URL
   - Save uploaded files to disk/cloud storage

2. **Implement overall score calculation**  
   - Aggregate individual metric scores
   - Weight by confidence and importance

3. **Add segments/tokens to transcript endpoint**  
   - Export from audio_to_json.py
   - Include timing and filler detection

### Production Enhancements:
1. **Database persistence** (replace in-memory storage)
   - PostgreSQL with SQLAlchemy
   - MongoDB with Motor

2. **Distributed task queue** (replace background tasks)
   - Celery + Redis
   - Or ARQ for async support

3. **Authentication & rate limiting**
   - API keys
   - JWT tokens
   - Rate limiting per user

4. **Monitoring & logging**
   - Structured logging
   - Error tracking (Sentry)
   - Metrics (Prometheus)

---

## Troubleshooting

### Port already in use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <pid> /F

# Or use a different port
uvicorn main:app --port 8001
```

### Module not found errors
```bash
# Ensure you're in the backend directory
cd backend

# Install missing dependencies
pip install -r requirements.txt
```

### Audio file not found
```bash
# Make sure test.wav exists in backend/ directory
# Or use absolute path in audio_url
```
