/home/phucle/Desktop/lab5
├── airflow
│   ├── dags
│   │   ├── model_monitoring_dag.py
│   │   ├── model_training_dag.py
│   │   ├── traffic_etl_dag.py
│   │   └── traffic_ingestion_dag.py
│   ├── Dockerfile
│   └── requirements.txt
├── artifacts
│   ├── inference
│   │   ├── candidate-onnx
│   │   │   ├── manifest.json
│   │   │   └── model.onnx
│   │   ├── candidate-tree
│   │   │   ├── manifest.json
│   │   │   ├── model.json
│   │   │   └── model_manifest.json
│   │   └── golden
│   │       └── golden_predictions.jsonl
│   ├── locks
│   ├── manifests
│   │   ├── ingestion_manifest.json
│   │   └── lab_assets.json
│   ├── metrics
│   │   └── metrics.json
│   ├── mlops
│   │   └── registry.json
│   ├── models
│   │   └── gbt
│   │       └── latest
│   │           ├── metadata
│   │           │   ├── part-00000
│   │           │   └── _SUCCESS
│   │           ├── model_metadata.json
│   │           └── stages
│   │               ├── 0_VectorAssembler_61f78158c6ef
│   │               │   └── metadata
│   │               │       ├── part-00000
│   │               │       └── _SUCCESS
│   │               └── 1_GBTRegressor_077fa9d49fcb
│   │                   ├── metadata
│   │                   │   ├── part-00000
│   │                   │   └── _SUCCESS
│   │                   └── treesMetadata
│   │                       └── _SUCCESS
│   ├── predictions
│   └── reports
│       ├── data_lineage.json
│       ├── data_quality.json
│       ├── phase_h0_baseline_benchmark.json
│       ├── request_budget.json
│       └── source_resolution.json
├── config
│   ├── application.yaml
│   ├── data_quality
│   │   ├── processed_expectations.yaml
│   │   └── raw_expectations.yaml
│   ├── development.yaml
│   ├── kafka
│   │   ├── consumer.properties
│   │   ├── producer.properties
│   │   └── topics.yaml
│   ├── log_config.yaml
│   ├── mlops
│   │   ├── drift_thresholds.yaml
│   │   └── promotion_rules.yaml
│   ├── production.yaml
│   ├── spark-defaults.conf
│   └── staging.yaml
├── contracts
│   ├── examples
│   │   ├── prediction_request.json
│   │   ├── prediction_response.json
│   │   └── traffic_event.json
│   ├── feature_contract.json
│   ├── model_manifest.schema.json
│   ├── prediction.openapi.yaml
│   ├── security
│   │   ├── endpoint_permissions.yaml
│   │   ├── jwt_claims.schema.json
│   │   ├── roles.yaml
│   │   └── scopes.yaml
│   ├── source_resolution.schema.json
│   └── traffic_event.proto
├── deploy
│   ├── environments
│   │   ├── production.env
│   │   └── staging.env
│   ├── helm
│   │   ├── Chart.yaml
│   │   ├── templates
│   │   │   ├── deployment.yaml
│   │   │   ├── hpa.yaml
│   │   │   ├── ingress.yaml
│   │   │   └── service.yaml
│   │   ├── values-production.yaml
│   │   ├── values-staging.yaml
│   │   └── values.yaml
│   ├── kubernetes
│   │   ├── api-deployment.yaml
│   │   ├── api-service.yaml
│   │   ├── configmap.yaml
│   │   ├── dashboard-deployment.yaml
│   │   ├── hpa.yaml
│   │   ├── ingress.yaml
│   │   ├── namespace.yaml
│   │   ├── network-policy.yaml
│   │   ├── pdb.yaml
│   │   ├── persistent-volumes.yaml
│   │   └── service-account.yaml
│   ├── nginx
│   │   ├── nginx.conf
│   │   └── security_headers.conf
│   └── secrets
│       └── README.md
├── docker-compose.yml
├── Dockerfile
├── Dockerfile.api
├── docs
│   ├── api_ingestion.md
│   ├── architecture.md
│   ├── backup_policy.md
│   ├── data_dictionary.md
│   ├── data_lineage.md
│   ├── data_retention_policy.md
│   ├── demo_guide.md
│   ├── disaster_recovery.md
│   ├── eda_report.md
│   ├── hdfs_ha_config.md
│   ├── lab_asset_inventory.md
│   ├── model_report.md
│   ├── restore_runbook.md
│   ├── schema_evolution.md
│   ├── secrets_rotation.md
│   ├── security_policy.md
│   ├── security_runtime_map.md
│   ├── ui_api_contract.md
│   ├── ui_user_flows.md
│   └── ui_wireframes.md
├── god_view
│   ├── data_flow_god_view.md
│   ├── platform_ops_god_view.md
│   ├── serving_god_view.md
│   └── training_mlops_god_view.md
├── grafana_alerts.yml
├── Makefile
├── monitoring
│   ├── alertmanager
│   │   └── alertmanager.yml
│   ├── grafana
│   │   ├── dashboards
│   │   │   └── traffic_system_dashboard.json
│   │   └── datasources
│   │       └── prometheus.yml
│   └── prometheus
│       ├── prometheus.yml
│       └── rules
│           ├── infrastructure.yml
│           ├── model.yml
│           └── pipeline.yml
├── nginx.conf
├── prometheus.yml
├── README.md
├── requirements.txt
├── scripts
│   ├── backup
│   │   ├── backup_databases.sh
│   │   ├── backup_hdfs_metadata.sh
│   │   ├── backup_models.sh
│   │   └── verify_backup.sh
│   ├── canary_check.sh
│   ├── clean_project.sh
│   ├── create_kafka_topics.sh
│   ├── generate_sbom.sh
│   ├── import_lab_assets.py
│   ├── init_hdfs.sh
│   ├── restore
│   │   ├── restore_airflow.sh
│   │   ├── restore_hdfs.sh
│   │   └── restore_mlflow.sh
│   ├── rollback_deployment.sh
│   ├── run_ingestion.sh
│   ├── run_offline_ingestion.sh
│   ├── run_online_ingestion.sh
│   ├── run_pipeline.sh
│   ├── run_prediction.sh
│   ├── run_processing.sh
│   ├── run_stream_processor.sh
│   ├── run_training.sh
│   ├── smoke_test.sh
│   ├── upload_seed_data.sh
│   ├── verify_phase_2.py
│   └── wait_for_hdfs.sh
├── services
│   ├── go-traffic
│   │   ├── cmd
│   │   │   ├── collector
│   │   │   │   └── main.go
│   │   │   ├── live-api
│   │   │   │   └── main.go
│   │   │   └── web-dashboard
│   │   │       └── main.go
│   │   ├── Dockerfile
│   │   ├── Dockerfile.live-api
│   │   ├── Dockerfile.web
│   │   ├── go.mod
│   │   ├── go.sum
│   │   ├── internal
│   │   │   ├── api
│   │   │   │   ├── handlers.go
│   │   │   │   └── handlers_test.go
│   │   │   ├── auth
│   │   │   │   ├── claims.go
│   │   │   │   ├── cors.go
│   │   │   │   ├── jwt_test.go
│   │   │   │   ├── jwt_verifier.go
│   │   │   │   └── middleware.go
│   │   │   ├── budget
│   │   │   │   ├── budget.go
│   │   │   │   └── budget_test.go
│   │   │   ├── collector
│   │   │   │   └── worker_pool.go
│   │   │   ├── config
│   │   │   │   └── config.go
│   │   │   ├── contract
│   │   │   │   ├── event.go
│   │   │   │   └── event_test.go
│   │   │   ├── health
│   │   │   │   └── health.go
│   │   │   ├── kafka
│   │   │   │   ├── consumer.go
│   │   │   │   └── producer.go
│   │   │   ├── retry
│   │   │   │   ├── circuit_breaker.go
│   │   │   │   └── circuit_breaker_test.go
│   │   │   ├── source
│   │   │   │   └── router.go
│   │   │   ├── store
│   │   │   │   ├── state_store.go
│   │   │   │   └── state_store_test.go
│   │   │   ├── telemetry
│   │   │   │   └── metrics.go
│   │   │   └── tomtom
│   │   │       └── client.go
│   │   └── web
│   │       ├── css
│   │       │   └── style.css
│   │       ├── index.html
│   │       └── js
│   │           └── app.js
│   └── rust-inference
│       ├── Cargo.lock
│       ├── Cargo.toml
│       ├── crates
│       │   ├── traffic-api
│       │   │   ├── Cargo.toml
│       │   │   └── src
│       │   │       ├── auth
│       │   │       │   ├── jwt.rs
│       │   │       │   ├── middleware.rs
│       │   │       │   └── mod.rs
│       │   │       ├── feature_builder.rs
│       │   │       ├── handlers
│       │   │       │   ├── health.rs
│       │   │       │   ├── model_info.rs
│       │   │       │   ├── mod.rs
│       │   │       │   └── predictions.rs
│       │   │       ├── main.rs
│       │   │       ├── metrics.rs
│       │   │       ├── middleware
│       │   │       │   ├── mod.rs
│       │   │       │   └── request_id.rs
│       │   │       └── state.rs
│       │   ├── traffic-contract
│       │   │   ├── Cargo.toml
│       │   │   └── src
│       │   │       └── lib.rs
│       │   ├── traffic-inference
│       │   │   ├── Cargo.toml
│       │   │   └── src
│       │   │       └── main.rs
│       │   ├── traffic-onnx-engine
│       │   │   ├── Cargo.toml
│       │   │   └── src
│       │   │       └── lib.rs
│       │   └── traffic-tree-engine
│       │       ├── Cargo.toml
│       │       └── src
│       │           └── lib.rs
│       └── Dockerfile
├── spec
│   ├── lab-bo-sung.md
│   ├── lab.md
│   ├── lab-prod.md
│   ├── model-v2.md
│   ├── refactor.md
│   └── ui.md
├── src
│   ├── common
│   │   ├── config.py
│   │   ├── csv_inspector.py
│   │   ├── file_manifest.py
│   │   ├── __init__.py
│   │   ├── logging_utils.py
│   │   ├── schemas.py
│   │   └── spark_session.py
│   ├── data_quality
│   │   ├── anomaly_detector.py
│   │   ├── expectations.py
│   │   ├── lineage_writer.py
│   │   ├── quality_runner.py
│   │   └── schema_registry.py
│   ├── export
│   │   ├── export_feature_contract.py
│   │   ├── export_gbt_onnx.py
│   │   ├── export_gbt_tree_model.py
│   │   ├── generate_golden_dataset.py
│   │   ├── __init__.py
│   │   ├── inspect_spark_pipeline.py
│   │   └── validate_exported_model.py
│   ├── ingestion
│   │   ├── api_healthcheck.py
│   │   ├── base_source.py
│   │   ├── crawl_traffic.py
│   │   ├── data_normalizer.py
│   │   ├── fallback_report.py
│   │   ├── hdfs_writer.py
│   │   ├── ingestion_manifest.py
│   │   ├── ingest.py
│   │   ├── __init__.py
│   │   ├── location_loader.py
│   │   ├── offline_lab_source.py
│   │   ├── online_tomtom_source.py
│   │   ├── request_budget.py
│   │   ├── seed_loader.py
│   │   ├── source_mode.py
│   │   ├── source_router.py
│   │   ├── tomtom_client.py
│   │   └── upload_to_hdfs.py
│   ├── __init__.py
│   ├── mlops
│   │   ├── drift_detector.py
│   │   ├── experiment_tracker.py
│   │   ├── model_promoter.py
│   │   ├── model_registry.py
│   │   ├── model_validator.py
│   │   ├── retraining_policy.py
│   │   └── rollback.py
│   ├── observability
│   │   ├── metrics_exporter.py
│   │   ├── metrics.py
│   │   ├── structured_logging.py
│   │   └── tracing.py
│   ├── orchestration
│   │   ├── job_lock.py
│   │   ├── notifications.py
│   │   └── pipeline_state.py
│   ├── prediction
│   │   ├── batch_predict.py
│   │   ├── feature_builder.py
│   │   ├── __init__.py
│   │   └── predictor.py
│   ├── processing
│   │   ├── data_quality_report.py
│   │   ├── exploratory_analysis.py
│   │   ├── __init__.py
│   │   ├── process_spark.py
│   │   └── validate_raw_data.py
│   ├── security
│   │   └── secret_provider.py
│   ├── streaming
│   │   ├── checkpoint_manager.py
│   │   ├── dead_letter_handler.py
│   │   ├── kafka_producer.py
│   │   ├── stream_schema.py
│   │   └── traffic_stream_processor.py
│   └── training
│       ├── evaluate_model.py
│       ├── hyperparameter_tuning.py
│       ├── __init__.py
│       ├── model_metadata.py
│       └── train_gbt.py
├── tests
│   ├── airflow
│   │   ├── test_dag_imports.py
│   │   ├── test_job_lock.py
│   │   └── test_model_lifecycle_dag.py
│   ├── api
│   │   ├── test_dashboard_api.py
│   │   ├── test_observability_metrics.py
│   │   ├── test_production_security.py
│   │   └── test_rust_serving_api.py
│   ├── __init__.py
│   ├── integration
│   │   ├── __init__.py
│   │   ├── test_hdfs_connection.py
│   │   ├── test_model_prediction.py
│   │   ├── test_offline_lab_ingestion.py
│   │   └── test_spark_processing.py
│   ├── mlops
│   │   └── test_mlops_lifecycle.py
│   └── unit
│       ├── __init__.py
│       ├── test_auto_fallback.py
│       ├── test_config.py
│       ├── test_contract_compatibility.py
│       ├── test_data_normalizer.py
│       ├── test_data_quality.py
│       ├── test_data_validation.py
│       ├── test_export_pipeline.py
│       ├── test_feature_builder.py
│       ├── test_lab_asset_import.py
│       ├── test_location_loader.py
│       ├── test_observability.py
│       ├── test_request_budget.py
│       ├── test_security_modules.py
│       ├── test_source_router.py
│       ├── test_streaming_boundary.py
│       ├── test_streaming_components.py
│       └── test_tomtom_client.py
├── tree.md
└── web
    ├── AGENTS.md
    ├── CLAUDE.md
    ├── eslint.config.mjs
    ├── next.config.ts
    ├── next-env.d.ts
    ├── package.json
    ├── package-lock.json
    ├── postcss.config.mjs
    ├── public
    │   ├── file.svg
    │   ├── globe.svg
    │   ├── next.svg
    │   ├── vercel.svg
    │   └── window.svg
    ├── README.md
    ├── src
    │   ├── api
    │   │   ├── liveTrafficClient.ts
    │   │   └── predictionClient.ts
    │   ├── app
    │   │   ├── favicon.ico
    │   │   ├── globals.css
    │   │   ├── layout.tsx
    │   │   ├── login
    │   │   │   └── page.tsx
    │   │   └── page.tsx
    │   ├── auth
    │   │   ├── config.ts
    │   │   └── permissions.ts
    │   ├── components
    │   │   ├── auth
    │   │   │   ├── ProtectedRoute.tsx
    │   │   │   └── UserMenu.tsx
    │   │   ├── layout
    │   │   │   └── AppShell.tsx
    │   │   ├── map
    │   │   │   ├── LocationSearch.tsx
    │   │   │   ├── PredictionLayer.tsx
    │   │   │   ├── TrafficLayer.tsx
    │   │   │   ├── TrafficLegend.tsx
    │   │   │   ├── TrafficMap.tsx
    │   │   │   └── TrafficRoadsLayer.tsx
    │   │   └── panels
    │   │       ├── HistoryPanel.tsx
    │   │       ├── LocationDetails.tsx
    │   │       ├── PredictionPanel.tsx
    │   │       ├── RoadListPanel.tsx
    │   │       └── SavedLocationsPanel.tsx
    │   ├── context
    │   │   └── AuthContext.tsx
    │   └── styles
    │       └── tokens.ts
    └── tsconfig.json

122 directories, 354 files
