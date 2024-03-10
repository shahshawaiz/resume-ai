ps -ef | grep "flask" | grep -v grep | awk '{print $2}' | xargs kill &
ps -ef | grep "node" | grep -v grep | awk '{print $2}' | xargs kill  &

#!/bin/bash

# Navigate to the Node server directory and start the Node development server in the background
cd client/app
npm run dev &

cd ../..

# Navigate to the Flask server directory
cd server

sleep 5

# Start the Flask server in the foreground
# Note: '&' is removed to keep Flask running in the foreground
python boot_server.py