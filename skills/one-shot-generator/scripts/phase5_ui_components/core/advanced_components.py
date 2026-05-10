"""
Advanced React Components - Data display, overlays, and layout

Generates:
- Table with sorting/filtering
- Modal dialogs with backdrop focus management
- Card and container components
- Pagination and navigation
"""

from typing import Dict, Any


class AdvancedComponentGenerator:
    """Generate advanced UI components"""

    def generate_table_component(self) -> str:
        """Generate data table with sorting and filtering"""
        return """
import React, { useState, useMemo } from 'react';
import styles from './Table.module.css';

export interface Column<T> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  width?: string;
  render?: (value: T[keyof T], row: T) => React.ReactNode;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  selectable?: boolean;
  onSelectionChange?: (selected: T[]) => void;
  onRowClick?: (row: T) => void;
}

type SortOrder = 'asc' | 'desc' | null;

export const Table = <T extends { id: string | number }>({
  data,
  columns,
  selectable = false,
  onSelectionChange,
  onRowClick,
}: TableProps<T>) => {
  const [sortKey, setSortKey] = useState<keyof T | null>(null);
  const [sortOrder, setSortOrder] = useState<SortOrder>(null);
  const [selectedRows, setSelectedRows] = useState<Set<string | number>>(new Set());

  const sortedData = useMemo(() => {
    if (!sortKey || !sortOrder) return data;

    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data, sortKey, sortOrder]);

  const handleSort = (key: keyof T) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : sortOrder === 'desc' ? null : 'asc');
      if (sortOrder === 'desc') setSortKey(null);
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
  };

  const handleSelectRow = (id: string | number) => {
    const updated = new Set(selectedRows);
    updated.has(id) ? updated.delete(id) : updated.add(id);
    setSelectedRows(updated);
    onSelectionChange?.(sortedData.filter(r => updated.has(r.id)));
  };

  const handleSelectAll = () => {
    if (selectedRows.size === sortedData.length) {
      setSelectedRows(new Set());
      onSelectionChange?.([]);
    } else {
      const allIds = new Set(sortedData.map(r => r.id));
      setSelectedRows(allIds);
      onSelectionChange?.(sortedData);
    }
  };

  return (
    <div className={styles.tableWrapper}>
      <table className={styles.table}>
        <thead>
          <tr>
            {selectable && (
              <th className={styles.checkboxCol}>
                <input
                  type="checkbox"
                  checked={selectedRows.size === sortedData.length && sortedData.length > 0}
                  onChange={handleSelectAll}
                  aria-label="Select all rows"
                />
              </th>
            )}
            {columns.map(col => (
              <th
                key={String(col.key)}
                style={{ width: col.width }}
                onClick={() => col.sortable && handleSort(col.key)}
                className={col.sortable ? styles.sortable : ''}
              >
                <div className={styles.headerContent}>
                  {col.label}
                  {col.sortable && sortKey === col.key && (
                    <span className={styles.sortIcon}>
                      {sortOrder === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map(row => (
            <tr
              key={row.id}
              onClick={() => onRowClick?.(row)}
              className={selectedRows.has(row.id) ? styles.selected : ''}
            >
              {selectable && (
                <td className={styles.checkboxCol}>
                  <input
                    type="checkbox"
                    checked={selectedRows.has(row.id)}
                    onChange={() => handleSelectRow(row.id)}
                    onClick={e => e.stopPropagation()}
                  />
                </td>
              )}
              {columns.map(col => (
                <td key={String(col.key)}>
                  {col.render ? col.render(row[col.key], row) : String(row[col.key])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

Table.displayName = 'Table';
"""

    def generate_modal_component(self) -> str:
        """Generate modal dialog with backdrop"""
        return """
import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import styles from './Modal.module.css';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  closeButton?: boolean;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  closeButton = true,
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
        className={`${styles.modal} ${styles[size]}`}
        onClick={e => e.stopPropagation()}
        role="dialog"
        aria-labelledby="modal-title"
        aria-modal="true"
      >
        {(title || closeButton) && (
          <div className={styles.header}>
            {title && <h2 id="modal-title" className={styles.title}>{title}</h2>}
            {closeButton && (
              <button
                className={styles.closeButton}
                onClick={onClose}
                aria-label="Close modal"
              >
                ✕
              </button>
            )}
          </div>
        )}
        <div className={styles.content}>{children}</div>
        {footer && <div className={styles.footer}>{footer}</div>}
      </div>
    </div>,
    document.body
  );
};

Modal.displayName = 'Modal';
"""

    def generate_card_component(self) -> str:
        """Generate card container component"""
        return """
import React from 'react';
import styles from './Card.module.css';

interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  footer?: React.ReactNode;
  onClick?: () => void;
  hoverable?: boolean;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  footer,
  onClick,
  hoverable = false,
  className,
}) => {
  return (
    <div
      className={`${styles.card} ${hoverable ? styles.hoverable : ''} ${className || ''}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyPress={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
    >
      {(title || subtitle) && (
        <div className={styles.header}>
          {title && <h3 className={styles.title}>{title}</h3>}
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        </div>
      )}
      <div className={styles.content}>{children}</div>
      {footer && <div className={styles.footer}>{footer}</div>}
    </div>
  );
};

Card.displayName = 'Card';
"""

    def generate_modal_styles(self) -> str:
        """Generate Modal styles"""
        return """
.backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  overflow: hidden;
  animation: slideUp 0.3s ease;

  &.sm {
    width: 90%;
    max-width: 400px;
  }

  &.md {
    width: 90%;
    max-width: 600px;
  }

  &.lg {
    width: 90%;
    max-width: 800px;
  }
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.closeButton {
  background: transparent;
  border: none;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  color: #666;
  transition: color 0.2s;

  &:hover {
    color: #333;
  }
}

.content {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.footer {
  padding: 20px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
"""

    def generate_card_styles(self) -> str:
        """Generate Card styles"""
        return """
.card {
  background: white;
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s ease;

  &.hoverable {
    cursor: pointer;

    &:hover {
      border-color: #0066cc;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      transform: translateY(-2px);
    }

    &:active {
      transform: translateY(0);
    }
  }
}

.header {
  padding: 16px;
  border-bottom: 1px solid #eee;
}

.title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.subtitle {
  margin: 4px 0 0;
  font-size: 14px;
  color: #666;
}

.content {
  padding: 16px;
}

.footer {
  padding: 16px;
  border-top: 1px solid #eee;
  background: #f9f9f9;
}
"""

    def generate_table_styles(self) -> str:
        """Generate Table styles"""
        return """
.tableWrapper {
  overflow-x: auto;
  border: 1px solid #eee;
  border-radius: 4px;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;

  thead {
    background-color: #f5f5f5;
    border-bottom: 2px solid #eee;
  }

  th {
    padding: 12px;
    text-align: left;
    font-weight: 600;
    color: #333;
    white-space: nowrap;
  }

  td {
    padding: 12px;
    border-bottom: 1px solid #eee;
    color: #666;
  }

  tbody tr:hover {
    background-color: #f9f9f9;
  }

  tbody tr.selected {
    background-color: #f0f7ff;
  }
}

.sortable {
  cursor: pointer;
  user-select: none;

  &:hover {
    background-color: #efefef;
  }
}

.headerContent {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sortIcon {
  font-size: 12px;
}

.checkboxCol {
  width: 40px;
  padding: 8px;
  text-align: center;
}
"""


def generate_advanced_components(component_type: str) -> Dict[str, str]:
    """Generate advanced components"""
    generator = AdvancedComponentGenerator()
    output = {}

    if component_type == "table":
        output["Table.tsx"] = generator.generate_table_component()
        output["Table.module.css"] = generator.generate_table_styles()

    elif component_type == "modal":
        output["Modal.tsx"] = generator.generate_modal_component()
        output["Modal.module.css"] = generator.generate_modal_styles()

    elif component_type == "card":
        output["Card.tsx"] = generator.generate_card_component()
        output["Card.module.css"] = generator.generate_card_styles()

    return output
