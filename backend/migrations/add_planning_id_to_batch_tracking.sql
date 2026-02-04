-- Version 1.1 - Session Isolation Migration
-- Adds planning_id to batch_tracking for session-aware filtering

-- Add planning_id column to batch_tracking table
ALTER TABLE batch_tracking 
ADD COLUMN planning_id INTEGER REFERENCES production_planning(id);

-- Optional: Create index for faster filtering
CREATE INDEX IF NOT EXISTS idx_batch_tracking_planning_id ON batch_tracking(planning_id);

-- Note: Existing records will have planning_id = NULL
-- New checkouts will populate this field automatically
-- Queries should filter by planning_id to get session-specific data
