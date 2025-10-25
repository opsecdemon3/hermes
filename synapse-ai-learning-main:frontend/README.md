# Synapse — Learn From Minds You Trust

A cyberpunk-inspired semantic search platform for TikTok transcripts. Search ideas, not videos. Instantly learn from creators you trust.

## Features

- **Semantic Search** - AI-powered natural language search across all transcripts
- **Creator Library** - Browse and explore ingested TikTok creators
- **Transcript Viewer** - Read full transcripts with timestamp navigation
- **System Dashboard** - Monitor system health and data coverage
- **Timestamp Jumping** - Click to jump to exact moments in transcripts from search results

## Tech Stack

- **Frontend**: React 19 + TypeScript + Vite
- **Routing**: React Router v6
- **UI Components**: shadcn/ui v4 + Tailwind CSS v4
- **Icons**: Phosphor Icons
- **Backend**: FastAPI (separate service)
- **State Management**: React hooks + Spark KV storage

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- FastAPI backend running (default: http://localhost:8000)

### Installation

1. Clone and install dependencies:
```bash
npm install
```

2. Configure your API backend:
```bash
cp .env.example .env
# Edit .env and set VITE_API_BASE to your FastAPI backend URL
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser to the provided URL (typically http://localhost:5173)

## Backend API Requirements

Your FastAPI backend must implement these endpoints:

- `GET /api/accounts` - List all creators
- `GET /api/accounts/{username}/tags` - Get creator topics
- `GET /api/accounts/{username}/category` - Get creator categories
- `POST /api/search/semantic` - Semantic search (body: `{query: string}`)
- `GET /api/transcript/{username}/{video_id}` - Get transcript (optional params: `jump`, `context`)
- `GET /api/verify/system` - System status
- `POST /api/verify/system` - Re-verify system

## Usage

### Login
Use any username/password to access the app (authentication is minimal for now).

### Search
Navigate to Search and enter any natural language query to find relevant transcript snippets across all creators.

### Browse Creators
Visit the Library to browse all ingested creators, their topics, and video counts.

### View Transcripts
Click any search result or creator video to view the full transcript with clickable timestamps.

### Monitor System
Visit the Dashboard to see system statistics and re-verify backend health.

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # shadcn components
│   ├── CreatorCard.tsx
│   ├── SearchResultCard.tsx
│   ├── Sidebar.tsx
│   ├── StatCard.tsx
│   └── TranscriptViewer.tsx
├── lib/
│   ├── api.ts          # API service layer
│   ├── types.ts        # TypeScript interfaces
│   └── utils.ts        # Utilities
├── pages/              # Route pages
│   ├── LoginPage.tsx
│   ├── SearchPage.tsx
│   ├── LibraryPage.tsx
│   ├── CreatorDetailPage.tsx
│   ├── TranscriptsPage.tsx
│   ├── TranscriptPage.tsx
│   └── DashboardPage.tsx
├── App.tsx             # Main app with routing
└── index.css           # Cyberpunk theme styles
```

## Design System

### Colors
- **Primary**: Electric Purple `oklch(0.65 0.25 300)`
- **Secondary**: Neon Blue `oklch(0.6 0.2 250)`
- **Accent**: Hot Pink `oklch(0.7 0.25 340)`
- **Background**: Deep Space `oklch(0.12 0.02 270)`

### Typography
- **UI**: Inter (400, 500, 600, 700)
- **Code/Data**: JetBrains Mono (400, 700)

### Visual Style
- Glass-morphic panels with backdrop blur
- Neon glow effects on interactive elements
- Smooth transitions and hover states
- Cyberpunk aesthetic with professional polish

## Future Enhancements

The UI is designed to be extendable for:
- Analytics and insights dashboard
- Competitor comparison tools
- Trend alerts and notifications
- Playlist/channel syncing
- Advanced filters and sorting
- User preferences and saved searches
- Export and sharing features

## License

MIT
