#!/usr/bin/env python3
import logging

"""
logger = logging.getLogger(__name__)

Agent Classifier
Classifies agents by type, status, and capability with measured statistics
"""

import json
from pathlib import Path
from typing import Dict, List, Any


def classify_agents() -> Dict[str, Any]:
    """Classify agents by type, status, and capability"""
    
    with open('agent_catalog_complete.json', 'r') as f:
        catalog = json.load(f)
    
    classification = {
        "by_type": {
            "learning": [],
            "analysis": [],
            "communication": [],
            "execution": [],
            "monitoring": [],
            "optimization": [],
            "management": [],
            "validation": [],
            "security": [],
            "lifecycle": [],
            "drafting": [],
            "editing": [],
            "enhancement": [],
            "orchestration": [],
            "unknown": []
        },
        "by_status": {
            "complete": [],
            "incomplete": [],
            "broken": [],
            "syntax_error": []
        },
        "by_capabilities": {
            "async": [],
            "sync_only": [],
            "database": [],
            "api": [],
            "file_ops": [],
            "base_agent_compliant": []
        },
        "summary": {}
    }
    
    for agent_detail in catalog["agents_detail"]:
        filepath = agent_detail["file"]
        filename = Path(filepath).name.lower()
        
        # Classify by status
        if agent_detail.get("status") == "syntax_error":
            classification["by_status"]["syntax_error"].append(agent_detail)
            continue
        elif "error" in agent_detail:
            classification["by_status"]["broken"].append(agent_detail)
            continue
        
        # Check completeness (has classes and basic agent structure)
        if (agent_detail.get("has_base_agent") and 
            agent_detail.get("class_count", 0) > 0 and
            (agent_detail.get("has_process_method") or agent_detail.get("has_async_init"))):
            classification["by_status"]["complete"].append(agent_detail)
        elif agent_detail.get("class_count", 0) == 0:
            classification["by_status"]["incomplete"].append(agent_detail)
        else:
            classification["by_status"]["incomplete"].append(agent_detail)
        
        # Classify by type (based on filename/content)
        classified = False
        
        if "learning" in filename:
            classification["by_type"]["learning"].append(agent_detail)
            classified = True
        
        if "analysis" in filename or "analyzer" in filename or "static_analysis" in filename:
            classification["by_type"]["analysis"].append(agent_detail)
            classified = True
        
        if "communication" in filename or "chat" in filename or "communicator" in filename:
            classification["by_type"]["communication"].append(agent_detail)
            classified = True
        
        if "execution" in filename or "executor" in filename or "worker" in filename:
            classification["by_type"]["execution"].append(agent_detail)
            classified = True
        
        if "monitor" in filename or "surveillance" in filename or "metrics" in filename:
            classification["by_type"]["monitoring"].append(agent_detail)
            classified = True
        
        if "optim" in filename:
            classification["by_type"]["optimization"].append(agent_detail)
            classified = True
        
        if "management" in filename or "manager" in filename or "registry" in filename:
            classification["by_type"]["management"].append(agent_detail)
            classified = True
        
        if "validation" in filename or "validator" in filename:
            classification["by_type"]["validation"].append(agent_detail)
            classified = True
        
        if "security" in filename:
            classification["by_type"]["security"].append(agent_detail)
            classified = True
        
        if "lifecycle" in filename:
            classification["by_type"]["lifecycle"].append(agent_detail)
            classified = True
        
        if "draft" in filename:
            classification["by_type"]["drafting"].append(agent_detail)
            classified = True
        
        if "edit" in filename or "editor" in filename:
            classification["by_type"]["editing"].append(agent_detail)
            classified = True
        
        if "enhancement" in filename or "enhance" in filename:
            classification["by_type"]["enhancement"].append(agent_detail)
            classified = True
        
        if "orchestrat" in filename or "coordinator" in filename:
            classification["by_type"]["orchestration"].append(agent_detail)
            classified = True
        
        if not classified:
            classification["by_type"]["unknown"].append(agent_detail)
        
        # Classify by capabilities
        if agent_detail.get("async_methods", 0) > 0 or agent_detail.get("async_function_count", 0) > 0:
            classification["by_capabilities"]["async"].append(agent_detail)
        else:
            classification["by_capabilities"]["sync_only"].append(agent_detail)
        
        if agent_detail.get("has_database"):
            classification["by_capabilities"]["database"].append(agent_detail)
        
        if agent_detail.get("has_api"):
            classification["by_capabilities"]["api"].append(agent_detail)
        
        if agent_detail.get("has_file_ops"):
            classification["by_capabilities"]["file_ops"].append(agent_detail)
        
        if agent_detail.get("has_base_agent"):
            classification["by_capabilities"]["base_agent_compliant"].append(agent_detail)
    
    # Generate summary statistics
    total_agents = len(catalog["agents_detail"])
    complete_count = len(classification["by_status"]["complete"])
    
    classification["summary"] = {
        "total_agents": total_agents,
        "by_type_counts": {k: len(v) for k, v in classification["by_type"].items()},
        "by_status_counts": {k: len(v) for k, v in classification["by_status"].items()},
        "by_capability_counts": {k: len(v) for k, v in classification["by_capabilities"].items()},
        "completion_rate": f"{(complete_count / total_agents * 100):.1f}%" if total_agents > 0 else "0%",
        "async_adoption": f"{(len(classification['by_capabilities']['async']) / total_agents * 100):.1f}%" if total_agents > 0 else "0%",
        "base_agent_compliance": f"{(len(classification['by_capabilities']['base_agent_compliant']) / total_agents * 100):.1f}%" if total_agents > 0 else "0%"
    }
    
    return classification


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("AGENT CLASSIFICATION ANALYZER")
    logger.info("=" * 60)
    logger.info()
    
    result = classify_agents()
    
    # Save classification
    output_file = "agent_classification.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info("Classification Summary:")
    logger.info("-" * 60)
    logger.info(f"Total agents: {result['summary']['total_agents']}")
    logger.info()
    
    logger.info("By Type:")
    for agent_type, count in result['summary']['by_type_counts'].items():
        if count > 0:
            logger.info(f"  {agent_type:20s}: {count:3d} ({count/result['summary']['total_agents']*100:5.1f}%)")
    logger.info()
    
    logger.info("By Status:")
    for status, count in result['summary']['by_status_counts'].items():
        logger.info(f"  {status:20s}: {count:3d} ({count/result['summary']['total_agents']*100:5.1f}%)")
    logger.info()
    
    logger.info("By Capabilities:")
    for capability, count in result['summary']['by_capability_counts'].items():
        logger.info(f"  {capability:20s}: {count:3d} ({count/result['summary']['total_agents']*100:5.1f}%)")
    logger.info()
    
    logger.info("Key Metrics:")
    logger.info(f"  Completion Rate:      {result['summary']['completion_rate']}")
    logger.info(f"  Async Adoption:       {result['summary']['async_adoption']}")
    logger.info(f"  BaseAgent Compliance: {result['summary']['base_agent_compliance']}")
    logger.info()
    logger.info(f"Classification saved to: {output_file}")
    logger.info("=" * 60)
