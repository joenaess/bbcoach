# Migration Plan: Streamlit → Next.js + FastAPI

## Overview
Migrating BBCoach from a monolithic Streamlit application to a modern Next.js frontend with FastAPI backend.

## Phase 1: Backend Foundation ✅ (Done)
- [x] Create configuration management system
- [x] Extract business logic into service layer
- [x] Set up FastAPI backend structure
- [x] Create RESTful API endpoints

## Phase 2: Frontend Setup (Current)
- [ ] Initialize Next.js 14 project with TypeScript
- [ ] Install shadcn/ui components
- [ ] Set up project structure
- [ ] Create API client layer
- [ ] Configure environment variables

## Phase 3: Core Features
- [ ] Dashboard page (data overview)
- [ ] League stats page
- [ ] Player comparison page
- [ ] Game predictor page
- [ ] Coach's Corner (chat)
- [ ] Schedule page

## Phase 4: Integration & Polish
- [ ] Connect all frontend to backend
- [ ] Add error handling
- [ ] Implement loading states
- [ ] Add authentication (optional)
- [ ] Performance optimization
- [ ] Testing
- [ ] Deployment

## File Structure

### Backend
```
api/
├── main.py              # FastAPI app
├── __init__.py
└── README.md

src/bbcoach/
├── config/
│   ├── __init__.py
│   └── settings.py      # Pydantic settings
├── core/
│   ├── __init__.py
│   ├── coach_service.py     # AI coach logic
│   ├── analytics_service.py # Statistics logic
│   └── data_service.py      # Data management
├── ai/
├── data/
├── rag/
└── ui/
```

### Frontend (To be created)
```
web/
├── app/
│   ├── api/
│   ├── (auth)/
│   ├── dashboard/
│   ├── stats/
│   ├── predictor/
│   ├── coach/
│   └── schedule/
├── components/
│   ├── ui/
│   ├── charts/
│   └── forms/
├── lib/
│   ├── api-client.ts
│   └── utils.ts
├── hooks/
└── types/
```

## Next Steps

1. **Create Next.js project** (Next)
   ```bash
   uv create --template next web
   cd web
   uv add @shadcn/ui
   ```

2. **Build API client** (Next)
   - Create typed API client
   - Add error handling
   - Implement caching

3. **Build first page** (Next)
   - Start with dashboard
   - Show data status
   - Display quick stats

4. **Iterate through features** (Next)
   - League stats table
   - Player comparison
   - Game predictor
   - Chat interface

5. **Testing & Deployment** (Last)
   - Unit tests
   - E2E tests
   - CI/CD setup
   - Deploy to Vercel (frontend) + Railway (backend)

## Benefits

- **Better UX**: Modern, responsive SPA
- **Performance**: Client-side rendering, no full reloads
- **Maintainability**: Separation of concerns
- **Scalability**: Independent frontend/backend
- **Flexibility**: Easy to add features (mobile, realtime, etc.)

## Estimated Timeline

- Phase 1: ✅ Complete (Done)
- Phase 2: 1-2 days (Next.js setup)
- Phase 3: 5-7 days (Core features)
- Phase 4: 3-5 days (Polish & deploy)

**Total**: 2-3 weeks
