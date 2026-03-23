-- MySQL schema bootstrap for the Smart Factory Predictive Maintenance Dashboard.
-- This file is intended for MySQL 8.x initialization and mirrors the backend ORM tables.

CREATE TABLE IF NOT EXISTS machines (
  id INT NOT NULL AUTO_INCREMENT,
  machine_code VARCHAR(64) NOT NULL,
  machine_name VARCHAR(120) NULL,
  line_name VARCHAR(120) NULL,
  asset_type VARCHAR(120) NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_machines_machine_code (machine_code),
  KEY ix_machines_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sensor_readings (
  id INT NOT NULL AUTO_INCREMENT,
  machine_id INT NOT NULL,
  source_udi INT NULL,
  product_id VARCHAR(64) NULL,
  product_type VARCHAR(8) NOT NULL,
  captured_at DATETIME(6) NOT NULL,
  air_temperature_k DECIMAL(8,3) NOT NULL,
  process_temperature_k DECIMAL(8,3) NOT NULL,
  rotational_speed_rpm DECIMAL(10,3) NOT NULL,
  torque_nm DECIMAL(8,3) NOT NULL,
  tool_wear_min DECIMAL(8,3) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  KEY ix_sensor_readings_machine_id (machine_id),
  KEY ix_sensor_readings_machine_captured_at (machine_id, captured_at),
  CONSTRAINT fk_sensor_readings_machine
    FOREIGN KEY (machine_id) REFERENCES machines (id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS predictions (
  id INT NOT NULL AUTO_INCREMENT,
  machine_id INT NOT NULL,
  sensor_reading_id INT NOT NULL,
  model_name VARCHAR(120) NOT NULL,
  failure_probability DOUBLE NOT NULL,
  threshold_used DOUBLE NOT NULL,
  predicted_failure TINYINT(1) NOT NULL,
  risk_level VARCHAR(32) NOT NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_predictions_sensor_reading_id (sensor_reading_id),
  KEY ix_predictions_machine_id (machine_id),
  KEY ix_predictions_machine_created_at (machine_id, created_at),
  CONSTRAINT fk_predictions_machine
    FOREIGN KEY (machine_id) REFERENCES machines (id)
    ON DELETE CASCADE,
  CONSTRAINT fk_predictions_sensor_reading
    FOREIGN KEY (sensor_reading_id) REFERENCES sensor_readings (id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS alerts (
  id INT NOT NULL AUTO_INCREMENT,
  machine_id INT NOT NULL,
  prediction_id INT NOT NULL,
  severity VARCHAR(32) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'open',
  message VARCHAR(255) NOT NULL,
  acknowledged_at DATETIME(6) NULL,
  created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id),
  UNIQUE KEY uq_alerts_prediction_id (prediction_id),
  KEY ix_alerts_machine_id (machine_id),
  KEY ix_alerts_machine_status_created_at (machine_id, status, created_at),
  CONSTRAINT fk_alerts_machine
    FOREIGN KEY (machine_id) REFERENCES machines (id)
    ON DELETE CASCADE,
  CONSTRAINT fk_alerts_prediction
    FOREIGN KEY (prediction_id) REFERENCES predictions (id)
    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
