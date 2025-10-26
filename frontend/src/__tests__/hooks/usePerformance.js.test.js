import { renderHook } from '@testing-library/react';
import { usePerformance } from '../../hooks/usePerformance.js';

describe('usePerformance', () => {
  it('initializes correctly', () => {
    const { result } = renderHook(() => usePerformance());
    expect(result.current).toBeDefined();
  });

  // Add more specific tests for usePerformance
});
