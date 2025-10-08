/**
 * PhaseIndicator component for displaying processing phases as a stepper.
 *
 * This component shows all processing phases with their completion status,
 * similar to a breadcrumb or stepper UI pattern.
 */

'use client';

import React from 'react';
import { CheckCircle, Circle, XCircle, Loader2 } from 'lucide-react';
import { ProgressState, PhaseName, PHASE_CONFIGS, PhaseStatus } from '@/types/progress';

export interface PhaseIndicatorProps {
  state: ProgressState;
  className?: string;
  orientation?: 'horizontal' | 'vertical';
  showLabels?: boolean;
  compact?: boolean;
}

/**
 * PhaseIndicator component
 *
 * @param props - Component props
 * @returns JSX element displaying phase progression
 */
export function PhaseIndicator({
  state,
  className = '',
  orientation = 'horizontal',
  showLabels = true,
  compact = false
}: PhaseIndicatorProps) {
  const currentPhase = state.overall.phase;
  const phases = state.phases;

  /**
   * Get icon for phase based on status
   */
  const getPhaseIcon = (phaseName: string, status?: PhaseStatus) => {
    const iconSize = compact ? 'w-5 h-5' : 'w-6 h-6';

    // Check if this is the current active phase
    const isActive = currentPhase === phaseName;

    // Determine status
    if (status === 'completed') {
      return <CheckCircle className={`${iconSize} text-green-500`} />;
    }
    if (status === 'failed') {
      return <XCircle className={`${iconSize} text-red-500`} />;
    }
    if (status === 'in_progress' || isActive) {
      return <Loader2 className={`${iconSize} text-blue-500 animate-spin`} />;
    }
    return <Circle className={`${iconSize} text-gray-400`} />;
  };

  /**
   * Get phase status color
   */
  const getPhaseColor = (phaseName: string, status?: PhaseStatus) => {
    if (status === 'completed') return 'text-green-600 dark:text-green-400';
    if (status === 'failed') return 'text-red-600 dark:text-red-400';
    if (status === 'in_progress' || currentPhase === phaseName) {
      return 'text-blue-600 dark:text-blue-400';
    }
    return 'text-gray-400 dark:text-gray-600';
  };

  /**
   * Get connector line color
   */
  const getConnectorColor = (status?: PhaseStatus) => {
    if (status === 'completed') return 'bg-green-500';
    if (status === 'failed') return 'bg-red-500';
    return 'bg-gray-300 dark:bg-gray-600';
  };

  const containerClass = orientation === 'horizontal'
    ? 'flex items-center'
    : 'flex flex-col';

  const itemClass = orientation === 'horizontal'
    ? 'flex flex-col items-center'
    : 'flex items-start';

  const connectorClass = orientation === 'horizontal'
    ? 'h-0.5 flex-1 mx-2'
    : 'w-0.5 h-8 ml-3 my-1';

  return (
    <div className={`${containerClass} ${className}`}>
      {PHASE_CONFIGS.map((config, index) => {
        const phaseData = phases[config.name];
        const phaseStatus = phaseData?.status;
        const isLast = index === PHASE_CONFIGS.length - 1;

        return (
          <React.Fragment key={config.name}>
            {/* Phase item */}
            <div className={itemClass}>
              {/* Icon */}
              <div className="flex items-center">
                {getPhaseIcon(config.name, phaseStatus)}
              </div>

              {/* Label and progress */}
              {showLabels && (
                <div
                  className={`
                    ${orientation === 'horizontal' ? 'mt-2 text-center' : 'ml-3'}
                    ${compact ? 'text-xs' : 'text-sm'}
                  `}
                >
                  <div className={`font-medium ${getPhaseColor(config.name, phaseStatus)}`}>
                    {config.label}
                  </div>
                  {phaseData && phaseStatus === 'in_progress' && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {phaseData.percentage}%
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Connector line */}
            {!isLast && (
              <div
                className={`
                  ${connectorClass}
                  ${getConnectorColor(phaseStatus)}
                  ${orientation === 'horizontal' ? 'self-start mt-3' : ''}
                `}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}