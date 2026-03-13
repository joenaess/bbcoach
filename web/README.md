# BBCoach Web

Modern Next.js 14 frontend for the BBCoach basketball analytics platform.

## Features

- 🏀 **Dashboard**: Real-time data overview and quick actions
- 📊 **League Statistics**: Top players, leaderboards, team stats
- 🔮 **Game Predictor**: AI-powered matchup analysis
- 🤖 **AI Coach**: Interactive coaching chat assistant
- ⚖️ **Player Comparison**: Side-by-side statistical comparison
- 📅 **Schedule**: Team schedules and roster view

## Tech Stack

- **Framework**: Next.js 14.1 (App Router)
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS + Custom dark theme
- ** Components**: Radix UI primitives (shadcn/ui style)
- **State**: Zustand
- **Data Fetching**: SWR
- **HTTP**: Axios
- **Icons**: Lucide React
- **Charts**: Recharts, Plotly.js

## Getting Started

### Prerequisites

- Node.js 18+
- npm, yarn, or pnpm
- Backend API running at http://localhost:8000

### Installation

```bash
# Install dependencies
npm install
# or
yarn install
# or
pnpm install
```

### Development

```bash
# Start development server
npm run dev

# Or use the provided script
./start.sh
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Pages

- `/` - Landing page with feature overview
- `/dashboard` - Data overview and quick actions
- `/stats` - League statistics and leaderboards
- `/predictor` - AI-powered game predictions
- `/coach` - Interactive AI coaching chat
- `/comparison` - Player comparison tool
- `/schedule` - Team schedules

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Project Structure

```
web/
├── app/                      # Next.js App Router
│   ├── page.tsx              # Landing page
│   ├── layout.tsx            # Root layout
│   ├── globals.css           # Global styles
│   ├── dashboard/            # Dashboard page
│   ├── stats/                # Stats page
│   ├── predictor/            # Game predictor
│   ├── coach/                # AI coach chat
│   ├── comparison/           # Player comparison
│   ├── schedule/             # Schedule page
│   └── not-found.tsx         # 404 page
├── components/               # React components
│   └── ui/                  # UI components (shadcn/ui)
├── hooks/                   # React hooks
│   ├── use-api.ts           # SWR data hooks
│   └── use-app-store.ts     # Zustand global state
├── lib/                     # Utilities
│   ├── api-client.ts        # Axios API client
│   └── utils.ts             # Helper functions
├── types/                   # TypeScript types
│   └── api.ts               # API type definitions
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── README.md
```

## API Integration

The frontend communicates with the FastAPI backend via `/lib/api-client.ts`:

```typescript
import api from '@/lib/api-client';

// Get data status
const status = await api.dataStatus();

// Get top players
const players = await api.getTopPlayers(2025, "Men", "PPG", 10);

// Ask AI coach
const response = await api.askCoach({ question: "Your question", context: "" });
```

## State Management

Global state using Zustand:

```typescript
import { useAppStore } from '@/hooks/use-app-store';

function MyComponent() {
  const { currentSeason, setCurrentSeason } = useAppStore();
  // ...
}
```

## Data Fetching

SWR hooks for efficient data fetching:

```typescript
import { useTopPlayers } from '@/hooks/use-api';

function StatsPage() {
  const { data, error, isLoading } = useTopPlayers(2025, "Men", "PPG", 10);
  // ...
}
```

## Styling

The app uses Tailwind CSS with a custom dark theme:
- Primary color: Basketball orange (#FF5722)
- Dark background with high-contrast text
- Responsive design for all screen sizes

## Performance

- Static generation where possible
- Client-side data fetching with SWR caching
- Optimized images
- Lazy loading components

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Follow code style guidelines
3. Run linter: `npm run lint`
4. Test thoroughly
5. Submit pull request

## License

MIT
