# Seed Data Notes

This folder contains deterministic seed/demo assets for MySQL and the cross-database demo scripts.

## Files

- `seed_machines.sql`: base machine metadata for MySQL
- `quick_demo_records.json`: deterministic quick-demo source record definitions used by `scripts/generate_demo_data.py --mode quick`

## Demo Modes

Quick demo mode:

- very small dataset
- deterministic machine set
- deterministic source UDI selection from the public dataset

Large demo mode:

- generated sensor readings across the same machine set
- deterministic timestamps and source-row selection
- intended for dashboard visuals and screenshots

## Recommended Flow

1. Reset the database with `scripts/reset_db.py`
2. Run `scripts/generate_demo_data.py --mode quick` or `--mode large`

For SQLite, the script creates the schema through the backend ORM.

For MySQL, the schema should come from `infra/mysql/schema.sql` first, either through Docker Compose init or a manual reset/schema load flow.
