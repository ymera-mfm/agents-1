import React, { useState } from 'react';
import { useApp } from '../../store/AppContext';
import { ParticleBackground } from '../../components/common/ParticleBackground';
import { Zap } from 'lucide-react';

export const LoginPage = () => {
  const { login } = useApp();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e?.preventDefault();

    try {
      setError('');
      setLoading(true);
      await login(username, password);
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <ParticleBackground />
      <div className="max-w-md w-full relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 mb-4 shadow-lg shadow-cyan-500/50 animate-pulse">
            <Zap className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent mb-2">
            AgentFlow
          </h1>
          <p className="text-gray-400 text-lg">AI Project Management Platform</p>
        </div>

        <form
          onSubmit={handleLogin}
          className="backdrop-blur-2xl bg-white/5 border border-white/10 rounded-2xl p-8 shadow-2xl"
        >
          <div className="space-y-6">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-2">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 text-white placeholder-gray-500 transition"
                placeholder="Enter your username"
                disabled={loading}
                required
                minLength={3}
                aria-required="true"
                aria-invalid={error ? 'true' : 'false'}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500 text-white placeholder-gray-500 transition"
                placeholder="Enter your password"
                disabled={loading}
                required
                aria-required="true"
              />
            </div>

            {error && (
              <div
                className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm"
                role="alert"
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !username.trim()}
              className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-semibold rounded-lg hover:from-cyan-600 hover:to-blue-700 transition transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/30"
              aria-busy={loading}
            >
              {loading ? 'Logging in...' : 'Enter AgentFlow'}
            </button>
          </div>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-400">Demo Mode - Enter any username</p>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
