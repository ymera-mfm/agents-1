#!/usr/bin/env python3
"""
Agent System Mapper
Creates visual representation of the agent system
"""

import json
from pathlib import Path

try:
    import graphviz
    HAS_GRAPHVIZ = True
except ImportError:
    HAS_GRAPHVIZ = False


def create_agent_map():
    """Create visual map of agent system"""
    
    with open('agent_classification.json', 'r') as f:
        classification = json.load(f)
    
    if not HAS_GRAPHVIZ:
        print("Warning: graphviz not installed, creating text-based report only")
        create_text_report(classification)
        return False
    
    # Create directed graph
    dot = graphviz.Digraph(comment='YMERA Agent System Map', format='png')
    dot.attr(rankdir='TB', size='16,20')
    dot.attr('node', shape='box', style='rounded,filled')
    
    # Add title
    dot.node('title', 'YMERA Agent System\n(Measured Data)', 
             shape='plaintext', fontsize='20', fontname='Arial Bold')
    
    # Add summary statistics node
    summary = classification["summary"]
    summary_text = f"Total Agents: {summary['total_agents']}\n"
    summary_text += f"Complete: {summary['by_status_counts']['complete']} ({summary['completion_rate']})\n"
    summary_text += f"Async: {summary['by_capability_counts']['async']} ({summary['async_adoption']})\n"
    summary_text += f"BaseAgent: {summary['by_capability_counts']['base_agent_compliant']} ({summary['base_agent_compliance']})"
    
    dot.node('summary', summary_text, shape='note', fillcolor='lightyellow', fontsize='10')
    dot.edge('title', 'summary', style='invis')
    
    # Add type clusters
    type_colors = {
        'learning': 'lightblue',
        'analysis': 'lightgreen',
        'communication': 'lightcoral',
        'execution': 'lightyellow',
        'monitoring': 'plum',
        'optimization': 'lightcyan',
        'management': 'wheat',
        'validation': 'lightpink',
        'security': 'lightgray',
        'lifecycle': 'lavender',
        'drafting': 'peachpuff',
        'editing': 'palegreen',
        'enhancement': 'lightsalmon',
        'orchestration': 'powderblue',
        'unknown': 'white'
    }
    
    type_nodes = []
    for agent_type, agents in classification["by_type"].items():
        if len(agents) == 0:
            continue
        
        count = len(agents)
        # Create cluster for each type
        with dot.subgraph(name=f'cluster_{agent_type}') as c:
            c.attr(label=f'{agent_type.upper()}\n({count} agents)', fontsize='12', fontname='Arial Bold')
            c.attr(style='filled,rounded', color='black', fillcolor=type_colors.get(agent_type, 'white'))
            
            # Add up to 5 agents from each type
            for idx, agent in enumerate(agents[:5]):
                agent_name = Path(agent["file"]).stem
                
                # Determine node color based on status
                if agent in classification["by_status"]["complete"]:
                    node_color = 'green'
                elif agent in classification["by_status"]["syntax_error"]:
                    node_color = 'red'
                else:
                    node_color = 'yellow'
                
                # Create node ID
                node_id = f'{agent_type}_{idx}'
                
                # Add capabilities as labels
                capabilities = []
                if agent.get("has_base_agent"):
                    capabilities.append("BA")
                if agent.get("async_methods", 0) > 0:
                    capabilities.append("A")
                if agent.get("has_database"):
                    capabilities.append("DB")
                if agent.get("has_api"):
                    capabilities.append("API")
                
                label = f"{agent_name[:20]}"
                if capabilities:
                    label += f"\n[{','.join(capabilities)}]"
                
                c.node(node_id, label, fillcolor=node_color, fontsize='9')
                type_nodes.append(node_id)
            
            # If more than 5, add ellipsis node
            if count > 5:
                ellipsis_id = f'{agent_type}_more'
                c.node(ellipsis_id, f'... +{count-5} more', shape='plaintext', fontsize='8')
    
    # Add legend
    with dot.subgraph(name='cluster_legend') as c:
        c.attr(label='Legend', fontsize='10')
        c.attr(style='filled', color='black', fillcolor='white')
        
        c.node('legend_complete', 'Complete', fillcolor='green', fontsize='8')
        c.node('legend_incomplete', 'Incomplete', fillcolor='yellow', fontsize='8')
        c.node('legend_error', 'Syntax Error', fillcolor='red', fontsize='8')
        c.node('legend_ba', 'BA=BaseAgent', shape='plaintext', fontsize='8')
        c.node('legend_a', 'A=Async', shape='plaintext', fontsize='8')
        c.node('legend_db', 'DB=Database', shape='plaintext', fontsize='8')
        c.node('legend_api', 'API=API Integration', shape='plaintext', fontsize='8')
    
    # Save graph
    try:
        dot.render('agent_system_map', cleanup=False)
        dot.save('agent_system_map.dot')
        print(f"Agent map created: agent_system_map.png")
        print(f"DOT source saved: agent_system_map.dot")
        return True
    except Exception as e:
        print(f"Error creating map: {e}")
        # Save the DOT file anyway
        dot.save('agent_system_map.dot')
        print(f"DOT source saved: agent_system_map.dot")
        print("Note: Install graphviz system package to generate PNG")
        return False


def create_text_report(classification):
    """Create text-based agent map"""
    print("\n=== AGENT SYSTEM MAP (Text Format) ===\n")
    
    summary = classification["summary"]
    print(f"Total Agents: {summary['total_agents']}")
    print(f"Complete: {summary['by_status_counts']['complete']} ({summary['completion_rate']})")
    print(f"Async: {summary['by_capability_counts']['async']} ({summary['async_adoption']})")
    print(f"BaseAgent Compliant: {summary['by_capability_counts']['base_agent_compliant']} ({summary['base_agent_compliance']})")
    print()
    
    for agent_type, agents in classification["by_type"].items():
        if len(agents) == 0:
            continue
            
        print(f"\n{agent_type.upper()} ({len(agents)} agents):")
        for idx, agent in enumerate(agents[:10]):  # Show first 10 of each type
            agent_name = Path(agent["file"]).stem
            
            # Determine status
            if agent in classification["by_status"]["complete"]:
                status = "✅"
            elif agent in classification["by_status"]["syntax_error"]:
                status = "❌"
            else:
                status = "⚠️"
            
            # Get capabilities
            caps = []
            if agent.get("has_base_agent"):
                caps.append("BA")
            if agent.get("async_methods", 0) > 0:
                caps.append("Async")
            if agent.get("has_database"):
                caps.append("DB")
            if agent.get("has_api"):
                caps.append("API")
            
            cap_str = f" [{', '.join(caps)}]" if caps else ""
            print(f"  {status} {agent_name}{cap_str}")
        
        if len(agents) > 10:
            print(f"  ... and {len(agents) - 10} more")


if __name__ == "__main__":
    print("=" * 60)
    print("AGENT SYSTEM MAPPER")
    print("=" * 60)
    print()
    
    success = create_agent_map()
    
    print()
    print("=" * 60)
