"""
React Component Generator - Functional components with hooks, testing, and Storybook

Generates:
- Functional components with React Hooks
- Props with TypeScript definitions
- Custom hooks for logic reuse
- State management integration (Context, Redux)
- Component testing (Jest, React Testing Library)
- Storybook stories
- Accessibility support (a11y)
"""

from typing import Dict, Any


class ReactComponentGenerator:
    """Generate React components with modern patterns"""

    def __init__(self):
        pass

    def generate_button_component(self) -> str:
        """Generate a reusable Button component"""
        return """
import React, { ButtonHTMLAttributes } from 'react';
import styles from './Button.module.css';

export type ButtonVariant = 'primary' | 'secondary' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  ariaLabel?: string;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  fullWidth = false,
  icon,
  iconPosition = 'left',
  ariaLabel,
  disabled,
  children,
  className,
  ...rest
}) => {
  const combinedClassName = [
    styles.button,
    styles[variant],
    styles[size],
    fullWidth && styles.fullWidth,
    isLoading && styles.loading,
    className
  ].filter(Boolean).join(' ');

  return (
    <button
      className={combinedClassName}
      disabled={disabled || isLoading}
      aria-label={ariaLabel}
      aria-busy={isLoading}
      {...rest}
    >
      {icon && iconPosition === 'left' && (
        <span className={styles.icon}>{icon}</span>
      )}
      {!isLoading && children}
      {isLoading && <span className={styles.spinner} />}
      {icon && iconPosition === 'right' && (
        <span className={styles.icon}>{icon}</span>
      )}
    </button>
  );
};

Button.displayName = 'Button';
"""

    def generate_button_styles(self) -> str:
        """Generate Button component CSS module"""
        return """
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;

  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  &:active:not(:disabled) {
    transform: translateY(0);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Variants */
  &.primary {
    background-color: #0066cc;
    color: white;

    &:hover:not(:disabled) {
      background-color: #0052a3;
    }
  }

  &.secondary {
    background-color: #e0e0e0;
    color: #333;

    &:hover:not(:disabled) {
      background-color: #d0d0d0;
    }
  }

  &.danger {
    background-color: #dc3545;
    color: white;

    &:hover:not(:disabled) {
      background-color: #c82333;
    }
  }

  /* Sizes */
  &.sm {
    padding: 6px 12px;
    font-size: 12px;
    height: 32px;
  }

  &.md {
    padding: 8px 16px;
    font-size: 14px;
    height: 40px;
  }

  &.lg {
    padding: 12px 24px;
    font-size: 16px;
    height: 48px;
  }

  &.fullWidth {
    width: 100%;
  }

  /* Loading state */
  &.loading {
    position: relative;
  }

  .spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  .icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
"""

    def generate_button_tests(self) -> str:
        """Generate Button component tests"""
        return """
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button Component', () => {
  it('renders with default props', () => {
    render(<Button>Click me</Button>);
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
  });

  it('renders all variants', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);
    expect(screen.getByRole('button')).toHaveClass('primary');

    rerender(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole('button')).toHaveClass('secondary');

    rerender(<Button variant="danger">Danger</Button>);
    expect(screen.getByRole('button')).toHaveClass('danger');
  });

  it('renders all sizes', () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    expect(screen.getByRole('button')).toHaveClass('sm');

    rerender(<Button size="md">Medium</Button>);
    expect(screen.getByRole('button')).toHaveClass('md');

    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole('button')).toHaveClass('lg');
  });

  it('handles click events', async () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click</Button>);

    await userEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('disables when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('disables when loading', () => {
    render(<Button isLoading>Loading</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
  });

  it('supports full width', () => {
    render(<Button fullWidth>Full Width</Button>);
    expect(screen.getByRole('button')).toHaveClass('fullWidth');
  });

  it('renders with icon', () => {
    render(
      <Button icon={<span data-testid="icon">🔍</span>}>
        Search
      </Button>
    );
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });

  it('supports custom aria label for accessibility', () => {
    render(<Button ariaLabel="Delete item">Delete</Button>);
    expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Delete item');
  });

  it('forwards HTML attributes', () => {
    render(<Button id="custom-id" data-testid="custom">Button</Button>);
    const button = screen.getByTestId('custom');
    expect(button).toHaveAttribute('id', 'custom-id');
  });
});
"""

    def generate_button_story(self) -> str:
        """Generate Button component Storybook story"""
        return """
import React from 'react';
import { Meta, StoryObj } from '@storybook/react';
import { Button } from './Button';

const meta: Meta<typeof Button> = {
  title: 'Components/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'radio',
      options: ['primary', 'secondary', 'danger'],
      description: 'Button style variant',
    },
    size: {
      control: 'radio',
      options: ['sm', 'md', 'lg'],
      description: 'Button size',
    },
    isLoading: {
      control: 'boolean',
      description: 'Show loading spinner',
    },
    fullWidth: {
      control: 'boolean',
      description: 'Expand to full width',
    },
    disabled: {
      control: 'boolean',
      description: 'Disable button',
    },
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
  args: {
    variant: 'primary',
    children: 'Primary Button',
  },
};

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary Button',
  },
};

export const Danger: Story = {
  args: {
    variant: 'danger',
    children: 'Delete',
  },
};

export const Loading: Story = {
  args: {
    isLoading: true,
    children: 'Loading...',
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
    children: 'Disabled Button',
  },
};

export const Sizes: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '16px' }}>
      <Button size="sm">Small</Button>
      <Button size="md">Medium</Button>
      <Button size="lg">Large</Button>
    </div>
  ),
};

export const AllVariants: Story = {
  render: () => (
    <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
      <Button variant="primary">Primary</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="danger">Danger</Button>
    </div>
  ),
};

export const WithIcon: Story = {
  args: {
    icon: '🔍',
    children: 'Search',
  },
};

export const FullWidth: Story = {
  args: {
    fullWidth: true,
    children: 'Full Width Button',
  },
};
"""

    def generate_form_component(self) -> str:
        """Generate Form component with field management"""
        return """
import React, { useCallback, useState } from 'react';
import styles from './Form.module.css';

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'textarea';
  required?: boolean;
  placeholder?: string;
  validation?: (value: string) => string | null;
}

interface FormProps {
  fields: FormField[];
  onSubmit: (data: Record<string, string>) => Promise<void>;
  submitLabel?: string;
}

interface FormState {
  values: Record<string, string>;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
  isSubmitting: boolean;
}

export const Form: React.FC<FormProps> = ({
  fields,
  onSubmit,
  submitLabel = 'Submit'
}) => {
  const [state, setState] = useState<FormState>({
    values: fields.reduce((acc, field) => ({ ...acc, [field.name]: '' }), {}),
    errors: {},
    touched: {},
    isSubmitting: false,
  });

  const handleChange = useCallback((name: string, value: string) => {
    setState(prev => ({
      ...prev,
      values: { ...prev.values, [name]: value },
      ...(prev.touched[name] && {
        errors: {
          ...prev.errors,
          [name]: fields.find(f => f.name === name)?.validation?.(value) || '',
        }
      })
    }));
  }, [fields]);

  const handleBlur = useCallback((name: string) => {
    const field = fields.find(f => f.name === name);
    const error = field?.validation?.(state.values[name]) || '';

    setState(prev => ({
      ...prev,
      touched: { ...prev.touched, [name]: true },
      errors: { ...prev.errors, [name]: error },
    }));
  }, [fields, state.values]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate all fields
    const newErrors: Record<string, string> = {};
    fields.forEach(field => {
      if (field.required && !state.values[field.name]) {
        newErrors[field.name] = `${field.label} is required`;
      } else if (field.validation) {
        const error = field.validation(state.values[field.name]);
        if (error) newErrors[field.name] = error;
      }
    });

    if (Object.keys(newErrors).length > 0) {
      setState(prev => ({ ...prev, errors: newErrors }));
      return;
    }

    setState(prev => ({ ...prev, isSubmitting: true }));
    try {
      await onSubmit(state.values);
    } finally {
      setState(prev => ({ ...prev, isSubmitting: false }));
    }
  };

  return (
    <form onSubmit={handleSubmit} className={styles.form} noValidate>
      {fields.map(field => (
        <div key={field.name} className={styles.formGroup}>
          <label htmlFor={field.name} className={styles.label}>
            {field.label}
            {field.required && <span className={styles.required}>*</span>}
          </label>

          {field.type === 'textarea' ? (
            <textarea
              id={field.name}
              name={field.name}
              value={state.values[field.name]}
              onChange={e => handleChange(field.name, e.target.value)}
              onBlur={() => handleBlur(field.name)}
              placeholder={field.placeholder}
              className={`${styles.input} ${state.errors[field.name] ? styles.error : ''}`}
              aria-invalid={!!state.errors[field.name]}
              aria-describedby={state.errors[field.name] ? `${field.name}-error` : undefined}
            />
          ) : (
            <input
              id={field.name}
              type={field.type}
              name={field.name}
              value={state.values[field.name]}
              onChange={e => handleChange(field.name, e.target.value)}
              onBlur={() => handleBlur(field.name)}
              placeholder={field.placeholder}
              className={`${styles.input} ${state.errors[field.name] ? styles.error : ''}`}
              aria-invalid={!!state.errors[field.name]}
              aria-describedby={state.errors[field.name] ? `${field.name}-error` : undefined}
            />
          )}

          {state.errors[field.name] && (
            <span id={`${field.name}-error`} className={styles.errorMessage} role="alert">
              {state.errors[field.name]}
            </span>
          )}
        </div>
      ))}

      <button
        type="submit"
        disabled={state.isSubmitting}
        className={styles.submitButton}
      >
        {state.isSubmitting ? 'Submitting...' : submitLabel}
      </button>
    </form>
  );
};

Form.displayName = 'Form';
"""

    def generate_use_fetch_hook(self) -> str:
        """Generate custom useFetch hook"""
        return """
import { useEffect, useState, useCallback } from 'react';

interface UseFetchState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

interface UseFetchOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: Record<string, any>;
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
}

export function useFetch<T = any>(
  url: string,
  options: UseFetchOptions = {}
): UseFetchState<T> & { refetch: () => Promise<void> } {
  const [state, setState] = useState<UseFetchState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const fetchData = useCallback(async () => {
    setState({ data: null, loading: true, error: null });

    try {
      const response = await fetch(url, {
        method: options.method || 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...(options.body && { body: JSON.stringify(options.body) }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json() as T;
      setState({ data, loading: false, error: null });
      options.onSuccess?.(data);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      setState({ data: null, loading: false, error: err });
      options.onError?.(err);
    }
  }, [url, options]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { ...state, refetch: fetchData };
}
"""

    def generate_input_component(self) -> str:
        """Generate Input component"""
        return """
import React, { InputHTMLAttributes, forwardRef } from 'react';
import styles from './Input.module.css';

export type InputSize = 'sm' | 'md' | 'lg';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helpText?: string;
  size?: InputSize;
  fullWidth?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  helpText,
  size = 'md',
  fullWidth = false,
  icon,
  iconPosition = 'left',
  className,
  id,
  ...rest
}, ref) => {
  const inputId = id || `input-${Math.random()}`;

  return (
    <div className={`${styles.wrapper} ${fullWidth ? styles.fullWidth : ''}`}>
      {label && <label htmlFor={inputId} className={styles.label}>{label}</label>}

      <div className={`${styles.inputWrapper} ${styles[size]} ${icon ? styles.hasIcon : ''}`}>
        {icon && iconPosition === 'left' && (
          <span className={styles.iconLeft}>{icon}</span>
        )}
        <input
          ref={ref}
          id={inputId}
          className={`${styles.input} ${error ? styles.error : ''} ${className || ''}`}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : helpText ? `${inputId}-help` : undefined}
          {...rest}
        />
        {icon && iconPosition === 'right' && (
          <span className={styles.iconRight}>{icon}</span>
        )}
      </div>

      {error && <span id={`${inputId}-error`} className={styles.errorText} role="alert">{error}</span>}
      {helpText && !error && <span id={`${inputId}-help`} className={styles.helpText}>{helpText}</span>}
    </div>
  );
});

Input.displayName = 'Input';
"""

    def generate_select_component(self) -> str:
        """Generate Select component"""
        return """
import React, { SelectHTMLAttributes, forwardRef } from 'react';
import styles from './Select.module.css';

interface Option {
  value: string | number;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  options: Option[];
  error?: string;
  helpText?: string;
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(({
  label,
  options,
  error,
  helpText,
  placeholder,
  id,
  className,
  ...rest
}, ref) => {
  const selectId = id || `select-${Math.random()}`;

  return (
    <div className={styles.wrapper}>
      {label && <label htmlFor={selectId} className={styles.label}>{label}</label>}

      <select
        ref={ref}
        id={selectId}
        className={`${styles.select} ${error ? styles.error : ''} ${className || ''}`}
        aria-invalid={!!error}
        aria-describedby={error ? `${selectId}-error` : helpText ? `${selectId}-help` : undefined}
        {...rest}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map(opt => (
          <option key={opt.value} value={opt.value} disabled={opt.disabled}>
            {opt.label}
          </option>
        ))}
      </select>

      {error && <span id={`${selectId}-error`} className={styles.errorText} role="alert">{error}</span>}
      {helpText && !error && <span id={`${selectId}-help`} className={styles.helpText}>{helpText}</span>}
    </div>
  );
});

Select.displayName = 'Select';
"""

    def generate_checkbox_component(self) -> str:
        """Generate Checkbox component"""
        return """
import React, { InputHTMLAttributes, forwardRef } from 'react';
import styles from './Checkbox.module.css';

interface CheckboxProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helpText?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(({
  label,
  helpText,
  id,
  className,
  ...rest
}, ref) => {
  const checkboxId = id || `checkbox-${Math.random()}`;

  return (
    <div className={styles.wrapper}>
      <div className={styles.inputWrapper}>
        <input
          ref={ref}
          id={checkboxId}
          type="checkbox"
          className={`${styles.input} ${className || ''}`}
          aria-describedby={helpText ? `${checkboxId}-help` : undefined}
          {...rest}
        />
        {label && <label htmlFor={checkboxId} className={styles.label}>{label}</label>}
      </div>
      {helpText && <span id={`${checkboxId}-help`} className={styles.helpText}>{helpText}</span>}
    </div>
  );
});

Checkbox.displayName = 'Checkbox';
"""

    def generate_alert_component(self) -> str:
        """Generate Alert component"""
        return """
import React from 'react';
import styles from './Alert.module.css';

export type AlertType = 'info' | 'success' | 'warning' | 'error';

interface AlertProps {
  type?: AlertType;
  title?: string;
  children: React.ReactNode;
  closable?: boolean;
  onClose?: () => void;
  icon?: React.ReactNode;
}

export const Alert: React.FC<AlertProps> = ({
  type = 'info',
  title,
  children,
  closable = false,
  onClose,
  icon,
}) => {
  const [isVisible, setIsVisible] = React.useState(true);

  if (!isVisible) return null;

  const handleClose = () => {
    setIsVisible(false);
    onClose?.();
  };

  return (
    <div
      className={`${styles.alert} ${styles[type]}`}
      role="alert"
      aria-live={type === 'error' ? 'assertive' : 'polite'}
    >
      <div className={styles.content}>
        {icon && <span className={styles.icon}>{icon}</span>}
        <div>
          {title && <div className={styles.title}>{title}</div>}
          <div className={styles.message}>{children}</div>
        </div>
      </div>
      {closable && (
        <button
          className={styles.closeButton}
          onClick={handleClose}
          aria-label="Close alert"
        >
          ✕
        </button>
      )}
    </div>
  );
};
"""

    def generate_toast_component(self) -> str:
        """Generate Toast component and hook"""
        return """
import React, { createContext, useContext, useState, useCallback } from 'react';
import styles from './Toast.module.css';

export type ToastType = 'info' | 'success' | 'warning' | 'error';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastContextType {
  addToast: (message: string, type?: ToastType, duration?: number) => string;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) throw new Error('useToast must be used within ToastProvider');
  return context;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((message: string, type: ToastType = 'info', duration = 3000) => {
    const id = `toast-${Date.now()}`;
    setToasts(prev => [...prev, { id, type, message, duration }]);

    if (duration) {
      setTimeout(() => removeToast(id), duration);
    }
    return id;
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <div className={styles.container}>
        {toasts.map(toast => (
          <ToastItem
            key={toast.id}
            toast={toast}
            onRemove={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
};

interface ToastItemProps {
  toast: Toast;
  onRemove: () => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, onRemove }) => (
  <div className={`${styles.toast} ${styles[toast.type]}`} role="status">
    <span>{toast.message}</span>
    <button onClick={onRemove} aria-label="Close toast">✕</button>
  </div>
);
"""

    def generate_input_styles(self) -> str:
        """Generate Input component styles"""
        return """
.wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.fullWidth {
  width: 100%;
}

.label {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.inputWrapper {
  display: flex;
  align-items: center;
  position: relative;
  border: 1px solid #ddd;
  border-radius: 4px;
  transition: border-color 0.2s;

  &.hasIcon {
    padding-left: 8px;
    padding-right: 8px;
  }

  &.sm input {
    padding: 4px 8px;
    font-size: 12px;
  }

  &.md input {
    padding: 8px 12px;
    font-size: 14px;
  }

  &.lg input {
    padding: 12px 16px;
    font-size: 16px;
  }

  &:focus-within {
    border-color: #0066cc;
    box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
  }
}

.input {
  flex: 1;
  border: none;
  background: transparent;
  font-family: inherit;
  outline: none;

  &.error {
    color: #dc3545;
  }
}

.iconLeft, .iconRight {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.errorText {
  font-size: 12px;
  color: #dc3545;
}

.helpText {
  font-size: 12px;
  color: #666;
}
"""

    def generate_select_styles(self) -> str:
        """Generate Select component styles"""
        return """
.wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
  font-size: 14px;
  color: #333;
  background-color: white;
  cursor: pointer;
  transition: border-color 0.2s;

  &:focus {
    outline: none;
    border-color: #0066cc;
    box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
  }

  &.error {
    border-color: #dc3545;

    &:focus {
      box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.1);
    }
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.errorText {
  font-size: 12px;
  color: #dc3545;
}

.helpText {
  font-size: 12px;
  color: #666;
}
"""

    def generate_checkbox_styles(self) -> str:
        """Generate Checkbox component styles"""
        return """
.wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.inputWrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.input {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #0066cc;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.label {
  font-size: 14px;
  color: #333;
  cursor: pointer;
}

.helpText {
  font-size: 12px;
  color: #666;
  margin-left: 26px;
}
"""

    def generate_alert_styles(self) -> str:
        """Generate Alert component styles"""
        return """
.alert {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 14px;

  &.info {
    background-color: #e7f3ff;
    border-left: 4px solid #0066cc;
    color: #0066cc;
  }

  &.success {
    background-color: #f0f9ff;
    border-left: 4px solid #28a745;
    color: #28a745;
  }

  &.warning {
    background-color: #fff8e1;
    border-left: 4px solid #ffc107;
    color: #856404;
  }

  &.error {
    background-color: #ffe7e7;
    border-left: 4px solid #dc3545;
    color: #dc3545;
  }
}

.content {
  display: flex;
  gap: 12px;
  flex: 1;
}

.icon {
  display: flex;
  align-items: flex-start;
  font-size: 18px;
}

.title {
  font-weight: 600;
  margin-bottom: 4px;
}

.message {
  line-height: 1.5;
}

.closeButton {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 0;
  color: inherit;
  opacity: 0.7;
  transition: opacity 0.2s;

  &:hover {
    opacity: 1;
  }
}
"""

    def generate_toast_styles(self) -> str:
        """Generate Toast component styles"""
        return """
.container {
  position: fixed;
  bottom: 16px;
  right: 16px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 400px;
}

.toast {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease;

  &.info {
    background-color: #e7f3ff;
    color: #0066cc;
  }

  &.success {
    background-color: #f0f9ff;
    color: #28a745;
  }

  &.warning {
    background-color: #fff8e1;
    color: #856404;
  }

  &.error {
    background-color: #ffe7e7;
    color: #dc3545;
  }

  button {
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 16px;
    padding: 0;
    color: inherit;
    opacity: 0.7;
    transition: opacity 0.2s;

    &:hover {
      opacity: 1;
    }
  }
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
"""


def generate_react_components(component_type: str = "button") -> Dict[str, str]:
    """
    Generate React components.

    Args:
        component_type: Type of component to generate

    Returns: dict of {filename: code_content}
    """
    generator = ReactComponentGenerator()
    output = {}

    if component_type == "button":
        output["Button.tsx"] = generator.generate_button_component()
        output["Button.module.css"] = generator.generate_button_styles()
        output["Button.test.tsx"] = generator.generate_button_tests()
        output["Button.stories.tsx"] = generator.generate_button_story()

    elif component_type == "form":
        output["Form.tsx"] = generator.generate_form_component()
        output["hooks/useFetch.ts"] = generator.generate_use_fetch_hook()

    elif component_type == "input":
        output["Input.tsx"] = generator.generate_input_component()
        output["Input.module.css"] = generator.generate_input_styles()

    elif component_type == "select":
        output["Select.tsx"] = generator.generate_select_component()
        output["Select.module.css"] = generator.generate_select_styles()

    elif component_type == "checkbox":
        output["Checkbox.tsx"] = generator.generate_checkbox_component()
        output["Checkbox.module.css"] = generator.generate_checkbox_styles()

    elif component_type == "alert":
        output["Alert.tsx"] = generator.generate_alert_component()
        output["Alert.module.css"] = generator.generate_alert_styles()

    elif component_type == "toast":
        output["Toast.tsx"] = generator.generate_toast_component()
        output["Toast.module.css"] = generator.generate_toast_styles()

    elif component_type == "all":
        # Generate all core components
        output.update(generate_react_components("button"))
        output.update(generate_react_components("form"))
        output.update(generate_react_components("input"))
        output.update(generate_react_components("select"))
        output.update(generate_react_components("checkbox"))
        output.update(generate_react_components("alert"))
        output.update(generate_react_components("toast"))

    return output
