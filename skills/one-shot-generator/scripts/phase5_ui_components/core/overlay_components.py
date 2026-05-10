"""
Overlay Components - Drawer, Popover, Dropdown, Tooltip

Generates:
- Side drawer/sheet with animation
- Floating popover with positioning
- Dropdown menu with keyboard support
- Tooltip on hover
"""

from typing import Dict, Any


class OverlayComponentGenerator:
    """Generate overlay components"""

    def generate_drawer_component(self) -> str:
        """Generate side drawer component"""
        return """
import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import styles from './Drawer.module.css';

interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  position?: 'left' | 'right';
  width?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  title,
  position = 'right',
  width = '360px',
  children,
  footer,
}) => {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
      return () => {
        document.removeEventListener('keydown', handleEscape);
        document.body.style.overflow = 'auto';
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div className={styles.backdrop} onClick={onClose}>
      <div
        className={`${styles.drawer} ${styles[position]}`}
        style={{ width }}
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-labelledby={title ? 'drawer-title' : undefined}
        aria-modal="true"
      >
        {title && <div className={styles.header}>{title}</div>}
        <div className={styles.content}>{children}</div>
        {footer && <div className={styles.footer}>{footer}</div>}
      </div>
    </div>,
    document.body
  );
};

Drawer.displayName = 'Drawer';
"""

    def generate_popover_component(self) -> str:
        """Generate popover component"""
        return """
import React, { useRef, useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import styles from './Popover.module.css';

export type PopoverPosition = 'top' | 'bottom' | 'left' | 'right';

interface PopoverProps {
  trigger: React.ReactNode;
  content: React.ReactNode;
  position?: PopoverPosition;
  offset?: number;
  closeOnClickOutside?: boolean;
  onOpenChange?: (isOpen: boolean) => void;
}

export const Popover: React.FC<PopoverProps> = ({
  trigger,
  content,
  position = 'bottom',
  offset = 8,
  closeOnClickOutside = true,
  onOpenChange,
}) => {
  const triggerRef = useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [popoverStyle, setPopoverStyle] = useState({});

  useEffect(() => {
    if (isOpen && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      const newStyle: React.CSSProperties = { position: 'fixed' };

      switch (position) {
        case 'top':
          newStyle.bottom = window.innerHeight - rect.top + offset;
          newStyle.left = rect.left + rect.width / 2;
          newStyle.transform = 'translateX(-50%)';
          break;
        case 'bottom':
          newStyle.top = rect.bottom + offset;
          newStyle.left = rect.left + rect.width / 2;
          newStyle.transform = 'translateX(-50%)';
          break;
        case 'left':
          newStyle.top = rect.top + rect.height / 2;
          newStyle.right = window.innerWidth - rect.left + offset;
          newStyle.transform = 'translateY(-50%)';
          break;
        case 'right':
          newStyle.top = rect.top + rect.height / 2;
          newStyle.left = rect.right + offset;
          newStyle.transform = 'translateY(-50%)';
          break;
      }

      setPopoverStyle(newStyle);
    }
  }, [isOpen, position, offset]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (closeOnClickOutside && triggerRef.current && !triggerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        onOpenChange?.(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, closeOnClickOutside, onOpenChange]);

  return (
    <>
      <div
        ref={triggerRef}
        onClick={() => {
          setIsOpen(!isOpen);
          onOpenChange?.(!isOpen);
        }}
        className={styles.trigger}
      >
        {trigger}
      </div>

      {isOpen &&
        createPortal(
          <div
            className={`${styles.popover} ${styles[position]}`}
            style={popoverStyle}
            role="dialog"
            aria-modal="false"
          >
            {content}
          </div>,
          document.body
        )}
    </>
  );
};

Popover.displayName = 'Popover';
"""

    def generate_dropdown_component(self) -> str:
        """Generate dropdown menu"""
        return """
import React, { useRef, useState, useEffect } from 'react';
import styles from './Dropdown.module.css';

export interface DropdownItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  onClick?: () => void;
  divider?: boolean;
  disabled?: boolean;
}

interface DropdownProps {
  trigger: React.ReactNode;
  items: DropdownItem[];
  onSelect?: (id: string) => void;
}

export const Dropdown: React.FC<DropdownProps> = ({
  trigger,
  items,
  onSelect,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const triggerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (triggerRef.current && !triggerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const handleSelect = (id: string, onClick?: () => void) => {
    onClick?.();
    onSelect?.(id);
    setIsOpen(false);
  };

  return (
    <div ref={triggerRef} className={styles.dropdown}>
      <button
        className={styles.trigger}
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="menu"
        aria-expanded={isOpen}
      >
        {trigger}
      </button>

      {isOpen && (
        <div className={styles.menu} role="menu">
          {items.map((item, idx) => (
            item.divider ? (
              <div key={idx} className={styles.divider} role="separator" />
            ) : (
              <button
                key={item.id}
                className={`${styles.item} ${item.disabled ? styles.disabled : ''}`}
                onClick={() => handleSelect(item.id, item.onClick)}
                disabled={item.disabled}
                role="menuitem"
              >
                {item.icon && <span className={styles.icon}>{item.icon}</span>}
                {item.label}
              </button>
            )
          ))}
        </div>
      )}
    </div>
  );
};

Dropdown.displayName = 'Dropdown';
"""

    def generate_tooltip_component(self) -> str:
        """Generate tooltip component"""
        return """
import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import styles from './Tooltip.module.css';

export type TooltipPosition = 'top' | 'bottom' | 'left' | 'right';

interface TooltipProps {
  content: string;
  children: React.ReactElement;
  position?: TooltipPosition;
  delay?: number;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'top',
  delay = 300,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipStyle, setTooltipStyle] = useState({});
  const triggerRef = useRef<HTMLDivElement>(null);
  const delayRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (isVisible && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      const newStyle: React.CSSProperties = { position: 'fixed' };

      const offset = 8;

      switch (position) {
        case 'top':
          newStyle.bottom = window.innerHeight - rect.top + offset;
          newStyle.left = rect.left + rect.width / 2;
          newStyle.transform = 'translateX(-50%)';
          break;
        case 'bottom':
          newStyle.top = rect.bottom + offset;
          newStyle.left = rect.left + rect.width / 2;
          newStyle.transform = 'translateX(-50%)';
          break;
        case 'left':
          newStyle.top = rect.top + rect.height / 2;
          newStyle.right = window.innerWidth - rect.left + offset;
          newStyle.transform = 'translateY(-50%)';
          break;
        case 'right':
          newStyle.top = rect.top + rect.height / 2;
          newStyle.left = rect.right + offset;
          newStyle.transform = 'translateY(-50%)';
          break;
      }

      setTooltipStyle(newStyle);
    }
  }, [isVisible, position]);

  const handleMouseEnter = () => {
    delayRef.current = setTimeout(() => setIsVisible(true), delay);
  };

  const handleMouseLeave = () => {
    if (delayRef.current) clearTimeout(delayRef.current);
    setIsVisible(false);
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {React.cloneElement(children, {
          'aria-describedby': isVisible ? 'tooltip' : undefined,
        })}
      </div>

      {isVisible &&
        createPortal(
          <div
            id="tooltip"
            className={`${styles.tooltip} ${styles[position]}`}
            style={tooltipStyle}
            role="tooltip"
          >
            {content}
          </div>,
          document.body
        )}
    </>
  );
};

Tooltip.displayName = 'Tooltip';
"""

    def generate_overlay_styles(self) -> str:
        """Generate overlay component styles"""
        return """
/* Drawer Styles */
.backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

.drawer {
  position: fixed;
  top: 0;
  height: 100%;
  background: white;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s ease;
  z-index: 1001;

  &.left {
    left: 0;
    animation-name: slideInLeft;
  }

  &.right {
    right: 0;
    animation-name: slideInRight;
  }
}

.header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  font-size: 18px;
  font-weight: 600;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.footer {
  padding: 20px;
  border-top: 1px solid #eee;
}

/* Popover Styles */
.trigger {
  cursor: pointer;
}

.popover {
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-width: 300px;
  animation: fadeIn 0.2s ease;

  &.top::after,
  &.bottom::after,
  &.left::after,
  &.right::after {
    content: '';
    position: absolute;
    width: 8px;
    height: 8px;
    background: white;
    border: 1px solid #ddd;
  }

  &.top::after {
    bottom: -4px;
    left: 50%;
    transform: translateX(-50%) rotate(45deg);
  }

  &.bottom::after {
    top: -4px;
    left: 50%;
    transform: translateX(-50%) rotate(45deg);
  }

  &.left::after {
    right: -4px;
    top: 50%;
    transform: translateY(-50%) rotate(45deg);
  }

  &.right::after {
    left: -4px;
    top: 50%;
    transform: translateY(-50%) rotate(45deg);
  }
}

/* Dropdown Styles */
.dropdown {
  position: relative;
  display: inline-block;
}

.menu {
  position: absolute;
  top: 100%;
  left: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  min-width: 160px;
  margin-top: 4px;
  animation: slideDown 0.2s ease;
}

.item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 10px 12px;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
  font-size: 14px;
  color: #333;
  transition: background-color 0.2s;

  &:hover:not(:disabled) {
    background-color: #f5f5f5;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.icon {
  margin-right: 8px;
}

.divider {
  height: 1px;
  background: #eee;
  margin: 4px 0;
}

/* Tooltip Styles */
.tooltip {
  background: #333;
  color: white;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  white-space: nowrap;
  z-index: 1000;
  animation: fadeIn 0.2s ease;

  &.top::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 4px solid transparent;
    border-top-color: #333;
  }

  &.bottom::after {
    content: '';
    position: absolute;
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 4px solid transparent;
    border-bottom-color: #333;
  }
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

@keyframes slideInLeft {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(0);
  }
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
"""


def generate_overlay_components(component_type: str) -> Dict[str, str]:
    """Generate overlay components"""
    generator = OverlayComponentGenerator()
    output = {}

    if component_type == "drawer":
        output["Drawer.tsx"] = generator.generate_drawer_component()

    elif component_type == "popover":
        output["Popover.tsx"] = generator.generate_popover_component()

    elif component_type == "dropdown":
        output["Dropdown.tsx"] = generator.generate_dropdown_component()

    elif component_type == "tooltip":
        output["Tooltip.tsx"] = generator.generate_tooltip_component()

    if component_type in ["drawer", "popover", "dropdown", "tooltip"]:
        output[f"{component_type.capitalize()}.module.css"] = generator.generate_overlay_styles()

    return output
