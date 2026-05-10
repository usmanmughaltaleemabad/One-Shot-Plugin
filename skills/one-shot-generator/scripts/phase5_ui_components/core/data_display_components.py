"""
Data Display Components - List, Badge, Avatar, Spinner, Progress, Skeleton

Generates:
- List view with item actions
- Badge/tag component
- Avatar with initials fallback
- Loading spinners
- Progress indicators
- Skeleton placeholder
"""

from typing import Dict, Any


class DataDisplayComponentGenerator:
    """Generate data display components"""

    def generate_list_component(self) -> str:
        """Generate list view component"""
        return """
import React from 'react';
import styles from './List.module.css';

export interface ListItem {
  id: string | number;
  title: string;
  subtitle?: string;
  avatar?: string;
  actions?: { label: string; onClick: () => void }[];
}

interface ListProps {
  items: ListItem[];
  onItemClick?: (item: ListItem) => void;
  isLoading?: boolean;
  emptyMessage?: string;
}

export const List: React.FC<ListProps> = ({
  items,
  onItemClick,
  isLoading,
  emptyMessage = 'No items found',
}) => {
  if (isLoading) {
    return (
      <div className={styles.list}>
        {[...Array(3)].map((_, i) => (
          <div key={i} className={styles.skeleton} />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return <div className={styles.empty}>{emptyMessage}</div>;
  }

  return (
    <ul className={styles.list} role="list">
      {items.map(item => (
        <li key={item.id} className={styles.item}>
          <div className={styles.content} onClick={() => onItemClick?.(item)}>
            {item.avatar && <img src={item.avatar} alt="" className={styles.avatar} />}
            <div className={styles.text}>
              <div className={styles.title}>{item.title}</div>
              {item.subtitle && <div className={styles.subtitle}>{item.subtitle}</div>}
            </div>
          </div>
          {item.actions && (
            <div className={styles.actions}>
              {item.actions.map((action, idx) => (
                <button
                  key={idx}
                  onClick={action.onClick}
                  className={styles.actionButton}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </li>
      ))}
    </ul>
  );
};

List.displayName = 'List';
"""

    def generate_badge_component(self) -> str:
        """Generate badge/tag component"""
        return """
import React from 'react';
import styles from './Badge.module.css';

export type BadgeVariant = 'default' | 'primary' | 'success' | 'warning' | 'error';
export type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  closable?: boolean;
  onClose?: () => void;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'default',
  size = 'md',
  closable = false,
  onClose,
  className,
}) => {
  return (
    <span className={`${styles.badge} ${styles[variant]} ${styles[size]} ${className || ''}`}>
      {children}
      {closable && (
        <button
          onClick={onClose}
          className={styles.closeButton}
          aria-label="Remove badge"
        >
          ✕
        </button>
      )}
    </span>
  );
};

Badge.displayName = 'Badge';
"""

    def generate_avatar_component(self) -> str:
        """Generate avatar component"""
        return """
import React from 'react';
import styles from './Avatar.module.css';

export type AvatarSize = 'sm' | 'md' | 'lg' | 'xl';

interface AvatarProps {
  src?: string;
  alt?: string;
  initials?: string;
  size?: AvatarSize;
  color?: string;
  className?: string;
}

export const Avatar: React.FC<AvatarProps> = ({
  src,
  alt = 'Avatar',
  initials,
  size = 'md',
  color,
  className,
}) => {
  return (
    <div
      className={`${styles.avatar} ${styles[size]} ${className || ''}`}
      style={{ backgroundColor: color }}
    >
      {src ? (
        <img src={src} alt={alt} className={styles.image} />
      ) : initials ? (
        <span className={styles.initials}>{initials}</span>
      ) : (
        <span className={styles.icon}>👤</span>
      )}
    </div>
  );
};

Avatar.displayName = 'Avatar';
"""

    def generate_spinner_component(self) -> str:
        """Generate loading spinner"""
        return """
import React from 'react';
import styles from './Spinner.module.css';

export type SpinnerSize = 'sm' | 'md' | 'lg';

interface SpinnerProps {
  size?: SpinnerSize;
  color?: string;
  label?: string;
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  color,
  label,
  className,
}) => {
  return (
    <div className={`${styles.container} ${className || ''}`}>
      <div
        className={`${styles.spinner} ${styles[size]}`}
        style={{ borderTopColor: color }}
        role="status"
        aria-label={label || 'Loading'}
      />
      {label && <p className={styles.label}>{label}</p>}
    </div>
  );
};

Spinner.displayName = 'Spinner';
"""

    def generate_progress_component(self) -> str:
        """Generate progress indicator"""
        return """
import React from 'react';
import styles from './Progress.module.css';

interface ProgressProps {
  value: number;
  max?: number;
  label?: string;
  showLabel?: boolean;
  variant?: 'default' | 'success' | 'warning' | 'error';
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  label,
  showLabel = true,
  variant = 'default',
  size = 'md',
  animated = false,
}) => {
  const percentage = (value / max) * 100;

  return (
    <div className={styles.container}>
      {showLabel && (label || `${Math.round(percentage)}%`) && (
        <div className={styles.labelContainer}>
          <span className={styles.label}>{label || `${Math.round(percentage)}%`}</span>
        </div>
      )}
      <div className={`${styles.bar} ${styles[size]}`}>
        <div
          className={`${styles.fill} ${styles[variant]} ${animated ? styles.animated : ''}`}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
        />
      </div>
    </div>
  );
};

Progress.displayName = 'Progress';
"""

    def generate_skeleton_component(self) -> str:
        """Generate skeleton placeholder"""
        return """
import React from 'react';
import styles from './Skeleton.module.css';

export type SkeletonVariant = 'text' | 'circular' | 'rectangular';

interface SkeletonProps {
  variant?: SkeletonVariant;
  width?: string | number;
  height?: string | number;
  count?: number;
  animated?: boolean;
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'text',
  width = '100%',
  height = '20px',
  count = 1,
  animated = true,
  className,
}) => {
  const items = [...Array(count)].map((_, i) => (
    <div
      key={i}
      className={`${styles.skeleton} ${styles[variant]} ${animated ? styles.animated : ''} ${className || ''}`}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
      }}
    />
  ));

  return count === 1 ? items[0] : <div className={styles.container}>{items}</div>;
};

Skeleton.displayName = 'Skeleton';
"""

    def generate_data_display_styles(self) -> str:
        """Generate data display styles"""
        return """
/* List Styles */
.list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  transition: background-color 0.2s;

  &:hover {
    background-color: #f9f9f9;
  }
}

.content {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 12px;
  cursor: pointer;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.text {
  flex: 1;
}

.title {
  font-weight: 500;
  color: #333;
}

.subtitle {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.actions {
  display: flex;
  gap: 8px;
}

.actionButton {
  padding: 6px 12px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;

  &:hover {
    border-color: #0066cc;
    color: #0066cc;
  }
}

.empty {
  padding: 40px 20px;
  text-align: center;
  color: #999;
}

.skeleton {
  padding: 12px 16px;
  margin-bottom: 8px;
  height: 60px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  border-radius: 4px;

  &.animated {
    animation: shimmer 1.5s infinite;
  }
}

/* Badge Styles */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  background-color: #e0e0e0;
  color: #333;

  &.primary {
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

  &.sm {
    padding: 2px 6px;
  }

  &.lg {
    padding: 6px 12px;
  }
}

.closeButton {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 12px;
  padding: 0;
  opacity: 0.7;

  &:hover {
    opacity: 1;
  }
}

/* Avatar Styles */
.avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: #e0e0e0;
  color: white;
  font-weight: 600;

  &.sm {
    width: 32px;
    height: 32px;
    font-size: 12px;
  }

  &.md {
    width: 40px;
    height: 40px;
    font-size: 14px;
  }

  &.lg {
    width: 56px;
    height: 56px;
    font-size: 18px;
  }

  &.xl {
    width: 80px;
    height: 80px;
    font-size: 24px;
  }
}

.image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.initials {
  text-transform: uppercase;
}

.icon {
  font-size: 1.5em;
}

/* Spinner Styles */
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.spinner {
  border: 3px solid #f0f0f0;
  border-top: 3px solid #0066cc;
  border-radius: 50%;
  animation: spin 1s linear infinite;

  &.sm {
    width: 24px;
    height: 24px;
  }

  &.md {
    width: 40px;
    height: 40px;
  }

  &.lg {
    width: 56px;
    height: 56px;
  }
}

.label {
  font-size: 14px;
  color: #666;
}

/* Progress Styles */
.bar {
  width: 100%;
  background-color: #f0f0f0;
  border-radius: 8px;
  overflow: hidden;

  &.sm {
    height: 4px;
  }

  &.md {
    height: 8px;
  }

  &.lg {
    height: 12px;
  }
}

.fill {
  height: 100%;
  background-color: #0066cc;
  transition: width 0.3s ease;

  &.success {
    background-color: #28a745;
  }

  &.warning {
    background-color: #ffc107;
  }

  &.error {
    background-color: #dc3545;
  }

  &.animated {
    animation: progress 1.5s ease-in-out infinite;
  }
}

/* Skeleton Styles */
.skeleton {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  border-radius: 4px;

  &.circular {
    border-radius: 50%;
  }

  &.rectangular {
    border-radius: 0;
  }

  &.animated {
    animation: shimmer 1.5s infinite;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}

@keyframes progress {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
"""


def generate_data_display_components(component_type: str) -> Dict[str, str]:
    """Generate data display components"""
    generator = DataDisplayComponentGenerator()
    output = {}

    if component_type == "list":
        output["List.tsx"] = generator.generate_list_component()

    elif component_type == "badge":
        output["Badge.tsx"] = generator.generate_badge_component()

    elif component_type == "avatar":
        output["Avatar.tsx"] = generator.generate_avatar_component()

    elif component_type == "spinner":
        output["Spinner.tsx"] = generator.generate_spinner_component()

    elif component_type == "progress":
        output["Progress.tsx"] = generator.generate_progress_component()

    elif component_type == "skeleton":
        output["Skeleton.tsx"] = generator.generate_skeleton_component()

    if component_type in ["list", "badge", "avatar", "spinner", "progress", "skeleton"]:
        output[f"{component_type.capitalize()}.module.css"] = generator.generate_data_display_styles()

    return output
