#!/bin/bash
# Simple deployment script - KISS approach

# Get server details
read -p "Enter server IP: " SERVER_IP
read -p "Enter username: " USER
read -sp "Enter password: " PASSWORD
echo

# Create archive of all necessary files
echo "Creating archive..."
tar -czf atlas.tar.gz Dockerfile requirements.txt .env frontend.py fonts/

# Send archive to server
echo "Sending files to server..."
sshpass -p "$PASSWORD" scp atlas.tar.gz $USER@$SERVER_IP:~/

# Run deployment on server
echo "Deploying application..."
sshpass -p "$PASSWORD" ssh $USER@$SERVER_IP << 'EOF'
  # Extract files
  mkdir -p ~/atlas
  tar -xzf ~/atlas.tar.gz -C ~/atlas
  cd ~/atlas
  
  # Build and run Docker
  docker build -t atlas-app .
  docker stop atlas-container 2>/dev/null || true
  docker rm atlas-container 2>/dev/null || true
  
  # Create output directory
  mkdir -p ~/atlas/output
  
  # Run new container
  docker run -d --name atlas-container -p 8508:80 \
    -v ~/atlas/output:/app/output \
    --restart unless-stopped \
    atlas-app
  
  # Cleanup
  cd ~
  rm -f atlas.tar.gz
  echo "Deployment complete! App running at http://$(hostname -I | awk '{print $1}'):8508"
EOF

# Local cleanup
rm -f atlas.tar.gz