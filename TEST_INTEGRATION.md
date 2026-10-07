# Integration Test Checklist

## ✅ Backend Tests

### 1. Health Check
```bash
curl http://localhost:8000/health
```
**Expected**: `{"status":"ok"}`
**Result**: ✅ PASS

### 2. API Documentation
**URL**: http://localhost:8000/docs
**Expected**: Swagger UI with all endpoints listed
**Result**: Check manually

### 3. CORS Configuration
**Expected**: Allows `http://localhost:3000`
**Result**: ✅ Configured

## ✅ Frontend Tests

### 1. Landing Page
**URL**: http://localhost:3000
**Expected**: 
- Om watermark visible
- Sun bursts animated
- Sparkles present
- Theme toggle in top-right
- "Get Started" button works
**Result**: Check manually

### 2. Login Page
**URL**: http://localhost:3000/login
**Expected**:
- Glass morphism card
- OTP/Google tabs
- Guest access button
- Floating theme toggle (top-right)
- Quote at bottom
**Result**: Check manually

### 3. Onboarding Flow
**URL**: http://localhost:3000/onboarding
**Expected**:
- 7 steps with StepperDots
- Pill options clickable
- Confidence slider works (1-10)
- Floating theme toggle (top-right)
- "Start my journey" button on step 7
**Result**: Check manually

**Action**: Complete onboarding
- Should create backend profile
- Should save to localStorage
- Should redirect to `/app/chat`

### 4. Chat Page
**URL**: http://localhost:3000/app/chat
**Expected**:
- Title: "Spiritual Guidance Session"
- Empty state with starter prompts
- Pill-shaped input at bottom
- Send message triggers API call
**Result**: Check manually

**Test Message**: "I failed my exam and feel worthless"
**Expected Response**:
- ThreeLayerCard appears
- Layer 1: Listening summary
- Layer 2: Documented teaching (or "No match" card)
- Layer 3: AI reflection with next step
**Result**: Will be 503 without Gemini key (expected)

### 5. Journal Page
**URL**: http://localhost:3000/app/journal
**Expected**:
- GlassCard with "Journal" title
- Date pill (top-right)
- Textarea for writing
- Live tag chips appear as you type
- Save button (saffron, rounded-full)
- History panel on right (desktop)
**Result**: Check manually

**Test Entry**: "I feel anxious about my upcoming exam"
**Expected Tags**: anxiety, academic_pressure
**Action**: Save entry
**Expected**: Entry appears in history panel

### 6. Growth Page
**URL**: http://localhost:3000/app/growth
**Expected**:
- Title: "Growth Journey & Weekly Dashboard"
- Bento grid layout:
  - "Your Week" metrics (4 tiles)
  - "Insights: What Changed?" narrative
  - "Pattern Recognition" with sparkline
  - "Focus for next week" saffron banner
- Demo data notice at bottom
**Result**: Check manually

### 7. Honesty/Vivekananda vs Me
**URL**: http://localhost:3000/app/honesty
**Expected**: Comparison view (if implemented)
**Result**: Check manually

## ✅ Integration Tests

### Test 1: Profile Creation
**Steps**:
1. Open DevTools Console
2. Clear localStorage: `localStorage.clear()`
3. Complete onboarding
4. Check localStorage: `localStorage.getItem('jagrat_profile_token')`
**Expected**: Token should be present
**Result**: Check manually

### Test 2: API Calls (Network Tab)
**Steps**:
1. Open DevTools Network tab
2. Send a chat message
3. Check for `POST http://localhost:8000/api/mentor`
**Expected**: 
- Request includes `X-Profile-Token` header
- Response: 503 (no Gemini key) or 200 (with key)
**Result**: Check manually

### Test 3: Journal Persistence
**Steps**:
1. Write and save a journal entry
2. Open Network tab
3. Check for `POST http://localhost:8000/api/journal`
4. Refresh the page
5. Check for `GET http://localhost:8000/api/journal`
**Expected**: 
- POST succeeds (200)
- GET returns the saved entry
- Entry appears in history panel
**Result**: Check manually

### Test 4: Theme Toggle
**Steps**:
1. Click theme toggle (Sun/Moon icon)
2. Verify theme switches
3. Refresh page
4. Verify theme persists
**Expected**: 
- Smooth transition
- All colors update
- Preference saved
**Result**: Check manually

### Test 5: Mock Mode Fallback
**Steps**:
1. Stop backend server
2. Set `NEXT_PUBLIC_USE_MOCK=true` in `.env.local`
3. Restart frontend
4. Try sending a chat message
**Expected**: 
- Uses mock responses
- No backend calls
- Still functional
**Result**: Check manually

## ✅ Visual QA

### Theme: Light Mode
- [ ] Peach-cream gradient (#FFF7EA→#F8C9A2)
- [ ] Saffron buttons readable
- [ ] Om watermark subtle
- [ ] Glass morphism cards visible
- [ ] Text contrast sufficient

### Theme: Dark Mode
- [ ] Dark gradient (#0B0D13→#161A26)
- [ ] Saffron buttons readable (dark text)
- [ ] Om watermark visible but subtle
- [ ] Glass morphism cards prominent
- [ ] Text contrast sufficient

### Responsive Design
- [ ] Mobile: History panel stacks below
- [ ] Mobile: Navigation hamburger works
- [ ] Tablet: Layout adapts
- [ ] Desktop: Full bento grid

## 🐛 Known Issues

1. **CSS Chunk Warnings**: Benign Next.js dev server warnings
2. **503 Without Gemini Key**: Expected behavior, backend needs API key
3. **Scroll Behavior Warning**: Can be ignored or add `data-scroll-behavior` to `<html>`

## 🎯 Success Criteria

- [x] Backend health endpoint responds
- [x] Frontend compiles without errors
- [x] Environment variables configured
- [x] Both servers running
- [x] FloatingThemeToggle on all pages
- [ ] Profile creation works (manual test)
- [ ] API calls include auth headers (manual test)
- [ ] Journal saves to backend (manual test)
- [ ] Theme persists across reloads (manual test)

## 📝 Notes

- Backend will return 503 for AI features without Gemini API key
- This is expected and documented
- All endpoints are accessible via `/api/*`
- Frontend gracefully handles backend errors

---

**Manual testing recommended** to verify all integration points work correctly.

To add Gemini API key for full functionality:
```bash
# In jagrat-backend/.env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

Then restart backend server.
