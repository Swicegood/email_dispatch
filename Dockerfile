# Start from a base Ubuntu image
FROM ubuntu:latest

# Install dependencies for adding Docker's repository
RUN apt-get update \
    && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common

# Add Docker’s official GPG key
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

# Add Docker's stable repository
RUN add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

# Install Docker
RUN apt-get update && apt-get install -y docker-ce

# Install Python and pip
RUN apt-get install -y python3.8 python3-pip

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the code into the container
COPY . .

# Set the command to run when the container starts
CMD ["python3", "main.py"]
