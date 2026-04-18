import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { AlertCircle, Lock, Eye } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './ui/card';

const ProtectedRoute = ({ 
  children, 
  requiredPermission = null, 
  requiredRole = null, 
  allowedRoles = [], 
  fallbackMessage = null 
}) => {
  const { user, userRole, isAuthenticated, isLoading, hasPermission } = useAuth();

  // Ainda está carregando a autenticação
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Usuário não autenticado
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mb-4">
              <Lock className="h-6 w-6 text-red-600" />
            </div>
            <CardTitle>Acesso Restrito</CardTitle>
            <CardDescription>
              Você precisa estar logado para acessar esta página
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  // Verificar permissão específica
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
              <AlertCircle className="h-6 w-6 text-yellow-600" />
            </div>
            <CardTitle>Permissão Insuficiente</CardTitle>
            <CardDescription>
              {fallbackMessage || `Você não tem permissão para ${requiredPermission}`}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-sm text-gray-500">
              Seu perfil: <strong>{userRole}</strong>
            </p>
            <p className="text-sm text-gray-500">
              Permissão necessária: <strong>{requiredPermission}</strong>
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Verificar role específico
  if (requiredRole && userRole !== requiredRole) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
              <AlertCircle className="h-6 w-6 text-yellow-600" />
            </div>
            <CardTitle>Acesso Restrito</CardTitle>
            <CardDescription>
              {fallbackMessage || `Apenas usuários do tipo ${requiredRole} podem acessar esta página`}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-sm text-gray-500">
              Seu perfil: <strong>{userRole}</strong>
            </p>
            <p className="text-sm text-gray-500">
              Perfil necessário: <strong>{requiredRole}</strong>
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Verificar lista de roles permitidos
  if (allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-yellow-100 rounded-lg flex items-center justify-center mb-4">
              <Eye className="h-6 w-6 text-yellow-600" />
            </div>
            <CardTitle>Acesso Restrito</CardTitle>
            <CardDescription>
              {fallbackMessage || 'Você não tem permissão para acessar esta página'}
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-sm text-gray-500">
              Seu perfil: <strong>{userRole}</strong>
            </p>
            <p className="text-sm text-gray-500">
              Perfis permitidos: <strong>{allowedRoles.join(', ')}</strong>
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Acesso permitido
  return children;
};

export default ProtectedRoute;