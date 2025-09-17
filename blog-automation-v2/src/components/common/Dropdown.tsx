import React, { useState, useRef, useEffect } from 'react';

export interface DropdownOption {
  id: string;
  name: string;
  description?: string;
  icon?: string;
}

interface DropdownProps {
  label: string;
  placeholder?: string;
  options: DropdownOption[];
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  className?: string;
}

const Dropdown: React.FC<DropdownProps> = ({
  label,
  placeholder = "선택해주세요",
  options,
  value,
  onChange,
  required = false,
  className = ""
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const selectedOption = options.find(option => option.id === value);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleSelect = (optionId: string) => {
    onChange(optionId);
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <label className="modern-label block mb-3">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`modern-input w-full px-5 py-4 text-left flex items-center justify-between ${
          value ? 'text-gray-900' : 'text-gray-500'
        }`}
      >
        <div className="flex items-center gap-4">
          {selectedOption?.icon && (
            <span className="text-2xl">{selectedOption.icon}</span>
          )}
          <div>
            <div className="font-semibold text-base">
              {selectedOption ? selectedOption.name : placeholder}
            </div>
            {selectedOption?.description && (
              <div className="text-sm text-gray-500 mt-1">
                {selectedOption.description}
              </div>
            )}
          </div>
        </div>
        <svg
          className={`w-5 h-5 text-gray-400 transition-transform duration-200 flex-shrink-0 ${
            isOpen ? 'transform rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg max-h-80 overflow-auto">
          {options.map((option) => (
            <button
              key={option.id}
              onClick={() => handleSelect(option.id)}
              className={`w-full px-5 py-4 text-left transition-colors first:rounded-t-xl last:rounded-b-xl ${
                value === option.id 
                  ? 'bg-blue-50 text-blue-900' 
                  : 'text-gray-900 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-center gap-4">
                {option.icon && (
                  <span className="text-2xl flex-shrink-0">{option.icon}</span>
                )}
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-base truncate">{option.name}</div>
                  {option.description && (
                    <div className="text-sm text-gray-500 mt-1 truncate">
                      {option.description}
                    </div>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default Dropdown;