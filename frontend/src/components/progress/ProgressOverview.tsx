/**
 * ProgressOverview component for displaying aggregate progress.
 *
 * This component shows an overall progress bar with percentage,
 * current phase, and animated transitions.
 */

'use client';

import React, { useMemo } from 'react';
import { ProgressState, PhaseName, PHASE_CONFIGS } from '@/types/progress';

export interface ProgressOverviewProps {
  state: ProgressState;
  className?: string;
  showPercentage?: boolean;
  showPhase?: boolean;
  animated?: boolean;
}

/**
 * ProgressOverview component
 *
 * @param props - Component props
 * @returns JSX element displaying overall progress
 */
export function ProgressOverview({
  state,
  className = '',
  showPercentage = true,
  showPhase = true,
  animated = true
}: ProgressOverviewProps) {
  const percentage = state.overall.percentage;
  const phase = state.overall.phase;

  // Get phase configuration for color
  const phaseConfig = useMemo(() => {
    return PHASE_CONFIGS.find(config => config.name === phase) || {
      label: phase,
      color: '#6B7280' // gray as default
    };
  }, [phase]);

  // Determine progress bar color based on state
  const progressColor = useMemo(() => {
    if (state.error) return '#EF4444'; // red for error
    if (phase === 'completed') return '#10B981'; // green for completed
    if (phase === 'failed') return '#EF4444'; // red for failed
    return phaseConfig.color || '#3B82F6'; // phase color or blue default
  }, [state.error, phase, phaseConfig]);

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Header with phase and percentage */}
      <div className="flex items-center justify-between text-sm">
        {showPhase && (
          <span className="font-medium text-gray-700 dark:text-gray-300">
            {phaseConfig.label}
          </span>
        )}
        {showPercentage && (
          <span className="font-semibold text-gray-900 dark:text-gray-100">
            {percentage}%
          </span>
        )}
      </div>

      {/* Progress bar container */}
      <div className="relative w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4 overflow-hidden">
        {/* Background pattern for visual interest */}
        <div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(0,0,0,0.1) 10px, rgba(0,0,0,0.1) 20px)'
          }}
        />

        {/* Progress bar fill */}
        <div
          className={`
            h-full flex items-center justify-center relative
            ${animated ? 'transition-all duration-500 ease-out' : ''}
          `}
          style={{
            width: `${percentage}%`,
            backgroundColor: progressColor
          }}
        >
          {/* Animated shimmer effect */}
          {animated && percentage > 0 && percentage < 100 && (
            <div
              className="absolute inset-0 opacity-20"
              style={{
                background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
                animation: 'shimmer 2s infinite'
              }}
            />
          )}

          {/* Percentage text inside bar (if wide enough) */}
          {showPercentage && percentage >= 20 && (
            <span className="absolute text-xs font-bold text-white">
              {percentage}%
            </span>
          )}
        </div>
      </div>

      {/* Status message */}
      {state.statusMessage && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          {state.statusMessage}
        </p>
      )}

      {/* Connection indicator */}
      {state.connectionState !== 'connected' && state.connectionState !== 'disconnected' && (
        <div className="flex items-center gap-2 mt-2">
          <div
            className={`
              w-2 h-2 rounded-full
              ${state.connectionState === 'connecting' ? 'bg-yellow-500 animate-pulse' : ''}
              ${state.connectionState === 'error' ? 'bg-red-500' : ''}
            `}
          />
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {state.connectionState === 'connecting' && 'Connecting...'}
            {state.connectionState === 'error' && 'Connection error'}
          </span>
        </div>
      )}

      <style jsx>{`
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(200%);
          }
        }
      `}</style>
    </div>
  );
}