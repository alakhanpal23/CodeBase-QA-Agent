# CodeBase QA Agent Frontend

Next.js 14 App Router frontend for the FastAPI-based Codebase QA Agent.

## Features

- **Repository Management**: Add repositories via GitHub URLs, view ingestion status
- **Interactive Chat**: Query codebases with natural language
- **Code Snippets**: View code snippets with syntax highlighting and line numbers
- **Citations**: Clickable citations with file paths and line ranges
- **Mobile Responsive**: Works on all device sizes

## Tech Stack

- Next.js 14 with App Router
- TypeScript
- TanStack Query for data fetching
- Zustand for state management
- Monaco Editor for code previews
- Tailwind CSS for styling
- Lucide React for icons

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.local.example .env.local
```

3. Update the API base URL in `.env.local`:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000)

## Pages

- `/` - Home page with navigation
- `/repos` - Repository management (add, view, delete)
- `/chat` - Interactive chat interface

## API Integration

The frontend integrates with the FastAPI backend running on `http://localhost:8000`:

- `GET /repos` - List repositories
- `POST /ingest` - Add new repository
- `DELETE /repos/{id}` - Delete repository
- `POST /query` - Query codebase

## Development

```bash
# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```