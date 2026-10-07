# 🚀 Jagrat Quick Start Guide

## Prerequisites
- ✅ Node.js installed
- ✅ Python 3.12+ installed
- ⚠️ Gemini API Key (optional, but recommended)

## Step 1: Start Backend (Terminal 1)

```powershell
cd jagrat-backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Expected Output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
GEMINI_API_KEY is not set: mentor, journal and Vivekananda-vs-Me requests will return 503.
INFO:     Application startup complete.
```

✅ Backend running at http://localhost:8000

## Step 2: Start Frontend (Terminal 2)

```powershell
cd jagrat-frontend
npm run dev
```

**Expected Output**:
```
  ▲ Next.js 15.x.x
  - Local:        http://localhost:3000
  - Environments: .env.local

 ✓ Starting...
 ✓ Ready in 2.5s
```

✅ Frontend running at http://localhost:3000

## Step 3: Test the Application

### 3.1 Open Frontend
Open your browser: **http://localhost:3000**

You should see:
- Om watermark in center
- Animated sun bursts
- Sparkles scattered around
- "जाग्रत Jagrat" logo
- "Get Started" button
- Theme toggle (Sun/Moon icon)

### 3.2 Complete Onboarding
1. Click "Get Started"
2. Complete all 7 steps:
   - Focus area
   - Biggest challenge  
   - Failure response
   - Confidence slider
   - Primary goal
   - Preferences
   - Review
3. Click "⚡ Start my journey"

✅ You should land on the Chat page

### 3.3 Test Chat
1. Type a message: "I feel anxious about my exam"
2. Click Send or press Enter
3. Wait for response

**With Gemini Key**: You'll get a full 3-layer card
**Without Gemini Key**: You'll see a 503 error (expected)

### 3.4 Test Journal
1. Navigate to **Journal** (sidebar)
2. Write an entry: "Today I studied for 3 hours"
3. Watch tags appear automatically
4. Click **Save**
5. Entry should appear in the history panel

### 3.5 Test Growth
1. Navigate to **Growth** (sidebar)
2. See the bento grid:
   - Your Week metrics (4 tiles)
   - Insights card
   - Pattern Recognition
   - Focus banner

## Step 4: Add Gemini API Key (Optional but Recommended)

### 4.1 Get API Key
1. Visit https://makersuite.google.com/app/apikey
2. Create a new API key
3. Copy the key

### 4.2 Update Backend
```powershell
cd jagrat-backend
notepad .env
```

Add your key:
```env
GEMINI_API_KEY=AIzaSy...your-key-here
```

Save and close.

### 4.3 Restart Backend
Press `Ctrl+C` in Terminal 1, then:
```powershell
uvicorn app.main:app --reload --port 8000
```

✅ AI features now fully functional!

## Troubleshooting

### Backend Won't Start
**Issue**: `ModuleNotFoundError`
**Fix**:
```powershell
cd jagrat-backend
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Won't Start
**Issue**: `Cannot find module`
**Fix**:
```powershell
cd jagrat-frontend
rm -rf node_modules
npm install
```

### 503 Errors in Chat
**Issue**: "Mentor API error: 503"
**Cause**: No Gemini API key
**Fix**: Add key to `jagrat-backend/.env` (see Step 4)

### CORS Errors
**Issue**: "CORS policy: No 'Access-Control-Allow-Origin'"
**Fix**: Check `jagrat-backend/.env`:
```env
CORS_ORIGINS=http://localhost:3000
```

### Profile Token Missing
**Issue**: Backend returns 401/403
**Fix**: Clear localStorage and re-do onboarding:
```javascript
// In browser console
localStorage.clear()
// Then reload page and complete onboarding again
```

## Verify Integration

### Check Backend Health
```powershell
Invoke-WebRequest -Uri http://localhost:8000/health -UseBasicParsing
```
**Expected**: `{"status":"ok"}`

### Check API Docs
Open: http://localhost:8000/docs

Should show Swagger UI with all endpoints.

### Check Frontend Pages
- Landing: http://localhost:3000
- Login: http://localhost:3000/login
- Onboarding: http://localhost:3000/onboarding
- Chat: http://localhost:3000/app/chat
- Journal: http://localhost:3000/app/journal
- Growth: http://localhost:3000/app/growth

All should load without errors.

## Next Steps

1. **Add Teaching Data**: Backend includes sample teachings in `jagrat-backend/data/articles.json`

2. **Configure Database**: For production, switch to PostgreSQL:
   ```env
   DATABASE_URL=postgresql://user:pass@host:5432/jagrat
   ```

3. **Deploy**:
   - Backend: Render, Railway, or any Python host
   - Frontend: Vercel, Netlify, or any Next.js host

4. **Customize**: Edit theme colors in `jagrat-frontend/styles/globals.css`

## Key URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

## Default Credentials

**No login required!** Anonymous profile created during onboarding.

## Support

- Backend README: `jagrat-backend/README.md`
- Frontend README: `jagrat-frontend/README.md`
- Full Documentation: `PROJECT_SUMMARY.md`
- Integration Guide: `INTEGRATION_COMPLETE.md`
- Test Checklist: `TEST_INTEGRATION.md`

---

## TL;DR

```powershell
# Terminal 1
cd jagrat-backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 2  
cd jagrat-frontend
npm run dev

# Browser
# Open: http://localhost:3000
```

**That's it! 🎉**

