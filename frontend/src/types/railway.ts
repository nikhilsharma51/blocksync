export type Department = 'Track' | 'Signal' | 'OHE';

export type PriorityLevel = 'P0' | 'P1' | 'P2';

export type TaskStatus = 'Pending' | 'Clashed' | 'Scheduled' | 'Merged' | 'Deferred' | 'Approved';

export type ActivePageView =
  | 'conflicts'
  | 'optimized'
  | 'intake'
  | 'safety'
  | 'corridormap'
  | 'execution';

export interface CorridorSection {
  id: string;
  name: string;
  lineType: 'UP' | 'DOWN' | 'BOTH';
  trackKm: string;
  speedLimit: string;
  trafficDensity: 'High' | 'Very High' | 'Moderate';
}

export interface DefectDetail {
  code: string;
  category: string;
  description: string;
  sourceSystem: 'TMS' | 'SMMS' | 'TDMS';
  severity: 1 | 2 | 3 | 4 | 5;
  overdueDays: number;
  reportedDate: string;
  recommendedAction: string;
}

export interface WorkCrewSpec {
  crewSize: number;
  supervisor: string;
  requiredMachine?: string;
  powerDisconnectionRequired: boolean;
  speedRestrictionAfterwards?: string;
}

export interface CriticalityBreakdown {
  severityScore: number;       // out of 35
  overduePenalty: number;      // out of 35
  assetWeight: number;         // out of 20
  trafficFactor: number;       // out of 10
  totalScore: number;          // out of 100
  formula: string;
}

export interface GeminiExplanation {
  headline: string;
  summary: string;
  keyDrivers: string[];
  tradeoffsEvaluated?: string;
  jointBlockRationale?: string;
}

export interface HardConstraintsAudit {
  noCorridorOverlap: boolean;
  fitsWindowDuration: boolean;
  tractionPowerIsolatedPrior: boolean;
  crewShiftCompliance: boolean;
  passengerHeadwayMaintained: boolean;
}

export interface MaintenanceTask {
  id: string;
  taskNumber: number;
  title: string;
  department: Department;
  corridorId: string;
  corridorName: string;
  requestedStartHour: number;   // 0 to 24 (e.g. 2.5 = 02:30)
  durationHours: number;        // e.g. 2.0 = 120 mins
  status: TaskStatus;
  priority: PriorityLevel;
  criticalityScore: number;
  defect: DefectDetail;
  crew: WorkCrewSpec;
  criticalityBreakdown: CriticalityBreakdown;
  geminiExplanation: GeminiExplanation;
  constraintsAudit: HardConstraintsAudit;
  clashingTaskId?: string;
  clashReason?: string;
}

export interface ConflictPair {
  id: string;
  taskA: MaintenanceTask;
  taskB: MaintenanceTask;
  corridorName: string;
  overlapStartHour: number;
  overlapEndHour: number;
  overlapDurationMins: number;
  severity: 'Critical' | 'High' | 'Moderate';
  conflictType: 'Physical Line Occupancy' | 'Power/OHE Dependency' | 'Signal Interlocking';
  resolutionStrategy: string;
}

export interface IntegratedJointBlock {
  id: string;
  jointBlockNumber: number;
  corridorId: string;
  corridorName: string;
  startHour: number;
  endHour: number;
  durationHours: number;
  departments: Department[];
  tasks: MaintenanceTask[];
  downtimeSavedMinutes: number;
  powerIsolationTime: string;
  workWindowTime: string;
  jointSupervisor: string;
}

export interface OptimizedAssignment {
  task: MaintenanceTask;
  assignedStartHour: number;
  assignedEndHour: number;
  isIntegrated: boolean;
  jointBlockId?: string;
  windowType: 'Night Gold Window' | 'Midday Freight Window' | 'Early Morning Window';
}

export interface UnscheduledTask {
  task: MaintenanceTask;
  mathematicalReason: string;
  deferredTo: string;
  nextRecommendedWindow: string;
}

export interface SolverStats {
  status: 'OPTIMAL' | 'FEASIBLE' | 'RUNNING' | 'IDLE';
  solveTimeSeconds: number;
  conflictsResolved: number;
  totalConflicts: number;
  jointBlocksFormed: number;
  downtimeSavedHours: number;
  totalTasksScheduled: number;
  totalTasksUnscheduled: number;
  constraintsEvaluated: number;
  objectiveValue: number;
}

// Page 3: Department Feeds & Intake
export interface DepartmentDefectFeedItem {
  id: string;
  taskNumber: number;
  department: Department;
  sourceSystem: 'TMS' | 'SMMS' | 'TDMS';
  defectCode: string;
  defectCategory: string;
  corridorName: string;
  trackKm: string;
  severity: 1 | 2 | 3 | 4 | 5;
  overdueDays: number;
  estimatedMinutes: number;
  requestedDateTime: string;
  status: 'Pending' | 'Queued' | 'Scheduled' | 'Merged' | 'Rejected';
  powerBlockRequired: boolean;
}

// Page 4: Safety & SLA Dashboard
export interface DefectAgingBucket {
  bucket: string;       // "0-3 Days", "4-7 Days", "8-14 Days", "15+ Days"
  Track: number;
  Signal: number;
  OHE: number;
}

export interface MonthlySavedHours {
  month: string;
  standaloneBlockHours: number;
  integratedBlockHours: number;
  hoursSaved: number;
}

export interface BottleneckCorridor {
  corridor: string;
  trainPathsPerDay: number;
  avgFreeWindowMins: number;
  pendingDefects: number;
  congestionIndex: 'Severe' | 'High' | 'Moderate';
  speedRestrictionKm: string;
}

// Page 5: Corridor Timetable & Free Windows
export interface StationNode {
  name: string;
  code: string;
  km: number;
  tracks: number;
  isJunction: boolean;
}

export interface TimetableFreeWindow {
  id: string;
  corridorId: string;
  line: 'UP' | 'DOWN';
  startHour: number;
  endHour: number;
  durationMins: number;
  isGoldWindow: boolean; // 01:30 - 05:00 AM
  conflictingTrainCount: number;
  goodsTrainBuffer: string;
}

// Page 6: Execution Kanban & Audit Log
export type ExecutionStatus = 'SCHEDULED' | 'GRANTED' | 'IN_PROGRESS' | 'RESTORED' | 'CANCELLED';

export interface ExecutionBlockItem {
  id: string;
  blockNumber: string;
  taskTitle: string;
  department: Department;
  corridorName: string;
  timeWindow: string;
  status: ExecutionStatus;
  isIntegrated: boolean;
  supervisor: string;
  speedRestriction: string;
  lastUpdated: string;
}

export interface AuditTrailLog {
  id: string;
  timestamp: string;
  userRole: string;
  action: string;
  targetTask: string;
  previousValue: string;
  newValue: string;
  validationStatus: 'Constraint Passed' | 'Approved by DOM' | 'Re-Validated';
}
