#!/bin/sh
set -e

# Start Express API server on port 3000 (internal)
node dist/core/server/index.js &

# Start Next.js dashboard on Railway's PORT (external)
npx next start dashboards -p ${PORT:-3001} &

# Wait for either process to exit
wait
