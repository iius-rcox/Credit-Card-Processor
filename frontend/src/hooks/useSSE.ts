/**
 * Custom hook for managing Server-Sent Events (SSE) connections.
 *
 * This hook handles EventSource connection management, reconnection logic,
 * and event parsing for real-time progress updates.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

export type SSEConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface UseSSEOptions {
  onMessage?: (event: MessageEvent) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatTimeout?: number;
}

export interface UseSSEReturn {
  connectionState: SSEConnectionState;
  connect: () => void;
  disconnect: () => void;
  isConnected: boolean;
}

/**
 * Custom hook for managing SSE connections
 *
 * @param url - The SSE endpoint URL
 * @param options - Configuration options
 * @returns SSE connection management functions and state
 */
export function useSSE(
  url: string | null,
  options: UseSSEOptions = {}
): UseSSEReturn {
  const {
    onMessage,
    onError,
    onOpen,
    onClose,
    reconnectInterval = 5000,
    maxReconnectAttempts = 5,
    heartbeatTimeout = 60000
  } = options;

  const [connectionState, setConnectionState] = useState<SSEConnectionState>('disconnected');
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Reset heartbeat timeout
   */
  const resetHeartbeatTimeout = useCallback(() => {
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
    }

    heartbeatTimeoutRef.current = setTimeout(() => {
      console.warn('SSE heartbeat timeout - reconnecting');
      disconnect();
      connect();
    }, heartbeatTimeout);
  }, [heartbeatTimeout]);

  /**
   * Clean up timeouts
   */
  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  /**
   * Connect to SSE endpoint
   */
  const connect = useCallback(() => {
    if (!url || eventSourceRef.current?.readyState === EventSource.OPEN) {
      return;
    }

    setConnectionState('connecting');

    try {
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log('SSE connection opened');
        setConnectionState('connected');
        reconnectAttemptsRef.current = 0;
        resetHeartbeatTimeout();
        onOpen?.();
      };

      eventSource.onmessage = (event) => {
        resetHeartbeatTimeout();
        onMessage?.(event);
      };

      eventSource.onerror = (error) => {
        console.error('SSE error:', error);
        setConnectionState('error');
        onError?.(error);

        // Attempt reconnection if under max attempts
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`Reconnecting SSE (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            disconnect();
            connect();
          }, reconnectInterval);
        } else {
          console.error('Max SSE reconnection attempts reached');
          setConnectionState('disconnected');
        }
      };

      // Listen for specific event types
      eventSource.addEventListener('progress', (event: MessageEvent) => {
        resetHeartbeatTimeout();
        const data = JSON.parse(event.data);
        onMessage?.(new MessageEvent('progress', { data }));
      });

      eventSource.addEventListener('heartbeat', (event: MessageEvent) => {
        resetHeartbeatTimeout();
        console.debug('SSE heartbeat received');
      });

      eventSource.addEventListener('complete', (event: MessageEvent) => {
        console.log('SSE complete event received');
        const data = JSON.parse(event.data);
        onMessage?.(new MessageEvent('complete', { data }));
        disconnect();
      });

      eventSource.addEventListener('error', (event: MessageEvent) => {
        console.error('SSE error event received:', event.data);
        const data = JSON.parse(event.data);
        onMessage?.(new MessageEvent('error', { data }));
      });

    } catch (error) {
      console.error('Failed to create EventSource:', error);
      setConnectionState('error');
    }
  }, [url, onMessage, onError, onOpen, reconnectInterval, maxReconnectAttempts, resetHeartbeatTimeout]);

  /**
   * Disconnect from SSE endpoint
   */
  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    clearTimeouts();
    setConnectionState('disconnected');
    onClose?.();
  }, [clearTimeouts, onClose]);

  /**
   * Auto-connect when URL changes
   */
  useEffect(() => {
    if (url) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [url]); // Only re-run when URL changes, not on every connect/disconnect

  return {
    connectionState,
    connect,
    disconnect,
    isConnected: connectionState === 'connected'
  };
}