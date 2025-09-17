import React from 'react';

interface StatusBadgeProps {
  status: 'disconnected' | 'connecting' | 'connected' | 'error';
  text?: string;
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, text }) => {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'connected':
        return {
          icon: '✅',
          bgColor: 'bg-green-100',
          textColor: 'text-green-800',
          text: text || '연결됨'
        };
      case 'connecting':
        return {
          icon: '🔄',
          bgColor: 'bg-blue-100',
          textColor: 'text-blue-800',
          text: text || '연결 중...'
        };
      case 'error':
        return {
          icon: '❌',
          bgColor: 'bg-red-100',
          textColor: 'text-red-800',
          text: text || '오류'
        };
      default:
        return {
          icon: '⚪',
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-800',
          text: text || '연결 안됨'
        };
    }
  };

  const config = getStatusConfig(status);

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bgColor} ${config.textColor}`}>
      <span className="mr-1">{config.icon}</span>
      {config.text}
    </span>
  );
};

export default StatusBadge;