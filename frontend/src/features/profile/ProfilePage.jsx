import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { fetchProfile, updateProfileData, changePassword } from './profileSlice';
import {
  User,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Camera,
  Save,
  CheckCircle,
  AlertCircle,
  Shield,
  Globe,
  Moon,
  Sun,
  Bell,
  Zap,
  Clock,
} from 'lucide-react';

export const ProfilePage = () => {
  const dispatch = useDispatch();
  const { data: profile, status, error } = useSelector((state) => state.profile);
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [passwordData, setPasswordData] = useState({
    current: '',
    new: '',
    confirm: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [activeTab, setActiveTab] = useState('profile');
  const [notificationSettings, setNotificationSettings] = useState({
    email: true,
    push: true,
    agentUpdates: true,
    projectAlerts: true,
  });
  const [theme, setTheme] = useState('dark');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    // In a real app, you would fetch the user ID from auth state
    const userId = 'user-001'; // Replace with actual user ID
    dispatch(fetchProfile(userId));
  }, [dispatch]);

  useEffect(() => {
    if (profile) {
      setEditData(profile);
      if (profile.notifications) {
        setNotificationSettings(profile.notifications);
      }
      if (profile.theme) {
        setTheme(profile.theme);
      }
    }
  }, [profile]);

  const handleSaveProfile = () => {
    dispatch(
      updateProfileData({
        userId: 'user-001', // Replace with actual user ID
        updates: editData,
      })
    ).then(() => {
      setSuccessMessage('Profile updated successfully!');
      setIsEditing(false);
      setTimeout(() => setSuccessMessage(''), 3000);
    });
  };

  const handlePasswordChange = () => {
    if (passwordData.new !== passwordData.confirm) {
      setSuccessMessage('Passwords do not match!');
      return;
    }
    dispatch(
      changePassword({
        currentPassword: passwordData.current,
        newPassword: passwordData.new,
      })
    ).then(() => {
      setSuccessMessage('Password changed successfully!');
      setPasswordData({ current: '', new: '', confirm: '' });
      setTimeout(() => setSuccessMessage(''), 3000);
    });
  };

  const handleNotificationChange = (key) => {
    const updatedSettings = { ...notificationSettings, [key]: !notificationSettings[key] };
    setNotificationSettings(updatedSettings);
    dispatch(
      updateProfileData({
        userId: 'user-001', // Replace with actual user ID
        updates: { notifications: updatedSettings },
      })
    );
  };

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
    dispatch(
      updateProfileData({
        userId: 'user-001', // Replace with actual user ID
        updates: { theme: newTheme },
      })
    );
  };

  if (status === 'loading') {
    return (
      <div className="pt-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto pb-8">
        <div className="text-center py-20">
          <div className="w-12 h-12 mx-auto mb-4 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-gray-400">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (status === 'failed') {
    return (
      <div className="pt-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto pb-8">
        <div className="text-center py-20">
          <AlertCircle size={48} className="mx-auto text-red-500 mb-4" />
          <p className="text-red-400">{error}</p>
          <button
            onClick={() => dispatch(fetchProfile('user-001'))}
            className="mt-4 px-6 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-600 text-white transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="pt-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto pb-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-pink-500 bg-clip-text text-transparent mb-2">
          Profile Settings
        </h1>
        <p className="text-gray-400 text-lg">Manage your account and preferences</p>
      </div>

      {successMessage && (
        <div className="mb-6 p-4 rounded-xl bg-green-500/10 border border-green-500/30 text-green-400 flex items-center gap-2">
          <CheckCircle size={20} />
          <span>{successMessage}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <div className="space-y-2">
            {[
              { id: 'profile', label: 'Profile', icon: User },
              { id: 'security', label: 'Security', icon: Shield },
              { id: 'notifications', label: 'Notifications', icon: Bell },
              { id: 'appearance', label: 'Appearance', icon: Moon },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  activeTab === tab.id
                    ? 'bg-cyan-500/20 border border-cyan-500/30 text-cyan-400'
                    : 'bg-white/5 border border-white/10 text-gray-400 hover:text-cyan-400'
                }`}
              >
                <tab.icon size={20} />
                <span className="font-medium">{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="lg:col-span-3">
          <div
            className="p-8 rounded-2xl"
            style={{
              background: 'rgba(20, 20, 20, 0.9)',
              backdropFilter: 'blur(25px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            {activeTab === 'profile' && (
              <div className="space-y-6">
                <div className="flex items-center gap-6 mb-6">
                  <div className="relative group">
                    <div className="w-24 h-24 rounded-full bg-gradient-to-r from-cyan-400 to-pink-500 flex items-center justify-center text-3xl font-bold">
                      {profile?.name?.charAt(0) || 'U'}
                    </div>
                    <button className="absolute inset-0 rounded-full bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <Camera size={24} className="text-white" />
                    </button>
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white">{profile?.name || 'User'}</h2>
                    <p className="text-gray-400">
                      {profile?.role || 'User'} • Member since{' '}
                      {profile?.joinDate
                        ? new Date(profile.joinDate).toLocaleDateString()
                        : 'Unknown'}
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Full Name</label>
                    <div className="relative">
                      <User
                        size={20}
                        className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500"
                      />
                      <input
                        type="text"
                        value={editData.name || ''}
                        onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                        disabled={!isEditing}
                        className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none transition-colors disabled:opacity-70"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Email Address</label>
                    <div className="relative">
                      <Mail
                        size={20}
                        className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500"
                      />
                      <input
                        type="email"
                        value={editData.email || ''}
                        onChange={(e) => setEditData({ ...editData, email: e.target.value })}
                        disabled={!isEditing}
                        className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none transition-colors disabled:opacity-70"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Role</label>
                    <div className="relative">
                      <User
                        size={20}
                        className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500"
                      />
                      <input
                        type="text"
                        value={editData.role || ''}
                        onChange={(e) => setEditData({ ...editData, role: e.target.value })}
                        disabled={!isEditing}
                        className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none transition-colors disabled:opacity-70"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Bio</label>
                    <textarea
                      value={editData.bio || ''}
                      onChange={(e) => setEditData({ ...editData, bio: e.target.value })}
                      disabled={!isEditing}
                      rows="4"
                      className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none transition-colors disabled:opacity-70 resize-none"
                    />
                  </div>

                  <div className="flex gap-3 pt-4">
                    {isEditing ? (
                      <>
                        <button
                          onClick={handleSaveProfile}
                          className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-600 text-white font-medium transition-colors"
                        >
                          <Save size={20} />
                          <span>Save Changes</span>
                        </button>
                        <button
                          onClick={() => {
                            setEditData(profile);
                            setIsEditing(false);
                          }}
                          className="px-6 py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-white transition-colors"
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => setIsEditing(true)}
                        className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-400 font-medium transition-colors"
                      >
                        <Save size={20} />
                        <span>Edit Profile</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-6">
                <div className="p-6 rounded-xl bg-white/5 border border-white/10">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-bold text-white mb-1">
                        Two-Factor Authentication
                      </h3>
                      <p className="text-sm text-gray-400">
                        Add an extra layer of security to your account
                      </p>
                    </div>
                    <button
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        profile?.twoFactorEnabled ? 'bg-cyan-500' : 'bg-gray-700'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          profile?.twoFactorEnabled ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                  {profile?.twoFactorEnabled && (
                    <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-sm">
                      <Shield size={16} className="inline mr-2" />
                      Two-factor authentication is enabled
                    </div>
                  )}
                </div>

                <div className="p-6 rounded-xl bg-white/5 border border-white/10">
                  <h3 className="text-lg font-bold text-white mb-4">Change Password</h3>
                  <div className="space-y-4">
                    <div className="relative">
                      <Lock
                        size={20}
                        className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500"
                      />
                      <input
                        type={showCurrentPassword ? 'text' : 'password'}
                        placeholder="Current password"
                        value={passwordData.current}
                        onChange={(e) =>
                          setPasswordData({ ...passwordData, current: e.target.value })
                        }
                        className="w-full pl-12 pr-12 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                      >
                        {showCurrentPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                      </button>
                    </div>

                    <div className="relative">
                      <Lock
                        size={20}
                        className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500"
                      />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        placeholder="New password"
                        value={passwordData.new}
                        onChange={(e) => setPasswordData({ ...passwordData, new: e.target.value })}
                        className="w-full pl-12 pr-12 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                      >
                        {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                      </button>
                    </div>

                    <div className="relative">
                      <Lock
                        size={20}
                        className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500"
                      />
                      <input
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Confirm new password"
                        value={passwordData.confirm}
                        onChange={(e) =>
                          setPasswordData({ ...passwordData, confirm: e.target.value })
                        }
                        className="w-full pl-12 pr-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-cyan-400 focus:outline-none"
                      />
                    </div>

                    <button
                      onClick={handlePasswordChange}
                      disabled={
                        !passwordData.new ||
                        !passwordData.confirm ||
                        passwordData.new !== passwordData.confirm
                      }
                      className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-600 text-white font-medium transition-colors disabled:opacity-50"
                    >
                      <Lock size={20} />
                      <span>Change Password</span>
                    </button>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-gray-800/50 border border-gray-700">
                  <div className="flex items-center gap-3 text-sm text-gray-400">
                    <Clock size={16} />
                    <span>
                      Last password change:{' '}
                      {profile?.lastPasswordChange
                        ? new Date(profile.lastPasswordChange).toLocaleDateString()
                        : 'Never'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'notifications' && (
              <div className="space-y-4">
                {[
                  {
                    key: 'email',
                    label: 'Email Notifications',
                    description: 'Receive updates via email',
                    icon: Mail,
                  },
                  {
                    key: 'push',
                    label: 'Push Notifications',
                    description: 'Receive browser notifications',
                    icon: Bell,
                  },
                  {
                    key: 'agentUpdates',
                    label: 'Agent Updates',
                    description: 'Get notified when agents complete tasks',
                    icon: Zap,
                  },
                  {
                    key: 'projectAlerts',
                    label: 'Project Alerts',
                    description: 'Important project milestone notifications',
                    icon: AlertCircle,
                  },
                ].map(({ key, label, description, icon: Icon }) => (
                  <div key={key} className="p-6 rounded-xl bg-white/5 border border-white/10">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="p-3 rounded-lg bg-cyan-500/20 border border-cyan-500/40">
                          <Icon size={20} className="text-cyan-400" />
                        </div>
                        <div>
                          <h3 className="text-lg font-bold text-white mb-1">{label}</h3>
                          <p className="text-sm text-gray-400">{description}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => handleNotificationChange(key)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          notificationSettings[key] ? 'bg-cyan-500' : 'bg-gray-700'
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            notificationSettings[key] ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'appearance' && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-white mb-4">Theme Preference</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                      {
                        id: 'dark',
                        label: 'Dark',
                        icon: Moon,
                        description: 'Dark mode for comfortable viewing',
                      },
                      {
                        id: 'light',
                        label: 'Light',
                        icon: Sun,
                        description: 'Light mode for bright environments',
                      },
                      {
                        id: 'auto',
                        label: 'Auto',
                        icon: Globe,
                        description: 'Sync with system preferences',
                      },
                    ].map(({ id, label, icon: Icon, description }) => (
                      <button
                        key={id}
                        onClick={() => handleThemeChange(id)}
                        className={`p-6 rounded-xl border-2 transition-all ${
                          theme === id
                            ? 'bg-cyan-500/20 border-cyan-500 text-cyan-400'
                            : 'bg-white/5 border-white/10 text-gray-400 hover:border-cyan-500/30'
                        }`}
                      >
                        <Icon size={32} className="mx-auto mb-3" />
                        <div className="font-bold mb-1">{label}</div>
                        <div className="text-xs opacity-75">{description}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-sm">
                  <Zap size={16} className="inline mr-2" />
                  More customization options coming soon
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
