"""
Navigation Components - Tabs, Pagination, Breadcrumb, Stepper

Generates:
- Tabbed interface with keyboard support
- Pagination controls
- Breadcrumb navigation
- Multi-step wizard stepper
"""

from typing import Dict, Any, List


class NavigationComponentGenerator:
    """Generate navigation components"""

    def generate_tabs_component(self) -> str:
        """Generate tabs component"""
        return """
import React, { useState } from 'react';
import styles from './Tabs.module.css';

export interface TabItem {
  id: string;
  label: string;
  content: React.ReactNode;
  disabled?: boolean;
}

interface TabsProps {
  tabs: TabItem[];
  defaultTab?: string;
  onChange?: (tabId: string) => void;
  variant?: 'default' | 'pills' | 'underline';
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  defaultTab,
  onChange,
  variant = 'default',
}) => {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
    onChange?.(tabId);
  };

  const activeTabItem = tabs.find(t => t.id === activeTab);

  return (
    <div className={`${styles.tabs} ${styles[variant]}`}>
      <div className={styles.tabList} role="tablist">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`${styles.tab} ${activeTab === tab.id ? styles.active : ''}`}
            onClick={() => handleTabChange(tab.id)}
            disabled={tab.disabled}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`panel-${tab.id}`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className={styles.content}>
        {activeTabItem && (
          <div
            id={`panel-${activeTabItem.id}`}
            className={styles.tabPanel}
            role="tabpanel"
            aria-labelledby={`tab-${activeTabItem.id}`}
          >
            {activeTabItem.content}
          </div>
        )}
      </div>
    </div>
  );
};

Tabs.displayName = 'Tabs';
"""

    def generate_pagination_component(self) -> str:
        """Generate pagination controls"""
        return """
import React from 'react';
import styles from './Pagination.module.css';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  siblingCount?: number;
  showFirstLast?: boolean;
}

export const Pagination: React.FC<PaginationProps> = ({
  currentPage,
  totalPages,
  onPageChange,
  siblingCount = 1,
  showFirstLast = true,
}) => {
  const getPageNumbers = () => {
    const delta = siblingCount + 2;
    const range = [];

    for (let i = Math.max(2, currentPage - delta); i <= Math.min(totalPages - 1, currentPage + delta); i++) {
      range.push(i);
    }

    if (currentPage - delta > 2) range.unshift('...');
    if (currentPage + delta < totalPages - 1) range.push('...');
    if (totalPages > 1) range.unshift(1);
    if (totalPages > 0) range.push(totalPages);

    return range;
  };

  const pages = getPageNumbers();

  return (
    <nav className={styles.pagination} aria-label="Pagination">
      <button
        className={styles.button}
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        aria-label="Previous page"
      >
        ← Previous
      </button>

      <div className={styles.pages}>
        {showFirstLast && currentPage > 1 && (
          <button
            className={styles.pageButton}
            onClick={() => onPageChange(1)}
            aria-label="Go to page 1"
          >
            1
          </button>
        )}

        {pages.map((page, idx) => (
          <React.Fragment key={idx}>
            {typeof page === 'number' ? (
              <button
                className={`${styles.pageButton} ${currentPage === page ? styles.active : ''}`}
                onClick={() => onPageChange(page)}
                aria-current={currentPage === page ? 'page' : undefined}
                aria-label={`Go to page ${page}`}
              >
                {page}
              </button>
            ) : (
              <span className={styles.ellipsis}>{page}</span>
            )}
          </React.Fragment>
        ))}
      </div>

      <button
        className={styles.button}
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        aria-label="Next page"
      >
        Next →
      </button>
    </nav>
  );
};

Pagination.displayName = 'Pagination';
"""

    def generate_breadcrumb_component(self) -> str:
        """Generate breadcrumb navigation"""
        return """
import React from 'react';
import styles from './Breadcrumb.module.css';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  onClick?: () => void;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  separator?: React.ReactNode;
}

export const Breadcrumb: React.FC<BreadcrumbProps> = ({
  items,
  separator = '/',
}) => {
  return (
    <nav className={styles.breadcrumb} aria-label="Breadcrumb">
      <ol className={styles.list}>
        {items.map((item, idx) => (
          <li key={idx}>
            {item.href || item.onClick ? (
              <a
                href={item.href}
                className={styles.link}
                onClick={e => {
                  if (item.onClick) {
                    e.preventDefault();
                    item.onClick();
                  }
                }}
              >
                {item.label}
              </a>
            ) : (
              <span className={styles.current} aria-current="page">
                {item.label}
              </span>
            )}
            {idx < items.length - 1 && <span className={styles.separator}>{separator}</span>}
          </li>
        ))}
      </ol>
    </nav>
  );
};

Breadcrumb.displayName = 'Breadcrumb';
"""

    def generate_stepper_component(self) -> str:
        """Generate multi-step wizard stepper"""
        return """
import React from 'react';
import styles from './Stepper.module.css';

export interface Step {
  id: string;
  label: string;
  description?: string;
  content: React.ReactNode;
  completed?: boolean;
  error?: boolean;
}

interface StepperProps {
  steps: Step[];
  currentStep: number;
  onStepChange?: (step: number) => void;
  showLabels?: boolean;
  orientation?: 'horizontal' | 'vertical';
}

export const Stepper: React.FC<StepperProps> = ({
  steps,
  currentStep,
  onStepChange,
  showLabels = true,
  orientation = 'horizontal',
}) => {
  const handleStepClick = (idx: number) => {
    if (idx < currentStep || steps[idx].completed) {
      onStepChange?.(idx);
    }
  };

  return (
    <div className={`${styles.stepper} ${styles[orientation]}`}>
      <div className={styles.stepsHeader}>
        {steps.map((step, idx) => (
          <div key={step.id} className={styles.stepWrapper}>
            <button
              className={`${styles.step} ${idx < currentStep ? styles.completed : ''} ${idx === currentStep ? styles.active : ''} ${step.error ? styles.error : ''}`}
              onClick={() => handleStepClick(idx)}
              disabled={idx > currentStep && !step.completed}
              aria-current={idx === currentStep ? 'step' : undefined}
            >
              <span className={styles.stepNumber}>
                {idx < currentStep ? '✓' : idx + 1}
              </span>
            </button>
            {showLabels && (
              <div className={styles.stepLabel}>
                <div className={styles.label}>{step.label}</div>
                {step.description && <div className={styles.description}>{step.description}</div>}
              </div>
            )}
            {idx < steps.length - 1 && <div className={styles.connector} />}
          </div>
        ))}
      </div>
      <div className={styles.stepContent}>
        {steps[currentStep] && steps[currentStep].content}
      </div>
    </div>
  );
};

Stepper.displayName = 'Stepper';
"""

    def generate_navigation_styles(self) -> str:
        """Generate navigation component styles"""
        return """
/* Tabs Styles */
.tabs {
  width: 100%;
}

.tabList {
  display: flex;
  border-bottom: 2px solid #eee;
  gap: 0;
}

.tab {
  padding: 12px 16px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-weight: 500;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;

  &:hover {
    color: #333;
  }

  &.active {
    color: #0066cc;
    border-bottom-color: #0066cc;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.tabPanel {
  padding: 20px 0;
}

/* Pagination Styles */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px 0;
}

.button {
  padding: 8px 12px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;

  &:hover:not(:disabled) {
    border-color: #0066cc;
    color: #0066cc;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.pages {
  display: flex;
  gap: 4px;
}

.pageButton {
  width: 36px;
  height: 36px;
  padding: 0;
  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;

  &:hover {
    border-color: #0066cc;
  }

  &.active {
    background: #0066cc;
    color: white;
    border-color: #0066cc;
  }
}

.ellipsis {
  padding: 0 4px;
  color: #666;
}

/* Breadcrumb Styles */
.breadcrumb {
  padding: 16px 0;
}

.list {
  list-style: none;
  display: flex;
  margin: 0;
  padding: 0;
  gap: 0;
}

.link {
  color: #0066cc;
  text-decoration: none;
  padding: 4px 8px;

  &:hover {
    text-decoration: underline;
  }
}

.current {
  color: #666;
  padding: 4px 8px;
}

.separator {
  color: #ddd;
  padding: 0 8px;
}

/* Stepper Styles */
.stepper {
  width: 100%;

  &.horizontal {
    .stepsHeader {
      display: flex;
      justify-content: space-between;
    }
  }

  &.vertical {
    .stepsHeader {
      display: flex;
      flex-direction: column;
      gap: 24px;
    }
  }
}

.stepsHeader {
  margin-bottom: 30px;
}

.stepWrapper {
  display: flex;
  align-items: center;
  flex: 1;
  position: relative;
}

.step {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid #ddd;
  background: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: #666;
  transition: all 0.2s;
  flex-shrink: 0;

  &:hover:not(:disabled) {
    border-color: #0066cc;
  }

  &.active {
    border-color: #0066cc;
    color: #0066cc;
  }

  &.completed {
    background: #28a745;
    border-color: #28a745;
    color: white;
  }

  &.error {
    border-color: #dc3545;
    color: #dc3545;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.stepNumber {
  font-size: 16px;
}

.stepLabel {
  margin-left: 12px;
}

.label {
  font-weight: 500;
  color: #333;
}

.description {
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

.connector {
  flex: 1;
  height: 2px;
  background: #ddd;
  margin: 0 16px;
  position: relative;
  top: -22px;
}

.stepContent {
  padding: 20px 0;
}
"""


def generate_navigation_components(component_type: str) -> Dict[str, str]:
    """Generate navigation components"""
    generator = NavigationComponentGenerator()
    output = {}

    if component_type == "tabs":
        output["Tabs.tsx"] = generator.generate_tabs_component()

    elif component_type == "pagination":
        output["Pagination.tsx"] = generator.generate_pagination_component()

    elif component_type == "breadcrumb":
        output["Breadcrumb.tsx"] = generator.generate_breadcrumb_component()

    elif component_type == "stepper":
        output["Stepper.tsx"] = generator.generate_stepper_component()

    if component_type in ["tabs", "pagination", "breadcrumb", "stepper"]:
        output[f"{component_type.capitalize()}.module.css"] = generator.generate_navigation_styles()

    return output
