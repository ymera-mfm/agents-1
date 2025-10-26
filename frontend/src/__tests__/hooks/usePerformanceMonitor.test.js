import { renderHook } from '@testing-library/react';
import { usePerformanceMonitor } from '../../hooks/usePerformanceMonitor';

describe('usePerformanceMonitor', () => {
  it('initializes correctly', () => {
    const { result } = renderHook(() => usePerformanceMonitor());
    expect(result.current).toBeDefined();
  });

  // Add more specific tests for usePerformanceMonitor
});
