# Frontend-Backend Integration Setup

This guide explains how to connect the Next.js frontend to the FastAPI backend for the VEEDxFAL video generation application.

## Backend Setup

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the `backend/` directory with your API keys:
```env
# Add your API keys here
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
# ... other required keys
```

### 3. Run Backend Locally
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

## Frontend Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Environment Variables
Create a `.env.local` file in the `frontend/` directory:

**For local development:**
```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

**For production (Azure deployment):**
```env
NEXT_PUBLIC_BACKEND_URL=https://your-backend-domain.azurewebsites.net
```

### 3. Run Frontend Locally
```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

The frontend connects to these backend endpoints:

### Text-based Generation
- **Endpoint:** `POST /generate-from-text`
- **Purpose:** Generate video from text journal entries
- **Parameters:**
  - `text`: Journal content
  - `gender`: User gender (male/female/non-binary)
  - `age_group`: Mapped from frontend age selections
  - `visual_style`: Mapped from frontend style selections
  - `voice_style`: For non-binary users (male/female)
  - `name`: Required for blog styles

### Video Upload Generation (Future)
- **Endpoint:** `POST /generate`
- **Purpose:** Generate video from uploaded video files
- **Parameters:** Similar to text generation + `video` file

### Job Status Tracking
- **Endpoint:** `GET /status/{job_id}`
- **Purpose:** Check video generation progress
- **Returns:** Status, progress percentage, video URL when complete

### Video Download
- **Endpoint:** `GET /download/{job_id}`
- **Purpose:** Download completed video files
- **Returns:** MP4 video file

## Data Mapping

### Frontend → Backend Style Mapping
```typescript
'ghibli' → 'Studio Ghibli'
'pixar' → 'Pixar'
'anime' → 'Anime'
'watercolor' → 'Watercolor'
'cyberpunk' → 'Cyberpunk'
'blog-female' → 'blog-female'
'blog-male' → 'blog-male'
'realistic' → 'Realistic'
```

### Frontend → Backend Age Mapping
```typescript
'teen' → '18-25'
'young-adult' → '26-35'
'adult' → '36-45'
'senior' → '55+'
```

### Voice Preference for Non-Binary Users
- Frontend collects: `'feminine'` or `'masculine'`
- Backend expects: `'female'` or `'male'`
- Mapping: `feminine → female`, `masculine → male`

## User Flow

1. **Input:** User enters text or uploads video (video upload disabled for now)
2. **Style Selection:** User selects gender, age, visual style, and name (for blog styles)
3. **Submission:** Frontend sends data to appropriate backend endpoint
4. **Processing:** Backend returns job ID, frontend polls status endpoint every 15 seconds
5. **Completion:** When status shows "completed", frontend displays download link
6. **Timeout:** If processing takes longer than 4 minutes, the request times out

## Performance Optimizations

- **Polling Frequency:** Status checked every 15 seconds for responsive updates
- **Estimated Wait Time:** 1-3 minutes for most generations
- **Timeout Protection:** 4-minute maximum wait time to prevent infinite waiting
- **Concurrent Processing:** Backend uses async processing for faster generation

## Error Handling

The integration includes comprehensive error handling:
- Network errors during submission
- Backend processing failures
- Job status check failures
- Invalid responses

## CORS Configuration

The backend includes CORS middleware to allow frontend requests:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Production Deployment

### Backend (Azure)
1. Deploy FastAPI backend to Azure App Service
2. Update CORS origins to include your frontend domain
3. Set environment variables in Azure

### Frontend (Vercel/Netlify)
1. Deploy Next.js frontend
2. Set `NEXT_PUBLIC_BACKEND_URL` to your Azure backend URL
3. Ensure environment variables are configured

## Testing the Integration

1. Start both frontend and backend locally
2. Navigate to `http://localhost:3000`
3. Enter journal text and select preferences
4. Submit and monitor the processing status
5. Download completed video when ready

## Troubleshooting

### Common Issues
- **CORS errors:** Check backend CORS configuration
- **Environment variables:** Ensure `.env.local` exists with correct URL
- **Network errors:** Verify backend is running and accessible
- **Job not found:** Check if job ID is being passed correctly

### Debug Steps
1. Check browser network tab for API calls
2. Verify backend logs at `/logs` endpoint
3. Test backend endpoints directly with curl/Postman
4. Check console for JavaScript errors 