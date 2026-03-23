-- Deterministic base machine metadata for MySQL quick-start demos.
-- This script is safe to re-run because it upserts by machine_code.

INSERT INTO machines (machine_code, machine_name, line_name, asset_type, status)
VALUES
  ('MILL-001', 'Mill 001', 'Line A', 'Milling Machine', 'active'),
  ('LATHE-002', 'Lathe 002', 'Line A', 'CNC Lathe', 'active'),
  ('PRESS-003', 'Press 003', 'Line B', 'Hydraulic Press', 'active'),
  ('CNC-004', 'CNC 004', 'Line B', 'Machining Center', 'active'),
  ('ROBOT-005', 'Robot 005', 'Line C', 'Robotic Arm', 'active'),
  ('PUMP-006', 'Pump 006', 'Line C', 'Coolant Pump', 'active')
ON DUPLICATE KEY UPDATE
  machine_name = VALUES(machine_name),
  line_name = VALUES(line_name),
  asset_type = VALUES(asset_type),
  status = VALUES(status);
