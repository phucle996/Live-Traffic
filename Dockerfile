# ==============================================================================
# Dockerfile Specification - Python 3.10 & PySpark Runtime Container
# ==============================================================================

# Base image: Python 3.10 slim Linux image
FROM python:3.10-slim

# Maintainer metadata
LABEL maintainer="Data Engineering Team"
LABEL description="Traffic Prediction Lab 5 Application Container"

# Set environment variables for non-interactive installs & Java setup
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    JAVA_HOME=/usr/lib/jvm/default-java \
    PATH="/usr/lib/jvm/default-java/bin:${PATH}"

# Install Java OpenJDK (default-jre-headless) and system dependencies required for PySpark & HDFS client
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    curl \
    wget \
    procps \
    netcat-openbsd \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Set working directory inside container
WORKDIR /app

# Copy requirements file first for Docker layer caching optimization
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source code and configuration into container
COPY . /app

# Set default PYTHONPATH
ENV PYTHONPATH=/app

# Expose Streamlit dashboard port
EXPOSE 8501

# Default command to run Streamlit app
CMD ["streamlit", "run", "src/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
