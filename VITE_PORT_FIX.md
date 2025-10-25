# Vite Port 5001 Issue Fix

## Problem
Vite dev server always starts on port 5000 instead of the configured port 5001, causing a blank screen in the browser.

## Root Cause
The **@github/spark** plugin has a hardcoded default port of 5000 that overrides the Vite config settings.

Location: `node_modules/@github/spark/dist/sparkVitePlugin.js`
```javascript
const { port = 5000, ... } = opts;
```

## Solution
Pass the port explicitly to the `sparkPlugin()` in `vite.config.ts`:

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    createIconImportProxy() as PluginOption,
    sparkPlugin({ port: 5001 }) as PluginOption,  // ← MUST pass port here
  ],
  resolve: {
    alias: {
      '@': resolve(projectRoot, 'src')
    }
  },
  server: {
    port: 5001,        // ← This alone is NOT enough
    strictPort: true,  // ← Helps catch port conflicts
    host: '0.0.0.0',
  },
});
```

## Why Regular Port Config Doesn't Work
- Vite's `server.port` config is overridden by Spark plugin
- `strictPort: false` (default) causes Vite to silently use next available port (5000)
- Port 5001 may appear blocked but it's actually the Spark plugin ignoring the Vite config

## Verification
After fixing, verify the output shows port 5001:
```bash
npm run dev

# Should show:
# ➜  Local:   http://localhost:5001/
# ➜  Network: http://140.232.174.170:5001/
```

## System Configuration
- **API Server**: Port 8000
- **Frontend (Vite)**: Port 5001
- **Frontend API Config**: `src/lib/api.ts` uses `http://localhost:8000`

## Quick Fix Commands
```bash
# Kill any running Vite processes
pkill -9 -f "vite|npm.*dev"

# Start fresh
cd synapse-ai-learning-main
npm run dev
```

## Related Files
- `synapse-ai-learning-main/vite.config.ts` - Main config (MUST pass port to sparkPlugin)
- `synapse-ai-learning-main/src/lib/api.ts` - API endpoint config
- `synapse-ai-learning-main/package.json` - Has `"kill": "fuser -k 5000/tcp"` referencing old port

## Notes
- Port 5000 shows blank screen because the app is configured for 5001
- Always check terminal output to verify actual port Vite is using
- The Spark plugin port parameter is REQUIRED, not optional
