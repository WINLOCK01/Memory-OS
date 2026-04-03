---
name: frontend-dashboard
description: >
  USE THIS SKILL whenever the user wants to modify, add, or improve the React frontend dashboard.
  Trigger when they mention: UI, dashboard, page, panel, component, visualization, graph viz,
  stats display, styling, CSS variables, theme, dark mode, React, or "show X in the frontend."
  Also trigger when connecting a new backend endpoint to the UI. If the user says "make it look
  better" or "add a new page," THIS skill applies.
---

# Frontend Dashboard Skill — Extending the MemoryOS React UI

## Overview

The MemoryOS frontend is a React application (or a single `MemoryOS.jsx` artifact).
It uses inline CSS with CSS variables for theming and communicates with the FastAPI backend
via `fetch()` calls. The dashboard includes: memory list, query interface, stats panel,
and knowledge graph visualization.

---

## File Structure

```
frontend/
├── src/
│   ├── App.jsx               ← Main app with routing
│   ├── components/
│   │   ├── QueryPanel.jsx    ← Search/query interface
│   │   ├── MemoryList.jsx    ← List of stored memories
│   │   ├── StatsPanel.jsx    ← Memory statistics
│   │   ├── GraphViz.jsx      ← Knowledge graph SVG visualization
│   │   └── IngestUpload.jsx  ← File upload for ingestion
│   ├── hooks/
│   │   └── useApi.js         ← Custom hook for API calls
│   └── styles/
│       └── variables.css     ← CSS variable definitions
├── public/
└── package.json
```

---

## CSS Variable System

All components use these CSS variables for consistent theming:

```css
/* frontend/src/styles/variables.css */

:root {
  /* Colors */
  --accent: #6366f1;          /* Indigo — primary action color */
  --accent-hover: #4f46e5;
  --surface: #1e1e2e;         /* Dark surface background */
  --surface-alt: #2a2a3e;     /* Slightly lighter surface */
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --border: #334155;
  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;
  
  /* Typography */
  --font-sans: 'Inter', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  
  /* Spacing */
  --radius: 8px;
  --radius-lg: 12px;
  --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
  
  /* Layout */
  --sidebar-width: 280px;
  --header-height: 64px;
}
```

**Convention**: NEVER use hardcoded colors. Always reference CSS variables.

---

## Adding a New Panel/Component

### Step 1: Create the Component

```jsx
// frontend/src/components/TopicClusters.jsx

import React, { useState, useEffect } from 'react';

const TopicClusters = () => {
  const [communities, setCommunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCommunities();
  }, []);

  const fetchCommunities = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/graph/communities');
      if (!response.ok) throw new Error('Failed to fetch communities');
      const data = await response.json();
      setCommunities(data.communities);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div style={styles.loading}>Loading clusters...</div>;
  if (error) return <div style={styles.error}>{error}</div>;

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Topic Clusters</h2>
      {communities.map((cluster, i) => (
        <div key={i} style={styles.cluster}>
          <span style={styles.badge}>Cluster {i + 1}</span>
          <span style={styles.count}>{cluster.length} memories</span>
        </div>
      ))}
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: 'var(--surface)',
    borderRadius: 'var(--radius-lg)',
    padding: '1.5rem',
    border: '1px solid var(--border)',
  },
  title: {
    fontFamily: 'var(--font-sans)',
    color: 'var(--text-primary)',
    marginBottom: '1rem',
  },
  cluster: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '0.75rem',
    backgroundColor: 'var(--surface-alt)',
    borderRadius: 'var(--radius)',
    marginBottom: '0.5rem',
  },
  badge: {
    color: 'var(--accent)',
    fontFamily: 'var(--font-mono)',
    fontSize: '0.875rem',
  },
  count: {
    color: 'var(--text-secondary)',
  },
  loading: {
    color: 'var(--text-secondary)',
    textAlign: 'center',
    padding: '2rem',
  },
  error: {
    color: 'var(--error)',
    textAlign: 'center',
    padding: '2rem',
  },
};

export default TopicClusters;
```

### Step 2: Add to App Layout

```jsx
// frontend/src/App.jsx

import TopicClusters from './components/TopicClusters';

function App() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
      {/* Existing panels */}
      <QueryPanel />
      <MemoryList />
      <StatsPanel />
      {/* New panel */}
      <TopicClusters />
    </div>
  );
}
```

---

## Demo Mode Fallback Pattern

When the backend is unavailable, show demo data instead of errors:

```jsx
const DEMO_STATS = {
  total_memories: 42,
  sources: { pdf: 15, url: 20, note: 7 },
  last_ingested: "2025-01-15T10:00:00",
};

const StatsPanel = () => {
  const [stats, setStats] = useState(DEMO_STATS);
  const [isDemo, setIsDemo] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/stats')
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(() => {
        setIsDemo(true);
        // Keep DEMO_STATS as fallback
      });
  }, []);

  return (
    <div style={styles.container}>
      {isDemo && <span style={styles.demoBadge}>Demo Mode</span>}
      <h3>Total Memories: {stats.total_memories}</h3>
      {/* ... */}
    </div>
  );
};
```

---

## Knowledge Graph SVG Visualization

The graph uses an SVG-based force-directed layout:

```jsx
// frontend/src/components/GraphViz.jsx

const GraphViz = ({ nodes, links }) => {
  const svgRef = useRef(null);
  
  // Node colors by source type
  const colorMap = {
    pdf: 'var(--accent)',
    url: 'var(--success)',
    note: 'var(--warning)',
    voice: 'var(--error)',
  };

  // Render nodes as circles, links as lines
  return (
    <svg ref={svgRef} width="100%" height="400"
         style={{ backgroundColor: 'var(--surface)', borderRadius: 'var(--radius-lg)' }}>
      {links.map((link, i) => (
        <line key={i}
          x1={link.source.x} y1={link.source.y}
          x2={link.target.x} y2={link.target.y}
          stroke="var(--border)" strokeWidth={link.weight * 2}
        />
      ))}
      {nodes.map((node, i) => (
        <circle key={i}
          cx={node.x} cy={node.y} r={8}
          fill={colorMap[node.group] || 'var(--text-secondary)'}
          style={{ cursor: 'pointer' }}
        >
          <title>{node.label}</title>
        </circle>
      ))}
    </svg>
  );
};
```

---

## Connecting to New API Endpoints

```jsx
// Custom hook pattern
const useApi = (endpoint, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${BASE_URL}${endpoint}`, options);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        setData(json);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [endpoint]);

  return { data, loading, error };
};
```

---

## Styling Conventions

1. **Always use CSS variables** — never hardcode colors
2. **Inline styles** for component-specific styling
3. **`var(--font-mono)`** for data, code, IDs
4. **`var(--font-sans)`** for headings and body text
5. **`var(--radius)`** for all border-radius values
6. **Dark theme by default** — surface colors are dark
7. **Hover states** — always add hover effects on interactive elements
