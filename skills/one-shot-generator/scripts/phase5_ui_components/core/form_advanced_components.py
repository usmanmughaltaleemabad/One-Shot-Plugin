"""
Advanced Form Components - TextArea, RadioGroup, Toggle, Label

Generates:
- Multi-line text input
- Radio button group
- Toggle/switch component
- Form label with required indicator
"""

from typing import Dict, Any


class FormAdvancedComponentGenerator:
    """Generate advanced form components"""

    def generate_textarea_component(self) -> str:
        """Generate textarea component"""
        return """
import React, { forwardRef } from 'react';
import styles from './TextArea.module.css';

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helpText?: string;
  rows?: number;
  maxLength?: number;
  showCount?: boolean;
}

export const TextArea = forwardRef<HTMLTextAreaElement, TextAreaProps>(({
  label,
  error,
  helpText,
  rows = 4,
  maxLength,
  showCount = false,
  value,
  className,
  id,
  ...rest
}, ref) => {
  const textareaId = id || `textarea-${Math.random()}`;
  const charCount = typeof value === 'string' ? value.length : 0;

  return (
    <div className={styles.wrapper}>
      {label && (
        <label htmlFor={textareaId} className={styles.label}>
          {label}
        </label>
      )}

      <textarea
        ref={ref}
        id={textareaId}
        rows={rows}
        maxLength={maxLength}
        value={value}
        className={`${styles.textarea} ${error ? styles.error : ''} ${className || ''}`}
        aria-invalid={!!error}
        aria-describedby={error ? `${textareaId}-error` : helpText ? `${textareaId}-help` : undefined}
        {...rest}
      />

      <div className={styles.footer}>
        <div>
          {error && (
            <span id={`${textareaId}-error`} className={styles.errorText} role="alert">
              {error}
            </span>
          )}
          {helpText && !error && (
            <span id={`${textareaId}-help`} className={styles.helpText}>
              {helpText}
            </span>
          )}
        </div>

        {showCount && maxLength && (
          <span className={styles.count}>
            {charCount}/{maxLength}
          </span>
        )}
      </div>
    </div>
  );
});

TextArea.displayName = 'TextArea';
"""

    def generate_radio_group_component(self) -> str:
        """Generate radio button group"""
        return """
import React from 'react';
import styles from './RadioGroup.module.css';

export interface RadioOption {
  value: string | number;
  label: string;
  disabled?: boolean;
  helpText?: string;
}

interface RadioGroupProps {
  name: string;
  options: RadioOption[];
  value?: string | number;
  onChange?: (value: string | number) => void;
  label?: string;
  error?: string;
  direction?: 'vertical' | 'horizontal';
}

export const RadioGroup: React.FC<RadioGroupProps> = ({
  name,
  options,
  value,
  onChange,
  label,
  error,
  direction = 'vertical',
}) => {
  const groupId = `radio-${name}`;

  return (
    <div className={styles.wrapper}>
      {label && (
        <label id={`${groupId}-label`} className={styles.label}>
          {label}
        </label>
      )}

      <div
        className={`${styles.group} ${styles[direction]}`}
        role="radiogroup"
        aria-labelledby={label ? `${groupId}-label` : undefined}
        aria-invalid={!!error}
      >
        {options.map(option => (
          <div key={option.value} className={styles.option}>
            <input
              type="radio"
              name={name}
              id={`${groupId}-${option.value}`}
              value={option.value}
              checked={value === option.value}
              onChange={e => onChange?.(e.target.value)}
              disabled={option.disabled}
              className={styles.input}
              aria-describedby={option.helpText ? `${groupId}-${option.value}-help` : undefined}
            />
            <label
              htmlFor={`${groupId}-${option.value}`}
              className={`${styles.optionLabel} ${option.disabled ? styles.disabled : ''}`}
            >
              {option.label}
            </label>
            {option.helpText && (
              <p id={`${groupId}-${option.value}-help`} className={styles.helpText}>
                {option.helpText}
              </p>
            )}
          </div>
        ))}
      </div>

      {error && (
        <span className={styles.errorText} role="alert">
          {error}
        </span>
      )}
    </div>
  );
};

RadioGroup.displayName = 'RadioGroup';
"""

    def generate_toggle_component(self) -> str:
        """Generate toggle/switch component"""
        return """
import React, { forwardRef } from 'react';
import styles from './Toggle.module.css';

interface ToggleProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  description?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const Toggle = forwardRef<HTMLInputElement, ToggleProps>(({
  label,
  description,
  size = 'md',
  id,
  className,
  ...rest
}, ref) => {
  const toggleId = id || `toggle-${Math.random()}`;

  return (
    <div className={styles.wrapper}>
      <label htmlFor={toggleId} className={styles.label}>
        <input
          ref={ref}
          id={toggleId}
          type="checkbox"
          className={`${styles.input} ${className || ''}`}
          {...rest}
        />
        <span className={`${styles.switch} ${styles[size]}`} />
        {label && <span className={styles.text}>{label}</span>}
      </label>
      {description && <p className={styles.description}>{description}</p>}
    </div>
  );
});

Toggle.displayName = 'Toggle';
"""

    def generate_form_label_component(self) -> str:
        """Generate form label component"""
        return """
import React from 'react';
import styles from './Label.module.css';

interface LabelProps {
  htmlFor: string;
  children: React.ReactNode;
  required?: boolean;
  error?: boolean;
  disabled?: boolean;
}

export const Label: React.FC<LabelProps> = ({
  htmlFor,
  children,
  required = false,
  error = false,
  disabled = false,
}) => {
  return (
    <label
      htmlFor={htmlFor}
      className={`${styles.label} ${error ? styles.error : ''} ${disabled ? styles.disabled : ''}`}
    >
      {children}
      {required && <span className={styles.required} aria-label="required">*</span>}
    </label>
  );
};

Label.displayName = 'Label';
"""

    def generate_form_advanced_styles(self) -> str:
        """Generate form advanced styles"""
        return """
/* TextArea Styles */
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

.textarea {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: inherit;
  font-size: 14px;
  resize: vertical;
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

.footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #666;
}

.errorText {
  color: #dc3545;
}

.helpText {
  color: #666;
}

.count {
  color: #999;
}

/* RadioGroup Styles */
.group {
  display: flex;
  gap: 16px;

  &.vertical {
    flex-direction: column;
  }
}

.option {
  display: flex;
  flex-direction: column;
  gap: 4px;
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

.optionLabel {
  font-size: 14px;
  color: #333;
  cursor: pointer;

  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

/* Toggle Styles */
.label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.input {
  appearance: none;
  width: 0;
  height: 0;
  margin: 0;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;

  &:checked + .switch {
    background-color: #0066cc;

    &::after {
      transform: translateX(20px);
    }
  }

  &:disabled + .switch {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.switch {
  display: inline-block;
  background-color: #ccc;
  border-radius: 12px;
  transition: background-color 0.2s;
  position: relative;

  &::after {
    content: '';
    position: absolute;
    width: 16px;
    height: 16px;
    background: white;
    border-radius: 50%;
    top: 2px;
    left: 2px;
    transition: transform 0.2s;
  }

  &.sm {
    width: 36px;
    height: 20px;

    &::after {
      width: 14px;
      height: 14px;
    }

    .input:checked + & {
      &::after {
        transform: translateX(16px);
      }
    }
  }

  &.md {
    width: 48px;
    height: 24px;
  }

  &.lg {
    width: 60px;
    height: 32px;

    &::after {
      width: 26px;
      height: 26px;
    }

    .input:checked + & {
      &::after {
        transform: translateX(28px);
      }
    }
  }
}

.text {
  font-weight: 500;
  color: #333;
}

.description {
  font-size: 12px;
  color: #666;
  margin: 0;
  margin-left: 44px;
}

/* Label Styles */
.required {
  color: #dc3545;
  margin-left: 2px;
}

.error {
  color: #dc3545;
}

.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
"""


def generate_form_advanced_components(component_type: str) -> Dict[str, str]:
    """Generate advanced form components"""
    generator = FormAdvancedComponentGenerator()
    output = {}

    if component_type == "textarea":
        output["TextArea.tsx"] = generator.generate_textarea_component()

    elif component_type == "radio":
        output["RadioGroup.tsx"] = generator.generate_radio_group_component()

    elif component_type == "toggle":
        output["Toggle.tsx"] = generator.generate_toggle_component()

    elif component_type == "label":
        output["Label.tsx"] = generator.generate_form_label_component()

    if component_type in ["textarea", "radio", "toggle", "label"]:
        output[f"{component_type.capitalize()}.module.css"] = generator.generate_form_advanced_styles()

    return output
