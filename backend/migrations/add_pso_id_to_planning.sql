-- Migration: Add pso_id to production_planning table
-- Date: 2026-02-04
-- Purpose: Track which PSO version was used in each balancing

-- Step 1: Add the pso_id column (nullable first to allow existing data)
ALTER TABLE production_planning 
ADD COLUMN pso_id INTEGER;

-- Step 2: Backfill existing records with best effort (most recent PSO for each product)
UPDATE production_planning pp
SET pso_id = (
    SELECT pso.id 
    FROM pso 
    JOIN products p ON pso.product_id = p.id
    JOIN production_orders po ON po.product_reference = p.reference
    WHERE po.id = pp.production_order_id
    ORDER BY pso.id DESC
    LIMIT 1
)
WHERE pso_id IS NULL;

-- Step 3: Add foreign key constraint
ALTER TABLE production_planning
ADD CONSTRAINT fk_production_planning_pso
FOREIGN KEY (pso_id) REFERENCES pso(id);

-- Step 4: Make column NOT NULL (after backfill)
-- Note: We keep it nullable in case there are edge cases
-- ALTER TABLE production_planning ALTER COLUMN pso_id SET NOT NULL;

-- Verification query
SELECT 
    pp.id,
    pp.version_name,
    pp.pso_id,
    pso.version_name as pso_version,
    p.reference as product_reference
FROM production_planning pp
LEFT JOIN pso ON pp.pso_id = pso.id
LEFT JOIN products p ON pso.product_id = p.id
ORDER BY pp.created_at DESC
LIMIT 10;
