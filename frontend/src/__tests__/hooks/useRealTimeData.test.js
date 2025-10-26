import { renderHook } from '@testing-library/react';
import { useRealTimeData } from '../../hooks/useRealTimeData';

describe('useRealTimeData', () => {
  it('initializes correctly', () => {
    const { result } = renderHook(() => useRealTimeData());
    expect(result.current).toBeDefined();
  });

  // Add more specific tests for useRealTimeData
});
