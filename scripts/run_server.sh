# ps -ef | grep "flask" | grep -v grep | awk '{print $2}' | xargs kill &
# ps -ef | grep "node" | grep -v grep | awk '{print $2}' | xargs kill  &

#!/bin/bash

# Navigate to the Node server directory and start the Node development server in the background
cd /app/client/app

# buiuld and start app.
npm run build
npm start

#
sleep 5

# Navigate to the Flask server directory
cd /app/server

# Start the Flask server in the foreground
# Note: '&' is removed to keep Flask running in the foreground
python boot_server.py
