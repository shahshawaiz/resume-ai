# ps -ef | grep "flask" | grep -v grep | awk '{print $2}' | xargs kill &
# ps -ef | grep "node" | grep -v grep | awk '{print $2}' | xargs kill  &

#!/bin/bash

# Navigate to the Node server directory and start the Node development server in the background
cd /app/client/app
npm run build &
npm start

# Navigate to the Flask server directory
cd /app/server

sleep 5

python boot_server.py
