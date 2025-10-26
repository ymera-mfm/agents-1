import { apiService } from '../../services/api';

describe('API Service', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  describe('request', () => {
    it('makes successful API requests', async () => {
      const mockData = { success: true, data: { id: 1 } };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      const result = await apiService.request('/test');
      expect(result).toEqual(mockData);
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/test'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      );
    });

    it('includes authorization header when token is set', async () => {
      const mockData = { success: true };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      apiService.setToken('test-token');
      await apiService.request('/test');

      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      );
    });

    it('retries failed requests', async () => {
      fetch
        .mockRejectedValueOnce(new Error('Network error'))
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        });

      const result = await apiService.request('/test');
      expect(result).toEqual({ success: true });
      expect(fetch).toHaveBeenCalledTimes(3);
    });

    it('throws error after max retry attempts', async () => {
      fetch.mockRejectedValue(new Error('Network error'));

      await expect(apiService.request('/test')).rejects.toThrow('Network error');
      expect(fetch).toHaveBeenCalledTimes(3); // CONFIG.RETRY_ATTEMPTS
    });

    it('handles HTTP errors', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        statusText: 'Not Found',
      });

      await expect(apiService.request('/test')).rejects.toThrow('HTTP 404');
    });
  });

  describe('login', () => {
    it('sends login credentials', async () => {
      const mockResponse = { token: 'test-token', user: { id: 1 } };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await apiService.login('user', 'pass');
      expect(result).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ username: 'user', password: 'pass' }),
        })
      );
    });
  });

  describe('getAgents', () => {
    it('fetches agents list', async () => {
      const mockAgents = [{ id: 1, name: 'Agent 1' }];
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockAgents,
      });

      const result = await apiService.getAgents();
      expect(result).toEqual(mockAgents);
      expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/agents'), expect.any(Object));
    });
  });

  describe('getProjects', () => {
    it('fetches projects list', async () => {
      const mockProjects = [{ id: 1, name: 'Project 1' }];
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProjects,
      });

      const result = await apiService.getProjects();
      expect(result).toEqual(mockProjects);
    });
  });

  describe('updateProject', () => {
    it('updates project data', async () => {
      const mockProject = { id: 1, name: 'Updated Project' };
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockProject,
      });

      const result = await apiService.updateProject(1, { name: 'Updated Project' });
      expect(result).toEqual(mockProject);
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/projects/1'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ name: 'Updated Project' }),
        })
      );
    });
  });
});
