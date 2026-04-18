import React, { useState, useEffect, useRef } from 'react';
import { Clock, Play, Pause, RotateCcw } from 'lucide-react';

const InterviewTimer = ({ 
  isActive = false, 
  onTimeUpdate = null,
  showControls = false,
  className = ""
}) => {
  const [time, setTime] = useState(0); // tempo em segundos
  const [isRunning, setIsRunning] = useState(false);
  const intervalRef = useRef(null);
  
  useEffect(() => {
    // Sincronizar com prop isActive
    if (isActive !== isRunning) {
      if (isActive) {
        start();
      } else {
        pause();
      }
    }
  }, [isActive]);
  
  useEffect(() => {
    // Limpar interval ao desmontar
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);
  
  const start = () => {
    if (!isRunning) {
      setIsRunning(true);
      intervalRef.current = setInterval(() => {
        setTime(prevTime => {
          const newTime = prevTime + 1;
          // Callback para informar o tempo atual
          if (onTimeUpdate) {
            onTimeUpdate(newTime);
          }
          return newTime;
        });
      }, 1000);
    }
  };
  
  const pause = () => {
    if (isRunning && intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
      setIsRunning(false);
    }
  };
  
  const reset = () => {
    pause();
    setTime(0);
    if (onTimeUpdate) {
      onTimeUpdate(0);
    }
  };
  
  const toggleTimer = () => {
    if (isRunning) {
      pause();
    } else {
      start();
    }
  };
  
  // Formatar tempo em MM:SS
  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  // Obter cor baseada no tempo decorrido
  const getTimeColor = () => {
    if (time < 60) return 'text-green-600 dark:text-green-400';
    if (time < 180) return 'text-blue-600 dark:text-blue-400';
    if (time < 300) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };
  
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className="flex items-center gap-2">
        <Clock className={`h-5 w-5 ${isRunning ? 'animate-pulse' : ''} ${getTimeColor()}`} />
        <div className="flex flex-col">
          <span className={`text-2xl font-mono font-bold ${getTimeColor()}`}>
            {formatTime(time)}
          </span>
          {isRunning && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Tempo de entrevista
            </span>
          )}
        </div>
      </div>
      
      {showControls && (
        <div className="flex items-center gap-2 ml-4">
          <button
            onClick={toggleTimer}
            className={`p-2 rounded-lg transition-colors ${
              isRunning 
                ? 'bg-red-100 hover:bg-red-200 text-red-600 dark:bg-red-900 dark:hover:bg-red-800' 
                : 'bg-green-100 hover:bg-green-200 text-green-600 dark:bg-green-900 dark:hover:bg-green-800'
            }`}
            title={isRunning ? 'Pausar' : 'Iniciar'}
          >
            {isRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </button>
          
          <button
            onClick={reset}
            className="p-2 rounded-lg bg-gray-100 hover:bg-gray-200 text-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700 dark:text-gray-400 transition-colors"
            title="Resetar"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>
      )}
      
      {/* Indicador visual de status */}
      {isRunning && (
        <div className="ml-2">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-gray-500 dark:text-gray-400">Gravando</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default InterviewTimer;