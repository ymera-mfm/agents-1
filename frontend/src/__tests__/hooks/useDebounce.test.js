import { renderHook } from '@testing-library/react';
import { useDebounce } from '../../hooks/useDebounce';

describe('useDebounce', () => {
  it('initializes correctly', () => {
    const { result } = renderHook(() => useDebounce());
    expect(result.current).toBeDefined();
  });

  // Add more specific tests for useDebounce
});
