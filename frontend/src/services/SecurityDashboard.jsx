import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Shield, Lock, Key, UserCheck, AlertTriangle, CheckCircle } from 'lucide-react';

// components/SecurityDashboard.jsx
export const SecurityDashboard = () => {
  const [securityStatus] = useState({
    twoFactor: false,
    encryption: true,
    auditLogs: true,
    apiSecurity: true,
    threatLevel: 'low',
  });

  const [accessLogs, setAccessLogs] = useState([]);
  const [securityAlerts, setSecurityAlerts] = useState([]);

  useEffect(() => {
    // Simulate fetching security data
    const mockAccessLogs = [
      {
        id: 1,
        user: 'admin',
        action: 'login',
        timestamp: new Date(),
        ip: '192.168.1.1',
        status: 'success',
      },
      {
        id: 2,
        user: 'user1',
        action: 'file_access',
        timestamp: new Date(),
        ip: '192.168.1.2',
        status: 'success',
      },
      {
        id: 3,
        user: 'unknown',
        action: 'login_attempt',
        timestamp: new Date(),
        ip: '192.168.1.100',
        status: 'failed',
      },
    ];

    const mockAlerts = [
      {
        id: 1,
        type: 'suspicious_login',
        severity: 'medium',
        message: 'Multiple failed login attempts from IP 192.168.1.100',
        timestamp: new Date(),
      },
    ];

    setAccessLogs(mockAccessLogs);
    setSecurityAlerts(mockAlerts);
  }, []);

  const SecurityStatusCard = ({ title, status, description, icon: Icon }) => (
    <motion.div
      className={`p-6 rounded-xl border-2 ${
        status ? 'border-green-500/50 bg-green-500/10' : 'border-red-500/50 bg-red-500/10'
      }`}
      whileHover={{ scale: 1.02 }}
    >
      <div className="flex items-center space-x-3 mb-3">
        <div
          className={`w-12 h-12 rounded-lg flex items-center justify-center ${
            status ? 'bg-green-500/20' : 'bg-red-500/20'
          }`}
        >
          <Icon className={`w-6 h-6 ${status ? 'text-green-400' : 'text-red-400'}`} />
        </div>
        <div>
          <h4 className="text-lg font-semibold text-white">{title}</h4>
          <p className="text-sm text-gray-400">{description}</p>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <span className={`text-sm font-semibold ${status ? 'text-green-400' : 'text-red-400'}`}>
          {status ? 'Secure' : 'Attention Required'}
        </span>
        {status ? (
          <CheckCircle className="w-5 h-5 text-green-400" />
        ) : (
          <AlertTriangle className="w-5 h-5 text-red-400" />
        )}
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold text-white">Security Center</h3>
          <p className="text-gray-400">Monitor and manage platform security</p>
        </div>

        <div className="flex items-center space-x-3">
          <button className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white hover:bg-white/10 transition">
            Run Security Scan
          </button>
          <button className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg hover:from-cyan-600 hover:to-blue-700 transition">
            Security Settings
          </button>
        </div>
      </div>

      {/* Security Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <SecurityStatusCard
          title="Two-Factor Auth"
          status={securityStatus.twoFactor}
          description="Extra layer of security"
          icon={Shield}
        />
        <SecurityStatusCard
          title="Data Encryption"
          status={securityStatus.encryption}
          description="All data encrypted at rest"
          icon={Lock}
        />
        <SecurityStatusCard
          title="Audit Logs"
          status={securityStatus.auditLogs}
          description="Complete activity tracking"
          icon={Key}
        />
        <SecurityStatusCard
          title="API Security"
          status={securityStatus.apiSecurity}
          description="Protected API endpoints"
          icon={UserCheck}
        />
      </div>

      {/* Security Alerts */}
      {securityAlerts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="backdrop-blur-xl bg-red-500/10 border border-red-500/20 rounded-xl p-6"
        >
          <div className="flex items-center space-x-3 mb-4">
            <AlertTriangle className="w-6 h-6 text-red-400" />
            <h4 className="text-lg font-semibold text-white">Security Alerts</h4>
          </div>

          <div className="space-y-3">
            {securityAlerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-center justify-between p-3 bg-red-500/10 rounded-lg"
              >
                <div>
                  <div className="text-white font-medium">{alert.message}</div>
                  <div className="text-sm text-red-300">
                    {alert.timestamp.toLocaleString()} • {alert.severity} severity
                  </div>
                </div>
                <button className="text-red-400 hover:text-red-300 text-sm">Investigate</button>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Access Logs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
          <h4 className="text-lg font-semibold text-white mb-4">Recent Access Logs</h4>

          <div className="space-y-2">
            {accessLogs.map((log) => (
              <div
                key={log.id}
                className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
              >
                <div>
                  <div className="text-white font-medium">{log.user}</div>
                  <div className="text-sm text-gray-400">
                    {log.action} • {log.ip}
                  </div>
                </div>
                <div className="text-right">
                  <div
                    className={`text-sm font-semibold ${
                      log.status === 'success' ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    {log.status}
                  </div>
                  <div className="text-xs text-gray-400">{log.timestamp.toLocaleTimeString()}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Security Recommendations */}
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
          <h4 className="text-lg font-semibold text-white mb-4">Security Recommendations</h4>

          <div className="space-y-4">
            {!securityStatus.twoFactor && (
              <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Shield className="w-5 h-5 text-yellow-400" />
                  <div>
                    <div className="text-yellow-400 font-semibold">
                      Enable Two-Factor Authentication
                    </div>
                    <div className="text-yellow-300 text-sm">
                      Add an extra layer of security to your account
                    </div>
                  </div>
                </div>
                <button className="mt-3 w-full px-4 py-2 bg-yellow-500/20 text-yellow-400 rounded-lg hover:bg-yellow-500/30 transition">
                  Enable 2FA
                </button>
              </div>
            )}

            <div className="p-4 bg-cyan-500/10 border border-cyan-500/20 rounded-lg">
              <div className="flex items-center space-x-3">
                <Key className="w-5 h-5 text-cyan-400" />
                <div>
                  <div className="text-cyan-400 font-semibold">Rotate API Keys</div>
                  <div className="text-cyan-300 text-sm">It's been 90 days since last rotation</div>
                </div>
              </div>
              <button className="mt-3 w-full px-4 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg hover:bg-cyan-500/30 transition">
                Rotate Keys
              </button>
            </div>

            <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg">
              <div className="flex items-center space-x-3">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <div>
                  <div className="text-green-400 font-semibold">Security Scan Complete</div>
                  <div className="text-green-300 text-sm">
                    Last scan: 2 hours ago • No critical issues found
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Threat Level Indicator */}
      <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-lg font-semibold text-white">Threat Level Monitoring</h4>
          <div
            className={`px-3 py-1 rounded-full text-sm font-semibold ${
              securityStatus.threatLevel === 'low'
                ? 'bg-green-500/20 text-green-400'
                : securityStatus.threatLevel === 'medium'
                  ? 'bg-yellow-500/20 text-yellow-400'
                  : 'bg-red-500/20 text-red-400'
            }`}
          >
            {securityStatus.threatLevel.toUpperCase()} THREAT LEVEL
          </div>
        </div>

        <div className="w-full bg-gray-700 rounded-full h-3 mb-2">
          <div
            className="h-3 rounded-full transition-all duration-500"
            style={{
              width:
                securityStatus.threatLevel === 'low'
                  ? '25%'
                  : securityStatus.threatLevel === 'medium'
                    ? '60%'
                    : '90%',
              backgroundColor:
                securityStatus.threatLevel === 'low'
                  ? '#10b981'
                  : securityStatus.threatLevel === 'medium'
                    ? '#eab308'
                    : '#ef4444',
            }}
          />
        </div>

        <div className="flex justify-between text-sm text-gray-400">
          <span>Low</span>
          <span>Medium</span>
          <span>High</span>
          <span>Critical</span>
        </div>
      </div>
    </div>
  );
};
