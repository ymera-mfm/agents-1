import { useCallback, useRef } from 'react';
import { FixedSizeList as List } from 'react-window';
import { AgentCard } from '../features/agents/AgentCard';

export const useDebouncedCallback = (callback, delay) => {
  const timeoutRef = useRef();

  return useCallback(
    (...args) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        callback(...args);
      }, delay);
    },
    [callback, delay]
  );
};

// Virtualized list for large datasets
export const VirtualizedAgentList = ({ agents, onAgentSelect }) => {
  const Row = ({ index, style }) => (
    <div style={style}>
      <AgentCard agent={agents[index]} onSelect={onAgentSelect} />
    </div>
  );

  return (
    <List height={600} width="100%" itemCount={agents.length} itemSize={120}>
      {Row}
    </List>
  );
};
