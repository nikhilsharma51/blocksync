-- =============================================================================
-- BlockSync: Initial Database Schema
-- Migration: 001_initial_schema.sql
-- Branch: hriday-dataset
-- Author: Hriday (Data & Pitch Lead)
--
-- Run this in the Supabase SQL editor or via psql:
--   psql $DATABASE_URL -f migrations/001_initial_schema.sql
-- =============================================================================

-- Enable the pgcrypto extension for UUID generation if needed
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =============================================================================
-- 1. DEPARTMENTS
-- Reference table for railway maintenance departments.
-- =============================================================================
CREATE TABLE IF NOT EXISTS departments (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(10)  UNIQUE NOT NULL,   -- e.g. TRK, SNT, OHE
    name        VARCHAR(100) NOT NULL,           -- e.g. Engineering (Track)
    color_hex   VARCHAR(7)   NOT NULL DEFAULT '#6B7280', -- UI Gantt bar color
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE departments IS
    'Lookup table for railway maintenance departments. Codes match the TMS/SMMS/TDMS source system prefixes.';

INSERT INTO departments (code, name, color_hex) VALUES
    ('TRK', 'Engineering (Track)',         '#F59E0B'),
    ('SNT', 'Signal & Telecom (S&T)',      '#3B82F6'),
    ('OHE', 'Traction (OHE/TRD)',          '#10B981')
ON CONFLICT (code) DO NOTHING;


-- =============================================================================
-- 2. CORRIDORS
-- Track sections / block sections managed by the Controller of Accounts (COA).
-- traffic_weight drives the Asset Criticality component of the scoring formula.
-- =============================================================================
CREATE TABLE IF NOT EXISTS corridors (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(30)  UNIQUE NOT NULL,  -- e.g. NDLS-CNB-UP
    name            VARCHAR(150) NOT NULL,
    line_type       VARCHAR(10)  NOT NULL CHECK (line_type IN ('UP', 'DOWN', 'BOTH', 'SINGLE')),
    track_km_from   NUMERIC(7,2),                  -- Start chainage in km
    track_km_to     NUMERIC(7,2),                  -- End chainage in km
    speed_limit_kmh INTEGER      NOT NULL DEFAULT 130,
    traffic_weight  NUMERIC(4,2) NOT NULL DEFAULT 1.0 CHECK (traffic_weight BETWEEN 0.1 AND 1.0),
    -- 1.0 = Trunk Mainline, 0.6 = Branch Line, 0.3 = Yard/Loop
    asset_class     VARCHAR(20)  NOT NULL DEFAULT 'Mainline Trunk'
                    CHECK (asset_class IN ('Mainline Trunk', 'Branch Line', 'Yard/Loop')),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE corridors IS
    'Block sections managed by COA. traffic_weight is used in the criticality scoring formula (W3 component).';
COMMENT ON COLUMN corridors.traffic_weight IS
    '1.0 = Trunk Mainline (100 pts), 0.6 = Branch Line (60 pts), 0.3 = Yard/Loop (30 pts).';

INSERT INTO corridors (code, name, line_type, track_km_from, track_km_to, speed_limit_kmh, traffic_weight, asset_class) VALUES
    ('NDLS-GZB-UP',  'New Delhi - Ghaziabad (UP Main)',      'UP',     0.00,  24.80, 130, 1.0, 'Mainline Trunk'),
    ('NDLS-GZB-DN',  'New Delhi - Ghaziabad (DOWN Main)',    'DOWN',  24.80,   0.00, 130, 1.0, 'Mainline Trunk'),
    ('GZB-ALJN-UP',  'Ghaziabad - Aligarh (UP Main)',        'UP',    24.80, 126.10, 160, 1.0, 'Mainline Trunk'),
    ('GZB-ALJN-DN',  'Ghaziabad - Aligarh (DOWN Main)',      'DOWN', 126.10,  24.80, 160, 1.0, 'Mainline Trunk'),
    ('ALJN-TDL-BOTH','Aligarh - Tundla Junction',            'BOTH', 126.10, 204.50, 140, 0.9, 'Mainline Trunk'),
    ('TDL-CNB-BOTH', 'Tundla - Kanpur Central',              'BOTH', 204.50, 440.20, 140, 0.9, 'Mainline Trunk'),
    ('DLI-RE-SL',    'Delhi - Rewari (Single Line)',         'SINGLE', 0.00, 82.50,  100, 0.7, 'Branch Line'),
    ('CNB-YARD',     'Kanpur Central Yard & Loop Lines',     'BOTH',   0.00,  10.00,   30, 0.3, 'Yard/Loop')
ON CONFLICT (code) DO NOTHING;


-- =============================================================================
-- 3. BLOCK WINDOWS
-- Free time slots granted by the Controller of Accounts (COA) / Train Controller.
-- These are the only slots the optimizer is allowed to schedule tasks into.
-- duration_min is a generated/computed column for convenience.
-- =============================================================================
CREATE TABLE IF NOT EXISTS block_windows (
    id              SERIAL PRIMARY KEY,
    corridor_id     INTEGER      NOT NULL REFERENCES corridors(id) ON DELETE CASCADE,
    window_label    VARCHAR(50)  NOT NULL DEFAULT 'Night Gold Window',
    -- 'Night Gold Window' | 'Midday Freight Window' | 'Early Morning Window' | 'Emergency Window'
    start_time      TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time        TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_min    INTEGER      GENERATED ALWAYS AS
                        (EXTRACT(EPOCH FROM (end_time - start_time))::INTEGER / 60) STORED,
    source          VARCHAR(50)  NOT NULL DEFAULT 'COA_Timetable_Gap',
    -- 'COA_Timetable_Gap' | 'Emergency_Grant' | 'Freight_Lull' | 'Sunday_MegaBlock'
    is_available    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT window_end_after_start CHECK (end_time > start_time)
);

COMMENT ON TABLE block_windows IS
    'Available maintenance windows granted by COA. The optimizer ONLY assigns tasks to these windows.';
COMMENT ON COLUMN block_windows.duration_min IS
    'Auto-computed from end_time - start_time. Used directly by the CP-SAT solver constraint: task_duration <= window_duration.';


-- =============================================================================
-- 4. MAINTENANCE TASKS
-- Raw requests arriving from TMS (Track), SMMS (Signal), TDMS (OHE).
-- criticality_score is populated by the Python scoring engine before insertion.
-- =============================================================================
CREATE TABLE IF NOT EXISTS maintenance_tasks (
    id                  VARCHAR(20)  PRIMARY KEY,   -- e.g. TRK-1001
    department_id       INTEGER      NOT NULL REFERENCES departments(id),
    corridor_id         INTEGER      NOT NULL REFERENCES corridors(id),

    -- Defect information
    defect_code         VARCHAR(30),                -- e.g. TMS-DF-1042-IMR
    defect_type         VARCHAR(150) NOT NULL,
    defect_category     VARCHAR(100),
    source_system       VARCHAR(10)  NOT NULL CHECK (source_system IN ('TMS', 'SMMS', 'TDMS')),
    description         TEXT,
    recommended_action  TEXT,

    -- Priority metrics
    severity            INTEGER      NOT NULL CHECK (severity BETWEEN 1 AND 5),
    days_overdue        INTEGER      NOT NULL DEFAULT 0 CHECK (days_overdue >= 0),
    reported_date       DATE,

    -- Timing
    est_duration_min    INTEGER      NOT NULL CHECK (est_duration_min > 0),
    requested_start     TIMESTAMP WITH TIME ZONE,

    -- Scoring (populated by scoring engine before INSERT)
    criticality_score   NUMERIC(5,2) CHECK (criticality_score BETWEEN 0 AND 100),
    score_severity_component  NUMERIC(5,2),
    score_overdue_component   NUMERIC(5,2),
    score_traffic_component   NUMERIC(5,2),
    score_formula       TEXT,                       -- Human-readable formula string

    -- Compatibility (for Integrated Joint Block logic)
    is_compatible_with  VARCHAR(10),                -- department code it can share a block with
    priority_level      VARCHAR(5)   NOT NULL DEFAULT 'P1' CHECK (priority_level IN ('P0', 'P1', 'P2')),
    status              VARCHAR(20)  NOT NULL DEFAULT 'Pending'
                        CHECK (status IN ('Pending', 'Clashed', 'Scheduled', 'Merged', 'Deferred', 'Approved')),

    -- Crew
    crew_size           INTEGER,
    supervisor          VARCHAR(200),
    required_machine    VARCHAR(200),
    power_disconnection_required BOOLEAN NOT NULL DEFAULT FALSE,
    speed_restriction_afterwards VARCHAR(100),

    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE maintenance_tasks IS
    'Raw maintenance requests from TMS/SMMS/TDMS. criticality_score is calculated deterministically by backend/core/scoring.py before any row is inserted.';
COMMENT ON COLUMN maintenance_tasks.severity IS
    '1=Routine, 2=Low, 3=Moderate, 4=High, 5=Critical/Safety-Hazard.';
COMMENT ON COLUMN maintenance_tasks.is_compatible_with IS
    'If set, this task CAN share a block with the named department. Enables the Integrated Joint Block feature.';

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_tasks_updated_at
    BEFORE UPDATE ON maintenance_tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- 5. CONFLICT PAIRS
-- Detected scheduling conflicts between two tasks on the same corridor/time.
-- Populated by the conflict-detection pass before the optimizer runs.
-- =============================================================================
CREATE TABLE IF NOT EXISTS conflict_pairs (
    id                  SERIAL PRIMARY KEY,
    task_a_id           VARCHAR(20) NOT NULL REFERENCES maintenance_tasks(id),
    task_b_id           VARCHAR(20) NOT NULL REFERENCES maintenance_tasks(id),
    corridor_id         INTEGER     NOT NULL REFERENCES corridors(id),
    overlap_start       TIMESTAMP WITH TIME ZONE,
    overlap_end         TIMESTAMP WITH TIME ZONE,
    overlap_duration_min INTEGER,
    conflict_severity   VARCHAR(10) NOT NULL CHECK (conflict_severity IN ('Critical', 'High', 'Moderate')),
    conflict_type       VARCHAR(50) NOT NULL,
    -- 'Physical Line Occupancy' | 'Power/OHE Dependency' | 'Signal Interlocking'
    resolution_strategy TEXT,
    detected_at         TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT different_tasks CHECK (task_a_id <> task_b_id)
);

COMMENT ON TABLE conflict_pairs IS
    'Pre-optimizer conflict matrix. Each row represents two tasks that request the same corridor at overlapping times. Used to populate the red Conflict Gantt view on the frontend.';


-- =============================================================================
-- 6. OPTIMIZATION PLANS
-- A versioned snapshot of a single optimizer run.
-- =============================================================================
CREATE TABLE IF NOT EXISTS optimization_plans (
    id              VARCHAR(50)  PRIMARY KEY,        -- e.g. PLAN-99281
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    solver_status   VARCHAR(20)  NOT NULL DEFAULT 'IDLE'
                    CHECK (solver_status IN ('IDLE', 'RUNNING', 'OPTIMAL', 'FEASIBLE', 'INFEASIBLE')),
    solve_time_sec  NUMERIC(8,3),
    objective_value NUMERIC(12,2),
    conflicts_resolved      INTEGER DEFAULT 0,
    total_conflicts         INTEGER DEFAULT 0,
    joint_blocks_formed     INTEGER DEFAULT 0,
    downtime_saved_hours    NUMERIC(6,2) DEFAULT 0,
    total_tasks_scheduled   INTEGER DEFAULT 0,
    total_tasks_unscheduled INTEGER DEFAULT 0,
    constraints_evaluated   INTEGER DEFAULT 0,
    notes           TEXT
);

COMMENT ON TABLE optimization_plans IS
    'Each row is a CP-SAT solver run. Versioned so the frontend can compare plans or revert to a previous schedule.';


-- =============================================================================
-- 7. BLOCK ASSIGNMENTS
-- The optimizer output: which task goes in which window, with optional integration.
-- =============================================================================
CREATE TABLE IF NOT EXISTS block_assignments (
    id                  SERIAL PRIMARY KEY,
    plan_id             VARCHAR(50) NOT NULL REFERENCES optimization_plans(id) ON DELETE CASCADE,
    task_id             VARCHAR(20) NOT NULL REFERENCES maintenance_tasks(id),
    window_id           INTEGER     NOT NULL REFERENCES block_windows(id),
    assigned_start      TIMESTAMP WITH TIME ZONE NOT NULL,
    assigned_end        TIMESTAMP WITH TIME ZONE NOT NULL,
    is_integrated       BOOLEAN     NOT NULL DEFAULT FALSE,
    joint_block_id      VARCHAR(20),               -- e.g. JB-01
    merged_with_task_id VARCHAR(20) REFERENCES maintenance_tasks(id),
    window_type         VARCHAR(50) DEFAULT 'Night Gold Window',
    ai_explanation      TEXT,                      -- Generated by Gemini explainability module
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT assignment_end_after_start CHECK (assigned_end > assigned_start)
);

COMMENT ON TABLE block_assignments IS
    'CP-SAT solver output. Each row is a scheduled task. is_integrated=TRUE means it was merged into a Joint Block with another department, saving a separate corridor downtime slot.';


-- =============================================================================
-- 8. INTEGRATED JOINT BLOCKS
-- The signature feature: multi-department blocks that share one power shutdown.
-- =============================================================================
CREATE TABLE IF NOT EXISTS integrated_joint_blocks (
    id                  VARCHAR(20)  PRIMARY KEY,  -- e.g. JB-01
    joint_block_number  INTEGER      NOT NULL,
    plan_id             VARCHAR(50)  NOT NULL REFERENCES optimization_plans(id) ON DELETE CASCADE,
    corridor_id         INTEGER      NOT NULL REFERENCES corridors(id),
    start_time          TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time            TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_hours      NUMERIC(4,2),
    departments         TEXT[]       NOT NULL,     -- e.g. ['TRK', 'OHE']
    downtime_saved_min  INTEGER      NOT NULL DEFAULT 0,
    power_isolation_time VARCHAR(50),             -- e.g. "01:45 to 04:15"
    work_window_time    VARCHAR(50),
    joint_supervisor    TEXT,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE integrated_joint_blocks IS
    'Represents a multi-department merged maintenance block. Each row groups 2–3 departments into a single corridor downtime window, eliminating redundant power blocks.';


-- =============================================================================
-- 9. UNSCHEDULED TASKS
-- Tasks the optimizer could not fit into any window. Triggers graceful degradation.
-- =============================================================================
CREATE TABLE IF NOT EXISTS unscheduled_tasks (
    id                      SERIAL PRIMARY KEY,
    plan_id                 VARCHAR(50) NOT NULL REFERENCES optimization_plans(id) ON DELETE CASCADE,
    task_id                 VARCHAR(20) NOT NULL REFERENCES maintenance_tasks(id),
    mathematical_reason     TEXT        NOT NULL,
    deferred_to             VARCHAR(100),
    next_recommended_window VARCHAR(100),
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE unscheduled_tasks IS
    'Tasks rejected by the CP-SAT solver due to infeasible constraints (e.g. duration > available window). Used to render the "Deferred Tasks" panel on the frontend and prove graceful degradation to judges.';


-- =============================================================================
-- 10. INDEXES (for query performance)
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_tasks_corridor     ON maintenance_tasks(corridor_id);
CREATE INDEX IF NOT EXISTS idx_tasks_department   ON maintenance_tasks(department_id);
CREATE INDEX IF NOT EXISTS idx_tasks_severity     ON maintenance_tasks(severity DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_score        ON maintenance_tasks(criticality_score DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_status       ON maintenance_tasks(status);
CREATE INDEX IF NOT EXISTS idx_windows_corridor   ON block_windows(corridor_id, start_time);
CREATE INDEX IF NOT EXISTS idx_assignments_plan   ON block_assignments(plan_id);
CREATE INDEX IF NOT EXISTS idx_assignments_task   ON block_assignments(task_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_task_a   ON conflict_pairs(task_a_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_task_b   ON conflict_pairs(task_b_id);

-- =============================================================================
-- 11. VIEWS (convenience queries for the FastAPI layer)
-- =============================================================================

-- Full task view joining department and corridor names
CREATE OR REPLACE VIEW v_tasks_pending AS
SELECT
    mt.id,
    d.code                          AS department,
    d.name                          AS department_name,
    c.code                          AS corridor,
    c.name                          AS corridor_name,
    mt.defect_type,
    mt.severity,
    mt.days_overdue,
    mt.est_duration_min,
    mt.criticality_score,
    mt.priority_level               AS priority,
    mt.status,
    mt.requested_start,
    mt.requested_start + (mt.est_duration_min || ' minutes')::INTERVAL AS requested_end,
    mt.is_compatible_with,
    mt.power_disconnection_required,
    mt.crew_size,
    mt.supervisor,
    mt.required_machine
FROM maintenance_tasks mt
JOIN departments d  ON mt.department_id = d.id
JOIN corridors   c  ON mt.corridor_id   = c.id
WHERE mt.status IN ('Pending', 'Clashed')
ORDER BY mt.criticality_score DESC;

COMMENT ON VIEW v_tasks_pending IS
    'Used by GET /api/v1/tasks/pending — returns all unscheduled tasks with denormalised names for the frontend conflict Gantt.';

-- Corridor availability view
CREATE OR REPLACE VIEW v_corridor_availability AS
SELECT
    bw.id                           AS window_id,
    c.code                          AS corridor_id,
    c.name                          AS corridor_name,
    bw.window_label,
    bw.start_time,
    bw.end_time,
    bw.duration_min,
    bw.source,
    bw.is_available
FROM block_windows bw
JOIN corridors c ON bw.corridor_id = c.id
WHERE bw.is_available = TRUE
ORDER BY bw.start_time ASC;

COMMENT ON VIEW v_corridor_availability IS
    'Used by GET /api/v1/corridors/availability — returns all open COA windows for the optimizer to fit tasks into.';

-- Full optimized assignment view
CREATE OR REPLACE VIEW v_optimized_assignments AS
SELECT
    ba.plan_id,
    ba.task_id,
    d.code                          AS department,
    c.code                          AS corridor,
    c.name                          AS corridor_name,
    mt.defect_type,
    mt.criticality_score,
    ba.assigned_start,
    ba.assigned_end,
    ba.is_integrated,
    ba.joint_block_id,
    ba.merged_with_task_id,
    ba.window_type,
    ba.ai_explanation
FROM block_assignments ba
JOIN maintenance_tasks mt ON ba.task_id    = mt.id
JOIN departments       d  ON mt.department_id = d.id
JOIN corridors         c  ON mt.corridor_id   = c.id
ORDER BY ba.plan_id, ba.assigned_start;

COMMENT ON VIEW v_optimized_assignments IS
    'Used by POST /api/v1/optimize response — full denormalized assignment rows for the frontend Optimized Gantt.';
