"""
Specialized Components - DatePicker, TimePicker, Slider, Rating, Image, Video, Link, Badge variants

Generates:
- Date/time selection components
- Range slider
- Star rating
- Media components
- Link wrapper
"""

from typing import Dict, Any


class SpecializedComponentGenerator:
    """Generate specialized UI components"""

    def generate_date_picker_component(self) -> str:
        """Generate date picker component"""
        return """
import React, { useState } from 'react';
import styles from './DatePicker.module.css';

interface DatePickerProps {
  value?: Date;
  onChange?: (date: Date) => void;
  min?: Date;
  max?: Date;
  disabled?: boolean;
  label?: string;
  format?: string;
}

export const DatePicker: React.FC<DatePickerProps> = ({
  value,
  onChange,
  min,
  max,
  disabled,
  label,
  format = 'MM/DD/YYYY',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(value || new Date());

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const formatDate = (date: Date) => {
    const d = new Date(date);
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const year = d.getFullYear();
    return format.replace('MM', month).replace('DD', day).replace('YYYY', String(year));
  };

  const days = Array.from({ length: getDaysInMonth(currentMonth) }, (_, i) => i + 1);
  const firstDay = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1).getDay();
  const paddedDays = [...Array(firstDay).fill(null), ...days];

  return (
    <div className={styles.wrapper}>
      {label && <label className={styles.label}>{label}</label>}
      <button
        className={styles.input}
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
      >
        {value ? formatDate(value) : 'Select date'}
      </button>

      {isOpen && (
        <div className={styles.calendar}>
          <div className={styles.header}>
            <button onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}>
              ‹
            </button>
            <span>{currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</span>
            <button onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}>
              ›
            </button>
          </div>

          <div className={styles.weekDays}>
            {['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa'].map(day => (
              <div key={day} className={styles.weekDay}>{day}</div>
            ))}
          </div>

          <div className={styles.days}>
            {paddedDays.map((day, idx) => (
              <button
                key={idx}
                className={`${styles.day} ${!day ? styles.empty : ''} ${value && day === value.getDate() && value.getMonth() === currentMonth.getMonth() ? styles.selected : ''}`}
                onClick={() => {
                  if (day) {
                    const newDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
                    onChange?.(newDate);
                    setIsOpen(false);
                  }
                }}
                disabled={!day}
              >
                {day}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

DatePicker.displayName = 'DatePicker';
"""

    def generate_slider_component(self) -> str:
        """Generate range slider component"""
        return """
import React, { useRef, useState } from 'react';
import styles from './Slider.module.css';

interface SliderProps {
  min?: number;
  max?: number;
  value?: number;
  onChange?: (value: number) => void;
  step?: number;
  label?: string;
  disabled?: boolean;
  showValue?: boolean;
}

export const Slider: React.FC<SliderProps> = ({
  min = 0,
  max = 100,
  value = 0,
  onChange,
  step = 1,
  label,
  disabled = false,
  showValue = true,
}) => {
  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div className={styles.wrapper}>
      {label && <label className={styles.label}>{label}</label>}
      <div className={styles.container}>
        <input
          type="range"
          min={min}
          max={max}
          value={value}
          step={step}
          onChange={e => onChange?.(Number(e.target.value))}
          disabled={disabled}
          className={styles.input}
          style={{
            background: `linear-gradient(to right, #0066cc 0%, #0066cc ${percentage}%, #ddd ${percentage}%, #ddd 100%)`
          }}
          aria-valuemin={min}
          aria-valuemax={max}
          aria-valuenow={value}
        />
        {showValue && <span className={styles.value}>{value}</span>}
      </div>
    </div>
  );
};

Slider.displayName = 'Slider';
"""

    def generate_rating_component(self) -> str:
        """Generate star rating component"""
        return """
import React, { useState } from 'react';
import styles from './Rating.module.css';

interface RatingProps {
  value?: number;
  onChange?: (rating: number) => void;
  max?: number;
  readonly?: boolean;
  size?: 'sm' | 'md' | 'lg';
  color?: string;
}

export const Rating: React.FC<RatingProps> = ({
  value = 0,
  onChange,
  max = 5,
  readonly = false,
  size = 'md',
  color = '#ffc107',
}) => {
  const [hoverValue, setHoverValue] = useState<number | null>(null);

  return (
    <div className={`${styles.rating} ${styles[size]}`} role="slider" aria-label="Rating">
      {Array.from({ length: max }).map((_, i) => {
        const starValue = i + 1;
        const isFilled = (hoverValue || value) >= starValue;

        return (
          <button
            key={i}
            className={`${styles.star} ${isFilled ? styles.filled : ''}`}
            onClick={() => !readonly && onChange?.(starValue)}
            onMouseEnter={() => !readonly && setHoverValue(starValue)}
            onMouseLeave={() => setHoverValue(null)}
            disabled={readonly}
            style={isFilled ? { color } : {}}
            aria-label={`Rate ${starValue} out of ${max}`}
          >
            ★
          </button>
        );
      })}
    </div>
  );
};

Rating.displayName = 'Rating';
"""

    def generate_image_component(self) -> str:
        """Generate lazy-loaded image component"""
        return """
import React, { useState, useRef, useEffect } from 'react';
import styles from './Image.module.css';

interface ImageProps {
  src: string;
  alt: string;
  width?: string | number;
  height?: string | number;
  placeholder?: string;
  lazy?: boolean;
  className?: string;
  onLoad?: () => void;
  onError?: () => void;
}

export const Image: React.FC<ImageProps> = ({
  src,
  alt,
  width,
  height,
  placeholder,
  lazy = true,
  className,
  onLoad,
  onError,
}) => {
  const [isLoaded, setIsLoaded] = useState(!lazy);
  const [imageSrc, setImageSrc] = useState(lazy ? placeholder : src);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    if (!lazy) return;

    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setImageSrc(src);
        observer.unobserve(entry.target);
      }
    });

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, [lazy, src]);

  return (
    <div
      className={`${styles.container} ${isLoaded ? styles.loaded : ''}`}
      style={{ width, height }}
    >
      <img
        ref={imgRef}
        src={imageSrc}
        alt={alt}
        className={`${styles.image} ${className || ''}`}
        onLoad={() => {
          setIsLoaded(true);
          onLoad?.();
        }}
        onError={onError}
      />
    </div>
  );
};

Image.displayName = 'Image';
"""

    def generate_link_component(self) -> str:
        """Generate styled link component"""
        return """
import React from 'react';
import styles from './Link.module.css';

interface LinkProps {
  href: string;
  children: React.ReactNode;
  target?: '_blank' | '_self' | '_parent' | '_top';
  rel?: string;
  disabled?: boolean;
  variant?: 'default' | 'primary' | 'underline';
  className?: string;
  onClick?: (e: React.MouseEvent) => void;
}

export const Link: React.FC<LinkProps> = ({
  href,
  children,
  target,
  rel,
  disabled = false,
  variant = 'default',
  className,
  onClick,
}) => {
  const handleClick = (e: React.MouseEvent) => {
    if (disabled) {
      e.preventDefault();
      return;
    }
    onClick?.(e);
  };

  return (
    <a
      href={disabled ? undefined : href}
      target={target}
      rel={target === '_blank' ? `noopener noreferrer ${rel || ''}` : rel}
      onClick={handleClick}
      className={`${styles.link} ${styles[variant]} ${disabled ? styles.disabled : ''} ${className || ''}`}
      aria-disabled={disabled}
    >
      {children}
    </a>
  );
};

Link.displayName = 'Link';
"""

    def generate_specialized_styles(self) -> str:
        """Generate specialized component styles"""
        return """
/* DatePicker Styles */
.wrapper {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.label {
  font-weight: 600;
  font-size: 14px;
}

.input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  text-align: left;
}

.calendar {
  position: absolute;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  width: 280px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 600;
}

.weekDays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 8px;
}

.weekDay {
  text-align: center;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.day {
  padding: 8px;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;

  &:hover:not(.empty):not(:disabled) {
    background-color: #f0f0f0;
  }

  &.selected {
    background-color: #0066cc;
    color: white;
    border-color: #0066cc;
  }

  &.empty {
    cursor: default;
  }
}

/* Slider Styles */
.container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  outline: none;
  -webkit-appearance: none;

  &::-webkit-slider-thumb {
    appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #0066cc;
    cursor: pointer;
  }

  &::-moz-range-thumb {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #0066cc;
    cursor: pointer;
    border: none;
  }
}

.value {
  min-width: 40px;
  text-align: right;
  font-weight: 600;
  color: #0066cc;
}

/* Rating Styles */
.rating {
  display: flex;
  gap: 4px;
}

.star {
  background: transparent;
  border: none;
  cursor: pointer;
  color: #ddd;
  transition: color 0.2s;
  font-size: 24px;

  &:hover {
    color: #ffc107;
  }

  &.filled {
    color: #ffc107;
  }

  &:disabled {
    cursor: default;
  }

  &.sm {
    font-size: 16px;
  }

  &.md {
    font-size: 24px;
  }

  &.lg {
    font-size: 32px;
  }
}

/* Image Styles */
.container {
  overflow: hidden;
  background: #f0f0f0;
}

.image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.loaded .image {
  opacity: 1;
}

/* Link Styles */
.link {
  color: #0066cc;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s;

  &:hover:not(.disabled) {
    color: #0052a3;
  }

  &.underline {
    text-decoration: underline;
  }

  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}
"""


def generate_specialized_components(component_type: str) -> Dict[str, str]:
    """Generate specialized components"""
    generator = SpecializedComponentGenerator()
    output = {}

    if component_type == "datepicker":
        output["DatePicker.tsx"] = generator.generate_date_picker_component()

    elif component_type == "slider":
        output["Slider.tsx"] = generator.generate_slider_component()

    elif component_type == "rating":
        output["Rating.tsx"] = generator.generate_rating_component()

    elif component_type == "image":
        output["Image.tsx"] = generator.generate_image_component()

    elif component_type == "link":
        output["Link.tsx"] = generator.generate_link_component()

    if component_type in ["datepicker", "slider", "rating", "image", "link"]:
        output[f"{component_type.capitalize()}.module.css"] = generator.generate_specialized_styles()

    return output
