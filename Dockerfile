# Base image
FROM node:16 AS base

# Set the working directory
WORKDIR /app

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

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
