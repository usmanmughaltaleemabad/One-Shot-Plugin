"""
Layout Components - Grid, Flex, Stack, Container utilities

Generates:
- Responsive grid system
- Flexbox utilities
- Stack (flex column/row)
- Container (centered wrapper)
- Spacer, Divider utilities
"""

from typing import Dict, Any


class LayoutComponentGenerator:
    """Generate layout utility components"""

    def generate_grid_component(self) -> str:
        """Generate responsive grid container"""
        return """
import React from 'react';
import styles from './Grid.module.css';

interface GridProps {
  children: React.ReactNode;
  columns?: number | { sm: number; md: number; lg: number };
  gap?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

export const Grid: React.FC<GridProps> = ({
  children,
  columns = 3,
  gap = 'md',
  className,
}) => {
  const gridStyle: React.CSSProperties = {};

  if (typeof columns === 'number') {
    gridStyle.gridTemplateColumns = `repeat(${columns}, 1fr)`;
  }

  return (
    <div
      className={`${styles.grid} ${styles[`gap-${gap}`]} ${className || ''}`}
      style={gridStyle}
    >
      {children}
    </div>
  );
};

Grid.displayName = 'Grid';
"""

    def generate_flex_component(self) -> str:
        """Generate flex container"""
        return """
import React from 'react';
import styles from './Flex.module.css';

type FlexDirection = 'row' | 'column' | 'row-reverse' | 'column-reverse';
type JustifyContent = 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
type AlignItems = 'start' | 'center' | 'end' | 'stretch' | 'baseline';

interface FlexProps {
  children: React.ReactNode;
  direction?: FlexDirection;
  justify?: JustifyContent;
  align?: AlignItems;
  gap?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  wrap?: boolean;
  className?: string;
}

export const Flex: React.FC<FlexProps> = ({
  children,
  direction = 'row',
  justify = 'start',
  align = 'stretch',
  gap = 'md',
  wrap = false,
  className,
}) => {
  return (
    <div
      className={`${styles.flex} ${styles[direction]} ${styles[`justify-${justify}`]} ${styles[`align-${align}`]} ${styles[`gap-${gap}`]} ${wrap ? styles.wrap : ''} ${className || ''}`}
    >
      {children}
    </div>
  );
};

Flex.displayName = 'Flex';
"""

    def generate_stack_component(self) -> str:
        """Generate stack (flex column/row shorthand)"""
        return """
import React from 'react';
import styles from './Stack.module.css';

interface StackProps {
  children: React.ReactNode;
  direction?: 'vertical' | 'horizontal';
  spacing?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  align?: 'start' | 'center' | 'end' | 'stretch';
  justify?: 'start' | 'center' | 'end' | 'between';
  className?: string;
}

export const Stack: React.FC<StackProps> = ({
  children,
  direction = 'vertical',
  spacing = 'md',
  align = 'stretch',
  justify = 'start',
  className,
}) => {
  const flexDirection = direction === 'vertical' ? 'column' : 'row';

  return (
    <div
      className={`${styles.stack} ${styles[`spacing-${spacing}`]} ${className || ''}`}
      style={{
        flexDirection,
        alignItems: align,
        justifyContent: justify,
      }}
    >
      {children}
    </div>
  );
};

Stack.displayName = 'Stack';
"""

    def generate_container_component(self) -> str:
        """Generate centered container"""
        return """
import React from 'react';
import styles from './Container.module.css';

type ContainerSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

interface ContainerProps {
  children: React.ReactNode;
  size?: ContainerSize;
  className?: string;
}

export const Container: React.FC<ContainerProps> = ({
  children,
  size = 'lg',
  className,
}) => {
  return (
    <div className={`${styles.container} ${styles[size]} ${className || ''}`}>
      {children}
    </div>
  );
};

Container.displayName = 'Container';
"""

    def generate_divider_component(self) -> str:
        """Generate divider/separator"""
        return """
import React from 'react';
import styles from './Divider.module.css';

interface DividerProps {
  orientation?: 'horizontal' | 'vertical';
  spacing?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: 'default' | 'light' | 'dark';
  className?: string;
}

export const Divider: React.FC<DividerProps> = ({
  orientation = 'horizontal',
  spacing = 'md',
  color = 'default',
  className,
}) => {
  return (
    <div
      className={`${styles.divider} ${styles[orientation]} ${styles[`spacing-${spacing}`]} ${styles[color]} ${className || ''}`}
      role="separator"
      aria-orientation={orientation}
    />
  );
};

Divider.displayName = 'Divider';
"""

    def generate_spacer_component(self) -> str:
        """Generate flexible spacer"""
        return """
import React from 'react';

interface SpacerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | number;
  direction?: 'vertical' | 'horizontal';
  flex?: boolean;
}

export const Spacer: React.FC<SpacerProps> = ({
  size = 'md',
  direction = 'vertical',
  flex = false,
}) => {
  const sizeMap: Record<string, string> = {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
  };

  const spacing = typeof size === 'number' ? `${size}px` : sizeMap[size] || size;
  const dimension = direction === 'vertical' ? 'height' : 'width';

  return (
    <div
      style={{
        [dimension]: spacing,
        flex: flex ? 1 : undefined,
      }}
    />
  );
};

Spacer.displayName = 'Spacer';
"""

    def generate_layout_styles(self) -> str:
        """Generate layout component styles"""
        return """
/* Grid Styles */
.grid {
  display: grid;
  width: 100%;

  &.gap-xs {
    gap: 4px;
  }
  &.gap-sm {
    gap: 8px;
  }
  &.gap-md {
    gap: 16px;
  }
  &.gap-lg {
    gap: 24px;
  }
  &.gap-xl {
    gap: 32px;
  }
}

/* Flex Styles */
.flex {
  display: flex;

  &.row {
    flex-direction: row;
  }
  &.column {
    flex-direction: column;
  }
  &.row-reverse {
    flex-direction: row-reverse;
  }
  &.column-reverse {
    flex-direction: column-reverse;
  }

  &.justify-start {
    justify-content: flex-start;
  }
  &.justify-center {
    justify-content: center;
  }
  &.justify-end {
    justify-content: flex-end;
  }
  &.justify-between {
    justify-content: space-between;
  }
  &.justify-around {
    justify-content: space-around;
  }
  &.justify-evenly {
    justify-content: space-evenly;
  }

  &.align-start {
    align-items: flex-start;
  }
  &.align-center {
    align-items: center;
  }
  &.align-end {
    align-items: flex-end;
  }
  &.align-stretch {
    align-items: stretch;
  }
  &.align-baseline {
    align-items: baseline;
  }

  &.gap-xs {
    gap: 4px;
  }
  &.gap-sm {
    gap: 8px;
  }
  &.gap-md {
    gap: 16px;
  }
  &.gap-lg {
    gap: 24px;
  }
  &.gap-xl {
    gap: 32px;
  }

  &.wrap {
    flex-wrap: wrap;
  }
}

/* Stack Styles */
.stack {
  display: flex;
  width: 100%;

  &.spacing-xs {
    gap: 4px;
  }
  &.spacing-sm {
    gap: 8px;
  }
  &.spacing-md {
    gap: 16px;
  }
  &.spacing-lg {
    gap: 24px;
  }
  &.spacing-xl {
    gap: 32px;
  }
}

/* Container Styles */
.container {
  width: 100%;
  margin: 0 auto;
  padding: 0 16px;

  &.sm {
    max-width: 640px;
  }
  &.md {
    max-width: 960px;
  }
  &.lg {
    max-width: 1280px;
  }
  &.xl {
    max-width: 1536px;
  }
  &.full {
    max-width: 100%;
  }
}

/* Divider Styles */
.divider {
  background-color: #eee;

  &.horizontal {
    width: 100%;
    height: 1px;
  }

  &.vertical {
    width: 1px;
    height: 100%;
  }

  &.spacing-xs {
    margin: 4px 0;

    &.vertical {
      margin: 0 4px;
    }
  }
  &.spacing-sm {
    margin: 8px 0;

    &.vertical {
      margin: 0 8px;
    }
  }
  &.spacing-md {
    margin: 16px 0;

    &.vertical {
      margin: 0 16px;
    }
  }
  &.spacing-lg {
    margin: 24px 0;

    &.vertical {
      margin: 0 24px;
    }
  }
  &.spacing-xl {
    margin: 32px 0;

    &.vertical {
      margin: 0 32px;
    }
  }

  &.light {
    background-color: #f5f5f5;
  }
  &.dark {
    background-color: #ccc;
  }
}
"""


def generate_layout_components(component_type: str) -> Dict[str, str]:
    """Generate layout components"""
    generator = LayoutComponentGenerator()
    output = {}

    if component_type == "grid":
        output["Grid.tsx"] = generator.generate_grid_component()

    elif component_type == "flex":
        output["Flex.tsx"] = generator.generate_flex_component()

    elif component_type == "stack":
        output["Stack.tsx"] = generator.generate_stack_component()

    elif component_type == "container":
        output["Container.tsx"] = generator.generate_container_component()

    elif component_type == "divider":
        output["Divider.tsx"] = generator.generate_divider_component()

    elif component_type == "spacer":
        output["Spacer.tsx"] = generator.generate_spacer_component()

    if component_type in ["grid", "flex", "stack", "container", "divider"]:
        output[f"{component_type.capitalize()}.module.css"] = generator.generate_layout_styles()

    return output
