import React, { useState } from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from './ui/alert-dialog';
import { LogOut, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const LogoutConfirmationDialog = ({ open, onOpenChange }) => {
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const { logout } = useAuth();

  const handleConfirmLogout = async () => {
    setIsLoggingOut(true);
    
    // Adicionar um pequeno delay para feedback visual
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Executar logout
    await logout();
    
    // Fechar o modal
    onOpenChange(false);
    
    // Mostrar notificação de sucesso (se tiver biblioteca de toast)
    // toast.success('Logout realizado com sucesso!');
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="max-w-md">
        <AlertDialogHeader>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
              <LogOut className="h-6 w-6 text-red-600 dark:text-red-400" />
            </div>
            <AlertDialogTitle className="text-xl">Confirmar Logout</AlertDialogTitle>
          </div>
          <AlertDialogDescription className="text-base mt-2">
            Tem certeza que deseja sair do sistema? Você precisará fazer login novamente para acessar sua conta.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="mt-6">
          <AlertDialogCancel 
            disabled={isLoggingOut}
            className="bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300"
          >
            Cancelar
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirmLogout}
            disabled={isLoggingOut}
            className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-lg shadow-red-500/25"
          >
            {isLoggingOut ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saindo...
              </>
            ) : (
              <>
                <LogOut className="mr-2 h-4 w-4" />
                Sim, sair
              </>
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default LogoutConfirmationDialog;