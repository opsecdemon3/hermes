# Synapse — Learn From Minds You Trust

Search ideas, not videos. Instantly learn from creators you trust.

**Experience Qualities**:
1. **Futuristic** - Cyberpunk aesthetic with neon accents creates a cutting-edge, tech-forward feeling
2. **Focused** - Clean information hierarchy guides users directly to insights without distraction
3. **Powerful** - Fast semantic search and instant transcript navigation makes learning feel effortless

**Complexity Level**: Light Application (multiple features with basic state)
This is a data-rich search and discovery interface that connects to an existing FastAPI backend. It manages multiple views (library, search, transcripts, dashboard) with client-side state, but doesn't require complex user workflows or heavy client-side business logic.

## Essential Features

### Semantic Search
- **Functionality**: Natural language search across all TikTok transcripts using AI-powered semantic matching
- **Purpose**: Core value proposition - find ideas and insights, not just keywords
- **Trigger**: User types query in main search bar
- **Progression**: Enter query → Submit search → View ranked results with snippets → Click to view full transcript at timestamp
- **Success criteria**: Results appear in <2s, snippets clearly show relevance, clicking opens transcript at exact moment

### Creator Library
- **Functionality**: Browse all ingested TikTok creators with stats and topic breakdowns
- **Purpose**: Helps users understand content coverage and discover new creators
- **Trigger**: User navigates to Library page
- **Progression**: View creator cards → Click creator → See video list and topics → Open specific transcripts
- **Success criteria**: All creators display with accurate stats, categories, and last update times

### Transcript Viewer
- **Functionality**: Display full transcript with timestamp navigation and semantic highlight
- **Purpose**: Allows deep reading and precise timestamp jumping from search results
- **Trigger**: User clicks "Open Transcript" from search or creator page
- **Progression**: View transcript → Auto-scroll to timestamp if from search → Read context → Click timestamps to jump
- **Success criteria**: Highlights appear on matching segments, timestamps are clickable, smooth scrolling

### System Dashboard
- **Functionality**: Display system health metrics and backend status
- **Purpose**: Provides admin/power users visibility into data coverage
- **Trigger**: User navigates to Dashboard page
- **Progression**: View metrics → Click "Re-verify system" → See updated status
- **Success criteria**: Metrics update in real-time, verification shows detailed status

### Authentication (Minimal)
- **Functionality**: Basic login/create account flow
- **Purpose**: Gate access and prepare for future user-specific features
- **Trigger**: User visits app without session
- **Progression**: Land on login → Enter credentials or create account → Access main app
- **Success criteria**: Session persists, protected routes redirect to login

## Edge Case Handling
- **No search results** - Display helpful empty state suggesting query refinement
- **API errors** - Show toast notifications with retry actions, don't crash the UI
- **Loading states** - Skeleton loaders for all async content (search, transcripts, creators)
- **Missing transcripts** - Handle gracefully if video_id doesn't exist
- **Slow network** - Show loading indicators immediately, timeout after 30s with error
- **Timestamp format errors** - Validate MM:SS format, show error if malformed

## Design Direction
The design should feel like a premium cyberpunk intelligence platform - dark, neon-accented, with glass morphism elements that evoke a high-tech command center. This is a professional tool for serious learners, not a playful app. Minimal interface serves the data-dense nature of semantic search results and transcript exploration.

## Color Selection
**Triadic** - Using cyberpunk neon purple, electric blue, and cyan to create a futuristic tech aesthetic with high energy and visual interest.

- **Primary Color**: Electric Purple `oklch(0.65 0.25 300)` - Represents AI/semantic intelligence, used for primary CTAs and brand elements
- **Secondary Colors**: 
  - Neon Blue `oklch(0.6 0.2 250)` for secondary actions and accents
  - Cyan `oklch(0.75 0.15 200)` for highlights and active states
- **Accent Color**: Hot Pink `oklch(0.7 0.25 340)` - High-energy color for search highlights and important UI moments
- **Foreground/Background Pairings**:
  - Background (Deep Space `oklch(0.12 0.02 270)`): Cyan text `oklch(0.95 0.05 200)` - Ratio 13.2:1 ✓
  - Card (Dark Void `oklch(0.18 0.03 270)`): White text `oklch(0.98 0 0)` - Ratio 14.5:1 ✓
  - Primary (Electric Purple `oklch(0.65 0.25 300)`): White text `oklch(0.98 0 0)` - Ratio 7.8:1 ✓
  - Secondary (Neon Blue `oklch(0.6 0.2 250)`): White text `oklch(0.98 0 0)` - Ratio 6.2:1 ✓
  - Accent (Hot Pink `oklch(0.7 0.25 340)`): Deep Space `oklch(0.12 0.02 270)` - Ratio 8.9:1 ✓
  - Muted (Midnight `oklch(0.25 0.05 270)`): Cyan `oklch(0.75 0.1 200)` - Ratio 4.8:1 ✓

## Font Selection
Typography should balance futuristic tech aesthetics with high readability for long-form transcript content. Primary font is a clean geometric sans for UI, with monospace accents for timestamps and technical data.

- **Typographic Hierarchy**:
  - H1 (Page Title): JetBrains Mono Bold/32px/tight tracking (-0.02em)
  - H2 (Section Header): Inter SemiBold/24px/normal
  - H3 (Card Title): Inter Medium/18px/normal
  - Body (Transcript/Results): Inter Regular/15px/relaxed leading (1.6)
  - Caption (Timestamps/Meta): JetBrains Mono Regular/13px/wide tracking (0.05em)
  - Button (CTAs): Inter SemiBold/14px/uppercase/wide tracking (0.1em)

## Animations
Motion should feel instantaneous and purposeful, like a responsive command-line interface. Subtle glows and state transitions reinforce the cyberpunk aesthetic without slowing interaction.

- **Purposeful Meaning**: Glow effects on hover communicate interactivity, smooth transitions between pages maintain spatial context
- **Hierarchy of Movement**: 
  - Instant feedback: Button states, input focus (100ms)
  - Page transitions: Fade + slide (250ms)
  - Search results: Staggered reveal (50ms delay per item)
  - Transcript highlights: Smooth scroll + glow pulse (400ms)

## Component Selection

- **Components**:
  - `Input` - Search bar with neon glow focus state
  - `Card` - Glass-morphic creator cards and search results with subtle borders
  - `Badge` - Topic chips with neon outline styling
  - `Button` - Primary (filled purple glow), Secondary (outline blue), Ghost (text only)
  - `Scroll-area` - Transcript viewer with custom neon scrollbar
  - `Separator` - Subtle neon dividers between sections
  - `Skeleton` - Loading states with pulsing neon effect
  - `Toast` (Sonner) - Error and success notifications
  - `Tabs` - Creator detail view switching

- **Customizations**:
  - Custom sidebar navigation with neon active indicators
  - Custom search result card with timestamp jump buttons
  - Custom transcript viewer with clickable timestamps and highlight overlay
  - Neon glow utility classes for borders and shadows
  - Glass-morphism card backgrounds with backdrop blur

- **States**:
  - Buttons: Default (neon border), Hover (glow intensifies), Active (pressed scale), Disabled (dimmed opacity)
  - Inputs: Default (subtle border), Focus (neon glow ring), Error (red glow), Filled (border accent)
  - Cards: Default (glass), Hover (border glow + lift), Selected (persistent glow)

- **Icon Selection**:
  - Library: `Books` (Phosphor)
  - Search: `MagnifyingGlass` (Phosphor)
  - Transcripts: `Article` (Phosphor)
  - Dashboard: `ChartBar` (Phosphor)
  - Play/Jump: `Play`, `CaretRight` (Phosphor)
  - User: `User`, `UserCircle` (Phosphor)
  - System: `Cpu`, `Database` (Phosphor)

- **Spacing**: 
  - Card padding: `p-6` (24px)
  - Section gaps: `gap-8` (32px)
  - Component gaps: `gap-4` (16px)
  - Inline spacing: `gap-2` (8px)

- **Mobile**: 
  - Sidebar collapses to bottom navigation bar
  - Search results stack vertically with full width
  - Creator cards single column
  - Transcript viewer takes full screen with fixed timestamp header
  - Dashboard metrics stack in 1-2 column grid vs 4-column desktop
