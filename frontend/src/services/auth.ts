import apiClient from './api';

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
  groups: string[];
  user_permissions: string[];
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  organization?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginResponse {
  user: User;
  tokens: AuthTokens;
}

class AuthService {
  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly USER_KEY = 'user';

  // Token management
  getAccessToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  setTokens(tokens: AuthTokens): void {
    localStorage.setItem(this.TOKEN_KEY, tokens.access);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, tokens.refresh);
  }

  clearTokens(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }

  // User management
  getCurrentUser(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }

  setCurrentUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }

  // Authentication methods
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    try {
      const response = await apiClient.post<LoginResponse>('/iam/auth/login/', credentials);

      // Store tokens and user data
      this.setTokens(response.tokens);
      this.setCurrentUser(response.user);

      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  async register(data: RegisterData): Promise<User> {
    try {
      const response = await apiClient.post<User>('/iam/auth/register/', data);
      return response;
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      // Call logout endpoint if it exists
      await apiClient.post('/iam/auth/logout/');
    } catch (error) {
      console.warn('Logout endpoint failed, clearing local data anyway:', error);
    } finally {
      // Always clear local data
      this.clearTokens();
    }
  }

  async refreshToken(): Promise<AuthTokens> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await apiClient.post<AuthTokens>('/iam/auth/refresh/', {
        refresh: refreshToken,
      });

      // Update stored tokens
      this.setTokens(response);
      return response;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Clear tokens if refresh fails
      this.clearTokens();
      throw error;
    }
  }

  // Utility methods
  isAuthenticated(): boolean {
    const token = this.getAccessToken();
    const user = this.getCurrentUser();
    return !!(token && user);
  }

  async getProfile(): Promise<User> {
    try {
      const response = await apiClient.get<User>('/iam/auth/profile/');
      this.setCurrentUser(response);
      return response;
    } catch (error) {
      console.error('Failed to get user profile:', error);
      throw error;
    }
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    try {
      const response = await apiClient.patch<User>('/iam/auth/profile/', data);
      this.setCurrentUser(response);
      return response;
    } catch (error) {
      console.error('Failed to update profile:', error);
      throw error;
    }
  }

  async changePassword(data: {
    old_password: string;
    new_password: string;
    confirm_password: string;
  }): Promise<void> {
    try {
      await apiClient.post('/iam/auth/change-password/', data);
    } catch (error) {
      console.error('Failed to change password:', error);
      throw error;
    }
  }

  // Password reset
  async requestPasswordReset(email: string): Promise<void> {
    try {
      await apiClient.post('/iam/auth/password-reset/', { email });
    } catch (error) {
      console.error('Failed to request password reset:', error);
      throw error;
    }
  }

  async resetPassword(data: {
    token: string;
    password: string;
    confirm_password: string;
  }): Promise<void> {
    try {
      await apiClient.post('/iam/auth/password-reset-confirm/', data);
    } catch (error) {
      console.error('Failed to reset password:', error);
      throw error;
    }
  }
}

// Create and export singleton instance
export const authService = new AuthService();
export default authService;