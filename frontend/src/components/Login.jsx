import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Eye, EyeOff, LogIn, User, Mail, Lock, AlertCircle, Loader2, Shield, Users, UserCheck, BarChart3, Eye as ViewIcon, Copy, CheckCircle, Sparkles, Zap, Star, Briefcase } from 'lucide-react';

const testCredentials = [
  {
    type: 'admin',
    name: 'Administrador',
    email: 'admin@test.com',
    password: 'admin123',
    description: 'Acesso completo ao sistema',
    icon: Shield,
    bgColor: 'bg-primary-700',
    borderColor: 'border-primary-600'
  },
  {
    type: 'recruiter',
    name: 'Recrutador',
    email: 'recruiter@test.com',
    password: 'test123',
    description: 'Gerenciar candidatos e entrevistas',
    icon: Users,
    bgColor: 'bg-primary-600',
    borderColor: 'border-primary-500'
  },
  {
    type: 'manager',
    name: 'Gerente',
    email: 'manager@test.com',
    password: 'test123',
    description: 'Supervisionar processos e relatórios',
    icon: UserCheck,
    bgColor: 'bg-primary-700',
    borderColor: 'border-primary-600'
  },
  {
    type: 'analyst',
    name: 'Analista',
    email: 'analyst@test.com',
    password: 'test123',
    description: 'Análises e relatórios detalhados',
    icon: BarChart3,
    bgColor: 'bg-secondary-700',
    borderColor: 'border-secondary-600'
  },
  {
    type: 'viewer',
    name: 'Visualizador',
    email: 'viewer@test.com',
    password: 'test123',
    description: 'Visualização apenas',
    icon: ViewIcon,
    bgColor: 'bg-secondary-600',
    borderColor: 'border-secondary-500'
  }
];

const Login = ({ onLoginSuccess }) => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [generalError, setGeneralError] = useState('');
  const [selectedCredential, setSelectedCredential] = useState(null);
  
  const { login } = useAuth();

  // Validação de email
  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Validação de formulário
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email é obrigatório';
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Email inválido';
    }
    
    if (!formData.password.trim()) {
      newErrors.password = 'Senha é obrigatória';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Senha deve ter pelo menos 6 caracteres';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Manipular mudanças nos campos
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Limpar erro do campo quando usuário começar a digitar
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
    
    // Limpar erro geral
    if (generalError) {
      setGeneralError('');
    }
  };

  // Preencher credenciais de teste
  const fillTestCredentials = (credential) => {
    setFormData({
      email: credential.email,
      password: credential.password
    });
    setErrors({});
    setGeneralError('');
    setSelectedCredential(credential.type);
    
    // Remover seleção após 3 segundos
    setTimeout(() => setSelectedCredential(null), 3000);
  };

  // Submeter formulário
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    setGeneralError('');
    
    try {
      const result = await login(formData.email.trim(), formData.password);
      
      if (result.success) {
        // Login bem-sucedido
        if (onLoginSuccess) {
          onLoginSuccess(result.user);
        }
      } else {
        // Erro de login
        setGeneralError(result.message || 'Erro no login. Verifique suas credenciais.');
      }
    } catch (error) {
      console.error('Erro no login:', error);
      setGeneralError('Erro de conexão. Tente novamente.');
    } finally {
      setIsLoading(false);
    }
  };

  // Manipular tecla Enter
  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-gray-50">
      {/* Background Profissional e Corporativo */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-100 via-gray-50 to-white"></div>
      
      {/* Padrão sutil de linhas */}
      <div className="absolute inset-0 opacity-5" style={{
        backgroundImage: `linear-gradient(to right, #e0e0e0 1px, transparent 1px), linear-gradient(to bottom, #e0e0e0 1px, transparent 1px)`,
        backgroundSize: '40px 40px'
      }}></div>

      <div className="relative z-10 min-h-screen flex items-center justify-center p-6">
        <div className="w-full max-w-7xl">
          {/* Header Principal */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 mb-6 bg-primary-700 rounded-lg shadow-sm">
              <Briefcase className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-5xl md:text-6xl font-semibold text-gray-900 mb-3">
              Apexus HR
            </h1>
            <p className="text-xl text-gray-600">Plataforma Inteligente de Recrutamento</p>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-12 items-start">
            
            {/* Seção de Credenciais de Teste - Profissional */}
            <div className="space-y-6">
              <div className="text-center xl:text-left">
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">Credenciais de Teste</h2>
                <p className="text-gray-600">Clique em qualquer perfil para login automático</p>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {testCredentials.map((credential, index) => {
                  const IconComponent = credential.icon;
                  const isSelected = selectedCredential === credential.type;
                  
                  return (
                    <div key={credential.type} className="group relative">
                      <button
                        onClick={() => fillTestCredentials(credential)}
                        disabled={isLoading}
                        className={`
                          w-full p-5 rounded-lg border-2 transition-all duration-200
                          bg-white hover:bg-gray-50 shadow-sm hover:shadow-md
                          ${isSelected ? 'border-primary-500 ring-2 ring-primary-200' : 'border-gray-200 hover:border-gray-300'}
                          disabled:opacity-50 disabled:cursor-not-allowed text-left
                        `}
                      >
                        <div className="flex items-start space-x-4 mb-3">
                          <div className={`p-2.5 rounded-md ${credential.bgColor}`}>
                            <IconComponent className="h-5 w-5 text-white" />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <h3 className="font-semibold text-gray-900">{credential.name}</h3>
                              {isSelected && (
                                <CheckCircle className="h-4 w-4 text-success-600" />
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{credential.description}</p>
                          </div>
                        </div>
                        
                        <div className="space-y-1.5 p-3 bg-gray-50 rounded border border-gray-200">
                          <div className="flex items-center space-x-2">
                            <Mail className="h-3.5 w-3.5 text-gray-500" />
                            <p className="text-xs text-gray-700 font-mono">{credential.email}</p>
                          </div>
                          <div className="flex items-center space-x-2">
                            <Lock className="h-3.5 w-3.5 text-gray-500" />
                            <p className="text-xs text-gray-700 font-mono">{credential.password}</p>
                          </div>
                        </div>
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Card de Login Profissional */}
            <div className="flex items-center justify-center">
              <div className="w-full max-w-md">
                <div className="p-8 rounded-lg shadow-lg border border-gray-200 bg-white">
                  {/* Header do Login */}
                  <div className="text-center mb-8">
                    <div className="mx-auto w-14 h-14 bg-primary-700 rounded-lg flex items-center justify-center mb-4">
                      <User className="h-7 w-7 text-white" />
                    </div>
                    <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                      Bem-vindo
                    </h2>
                    <p className="text-gray-600">Faça login para continuar</p>
                  </div>

                  {/* Formulário */}
                  <form onSubmit={handleSubmit} className="space-y-5">
                    {/* Erro geral */}
                    {generalError && (
                      <div className="flex items-center space-x-2 p-3 rounded-md bg-red-50 border border-red-200">
                        <AlertCircle className="h-4 w-4 text-danger-600" />
                        <p className="text-sm text-danger-700">{generalError}</p>
                      </div>
                    )}

                    {/* Campo Email */}
                    <div className="space-y-2">
                      <Label htmlFor="email" className="text-gray-700 font-medium text-sm">
                        Email
                      </Label>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        placeholder="seu@email.com"
                        value={formData.email}
                        onChange={handleInputChange}
                        onKeyPress={handleKeyPress}
                        disabled={isLoading}
                        className={`
                          h-11 px-3 text-sm rounded-md bg-white border transition-colors
                          ${errors.email ? 'border-danger-500 focus:ring-danger-200' : 'border-gray-300 focus:border-primary-500 focus:ring-primary-200'}
                        `}
                      />
                      {errors.email && (
                        <p className="text-danger-600 flex items-center space-x-1 text-xs">
                          <AlertCircle className="h-3 w-3" />
                          <span>{errors.email}</span>
                        </p>
                      )}
                    </div>

                    {/* Campo Senha */}
                    <div className="space-y-2">
                      <Label htmlFor="password" className="text-gray-700 font-medium text-sm">
                        Senha
                      </Label>
                      <div className="relative">
                        <Input
                          id="password"
                          name="password"
                          type={showPassword ? 'text' : 'password'}
                          placeholder="Digite sua senha"
                          value={formData.password}
                          onChange={handleInputChange}
                          onKeyPress={handleKeyPress}
                          disabled={isLoading}
                          className={`
                            h-11 px-3 pr-10 text-sm rounded-md bg-white border transition-colors
                            ${errors.password ? 'border-danger-500 focus:ring-danger-200' : 'border-gray-300 focus:border-primary-500 focus:ring-primary-200'}
                          `}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1.5 text-gray-500 hover:text-gray-700 transition-colors"
                          disabled={isLoading}
                        >
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                      {errors.password && (
                        <p className="text-danger-600 flex items-center space-x-1 text-xs">
                          <AlertCircle className="h-3 w-3" />
                          <span>{errors.password}</span>
                        </p>
                      )}
                    </div>

                    {/* Botão de Login Profissional */}
                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="w-full h-11 text-sm font-medium bg-primary-700 hover:bg-primary-800 
                               text-white rounded-md shadow-sm transition-colors
                               disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Entrando...
                        </>
                      ) : (
                        <>
                          <LogIn className="h-4 w-4 mr-2" />
                          Entrar no Sistema
                        </>
                      )}
                    </Button>
                  </form>

                  {/* Footer */}
                  <div className="mt-6 text-center">
                    <p className="text-xs text-gray-500">Ambiente de Desenvolvimento</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;