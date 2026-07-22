#!/usr/bin/env bash
# ==============================================================================
# Kafka Topic Creation Script (scripts/create_kafka_topics.sh)
# Creates Required Production Kafka Topics (traffic.raw, validated, dead-letter)
# ==============================================================================

set -eo pipefail

KAFKA_HOST="${KAFKA_HOST:-localhost:9092}"

echo "======================================================================"
echo "[INFO] Creating Production Kafka Topics on '${KAFKA_HOST}'..."
echo "======================================================================"

# Create traffic.raw topic
kafka-topics.sh --bootstrap-server "${KAFKA_HOST}" --create --if-not-exists --topic traffic.raw --partitions 3 --replication-factor 1

# Create traffic.validated topic
kafka-topics.sh --bootstrap-server "${KAFKA_HOST}" --create --if-not-exists --topic traffic.validated --partitions 3 --replication-factor 1

# Create traffic.invalid topic
kafka-topics.sh --bootstrap-server "${KAFKA_HOST}" --create --if-not-exists --topic traffic.invalid --partitions 1 --replication-factor 1

# Create traffic.dead-letter topic
kafka-topics.sh --bootstrap-server "${KAFKA_HOST}" --create --if-not-exists --topic traffic.dead-letter --partitions 1 --replication-factor 1

echo "======================================================================"
echo "[SUCCESS] All Production Kafka Topics Created Successfully!"
echo "======================================================================"
