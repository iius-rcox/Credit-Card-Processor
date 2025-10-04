"use client"

import { useState, useEffect } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { AlertTriangle, X } from 'lucide-react'

interface CompatibilityWarningProps {
  className?: string
}

export function CompatibilityWarning({ className }: CompatibilityWarningProps) {
  const [isSupported, setIsSupported] = useState<boolean | null>(null)
  const [isDismissed, setIsDismissed] = useState(false)

  useEffect(() => {
    // Check OKLCH support
    const checkOKLCHSupport = () => {
      if (typeof window !== 'undefined' && window.CSS?.supports) {
        return window.CSS.supports('color', 'oklch(0.5 0.2 180)')
      }
      return false
    }

    const supported = checkOKLCHSupport()
    setIsSupported(supported)

    // Check if warning was previously dismissed
    if (typeof window !== 'undefined') {
      const dismissed = localStorage.getItem('oklch-warning-dismissed')
      setIsDismissed(dismissed === 'true')
    }
  }, [])

  const handleDismiss = () => {
    setIsDismissed(true)
    if (typeof window !== 'undefined') {
      localStorage.setItem('oklch-warning-dismissed', 'true')
    }
  }

  // Don't render if OKLCH is supported or warning is dismissed
  if (isSupported || isDismissed || isSupported === null) {
    return null
  }

  return (
    <Alert variant="default" className={`border-amber-200 bg-amber-50 text-amber-800 ${className}`}>
      <AlertTriangle className="h-4 w-4" />
      <div className="flex justify-between items-start w-full">
        <div className="flex-1">
          <AlertDescription className="text-amber-800">
            <strong>Browser Compatibility Notice:</strong> Your browser has limited color support.
            The application will work normally, but some colors may appear differently than intended.
            For the best experience, please consider updating to a modern browser.
          </AlertDescription>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleDismiss}
          className="h-6 w-6 text-amber-600 hover:text-amber-800 hover:bg-amber-100 ml-2 flex-shrink-0"
          aria-label="Dismiss warning"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </Alert>
  )
}

// Hook for checking OKLCH support in other components
export function useOKLCHSupport() {
  const [isSupported, setIsSupported] = useState<boolean | null>(null)

  useEffect(() => {
    const checkOKLCHSupport = () => {
      if (typeof window !== 'undefined' && window.CSS?.supports) {
        return window.CSS.supports('color', 'oklch(0.5 0.2 180)')
      }
      return false
    }

    setIsSupported(checkOKLCHSupport())
  }, [])

  return isSupported
}

// Utility function for checking if warning should be shown
export function shouldShowCompatibilityWarning(): boolean {
  if (typeof window === 'undefined') return false

  const isSupported = window.CSS?.supports?.('color', 'oklch(0.5 0.2 180)') ?? false
  const isDismissed = localStorage.getItem('oklch-warning-dismissed') === 'true'

  return !isSupported && !isDismissed
}