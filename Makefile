# ==============================================================================
# Traffic Prediction Project Automation (Makefile)
# Convenient Command Targets & Shortcuts for End-to-End Execution
# ==============================================================================

.PHONY: help up down init ingest process eda train predict dashboard pipeline test clean

# Default target: display help menu
help:
	@echo "======================================================================"
	@echo " Traffic Prediction System — Makefile Commands Menu"
	@echo "======================================================================"
	@echo " make up        - Start all Docker Compose services"
	@echo " make down      - Stop all Docker Compose services"
	@echo " make init      - Provision initial HDFS folder structure"
	@echo " make ingest    - Execute data ingestion pipeline (API / Seed)"
	@echo " make process   - Run Apache Spark ETL data processing job"
	@echo " make eda       - Run Exploratory Data Analysis & export reports"
	@echo " make train     - Train Spark MLlib GBTRegressor model"
	@echo " make predict   - Run batch prediction engine smoke test"
	@echo " make dashboard - Start Streamlit web dashboard container"
	@echo " make pipeline  - Execute full end-to-end master pipeline"
	@echo " make test      - Execute pytest test suites"
	@echo " make clean     - Clean temporary bytecode and caches"
	@echo "======================================================================"

# Start Docker containers
up:
	docker compose up -d

# Stop Docker containers
down:
	docker compose down

# Provision initial HDFS directory paths
init:
	bash scripts/init_hdfs.sh

# Run data ingestion pipeline
ingest:
	bash scripts/run_ingestion.sh

# Run Spark ETL processing job
process:
	bash scripts/run_processing.sh

# Run Exploratory Data Analysis script
eda:
	PYTHONPATH=. python3 -m src.processing.exploratory_analysis

# Train GBTRegressor model
train:
	bash scripts/run_training.sh

# Run batch prediction smoke test
predict:
	bash scripts/run_prediction.sh

# Launch Streamlit dashboard container
dashboard:
	docker compose up -d streamlit

# Run full master pipeline
pipeline:
	bash scripts/run_pipeline.sh

# Run pytest unit & integration test suites
test:
	pytest -v

# Clean temporary files & caches
clean:
	bash scripts/clean_project.sh
