import React from 'react';

interface SimpleDialogProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  message: string;
  onConfirm?: () => void;
  confirmText?: string;
  cancelText?: string;
}

const SimpleDialog: React.FC<SimpleDialogProps> = ({
  isOpen,
  onClose,
  title,
  message,
  onConfirm,
  confirmText = '확인',
  cancelText = '취소'
}) => {
  if (!isOpen) return null;

  const handleConfirm = () => {
    console.log('SimpleDialog confirm clicked');
    if (onConfirm) {
      onConfirm();
    }
    onClose();
  };

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div 
        style={{
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '8px',
          maxWidth: '400px',
          width: '90%',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
        }}
      >
        <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', fontWeight: 'bold' }}>
          {title}
        </h3>
        
        <p style={{ margin: '0 0 24px 0', lineHeight: '1.5', whiteSpace: 'pre-line' }}>
          {message}
        </p>
        
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          {onConfirm && (
            <button
              onClick={onClose}
              style={{
                padding: '8px 16px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                backgroundColor: 'white',
                cursor: 'pointer'
              }}
            >
              {cancelText}
            </button>
          )}
          
          <button
            onClick={handleConfirm}
            style={{
              padding: '8px 16px',
              border: 'none',
              borderRadius: '4px',
              backgroundColor: '#2563eb',
              color: 'white',
              cursor: 'pointer'
            }}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SimpleDialog;