import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};

// Mapeamento de permissões do backend
const ROLE_PERMISSIONS = {
  admin: ['create', 'read', 'update', 'delete', 'manage_users', 'view_analytics'],
  recruiter: ['create', 'read', 'update', 'conduct_interviews', 'view_candidates'],
  manager: ['read', 'update', 'view_analytics', 'approve_candidates'],
  analyst: ['read', 'view_analytics', 'generate_reports'],
  viewer: ['read'],
  // Perfil especial para entrevistados (sem login)
  candidate: ['basic_settings', 'accessibility']
};

// Configurações permitidas por role
const SETTINGS_ACCESS = {
  admin: ['general', 'notifications', 'interviews', 'reports', 'privacy', 'accessibility', 'system'],
  recruiter: ['general', 'notifications', 'interviews', 'accessibility'],
  manager: ['general', 'notifications', 'reports', 'accessibility'],
  analyst: ['general', 'reports', 'accessibility'],
  viewer: ['general', 'accessibility'],
  candidate: ['accessibility', 'privacy-basic'] // Apenas configurações básicas
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState('candidate'); // Default para entrevistados

  // Carregar dados do usuário autenticado
  useEffect(() => {
    const loadUserData = async () => {
      try {
        // Verificar se tem token JWT
        const token = localStorage.getItem('auth_token');
        if (!token) {
          // Sem token = usuário não logado (provavelmente entrevistado)
          setUserRole('candidate');
          setIsAuthenticated(false);
          setIsLoading(false);
          return;
        }

        // Buscar dados do usuário autenticado
        const response = await fetch('/api/auth/me', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.success && data.user) {
            setUser(data.user);
            setUserRole(data.user.role);
            setIsAuthenticated(true);
          } else {
            // Token inválido
            localStorage.removeItem('auth_token');
            setUserRole('candidate');
            setIsAuthenticated(false);
          }
        } else {
          // Erro na autenticação
          localStorage.removeItem('auth_token');
          setUserRole('candidate');
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error('Erro ao carregar dados do usuário:', error);
        setUserRole('candidate');
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    loadUserData();
  }, []);

  // Verificar se usuário tem permissão específica
  const hasPermission = (permission) => {
    const userPermissions = ROLE_PERMISSIONS[userRole] || [];
    return userPermissions.includes(permission);
  };

  // Verificar se usuário pode acessar configuração específica
  const canAccessSetting = (settingCategory) => {
    const allowedSettings = SETTINGS_ACCESS[userRole] || [];
    return allowedSettings.includes(settingCategory);
  };

  // Obter todas as configurações acessíveis para o usuário
  const getAccessibleSettings = () => {
    return SETTINGS_ACCESS[userRole] || [];
  };

  // Login do usuário
  const login = async (email, password) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        localStorage.setItem('auth_token', data.token);
        setUser(data.user);
        setUserRole(data.user.role);
        setIsAuthenticated(true);
        return { success: true, user: data.user };
      } else {
        return { success: false, message: data.message || 'Erro no login' };
      }
    } catch (error) {
      console.error('Erro no login:', error);
      return { success: false, message: 'Erro de conexão' };
    }
  };

  // Logout do usuário
  const logout = async () => {
    try {
      // Limpar token do localStorage
      localStorage.removeItem('auth_token');
      
      // Limpar estado do usuário
      setUser(null);
      setUserRole('candidate');
      setIsAuthenticated(false);
      
      // Opcionalmente, fazer chamada para o backend para invalidar a sessão
      // await fetch('/api/auth/logout', {
      //   method: 'POST',
      //   headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
      // });
      
      // Redirecionar para login (será tratado no componente App)
      return { success: true };
    } catch (error) {
      console.error('Erro ao fazer logout:', error);
      return { success: false, message: 'Erro ao fazer logout' };
    }
  };

  // Obter nome de exibição do role
  const getRoleDisplayName = (role = userRole) => {
    const roleNames = {
      admin: 'Administrador',
      recruiter: 'Recrutador',
      manager: 'Gerente',
      analyst: 'Analista',
      viewer: 'Visualizador',
      candidate: 'Entrevistado'
    };
    return roleNames[role] || role;
  };

  // Verificar se é um entrevistado (sem login)
  const isCandidate = () => {
    return userRole === 'candidate' || !isAuthenticated;
  };

  // Verificar se tem acesso administrativo
  const isAdmin = () => {
    return userRole === 'admin';
  };

  // Verificar se pode gerenciar entrevistas
  const canManageInterviews = () => {
    return hasPermission('conduct_interviews') || isAdmin();
  };

  // Verificar se pode ver analytics
  const canViewAnalytics = () => {
    return hasPermission('view_analytics');
  };

  const value = {
    user,
    userRole,
    isLoading,
    isAuthenticated,
    hasPermission,
    canAccessSetting,
    getAccessibleSettings,
    login,
    logout,
    getRoleDisplayName,
    isCandidate,
    isAdmin,
    canManageInterviews,
    canViewAnalytics,
    
    // Dados úteis para interface
    permissions: ROLE_PERMISSIONS[userRole] || [],
    accessibleSettings: SETTINGS_ACCESS[userRole] || []
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};