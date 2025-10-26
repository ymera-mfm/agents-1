# AGENT TESTING REPORT
## Comprehensive Test Results with MEASURED Data

**Report Generated:** 2025-10-20T14:05:57.721134

---

## 🧪 Test Execution Summary

### Passing Agents (11)

#### agent_benchmarks.py
- Tests Run: 7
- Tests Passed: 7
- Agent Classes: AgentBenchmark

#### backup_manager.py
- Tests Run: 7
- Tests Passed: 7
- Agent Classes: BackupManager

#### task_queue.py
- Tests Run: 7
- Tests Passed: 7
- Agent Classes: AsyncTaskQueue

#### testing_framework.py
- Tests Run: 7
- Tests Passed: 7
- Agent Classes: EnhancedComponentTester

#### agent_tester.py
- Tests Run: 6
- Tests Passed: 6
- Agent Classes: AgentTester

#### activate_agents.py
- Tests Run: 7
- Tests Passed: 7
- Agent Classes: AgentActivator

#### metrics_collector.py
- Tests Run: 7
- Tests Passed: 7
- Agent Classes: MetricsCollector

#### performance_monitor.py
- Tests Run: 6
- Tests Passed: 6
- Agent Classes: PerformanceMonitor

#### metrics.py
- Tests Run: 5
- Tests Passed: 5
- Agent Classes: MetricsCollector

#### database_wrapper.py
- Tests Run: 6
- Tests Passed: 6
- Agent Classes: DatabaseManager

#### agent_discovery_complete.py
- Tests Run: 3
- Tests Passed: 3
- Agent Classes: AgentDiscoverySystem


### Failing Agents (152)


#### prod_agent_manager.py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: ModuleNotFoundError - No module named 'shared.security'

#### integration.py
- Tests Run: 2
- Tests Passed: 1
- Tests Failed: 1

#### ai_agents_production.py
- Tests Run: 10
- Tests Passed: 6
- Tests Failed: 4

#### read_replica_config.py
- Tests Run: 2
- Tests Passed: 1
- Tests Failed: 1

#### production_intelligence_engine.py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: ModuleNotFoundError - No module named 'opentelemetry.exporter.prometheus'

#### editing_agent_v2 (1).py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: ModuleNotFoundError - No module named 'opentelemetry.exporter.prometheus'

#### production_specialized_engines.py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: ModuleNotFoundError - No module named 'opentelemetry.exporter.prometheus'

#### report_generator.py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: ImportError - attempted relative import with no known parent package

#### monitoring.py
- Tests Run: 2
- Tests Passed: 1
- Tests Failed: 1

#### prod_monitoring_agent.py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: ModuleNotFoundError - No module named 'opentelemetry.exporter.prometheus'

#### ymera_api_system.py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: ModuleNotFoundError - No module named 'google.generativeai'

#### llm_agent.py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: ModuleNotFoundError - No module named 'sentence_transformers'

#### static_analysis_prod.py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: ModuleNotFoundError - No module named 'opentelemetry.exporter.prometheus'

#### BaseEvent.py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: NameError - name 'BaseModel' is not defined

#### chat_handler.py
- Tests Run: 2
- Tests Passed: 1
- Tests Failed: 1

#### chatting_files_agent_api_system.py
- Tests Run: 10
- Tests Passed: 7
- Tests Failed: 3

#### examination_agent.py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: ModuleNotFoundError - No module named 'opentelemetry.exporter.prometheus'

#### batch_processor.py
- Tests Run: 2
- Tests Passed: 1
- Tests Failed: 1

#### learning-agent-security.py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: ImportError - cannot import name 'PBKDF2' from 'cryptography.hazmat.primitives.kdf.pbkdf2' (/usr/lib/python3/dist-

#### prod_analyzer_engine.py
- Tests Run: 1
- Tests Passed: 0
- Tests Failed: 1
- Import Error: ModuleNotFoundError - No module named 'opentelemetry.exporter.prometheus'

*...and 132 more failing agents*


---

**Report Status:** COMPLETE  
**Data Type:** 100% MEASURED (zero estimates)  
