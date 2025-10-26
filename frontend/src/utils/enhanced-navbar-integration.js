// src/components/NavBar.jsx - Enhanced Enterprise Version with StatusAvatar
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../store/auth';
import { useAgentStatus, AgentStatus } from '../store/agent-status';
import StatusAvatar from './StatusAvatar';
import {
  Menu,
  X,
  User,
  Settings,
  LogOut,
  Bell,
  Search,
  Shield,
  Activity,
  Zap,
  Brain,
} from 'lucide-react';
import clsx from 'clsx';

// Enhanced notification component with real-time updates
const NotificationIndicator = () => {
  // eslint-disable-next-line no-unused-vars
  const { notificationCount, notifications } = useAgentStatus(); // notifications used by parent component
  const [hasNewNotifications, setHasNewNotifications] = useState(false);

  useEffect(() => {
    if (notificationCount > 0) {
      setHasNewNotifications(true);
      const timer = setTimeout(() => setHasNewNotifications(false), 3000);
      return () => clearTimeout(timer);
    }
  }, [notificationCount]);

  if (notificationCount === 0) {
    return null;
  }

  return (
    <motion.div
      className="relative"
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: 'spring', stiffness: 300 }}
    >
      <div
        className={clsx(
          'absolute -top-1 -right-1 rounded-full text-xs font-bold text-white flex items-center justify-center min-w-[18px] h-[18px] px-1',
          hasNewNotifications
            ? 'bg-red-500 animate-pulse shadow-lg shadow-red-500/50'
            : 'bg-red-500'
        )}
      >
        {notificationCount > 99 ? '99+' : notificationCount}
      </div>

      {/* Pulse animation for new notifications */}
      {hasNewNotifications && (
        <motion.div
          className="absolute -top-1 -right-1 w-[18px] h-[18px] bg-red-500/30 rounded-full"
          animate={{
            scale: [1, 1.8, 1],
            opacity: [0.7, 0, 0.7],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeOut',
          }}
        />
      )}
    </motion.div>
  );
};

// Enhanced search component with AI suggestions
const SmartSearch = ({ isExpanded, onToggle }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      setQuery('');
      onToggle();
    }
  };

  // Simulate AI-powered search suggestions
  useEffect(() => {
    if (query.length > 2) {
      const mockSuggestions = [
        'Optimize dashboard layout',
        'Agent performance metrics',
        'User behavior analytics',
        'Accessibility audit results',
      ].filter((s) => s.toLowerCase().includes(query.toLowerCase()));

      setSuggestions(mockSuggestions);
    } else {
      setSuggestions([]);
    }
  }, [query]);

  return (
    <div className="relative">
      <motion.button
        type="button"
        onClick={onToggle}
        className="p-2 rounded-full text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all duration-200 group"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        aria-label="Smart Search"
      >
        <Search className="w-5 h-5" />

        {/* Search enhancement indicator */}
        <motion.div
          className="absolute -top-1 -right-1 w-2 h-2 bg-ymera-glow rounded-full opacity-60"
          animate={{ scale: [1, 1.2, 1], opacity: [0.6, 1, 0.6] }}
          transition={{ duration: 2, repeat: Infinity }}
        />
      </motion.button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            className="absolute top-full mt-2 right-0 w-96 bg-slate-900/95 backdrop-blur-xl border border-ymera-glow/20 rounded-xl shadow-2xl z-50"
          >
            <form onSubmit={handleSearch} className="p-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search with AI assistance..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-600 rounded-lg 
                           text-slate-100 placeholder-slate-400 focus:outline-none focus:border-ymera-glow/50 
                           focus:ring-1 focus:ring-ymera-glow/25 transition-all"
                  autoFocus
                />
                <Brain className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-ymera-glow/50" />
              </div>

              {/* AI Suggestions */}
              {suggestions.length > 0 && (
                <motion.div
                  className="mt-3 space-y-1"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <p className="text-xs text-slate-400 mb-2">AI Suggestions:</p>
                  {suggestions.map((suggestion, index) => (
                    <motion.button
                      key={suggestion}
                      type="button"
                      onClick={() => {
                        setQuery(suggestion);
                        handleSearch({ preventDefault: () => {} });
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800/50 rounded-lg transition-colors"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Zap className="inline w-3 h-3 mr-2 text-ymera-glow" />
                      {suggestion}
                    </motion.button>
                  ))}
                </motion.div>
              )}
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Navigation items with enhanced metadata
const navigation = [
  { name: 'Dashboard', href: '/', public: false, protected: true, icon: Activity },
  { name: 'Agents', href: '/agents', public: false, protected: true, icon: Brain },
  { name: 'Analytics', href: '/analytics', public: false, protected: true, icon: Activity },
  { name: 'Settings', href: '/settings', public: false, protected: true, icon: Settings },
  { name: 'Help', href: '/help', public: true, protected: false, icon: Shield },
];

export default function NavBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout, isAdmin } = useAuth();
  // eslint-disable-next-line no-unused-vars
  const { status, notificationCount } = useAgentStatus(); // notificationCount displayed in UI

  // Component state
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isSearchExpanded, setIsSearchExpanded] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  // Memoized visible navigation items
  const visibleNavItems = useMemo(
    () =>
      navigation.filter(
        (item) =>
          item.public || (item.protected && isAuthenticated()) || (item.adminOnly && isAdmin())
      ),
    [isAuthenticated, isAdmin]
  );

  // Scroll detection for navbar styling
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close menus on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
    setIsUserMenuOpen(false);
    setIsSearchExpanded(false);
  }, [location.pathname]);

  // Handle logout
  const handleLogout = useCallback(() => {
    logout();
    setIsUserMenuOpen(false);
    navigate('/login');
  }, [logout, navigate]);

  // Handle outside clicks
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        isUserMenuOpen &&
        !event.target.closest('#user-menu-button') &&
        !event.target.closest('[role="menu"]')
      ) {
        setIsUserMenuOpen(false);
      }
      if (isSearchExpanded && !event.target.closest('.search-container')) {
        setIsSearchExpanded(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isUserMenuOpen, isSearchExpanded]);

  return (
    <>
      {/* Desktop Navbar */}
      <motion.nav
        className={clsx(
          'fixed top-0 left-0 right-0 z-40 transition-all duration-300',
          isScrolled
            ? 'backdrop-blur-xl bg-black/80 shadow-2xl border-b border-ymera-glow/20'
            : 'backdrop-blur-md bg-black/60 shadow-lg border-b border-ymera-glow/10'
        )}
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Primary Navigation */}
            <div className="flex items-center space-x-8">
              <Link
                to="/"
                className="flex items-center space-x-2 text-2xl font-bold text-ymera-glow hover:text-white transition-colors group"
              >
                <motion.div
                  className="w-8 h-8 bg-gradient-to-br from-ymera-glow to-ymera-accent rounded-lg flex items-center justify-center"
                  whileHover={{ rotate: 360, scale: 1.1 }}
                  transition={{ duration: 0.6, ease: 'easeInOut' }}
                >
                  <Brain className="w-5 h-5 text-black" />
                </motion.div>
                <span className="group-hover:tracking-wider transition-all duration-300">
                  Ymera
                </span>
              </Link>

              {/* Desktop Navigation Links */}
              <div className="hidden md:flex items-center space-x-1">
                {visibleNavItems.slice(0, 5).map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={clsx(
                      'relative px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 group',
                      location.pathname === item.href
                        ? 'text-ymera-glow bg-ymera-glow/10 shadow-lg'
                        : 'text-slate-300 hover:text-ymera-glow hover:bg-slate-800/40'
                    )}
                  >
                    <div className="flex items-center space-x-2">
                      {item.icon && <item.icon size={16} />}
                      <span>{item.name}</span>
                    </div>

                    {/* Active indicator */}
                    {location.pathname === item.href && (
                      <motion.div
                        className="absolute inset-0 bg-ymera-glow/5 rounded-lg border border-ymera-glow/20"
                        layoutId="activeNavItem"
                        transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                      />
                    )}
                  </Link>
                ))}
              </div>
            </div>

            {/* Right Side: Search, Notifications, Avatar, User Menu */}
            <div className="hidden md:flex items-center space-x-4">
              {/* Smart Search */}
              <div className="search-container">
                <SmartSearch
                  isExpanded={isSearchExpanded}
                  onToggle={() => setIsSearchExpanded(!isSearchExpanded)}
                />
              </div>

              {/* Notifications with enhanced indicator */}
              <div className="relative">
                <motion.button
                  type="button"
                  onClick={() => navigate('/notifications')}
                  className="relative p-2 rounded-full text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all duration-200"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  aria-label="Notifications"
                >
                  <Bell className="w-5 h-5" />
                  <NotificationIndicator />
                </motion.button>
              </div>

              {/* Enhanced StatusAvatar Integration */}
              {isAuthenticated() && (
                <div className="flex items-center space-x-3">
                  {/* Agent Status Info */}
                  <motion.div
                    className="hidden lg:flex items-center space-x-2 px-3 py-1 bg-slate-800/30 rounded-full border border-slate-700/50"
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 }}
                  >
                    <div
                      className={clsx('w-2 h-2 rounded-full', {
                        'bg-green-400 animate-pulse': status === AgentStatus.IDLE,
                        'bg-ymera-glow animate-pulse':
                          status === AgentStatus.RUNNING || status === AgentStatus.PROCESSING,
                        'bg-yellow-400 animate-pulse': status === AgentStatus.ALERT,
                        'bg-red-400 animate-pulse': status === AgentStatus.ERROR,
                        'bg-slate-400': status === AgentStatus.OFFLINE,
                      })}
                    />
                    <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">
                      {status === AgentStatus.RUNNING
                        ? 'Active'
                        : status === AgentStatus.PROCESSING
                          ? 'Analyzing'
                          : status === AgentStatus.IDLE
                            ? 'Ready'
                            : status}
                    </span>
                  </motion.div>

                  {/* StatusAvatar */}
                  <StatusAvatar
                    size="md"
                    className="ring-2 ring-offset-2 ring-offset-black ring-slate-600/30 hover:ring-ymera-glow/50 transition-all duration-300"
                  />
                </div>
              )}

              {/* User Menu Dropdown */}
              {isAuthenticated() && (
                <div className="relative">
                  <motion.button
                    type="button"
                    className="flex items-center space-x-2 px-3 py-2 rounded-lg text-sm bg-slate-800/30 hover:bg-slate-800/50 border border-slate-700/50 hover:border-ymera-glow/30 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black focus:ring-ymera-glow/50 transition-all duration-200"
                    id="user-menu-button"
                    aria-expanded={isUserMenuOpen}
                    aria-haspopup="true"
                    onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <User className="w-4 h-4 text-slate-400" />
                    <span className="text-slate-300 font-medium">
                      {user?.name?.split(' ')[0] ||
                        (user?.email && user.email.includes('@')
                          ? user.email.split('@')[0]
                          : 'User')}
                    </span>
                    <motion.div
                      animate={{ rotate: isUserMenuOpen ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <svg
                        className="w-4 h-4 text-slate-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M19 9l-7 7-7-7"
                        />
                      </svg>
                    </motion.div>
                  </motion.button>

                  {/* Enhanced User Menu Dropdown */}
                  <AnimatePresence>
                    {isUserMenuOpen && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -10 }}
                        transition={{ duration: 0.15 }}
                        className="absolute right-0 mt-2 w-64 bg-slate-900/95 backdrop-blur-xl rounded-xl shadow-2xl border border-ymera-glow/20 z-50"
                        role="menu"
                        aria-orientation="vertical"
                        aria-labelledby="user-menu-button"
                      >
                        {/* User Info Header */}
                        <div className="px-4 py-3 border-b border-slate-700/50">
                          <div className="flex items-center space-x-3">
                            <img
                              className="w-10 h-10 rounded-full ring-2 ring-ymera-glow/30"
                              src={
                                user?.avatar_url ||
                                `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.name || 'U')}&background=64f4ac&color=000000`
                              }
                              alt="User avatar"
                            />
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-slate-100 truncate">
                                {user?.name || user?.email}
                              </p>
                              <div className="flex items-center space-x-2">
                                <span
                                  className={clsx(
                                    'text-xs font-medium px-2 py-0.5 rounded-full',
                                    user?.role === 'admin'
                                      ? 'bg-red-500/20 text-red-400'
                                      : user?.role === 'moderator'
                                        ? 'bg-yellow-500/20 text-yellow-400'
                                        : 'bg-ymera-glow/20 text-ymera-glow'
                                  )}
                                >
                                  {user?.role || 'user'}
                                </span>
                                {status !== AgentStatus.OFFLINE && (
                                  <div className="flex items-center space-x-1">
                                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                                    <span className="text-xs text-slate-400">Online</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Agent Status Section */}
                        <div className="px-4 py-2 border-b border-slate-700/50">
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-slate-400 flex items-center space-x-1">
                              <Brain className="w-3 h-3" />
                              <span>Agent Status</span>
                            </span>
                            <span
                              className={clsx('font-medium uppercase tracking-wider', {
                                'text-green-400': status === AgentStatus.IDLE,
                                'text-ymera-glow':
                                  status === AgentStatus.RUNNING ||
                                  status === AgentStatus.PROCESSING,
                                'text-yellow-400': status === AgentStatus.ALERT,
                                'text-red-400': status === AgentStatus.ERROR,
                                'text-slate-400': status === AgentStatus.OFFLINE,
                              })}
                            >
                              {status}
                            </span>
                          </div>
                        </div>

                        {/* Menu Items */}
                        <div className="py-1">
                          <Link
                            to="/profile"
                            onClick={() => setIsUserMenuOpen(false)}
                            className="flex items-center px-4 py-2 text-sm text-slate-300 hover:bg-slate-800/50 hover:text-ymera-glow transition-colors"
                            role="menuitem"
                          >
                            <User className="w-4 h-4 mr-3" />
                            Profile & Account
                          </Link>

                          <Link
                            to="/settings"
                            onClick={() => setIsUserMenuOpen(false)}
                            className="flex items-center px-4 py-2 text-sm text-slate-300 hover:bg-slate-800/50 hover:text-ymera-glow transition-colors"
                            role="menuitem"
                          >
                            <Settings className="w-4 h-4 mr-3" />
                            Settings & Preferences
                          </Link>

                          <Link
                            to="/agent-dashboard"
                            onClick={() => setIsUserMenuOpen(false)}
                            className="flex items-center px-4 py-2 text-sm text-slate-300 hover:bg-slate-800/50 hover:text-ymera-glow transition-colors"
                            role="menuitem"
                          >
                            <Brain className="w-4 h-4 mr-3" />
                            Agent Dashboard
                          </Link>

                          {isAdmin() && (
                            <Link
                              to="/admin"
                              onClick={() => setIsUserMenuOpen(false)}
                              className="flex items-center px-4 py-2 text-sm text-orange-300 hover:bg-orange-500/10 hover:text-orange-400 transition-colors"
                              role="menuitem"
                            >
                              <Shield className="w-4 h-4 mr-3" />
                              Admin Panel
                            </Link>
                          )}
                        </div>

                        {/* Logout Section */}
                        <div className="border-t border-slate-700/50 py-1">
                          <button
                            onClick={handleLogout}
                            className="flex items-center w-full px-4 py-2 text-sm text-red-300 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                            role="menuitem"
                          >
                            <LogOut className="w-4 h-4 mr-3" />
                            Sign Out
                          </button>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* Login/Register buttons for unauthenticated users */}
              {!isAuthenticated() && (
                <div className="flex items-center space-x-3">
                  <Link
                    to="/login"
                    className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/register"
                    className="px-4 py-2 text-sm font-medium bg-ymera-glow hover:bg-ymera-accent text-black rounded-lg transition-all duration-200 hover:scale-105"
                  >
                    Sign Up
                  </Link>
                </div>
              )}
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden flex items-center space-x-2">
              {isAuthenticated() && <StatusAvatar size="sm" />}

              <motion.button
                type="button"
                className="inline-flex items-center justify-center p-2 rounded-md text-slate-400 hover:text-white hover:bg-slate-700/50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black focus:ring-ymera-glow"
                aria-controls="mobile-menu"
                aria-expanded={isMobileMenuOpen}
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <span className="sr-only">Open main menu</span>
                <AnimatePresence mode="wait" initial={false}>
                  {isMobileMenuOpen ? (
                    <motion.div
                      key="close"
                      initial={{ rotate: -90, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      exit={{ rotate: 90, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <X className="block h-6 w-6" />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="menu"
                      initial={{ rotate: 90, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      exit={{ rotate: -90, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <Menu className="block h-6 w-6" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.button>
            </div>
          </div>
        </div>

        {/* Enhanced Mobile Menu */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.div
              id="mobile-menu"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
              className="md:hidden border-t border-slate-700/50 bg-slate-900/95 backdrop-blur-xl"
            >
              <div className="px-4 pt-4 pb-3 space-y-3">
                {/* Mobile Search */}
                <div className="relative mb-4">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search with AI..."
                    className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-600 rounded-lg 
                             text-slate-100 placeholder-slate-400 focus:outline-none focus:border-ymera-glow/50 
                             focus:ring-1 focus:ring-ymera-glow/25 transition-colors"
                  />
                  <Brain className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-ymera-glow/50" />
                </div>

                {/* Navigation Links */}
                <div className="space-y-1">
                  {visibleNavItems.map((item, index) => (
                    <motion.div
                      key={item.name}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Link
                        to={item.href}
                        className={clsx(
                          'flex items-center space-x-3 px-3 py-3 text-base font-medium rounded-lg transition-all',
                          location.pathname === item.href
                            ? 'text-ymera-glow bg-ymera-glow/10 border border-ymera-glow/20'
                            : 'text-slate-300 hover:text-ymera-glow hover:bg-slate-800/50'
                        )}
                      >
                        {item.icon && <item.icon size={20} />}
                        <span>{item.name}</span>
                        {location.pathname === item.href && (
                          <div className="ml-auto w-2 h-2 bg-ymera-glow rounded-full" />
                        )}
                      </Link>
                    </motion.div>
                  ))}
                </div>

                {/* Mobile User Section */}
                {isAuthenticated() && (
                  <motion.div
                    className="pt-4 border-t border-slate-700/50"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.2 }}
                  >
                    <div className="flex items-center space-x-3 px-3 py-3 bg-slate-800/30 rounded-lg">
                      <img
                        className="w-10 h-10 rounded-full ring-2 ring-ymera-glow/30"
                        src={
                          user?.avatar_url ||
                          `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.name || 'U')}&background=64f4ac&color=000000`
                        }
                        alt="User avatar"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-100 truncate">
                          {user?.name || user?.email}
                        </p>
                        <p className="text-xs text-ymera-glow font-medium">
                          Agent: {status.toUpperCase()}
                        </p>
                      </div>
                      <button
                        onClick={handleLogout}
                        className="p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
                      >
                        <LogOut size={16} />
                      </button>
                    </div>
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.nav>

      {/* Spacer to prevent content from being hidden behind fixed navbar */}
      <div className="h-16" />
    </>
  );
}
