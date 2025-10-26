import {
  validateEmail,
  validatePassword,
  validateUrl,
  sanitizeInput,
  validateProjectName,
  validateAgentName,
} from '../../utils/validation';

describe('Validation Utils', () => {
  describe('validateEmail', () => {
    it('validates correct email addresses', () => {
      expect(validateEmail('user@example.com')).toBe(true);
      expect(validateEmail('test.user+tag@example.co.uk')).toBe(true);
      expect(validateEmail('user123@test-domain.com')).toBe(true);
    });

    it('rejects invalid email addresses', () => {
      expect(validateEmail('invalid')).toBe(false);
      expect(validateEmail('user@')).toBe(false);
      expect(validateEmail('@example.com')).toBe(false);
      expect(validateEmail('user @example.com')).toBe(false);
      expect(validateEmail('')).toBe(false);
    });
  });

  describe('validatePassword', () => {
    it('validates strong passwords', () => {
      expect(validatePassword('Password123!')).toBe(true);
      expect(validatePassword('MyP@ssw0rd')).toBe(true);
      expect(validatePassword('Str0ng!Pass')).toBe(true);
    });

    it('rejects weak passwords', () => {
      expect(validatePassword('short')).toBe(false);
      expect(validatePassword('nouppercase1!')).toBe(false);
      expect(validatePassword('NOLOWERCASE1!')).toBe(false);
      expect(validatePassword('NoSpecialChar1')).toBe(false);
      expect(validatePassword('NoNumbers!')).toBe(false);
      expect(validatePassword('')).toBe(false);
    });

    it('requires minimum length', () => {
      expect(validatePassword('Sh0rt!')).toBe(false);
      expect(validatePassword('LongEnough1!')).toBe(true);
    });
  });

  describe('validateUrl', () => {
    it('validates correct URLs', () => {
      expect(validateUrl('https://example.com')).toBe(true);
      expect(validateUrl('http://test.com/path')).toBe(true);
      expect(validateUrl('https://sub.domain.com:8080/path?query=1')).toBe(true);
    });

    it('rejects invalid URLs', () => {
      expect(validateUrl('not a url')).toBe(false);
      expect(validateUrl('htp://wrong-protocol.com')).toBe(false);
      expect(validateUrl('')).toBe(false);
    });

    it('allows custom protocols when specified', () => {
      expect(validateUrl('ws://websocket.com', ['ws', 'wss'])).toBe(true);
      expect(validateUrl('ftp://ftp.server.com', ['ftp'])).toBe(true);
    });
  });

  describe('sanitizeInput', () => {
    it('removes HTML tags', () => {
      expect(sanitizeInput('<script>alert("xss")</script>')).toBe('');
      expect(sanitizeInput('<div>Hello</div>')).toBe('Hello');
      expect(sanitizeInput('Normal text')).toBe('Normal text');
    });

    it('escapes special characters', () => {
      expect(sanitizeInput('Test & Co.')).not.toContain('&');
      expect(sanitizeInput('Price < 100')).not.toContain('<');
      expect(sanitizeInput('x > y')).not.toContain('>');
    });

    it('trims whitespace', () => {
      expect(sanitizeInput('  spaced  ')).toBe('spaced');
      expect(sanitizeInput('\n\ttext\n')).toBe('text');
    });

    it('handles empty and null values', () => {
      expect(sanitizeInput('')).toBe('');
      expect(sanitizeInput(null)).toBe('');
      expect(sanitizeInput(undefined)).toBe('');
    });
  });

  describe('validateProjectName', () => {
    it('validates correct project names', () => {
      expect(validateProjectName('my-project')).toBe(true);
      expect(validateProjectName('Project_123')).toBe(true);
      expect(validateProjectName('valid-project-name')).toBe(true);
    });

    it('rejects invalid project names', () => {
      expect(validateProjectName('')).toBe(false);
      expect(validateProjectName('a')).toBe(false); // too short
      expect(validateProjectName('project with spaces')).toBe(false);
      expect(validateProjectName('project@name')).toBe(false);
      expect(validateProjectName('a'.repeat(100))).toBe(false); // too long
    });

    it('requires minimum length', () => {
      expect(validateProjectName('ab')).toBe(false);
      expect(validateProjectName('abc')).toBe(true);
    });
  });

  describe('validateAgentName', () => {
    it('validates correct agent names', () => {
      expect(validateAgentName('agent-1')).toBe(true);
      expect(validateAgentName('MyAgent')).toBe(true);
      expect(validateAgentName('test_agent_123')).toBe(true);
    });

    it('rejects invalid agent names', () => {
      expect(validateAgentName('')).toBe(false);
      expect(validateAgentName('a')).toBe(false);
      expect(validateAgentName('agent name')).toBe(false);
      expect(validateAgentName('agent@123')).toBe(false);
    });
  });
});
