/**
 * Integration tests for progress persistence across page refresh
 *
 * These tests verify that progress state persists and recovers correctly
 * as described in specs/006-better-status-updates/quickstart.md Step 5 and 10
 *
 * All tests are expected to FAIL until implementation is complete (TDD approach).
 */

import { test, expect, Page } from '@playwright/test';

test.describe('Progress Persistence', () => {
  test('should persist progress state to localStorage during processing', async ({ page }) => {
    /**
     * Integration Test: Progress state saved to localStorage
     *
     * Given: A session is actively processing
     * When: Progress updates are received
     * Then: Progress state is saved to localStorage
     *
     * Validates: Quickstart Step 5 (Test Progress Persistence)
     */

    // Navigate to session detail page with active processing
    const sessionId = 'test-session-id'; // Should be replaced with actual test session
    await page.goto(`http://localhost:3000/sessions/${sessionId}`);

    // Wait for progress to load
    await page.waitForSelector('[data-testid="progress-overview"]', { timeout: 5000 });

    // Check localStorage for progress data
    const progressData = await page.evaluate(() => {
      const stored = localStorage.getItem('session-progress');
      return stored ? JSON.parse(stored) : null;
    });

    expect(progressData).not.toBeNull();
    expect(progressData).toHaveProperty('session_id');
    expect(progressData).toHaveProperty('current_phase');
    expect(progressData).toHaveProperty('overall_percentage');
  });

  test('should restore progress state from localStorage after page refresh', async ({ page }) => {
    /**
     * Integration Test: Progress state restored after refresh
     *
     * Given: Progress state exists in localStorage
     * When: User refreshes the page
     * Then: Progress is immediately visible (no loading state)
     *
     * Validates: Quickstart Step 10 (Test Page Refresh Recovery)
     */

    const sessionId = 'test-session-id';
    await page.goto(`http://localhost:3000/sessions/${sessionId}`);

    // Wait for initial progress load
    await page.waitForSelector('[data-testid="progress-percentage"]', { timeout: 5000 });

    // Capture current progress
    const initialProgress = await page.textContent('[data-testid="progress-percentage"]');

    // Hard refresh the page
    await page.reload({ waitUntil: 'domcontentloaded' });

    // Progress should be visible immediately (from localStorage)
    const cachedProgress = await page.textContent('[data-testid="progress-percentage"]');
    expect(cachedProgress).toBeTruthy();

    // Should match or be close to previous state
    // (allowing for some advancement if processing continued)
    expect(cachedProgress).toBe(initialProgress);
  });

  test('should reconnect to progress polling after refresh', async ({ page }) => {
    /**
     * Integration Test: Progress polling resumes after refresh
     *
     * Given: User refreshed during active processing
     * When: Page loads with cached progress
     * Then: Real-time updates resume within 3 seconds
     *
     * Validates: FR-013 (progress visible after navigation/refresh)
     */

    const sessionId = 'test-session-id';
    await page.goto(`http://localhost:3000/sessions/${sessionId}`);

    // Wait for progress
    await page.waitForSelector('[data-testid="progress-percentage"]');

    // Refresh page
    await page.reload();

    // Wait for progress to update (polling resumed)
    await page.waitForTimeout(3500); // Allow 3.5s for polling to resume

    // Verify last_update timestamp is recent
    const lastUpdate = await page.getAttribute('[data-testid="last-update"]', 'data-timestamp');
    const now = Date.now();
    const updateTime = new Date(lastUpdate!).getTime();
    const elapsedSeconds = (now - updateTime) / 1000;

    expect(elapsedSeconds).toBeLessThan(10); // Should be within last 10 seconds
  });

  test('should clear cached progress when session completes', async ({ page }) => {
    /**
     * Integration Test: Progress cache cleared on completion
     *
     * Given: A session has completed processing
     * When: Final progress state received
     * Then: Transient progress data removed from localStorage
     *
     * Validates: FR-009 (completion state), data cleanup
     */

    const sessionId = 'test-session-completed';
    await page.goto(`http://localhost:3000/sessions/${sessionId}`);

    // Wait for completion state
    await page.waitForSelector('[data-testid="progress-completed"]', { timeout: 10000 });

    // Check localStorage - detailed progress should be cleared
    const progressData = await page.evaluate(() => {
      const stored = localStorage.getItem('session-progress');
      return stored ? JSON.parse(stored) : null;
    });

    if (progressData) {
      // Should not have detailed phase_details for completed session
      expect(progressData.phase_details).toBeNull();
      expect(progressData.overall_percentage).toBe(100);
    }
  });

  test('should handle localStorage quota exceeded gracefully', async ({ page }) => {
    /**
     * Integration Test: Graceful handling of storage quota errors
     *
     * Given: localStorage is full or unavailable
     * When: Attempting to save progress
     * Then: App continues without crashing, uses memory fallback
     *
     * Validates: Error resilience
     */

    const sessionId = 'test-session-id';

    // Fill up localStorage to trigger quota error
    await page.evaluate(() => {
      try {
        const largeData = 'x'.repeat(5 * 1024 * 1024); // 5MB
        localStorage.setItem('dummy', largeData);
      } catch (e) {
        // Quota exceeded - this is expected
      }
    });

    await page.goto(`http://localhost:3000/sessions/${sessionId}`);

    // Should still load and function
    await page.waitForSelector('[data-testid="progress-overview"]', { timeout: 5000 });

    // Progress should be visible even without localStorage
    const progress = await page.textContent('[data-testid="progress-percentage"]');
    expect(progress).toBeTruthy();
  });

  test('should not restore stale progress from old session', async ({ page }) => {
    /**
     * Integration Test: Stale cache detection
     *
     * Given: localStorage contains progress for a different session
     * When: Loading a new session
     * Then: Stale cache is ignored, fresh progress loaded
     *
     * Validates: Cache invalidation logic
     */

    const oldSessionId = 'old-session-id';
    const newSessionId = 'new-session-id';

    // Set stale progress in localStorage
    await page.evaluate((sessionId) => {
      const staleProgress = {
        session_id: sessionId,
        current_phase: 'processing',
        overall_percentage: 50,
        last_update: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
      };
      localStorage.setItem('session-progress', JSON.stringify(staleProgress));
    }, oldSessionId);

    // Navigate to different session
    await page.goto(`http://localhost:3000/sessions/${newSessionId}`);

    // Should load fresh progress, not stale cache
    await page.waitForSelector('[data-testid="progress-overview"]');

    const displayedSessionId = await page.getAttribute(
      '[data-testid="progress-overview"]',
      'data-session-id'
    );

    expect(displayedSessionId).toBe(newSessionId);
    expect(displayedSessionId).not.toBe(oldSessionId);
  });

  test('should display cached progress immediately while fetching updates', async ({ page }) => {
    /**
     * Integration Test: Optimistic UI with cached data
     *
     * Given: Cached progress exists in localStorage
     * When: Page loads
     * Then: Cached progress shown immediately, then updated with fresh data
     *
     * Validates: No "loading" or "unknown status" shown (FR-013)
     */

    const sessionId = 'test-session-id';

    // Pre-populate cache
    await page.evaluate((sessionId) => {
      const cachedProgress = {
        session_id: sessionId,
        current_phase: 'processing',
        overall_percentage: 45,
        last_update: new Date().toISOString(),
        status_message: 'Processing File 2 of 3: Page 5/12',
      };
      localStorage.setItem('session-progress', JSON.stringify(cachedProgress));
    }, sessionId);

    // Navigate to page
    await page.goto(`http://localhost:3000/sessions/${sessionId}`);

    // Progress should be visible immediately (from cache)
    await page.waitForSelector('[data-testid="progress-percentage"]', { timeout: 1000 });

    const immediateProgress = await page.textContent('[data-testid="progress-percentage"]');
    expect(immediateProgress).toContain('45');

    // Should not show loading spinner for cached data
    const loadingSpinner = await page.$('[data-testid="progress-loading"]');
    expect(loadingSpinner).toBeNull();
  });

  test('should sync progress updates across multiple tabs', async ({ browser }) => {
    /**
     * Integration Test: Multi-tab synchronization
     *
     * Given: Same session open in two tabs
     * When: Progress updates in one tab
     * Then: Other tab reflects the update (via storage event)
     *
     * Validates: Cross-tab consistency
     */

    const context = await browser.newContext();
    const page1 = await context.newPage();
    const page2 = await context.newPage();

    const sessionId = 'test-session-id';

    // Open same session in both tabs
    await page1.goto(`http://localhost:3000/sessions/${sessionId}`);
    await page2.goto(`http://localhost:3000/sessions/${sessionId}`);

    // Wait for progress in both tabs
    await page1.waitForSelector('[data-testid="progress-percentage"]');
    await page2.waitForSelector('[data-testid="progress-percentage"]');

    // Get initial progress in tab 2
    const initialProgress2 = await page2.textContent('[data-testid="progress-percentage"]');

    // Simulate progress update in tab 1
    await page1.evaluate(() => {
      const updatedProgress = {
        session_id: 'test-session-id',
        current_phase: 'processing',
        overall_percentage: 75,
        last_update: new Date().toISOString(),
      };
      localStorage.setItem('session-progress', JSON.stringify(updatedProgress));

      // Trigger storage event
      window.dispatchEvent(new StorageEvent('storage', {
        key: 'session-progress',
        newValue: JSON.stringify(updatedProgress),
      }));
    });

    // Wait for update in tab 2
    await page2.waitForTimeout(1000);

    const updatedProgress2 = await page2.textContent('[data-testid="progress-percentage"]');
    expect(updatedProgress2).not.toBe(initialProgress2);
    expect(updatedProgress2).toContain('75');

    await context.close();
  });

  test('should handle corrupted localStorage data gracefully', async ({ page }) => {
    /**
     * Integration Test: Corrupted cache recovery
     *
     * Given: localStorage contains invalid JSON
     * When: Loading progress
     * Then: Invalid cache is cleared, fresh data loaded
     *
     * Validates: Error resilience
     */

    const sessionId = 'test-session-id';

    // Set corrupted data
    await page.evaluate(() => {
      localStorage.setItem('session-progress', '{invalid json}');
    });

    await page.goto(`http://localhost:3000/sessions/${sessionId}`);

    // Should load successfully despite corrupted cache
    await page.waitForSelector('[data-testid="progress-overview"]', { timeout: 5000 });

    // Progress should be loaded from API
    const progress = await page.textContent('[data-testid="progress-percentage"]');
    expect(progress).toBeTruthy();
  });
});

test.describe('Progress Auto-Refresh', () => {
  test('should poll progress endpoint every 2-3 seconds', async ({ page }) => {
    /**
     * Integration Test: Polling interval validation
     *
     * Given: Session is actively processing
     * When: Monitoring network requests
     * Then: Progress endpoint called every 2-3 seconds
     *
     * Validates: FR-005 (updates at 2-3 second intervals)
     */

    const sessionId = 'test-session-id';

    // Track progress API calls
    const apiCalls: number[] = [];
    page.on('request', (request) => {
      if (request.url().includes('/progress')) {
        apiCalls.push(Date.now());
      }
    });

    await page.goto(`http://localhost:3000/sessions/${sessionId}`);

    // Wait for multiple polls
    await page.waitForTimeout(10000); // 10 seconds

    // Calculate intervals between calls
    const intervals = [];
    for (let i = 1; i < apiCalls.length; i++) {
      const interval = (apiCalls[i] - apiCalls[i - 1]) / 1000; // Convert to seconds
      intervals.push(interval);
    }

    // Verify intervals are approximately 2-3 seconds
    expect(intervals.length).toBeGreaterThan(2);
    for (const interval of intervals) {
      expect(interval).toBeGreaterThanOrEqual(1.5);
      expect(interval).toBeLessThanOrEqual(4.0);
    }
  });

  test('should stop polling when processing completes', async ({ page }) => {
    /**
     * Integration Test: Polling lifecycle management
     *
     * Given: Processing completes
     * When: Final progress state received
     * Then: Polling stops (no unnecessary API calls)
     *
     * Validates: Resource efficiency
     */

    const sessionId = 'test-session-completed';

    let apiCallCount = 0;
    page.on('request', (request) => {
      if (request.url().includes('/progress')) {
        apiCallCount++;
      }
    });

    await page.goto(`http://localhost:3000/sessions/${sessionId}`);

    // Wait for completion
    await page.waitForSelector('[data-testid="progress-completed"]', { timeout: 10000 });

    const callsBeforeWait = apiCallCount;

    // Wait additional time
    await page.waitForTimeout(10000);

    const callsAfterWait = apiCallCount;

    // Should not have made many more calls after completion
    expect(callsAfterWait - callsBeforeWait).toBeLessThan(3);
  });
});

/**
 * Test Data Setup Notes:
 *
 * These tests require:
 * 1. Backend server running on localhost:8000
 * 2. Frontend running on localhost:3000
 * 3. Test sessions with known IDs ('test-session-id', 'test-session-completed')
 * 4. Playwright installed and configured
 *
 * Run with: npx playwright test __tests__/integration/test_progress_persistence.spec.ts
 */
