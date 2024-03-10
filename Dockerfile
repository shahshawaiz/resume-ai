# Start with the official Python image
FROM python:3.8-slim as base

# Install Node.js
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_current.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, and wheel to the latest versions
RUN pip3 install --upgrade pip setuptools wheel

# Copy and install Python requirements
COPY server/requirements.txt /app/server/
RUN pip3 install --no-cache-dir -r /app/server/requirements.txt

# Copy package.json and package-lock.json (or yarn.lock) for Node dependencies
COPY client/ /app/client/

# Install Node dependencies
WORKDIR /app/client/app
RUN npm install

# # Copy the client app and build it
# COPY client/ /app/client/
# RUN yarn build

# Copy the server code
WORKDIR /app/server
COPY server/ /app/server/

# Copy scripts
COPY scripts/ /app/scripts/

# Make the init script executable
RUN chmod +x /app/scripts/run_server.sh

# Expose the port your server listens on
EXPOSE 3000
EXPOSE 8000

WORKDIR /app 


# Command to run the server.
# The CMD should call the init_server.sh script which should start both the Python server and the Next.js app.
CMD ["/app/scripts/run_server.sh"]
