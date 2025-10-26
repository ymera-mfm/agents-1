import { renderHook } from '@testing-library/react';
import { useWebSocketStatus } from '../../hooks/useWebSocketStatus';

describe('useWebSocketStatus', () => {
  it('initializes correctly', () => {
    const { result } = renderHook(() => useWebSocketStatus());
    expect(result.current).toBeDefined();
  });

  // Add more specific tests for useWebSocketStatus
});
