# Image for a NYU Lab development environment
# FROM rofrano/nyu-devops-base:su25
FROM rofrano/pipeline-selenium:latest

# Set up the Python development environment
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN sudo python -m pip install --upgrade pip pipenv && \
    sudo pipenv install --system --dev

# Become a regular user and nstall user mode tools
USER ${USERNAME}
COPY .devcontainer/scripts/install-tools.sh /tmp/
RUN cd /tmp && bash ./install-tools.sh
