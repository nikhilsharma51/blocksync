'use client';

import React, { useState } from 'react';
import { AppHeader } from '../components/layout/AppHeader';
import { AppSidebar } from '../components/layout/AppSidebar';
import { ConflictGantt } from '../components/timeline/ConflictGantt';
import { OptimizedGantt } from '../components/timeline/OptimizedGantt';
import { ExplainabilityDrawer } from '../components/drawer/ExplainabilityDrawer';
import { ConflictListPanel } from '../components/shared/ConflictListPanel';
import { SolverProgressOverlay } from '../components/shared/SolverProgressOverlay';
import { BlockBulletinModal } from '../components/modals/BlockBulletinModal';
import { DepartmentIntakePage } from '../components/pages/DepartmentIntakePage';
import { SafetyDashboardPage } from '../components/pages/SafetyDashboardPage';
import { CorridorMapPage } from '../components/pages/CorridorMapPage';
import { ExecutionTrackingPage } from '../components/pages/ExecutionTrackingPage';
import { DemoPresentationBar } from '../components/shared/DemoPresentationBar';
import {
  CORRIDORS,
  RAW_MAINTENANCE_TASKS,
  CONFLICT_PAIRS,
  INTEGRATED_JOINT_BLOCKS,
  OPTIMIZED_ASSIGNMENTS,
  UNSCHEDULED_TASKS,
  INITIAL_SOLVER_STATS,
  DEPARTMENT_FEEDS,
  DEFECT_AGING_DATA,
  MONTHLY_HOURS_SAVED_DATA,
  BOTTLENECK_CORRIDORS,
  STATION_NODES,
  TIMETABLE_FREE_WINDOWS,
  INITIAL_EXECUTION_ITEMS,
  AUDIT_TRAIL_LOGS,
} from '../data/mockRailwayData';
import {
  Department,
  MaintenanceTask,
  ActivePageView,
  DepartmentDefectFeedItem,
} from '../types/railway';

export default function BlockSyncApp() {
  // Navigation & View State
  const [activeView, setActiveView] = useState<ActivePageView>('conflicts');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false);

  // Department Filters (All enabled by default)
  const [selectedDepartments, setSelectedDepartments] = useState<Department[]>([
    'Track',
    'Signal',
    'OHE',
  ]);

  // Feed & Intake Data State
  const [feeds, setFeeds] = useState<DepartmentDefectFeedItem[]>(DEPARTMENT_FEEDS);

  // Modals & Panels State
  const [selectedTask, setSelectedTask] = useState<MaintenanceTask | null>(null);
  const [isConflictPanelOpen, setIsConflictPanelOpen] = useState<boolean>(false);
  const [isSolving, setIsSolving] = useState<boolean>(false);
  const [isBulletinOpen, setIsBulletinOpen] = useState<boolean>(false);
  const [isPlanApproved, setIsPlanApproved] = useState<boolean>(false);

  // Judge Demo Presentation Mode
  const [isDemoModeOpen, setIsDemoModeOpen] = useState<boolean>(false);
  const [demoStep, setDemoStep] = useState<number>(1);

  const handleToggleDepartment = (dept: Department) => {
    setSelectedDepartments((prev) =>
      prev.includes(dept) ? prev.filter((d) => d !== dept) : [...prev, dept]
    );
  };

  const handleRunOptimizer = () => {
    setIsSolving(true);
  };

  const handleSolverComplete = () => {
    setIsSolving(false);
    setActiveView('optimized');
    setDemoStep(4);
  };

  const handleApprovePlan = () => {
    setIsPlanApproved(true);
    setIsBulletinOpen(true);
    setDemoStep(5);
  };

  const handleAddFeedItem = (newItem: DepartmentDefectFeedItem) => {
    setFeeds((prev) => [newItem, ...prev]);
  };

  const handleInjectConflicts = () => {
    setActiveView('conflicts');
    setIsConflictPanelOpen(true);
  };

  const handleResetSeedData = () => {
    setFeeds(DEPARTMENT_FEEDS);
    setIsPlanApproved(false);
    setActiveView('conflicts');
  };

  // Step progression in Judge Mode
  const handleSelectDemoStep = (stepNumber: number) => {
    setDemoStep(stepNumber);
    if (stepNumber === 1) {
      setActiveView('conflicts');
      setSelectedTask(null);
      setIsBulletinOpen(false);
    } else if (stepNumber === 2) {
      setActiveView('conflicts');
      setSelectedTask(RAW_MAINTENANCE_TASKS[0]); // Task #101 14-day overdue IMR fracture
    } else if (stepNumber === 3) {
      setSelectedTask(null);
      setIsSolving(true);
    } else if (stepNumber === 4) {
      setActiveView('optimized');
      setSelectedTask(RAW_MAINTENANCE_TASKS[0]); // Inspect merged Joint Block
    } else if (stepNumber === 5) {
      setActiveView('optimized');
      setIsPlanApproved(true);
      setIsBulletinOpen(true);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-100 font-sans text-slate-900">
      {/* 1. Collapsible Left Sidebar */}
      <AppSidebar
        activeView={activeView}
        onViewChange={setActiveView}
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        conflictCount={CONFLICT_PAIRS.length}
        resolvedCount={OPTIMIZED_ASSIGNMENTS.length}
      />

      {/* 2. Main Content Area */}
      <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden">
        {/* Top Header Bar */}
        <AppHeader
          activeView={activeView}
          onViewChange={setActiveView}
          onRunOptimizer={handleRunOptimizer}
          selectedDepartments={selectedDepartments}
          onToggleDepartment={handleToggleDepartment}
          isPlanApproved={isPlanApproved}
          onToggleDemoMode={() => setIsDemoModeOpen((prev) => !prev)}
          isDemoModeOpen={isDemoModeOpen}
        />

        {/* Scrollable Workspace Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 pb-20">
          {/* Page 1: Conflict Matrix Timeline */}
          {activeView === 'conflicts' && (
            <>
              {/* Conflict Pairs Diagnostic Drawer */}
              <ConflictListPanel
                conflicts={CONFLICT_PAIRS}
                isOpen={isConflictPanelOpen}
                onClose={() => setIsConflictPanelOpen(false)}
                onSelectTask={(task) => setSelectedTask(task)}
                onRunOptimizer={handleRunOptimizer}
              />

              <ConflictGantt
                corridors={CORRIDORS}
                tasks={RAW_MAINTENANCE_TASKS}
                conflicts={CONFLICT_PAIRS}
                selectedDepartments={selectedDepartments}
                onSelectTask={(task) => setSelectedTask(task)}
                onRunOptimizer={handleRunOptimizer}
                onToggleConflictPanel={() => setIsConflictPanelOpen((prev) => !prev)}
                isConflictPanelOpen={isConflictPanelOpen}
              />
            </>
          )}

          {/* Page 2: Master Optimized Gantt */}
          {activeView === 'optimized' && (
            <OptimizedGantt
              corridors={CORRIDORS}
              assignments={OPTIMIZED_ASSIGNMENTS}
              jointBlocks={INTEGRATED_JOINT_BLOCKS}
              unscheduledTasks={UNSCHEDULED_TASKS}
              solverStats={INITIAL_SOLVER_STATS}
              selectedDepartments={selectedDepartments}
              onSelectTask={(task) => setSelectedTask(task)}
              onOpenBulletin={() => setIsBulletinOpen(true)}
              onApprovePlan={handleApprovePlan}
              isPlanApproved={isPlanApproved}
            />
          )}

          {/* Page 3: Department Feeds & Intake */}
          {activeView === 'intake' && (
            <DepartmentIntakePage
              feeds={feeds}
              corridors={CORRIDORS}
              onAddFeedItem={handleAddFeedItem}
              onInjectConflicts={handleInjectConflicts}
              onResetSeedData={handleResetSeedData}
            />
          )}

          {/* Page 4: Safety & SLA Backlog Dashboard */}
          {activeView === 'safety' && (
            <SafetyDashboardPage
              agingData={DEFECT_AGING_DATA}
              monthlySavedData={MONTHLY_HOURS_SAVED_DATA}
              bottlenecks={BOTTLENECK_CORRIDORS}
            />
          )}

          {/* Page 5: Corridor Timetable & Map Schematics */}
          {activeView === 'corridormap' && (
            <CorridorMapPage
              stations={STATION_NODES}
              windows={TIMETABLE_FREE_WINDOWS}
              corridors={CORRIDORS}
            />
          )}

          {/* Page 6: Shift Execution Tracking & Audit Log */}
          {activeView === 'execution' && (
            <ExecutionTrackingPage
              initialItems={INITIAL_EXECUTION_ITEMS}
              auditLogs={AUDIT_TRAIL_LOGS}
            />
          )}
        </main>
      </div>

      {/* 3. Interactive Explainability Drawer */}
      <ExplainabilityDrawer
        task={selectedTask}
        onClose={() => setSelectedTask(null)}
      />

      {/* 4. CP-SAT Solver Progression Modal */}
      <SolverProgressOverlay
        isOpen={isSolving}
        onComplete={handleSolverComplete}
      />

      {/* 5. Official Indian Railways Block Bulletin Modal */}
      <BlockBulletinModal
        isOpen={isBulletinOpen}
        onClose={() => setIsBulletinOpen(false)}
        jointBlocks={INTEGRATED_JOINT_BLOCKS}
        assignments={OPTIMIZED_ASSIGNMENTS}
      />

      {/* 6. Guided Demo Presentation Bar (Judge Mode) */}
      <DemoPresentationBar
        currentStep={demoStep}
        onSelectStep={handleSelectDemoStep}
        isOpen={isDemoModeOpen}
        onToggle={() => setIsDemoModeOpen((prev) => !prev)}
      />
    </div>
  );
}
