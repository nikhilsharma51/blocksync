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
import {
  CORRIDORS,
  RAW_MAINTENANCE_TASKS,
  CONFLICT_PAIRS,
  INTEGRATED_JOINT_BLOCKS,
  OPTIMIZED_ASSIGNMENTS,
  UNSCHEDULED_TASKS,
  INITIAL_SOLVER_STATS,
} from '../data/mockRailwayData';
import { Department, MaintenanceTask } from '../types/railway';

export default function BlockSyncApp() {
  // Navigation & View State
  const [activeView, setActiveView] = useState<'conflicts' | 'optimized'>('conflicts');
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState<boolean>(false);

  // Department Filters (All enabled by default)
  const [selectedDepartments, setSelectedDepartments] = useState<Department[]>([
    'Track',
    'Signal',
    'OHE',
  ]);

  // Modals & Panels State
  const [selectedTask, setSelectedTask] = useState<MaintenanceTask | null>(null);
  const [isConflictPanelOpen, setIsConflictPanelOpen] = useState<boolean>(false);
  const [isSolving, setIsSolving] = useState<boolean>(false);
  const [isBulletinOpen, setIsBulletinOpen] = useState<boolean>(false);
  const [isPlanApproved, setIsPlanApproved] = useState<boolean>(false);

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
  };

  const handleApprovePlan = () => {
    setIsPlanApproved(true);
    setIsBulletinOpen(true);
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
        />

        {/* Scrollable Workspace Content */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
          {/* Active Conflict Pairs Inspection Drawer */}
          {activeView === 'conflicts' && (
            <ConflictListPanel
              conflicts={CONFLICT_PAIRS}
              isOpen={isConflictPanelOpen}
              onClose={() => setIsConflictPanelOpen(false)}
              onSelectTask={(task) => setSelectedTask(task)}
              onRunOptimizer={handleRunOptimizer}
            />
          )}

          {/* Page 1: Conflict Matrix Timeline */}
          {activeView === 'conflicts' && (
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
    </div>
  );
}
