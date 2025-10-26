# Add these endpoints to your app.py file

# ============================================================================
# AGENT MANAGEMENT ENDPOINTS (Enhanced Authority)
# ============================================================================

@app.post("/agents/{agent_id}/actions", response_model=Dict, dependencies=[Depends(zero_trust_enforcement)])
@require_permission(Permission.MANAGE_AGENTS)
async def execute_agent_action(
    agent_id: str,
    action_request: AgentActionRequest,
    current_user: Dict = Depends(get_rbac_manager_instance_dependency().get_current_user)
):
    """Execute administrative action on an agent (suspend, freeze, resume, decommission).
    
    Requires MANAGE_AGENTS permission. Critical actions may require additional approval.
    """
    global agent_lifecycle_manager, telemetry_manager
    
    if not agent_lifecycle_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent lifecycle manager not initialized"
        )
    
    try:
        # Verify the admin has authority
        action_request.admin_id = current_user["id"]
        
        result = await agent_lifecycle_manager.execute_agent_action(
            agent_id, 
            action_request
        )
        
        if telemetry_manager:
            await telemetry_manager.record_event(
                "agent_action_executed",
                {
                    "agent_id": agent_id,
                    "action": action_request.action.value,
                    "admin_id": current_user["id"],
                    "result": result["status"]
                }
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute action on agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute action: {str(e)}"
        )


@app.post("/agents/{agent_id}/security-violation", response_model=Dict, dependencies=[Depends(zero_trust_enforcement)])
@require_permission(Permission.MANAGE_AGENTS)
async def report_security_violation(
    agent_id: str,
    violation_type: str,
    severity: str,
    details: Dict[str, Any],
    current_user: Dict = Depends(get_rbac_manager_instance_dependency().get_current_user)
):
    """Report a security violation by an agent (called by surveillance system or manually).
    
    This endpoint allows the Agent Manager to handle security violations with appropriate
    enforcement actions including automatic suspension if configured.
    """
    global agent_lifecycle_manager
    
    if not agent_lifecycle_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent lifecycle manager not initialized"
        )
    
    try:
        # Convert string severity to enum
        severity_enum = AlertSeverity(severity.lower())
        
        result = await agent_lifecycle_manager.handle_security_violation(
            agent_id=agent_id,
            violation_type=violation_type,
            severity=severity_enum,
            details={**details, "reported_by": current_user["id"]}
        )
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid severity level: {severity}"
        )
    except Exception as e:
        logger.error(f"Failed to handle security violation for agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to handle violation: {str(e)}"
        )


@app.get("/agents/{agent_id}/surveillance-report", response_model=Dict, dependencies=[Depends(zero_trust_enforcement)])
@require_permission(Permission.VIEW_AGENTS)
async def get_agent_surveillance_report(
    agent_id: str,
    current_user: Dict = Depends(get_rbac_manager_instance_dependency().get_current_user)
):
    """Get detailed surveillance report for a specific agent.
    
    Includes performance metrics, security scores, anomaly detection results,
    and behavioral analysis from the surveillance system.
    """
    global agent_surveillance_system, agent_lifecycle_manager
    
    if not agent_surveillance_system or not agent_lifecycle_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Surveillance system not initialized"
        )
    
    try:
        # Get agent details
        agent = await agent_lifecycle_manager.get_agent(agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        # Verify tenant access
        if agent.tenant_id != current_user["tenant_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this agent"
            )
        
        # Get surveillance metrics
        metrics = await agent_surveillance_system.get_agent_metrics(agent_id)
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "status": agent.status,
            "security_score": agent.security_score,
            "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
            "surveillance_metrics": metrics or {},
            "performance_metrics": agent.performance_metrics or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get surveillance report for agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@app.get("/surveillance/dashboard", response_model=Dict, dependencies=[Depends(zero_trust_enforcement)])
@require_permission(Permission.VIEW_AGENTS)
async def get_surveillance_dashboard(
    current_user: Dict = Depends(get_rbac_manager_instance_dependency().get_current_user)
):
    """Get comprehensive surveillance dashboard for all agents in tenant.
    
    Provides overview of agent health, security status, and system-wide metrics.
    """
    global agent_surveillance_system, agent_lifecycle_manager
    
    if not agent_surveillance_system or not agent_lifecycle_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Surveillance system not initialized"
        )
    
    try:
        tenant_id = current_user["tenant_id"]
        
        # Get all agents for tenant
        agents = await agent_lifecycle_manager.list_agents(tenant_id)
        
        # Get surveillance report
        surveillance_report = await agent_surveillance_system.get_surveillance_report()
        
        # Aggregate statistics
        total_agents = len(agents)
        active_agents = sum(1 for a in agents if a.status == "active")
        suspended_agents = sum(1 for a in agents if a.status == "suspended")
        frozen_agents = sum(1 for a in agents if a.status == "frozen")
        compromised_agents = sum(1 for a in agents if a.status == "compromised")
        
        avg_security_score = (
            sum(a.security_score for a in agents) / total_agents 
            if total_agents > 0 else 100
        )
        
        # Agents requiring attention
        low_security_agents = [
            {
                "id": str(a.id),
                "name": a.name,
                "security_score": a.security_score,
                "status": a.status
            }
            for a in agents if a.security_score < 70
        ]
        
        return {
            "tenant_id": tenant_id,
            "summary": {
                "total_agents": total_agents,
                "active_agents": active_agents,
                "suspended_agents": suspended_agents,
                "frozen_agents": frozen_agents,
                "compromised_agents": compromised_agents,
                "average_security_score": round(avg_security_score, 2)
            },
            "agents_requiring_attention": low_security_agents,
            "surveillance_status": surveillance_report,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to generate surveillance dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard: {str(e)}"
        )


@app.post("/agents/{agent_id}/approve-action", response_model=Dict, dependencies=[Depends(zero_trust_enforcement)])
@require_permission(Permission.MANAGE_AGENTS)
async def approve_agent_action(
    agent_id: str,
    action: str,
    approval_notes: str,
    current_user: Dict = Depends(get_rbac_manager_instance_dependency().get_current_user)
):
    """Approve a pending agent action (e.g., decommission).
    
    Used when actions require admin approval. Only users with MANAGE_AGENTS
    permission can approve.
    """
    global agent_lifecycle_manager, telemetry_manager
    
    if not agent_lifecycle_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent lifecycle manager not initialized"
        )
    
    try:
        # Generate approval ID
        approval_id = f"approval_{current_user['id']}_{int(datetime.utcnow().timestamp())}"
        
        # Execute the approved action
        action_request = AgentActionRequest(
            action=AgentAction(action),
            reason=f"Admin approved: {approval_notes}",
            admin_id=current_user["id"],
            approval_id=approval_id
        )
        
        result = await agent_lifecycle_manager.execute_agent_action(
            agent_id,
            action_request
        )
        
        if telemetry_manager:
            await telemetry_manager.record_event(
                "agent_action_approved",
                {
                    "agent_id": agent_id,
                    "action": action,
                    "approved_by": current_user["id"],
                    "approval_id": approval_id
                }
            )
        
        return {
            **result,
            "approval_id": approval_id,
            "approved_by": current_user["username"],
            "approval_timestamp": datetime.utcnow().isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {action}"
        )
    except Exception as e:
        logger.error(f"Failed to approve action for agent {agent_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve action: {str(e)}"
        )


# Import the new types at the top of app.py
from agent_lifecycle_manager import AgentStatus, AgentAction, AgentActionRequest
