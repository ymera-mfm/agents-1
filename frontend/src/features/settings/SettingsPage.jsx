import React, { useState } from 'react';
import { useApp } from '../../store/AppContext';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

export const SettingsPage = () => {
  const { user } = useApp();
  const [settings, setSettings] = useState({
    notifications: true,
    autoSave: true,
    darkMode: true,
    language: 'en',
  });

  const handleSettingChange = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  if (!user) {
    return <LoadingSpinner />;
  }

  return (
    <div className="min-h-screen pt-24 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <div className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-8">
          <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
          <p className="text-gray-400 mb-8">Customize your AgentFlow experience</p>

          <div className="space-y-6">
            <div className="p-6 bg-white/5 rounded-xl border border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">Preferences</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-white">Notifications</h4>
                    <p className="text-sm text-gray-400">Receive updates about agent activities</p>
                  </div>
                  <button
                    onClick={() => handleSettingChange('notifications', !settings.notifications)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
                      settings.notifications ? 'bg-cyan-500' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                        settings.notifications ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-white">Auto Save</h4>
                    <p className="text-sm text-gray-400">Automatically save your work</p>
                  </div>
                  <button
                    onClick={() => handleSettingChange('autoSave', !settings.autoSave)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
                      settings.autoSave ? 'bg-cyan-500' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                        settings.autoSave ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-white">Dark Mode</h4>
                    <p className="text-sm text-gray-400">Use dark theme</p>
                  </div>
                  <button
                    onClick={() => handleSettingChange('darkMode', !settings.darkMode)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition ${
                      settings.darkMode ? 'bg-cyan-500' : 'bg-gray-600'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
                        settings.darkMode ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-white">Language</h4>
                    <p className="text-sm text-gray-400">Interface language</p>
                  </div>
                  <select
                    value={settings.language}
                    onChange={(e) => handleSettingChange('language', e.target.value)}
                    className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  >
                    <option value="en">English</option>
                    <option value="es">Español</option>
                    <option value="fr">Français</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="p-6 bg-white/5 rounded-xl border border-white/10">
              <h3 className="text-xl font-bold text-white mb-4">Account</h3>
              <div className="space-y-4">
                <button className="w-full text-left p-4 bg-white/5 rounded-lg hover:bg-white/10 transition text-white">
                  Change Password
                </button>
                <button className="w-full text-left p-4 bg-white/5 rounded-lg hover:bg-white/10 transition text-white">
                  Export Data
                </button>
                <button className="w-full text-left p-4 bg-red-500/10 rounded-lg hover:bg-red-500/20 transition text-red-400">
                  Delete Account
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
