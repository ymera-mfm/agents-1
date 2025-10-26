"""
Query Performance Monitoring and Optimization System
"""
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class QueryPerformanceMonitor:
    """Monitor and log SQL query performance"""
    
    def __init__(self, slow_query_threshold: float = 1.0):
        self.slow_query_threshold = slow_query_threshold
        self.query_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'min_time': float('inf'),
            'max_time': 0,
            'errors': 0
        })
        self.slow_queries = []
        self.log_file = Path("logs/query_performance.json")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def register_listeners(self, engine: Engine):
        """Register SQLAlchemy event listeners for query monitoring"""
        
        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, 
                                         parameters, context, executemany):
            context._query_start_time = time.time()
            context._query_statement = statement
        
        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement,
                                        parameters, context, executemany):
            total_time = time.time() - context._query_start_time
            
            # Update statistics
            query_hash = hash(statement[:100])
            stats = self.query_stats[query_hash]
            stats['count'] += 1
            stats['total_time'] += total_time
            stats['min_time'] = min(stats['min_time'], total_time)
            stats['max_time'] = max(stats['max_time'], total_time)
            
            # Log slow queries
            if total_time > self.slow_query_threshold:
                self._log_slow_query(statement, total_time, parameters)
        
        @event.listens_for(engine, "dbapi_error")
        def receive_dbapi_error(conn, cursor, statement, parameters,
                               context, exception):
            query_hash = hash(statement[:100])
            self.query_stats[query_hash]['errors'] += 1
            logger.error(f"Query error: {exception}")
    
    def _log_slow_query(self, statement: str, execution_time: float, 
                       parameters: Optional[Dict] = None):
        """Log slow query for analysis"""
        slow_query = {
            'timestamp': datetime.now().isoformat(),
            'statement': statement[:500],  # Truncate long queries
            'execution_time': execution_time,
            'parameters': str(parameters)[:200] if parameters else None
        }
        
        self.slow_queries.append(slow_query)
        logger.warning(f"Slow query detected: {execution_time:.2f}s - {statement[:100]}")
        
        # Save to file periodically
        if len(self.slow_queries) >= 100:
            self._flush_slow_queries()
    
    def _flush_slow_queries(self):
        """Save slow queries to file"""
        try:
            existing_data = []
            if self.log_file.exists():
                existing_data = json.loads(self.log_file.read_text())
            
            existing_data.extend(self.slow_queries)
            self.log_file.write_text(json.dumps(existing_data, indent=2))
            
            self.slow_queries = []
        except Exception as e:
            logger.error(f"Failed to flush slow queries: {e}")
    
    def get_query_statistics(self) -> List[Dict]:
        """Get aggregated query statistics"""
        stats_list = []
        
        for query_hash, stats in self.query_stats.items():
            if stats['count'] > 0:
                avg_time = stats['total_time'] / stats['count']
                stats_list.append({
                    'query_hash': query_hash,
                    'count': stats['count'],
                    'avg_time': avg_time,
                    'min_time': stats['min_time'],
                    'max_time': stats['max_time'],
                    'total_time': stats['total_time'],
                    'errors': stats['errors']
                })
        
        # Sort by total time (most expensive queries first)
        stats_list.sort(key=lambda x: x['total_time'], reverse=True)
        return stats_list
    
    def get_slow_queries(self, limit: int = 50) -> List[Dict]:
        """Get recent slow queries"""
        # Load from file if needed
        if self.log_file.exists():
            all_queries = json.loads(self.log_file.read_text())
            return all_queries[-limit:]
        return self.slow_queries[-limit:]
    
    def clear_statistics(self):
        """Clear collected statistics"""
        self.query_stats.clear()
        self.slow_queries = []


class IndexAnalyzer:
    """Analyze and suggest database indexes"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def find_missing_indexes(self) -> List[Dict]:
        """Find missing indexes based on query patterns"""
        query = text("""
            SELECT 
                migs.avg_total_user_cost * (migs.avg_user_impact / 100.0) * 
                (migs.user_seeks + migs.user_scans) AS improvement_measure,
                'CREATE INDEX IX_' + 
                OBJECT_NAME(mid.object_id, mid.database_id) + '_' +
                REPLACE(REPLACE(REPLACE(ISNULL(mid.equality_columns, ''), ', ', '_'), '[', ''), ']', '') +
                CASE WHEN mid.equality_columns IS NOT NULL AND mid.inequality_columns IS NOT NULL 
                     THEN '_' ELSE '' END +
                REPLACE(REPLACE(REPLACE(ISNULL(mid.inequality_columns, ''), ', ', '_'), '[', ''), ']', '') +
                ' ON ' + mid.statement +
                ' (' + ISNULL(mid.equality_columns, '') +
                CASE WHEN mid.equality_columns IS NOT NULL AND mid.inequality_columns IS NOT NULL 
                     THEN ',' ELSE '' END +
                ISNULL(mid.inequality_columns, '') + ')' +
                ISNULL(' INCLUDE (' + mid.included_columns + ')', '') AS create_index_statement,
                migs.avg_user_impact,
                migs.user_seeks + migs.user_scans AS total_seeks_scans
            FROM sys.dm_db_missing_index_group_stats AS migs
            INNER JOIN sys.dm_db_missing_index_groups AS mig 
                ON migs.group_handle = mig.index_group_handle
            INNER JOIN sys.dm_db_missing_index_details AS mid 
                ON mig.index_handle = mid.index_handle
            WHERE migs.avg_total_user_cost * (migs.avg_user_impact / 100.0) * 
                  (migs.user_seeks + migs.user_scans) > 10
            ORDER BY improvement_measure DESC
        """)
        
        try:
            result = self.session.execute(query)
            missing_indexes = []
            
            for row in result:
                missing_indexes.append({
                    'improvement_measure': float(row[0]),
                    'create_statement': row[1],
                    'avg_user_impact': float(row[2]),
                    'total_seeks_scans': int(row[3])
                })
            
            return missing_indexes
        except Exception as e:
            logger.error(f"Failed to find missing indexes: {e}")
            return []
    
    def analyze_index_usage(self) -> List[Dict]:
        """Analyze existing index usage"""
        query = text("""
            SELECT 
                OBJECT_NAME(s.object_id) AS table_name,
                i.name AS index_name,
                i.type_desc AS index_type,
                s.user_seeks,
                s.user_scans,
                s.user_lookups,
                s.user_updates,
                s.last_user_seek,
                s.last_user_scan,
                s.last_user_lookup
            FROM sys.dm_db_index_usage_stats s
            INNER JOIN sys.indexes i ON s.object_id = i.object_id 
                AND s.index_id = i.index_id
            WHERE OBJECTPROPERTY(s.object_id, 'IsUserTable') = 1
                AND s.database_id = DB_ID()
            ORDER BY s.user_seeks + s.user_scans + s.user_lookups DESC
        """)
        
        try:
            result = self.session.execute(query)
            index_usage = []
            
            for row in result:
                index_usage.append({
                    'table_name': row[0],
                    'index_name': row[1],
                    'index_type': row[2],
                    'user_seeks': row[3],
                    'user_scans': row[4],
                    'user_lookups': row[5],
                    'user_updates': row[6],
                    'last_used': max(filter(None, [row[7], row[8], row[9]])) if any([row[7], row[8], row[9]]) else None
                })
            
            return index_usage
        except Exception as e:
            logger.error(f"Failed to analyze index usage: {e}")
            return []
    
    def find_unused_indexes(self, days_threshold: int = 30) -> List[Dict]:
        """Find indexes that haven't been used recently"""
        unused = []
        all_usage = self.analyze_index_usage()
        
        threshold_date = datetime.now() - timedelta(days=days_threshold)
        
        for idx in all_usage:
            last_used = idx.get('last_used')
            total_usage = (idx['user_seeks'] + idx['user_scans'] + idx['user_lookups'])
            
            if total_usage == 0 or (last_used and last_used < threshold_date):
                unused.append({
                    'table_name': idx['table_name'],
                    'index_name': idx['index_name'],
                    'last_used': last_used,
                    'total_usage': total_usage,
                    'recommendation': f"DROP INDEX {idx['index_name']} ON {idx['table_name']}"
                })
        
        return unused


class QueryOptimizer:
    """Query optimization utilities"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def analyze_query_plan(self, query: str) -> Dict:
        """Get execution plan for a query"""
        try:
            # Enable execution plan
            self.session.execute(text("SET SHOWPLAN_XML ON"))
            
            # Get execution plan
            result = self.session.execute(text(query))
            plan = result.fetchone()[0]
            
            self.session.execute(text("SET SHOWPLAN_XML OFF"))
            
            return {
                'query': query,
                'execution_plan': plan,
                'analyzed_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to analyze query plan: {e}")
            return {}
    
    def get_expensive_queries(self, top_n: int = 20) -> List[Dict]:
        """Get most expensive queries by resource usage"""
        query = text("""
            SELECT TOP :top_n
                qs.execution_count,
                qs.total_worker_time / 1000 AS total_cpu_ms,
                qs.total_worker_time / qs.execution_count / 1000 AS avg_cpu_ms,
                qs.total_logical_reads,
                qs.total_logical_reads / qs.execution_count AS avg_logical_reads,
                qs.total_elapsed_time / 1000 AS total_elapsed_ms,
                qs.total_elapsed_time / qs.execution_count / 1000 AS avg_elapsed_ms,
                SUBSTRING(st.text, (qs.statement_start_offset/2)+1,
                    ((CASE qs.statement_end_offset
                        WHEN -1 THEN DATALENGTH(st.text)
                        ELSE qs.statement_end_offset
                    END - qs.statement_start_offset)/2) + 1) AS query_text
            FROM sys.dm_exec_query_stats qs
            CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
            ORDER BY qs.total_worker_time DESC
        """)
        
        try:
            result = self.session.execute(query, {'top_n': top_n})
            expensive_queries = []
            
            for row in result:
                expensive_queries.append({
                    'execution_count': row[0],
                    'total_cpu_ms': row[1],
                    'avg_cpu_ms': row[2],
                    'total_logical_reads': row[3],
                    'avg_logical_reads': row[4],
                    'total_elapsed_ms': row[5],
                    'avg_elapsed_ms': row[6],
                    'query_text': row[7][:500]  # Truncate long queries
                })
            
            return expensive_queries
        except Exception as e:
            logger.error(f"Failed to get expensive queries: {e}")
            return []
    
    def update_statistics(self, table_name: Optional[str] = None):
        """Update statistics for better query optimization"""
        try:
            if table_name:
                query = text(f"UPDATE STATISTICS {table_name} WITH FULLSCAN")
            else:
                query = text("EXEC sp_updatestats")
            
            self.session.execute(query)
            logger.info(f"Statistics updated for {table_name or 'all tables'}")
        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
            raise