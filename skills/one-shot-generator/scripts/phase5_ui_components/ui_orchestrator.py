"""
Phase 5 UI Component Orchestrator - Coordinates all UI component generation

Generates:
- React, Vue, Angular component libraries
- Storybook configuration and stories
- Testing setup (Jest, Vitest, Jasmine)
- Design system integration
- API client generation from OpenAPI specs
"""

import os
import json
from typing import Dict, Any, List
from core.react_generator import generate_react_components
from core.vue_generator import generate_vue_components
from core.angular_generator import generate_angular_components


class UIComponentOrchestrator:
    """Master coordinator for UI component generation across all frameworks"""

    def __init__(self, project_name: str = "app", output_dir: str = "."):
        self.project_name = project_name
        self.output_dir = output_dir
        self.react_components = []
        self.vue_components = []
        self.angular_components = []

    def generate_react_library(self) -> Dict[str, str]:
        """Generate complete React component library"""
        output = {}
        components = ["button", "form", "input", "select", "checkbox", "alert", "toast"]

        for component in components:
            files = generate_react_components(component)
            output.update(files)

        # Add barrel export
        output["components/index.ts"] = self._generate_react_barrel_export(components)
        # Add testing setup
        output["jest.config.js"] = self._generate_jest_config()
        # Add Storybook config
        output[".storybook/main.ts"] = self._generate_storybook_main()

        return output

    def generate_vue_library(self) -> Dict[str, str]:
        """Generate complete Vue component library"""
        output = {}
        components = ["button", "form", "input", "select", "alert", "toast"]

        for component in components:
            files = generate_vue_components(component)
            output.update(files)

        # Add barrel export
        output["components/index.ts"] = self._generate_vue_barrel_export(components)
        # Add Vitest config
        output["vitest.config.ts"] = self._generate_vitest_config()
        # Add Storybook config
        output[".storybook/main.ts"] = self._generate_storybook_main_vue()

        return output

    def generate_angular_library(self) -> Dict[str, str]:
        """Generate complete Angular component library"""
        output = {}
        components = ["button", "form", "input", "alert"]

        for component in components:
            files = generate_angular_components(component)
            output.update(files)

        # Add module definitions
        output["app.module.ts"] = self._generate_angular_module(components)
        # Add Karma config
        output["karma.conf.js"] = self._generate_karma_config()
        # Add Storybook config
        output[".storybook/main.ts"] = self._generate_storybook_main_angular()

        return output

    def _generate_react_barrel_export(self, components: List[str]) -> str:
        """Generate React component barrel export"""
        exports = [
            "export { Button } from './Button';",
            "export { Form } from './Form';",
            "export { useFetch } from './hooks/useFetch';",
            "export { Input } from './Input';",
            "export { Select } from './Select';",
            "export { Checkbox } from './Checkbox';",
            "export { Alert } from './Alert';",
            "export { useToast, ToastProvider } from './Toast';",
        ]
        return "\n".join(exports)

    def _generate_vue_barrel_export(self, components: List[str]) -> str:
        """Generate Vue component barrel export"""
        exports = [
            "export { default as Button } from './Button.vue';",
            "export { default as Form } from './Form.vue';",
            "export { useFetch } from './composables/useFetch';",
            "export { default as Input } from './Input.vue';",
            "export { default as Select } from './Select.vue';",
            "export { default as Alert } from './Alert.vue';",
            "export { default as Toast } from './Toast.vue';",
        ]
        return "\n".join(exports)

    def _generate_jest_config(self) -> str:
        """Generate Jest configuration for React testing"""
        return """
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.ts?(x)', '**/?(*.)+(spec|test).ts?(x)'],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  moduleNameMapper: {
    '\\\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  transform: {
    '^.+\\\\.tsx?$': 'ts-jest',
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 75,
      lines: 75,
      statements: 75,
    },
  },
};
"""

    def _generate_vitest_config(self) -> str:
        """Generate Vitest configuration for Vue testing"""
        return """
import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import path from 'path';

export default defineConfig({
  plugins: [vue()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
"""

    def _generate_karma_config(self) -> str:
        """Generate Karma configuration for Angular testing"""
        return """
module.exports = function(config) {
  config.set({
    basePath: '',
    frameworks: ['jasmine', '@angular-devkit/build-angular'],
    plugins: [
      require('karma-jasmine'),
      require('karma-chrome-launcher'),
      require('karma-jasmine-html-reporter'),
      require('karma-coverage'),
      require('@angular-devkit/build-angular/plugins/karma'),
    ],
    client: {
      clearContext: false,
    },
    jasmineHtmlReporter: {
      suppressAll: true,
    },
    coverageReporter: {
      dir: require('path').join(__dirname, './coverage'),
      subdir: '.',
      reporters: [
        { type: 'html' },
        { type: 'text-summary' },
      ],
    },
    reporters: ['progress', 'kjhtml'],
    port: 9876,
    colors: true,
    logLevel: config.LOG_INFO,
    autoWatch: true,
    browsers: ['Chrome'],
    singleRun: false,
    restartOnFileChange: true,
  });
};
"""

    def _generate_storybook_main(self) -> str:
        """Generate Storybook main config for React"""
        return """
import type { StorybookConfig } from '@storybook/react-webpack5';

const config: StorybookConfig = {
  stories: [
    '../src/**/*.mdx',
    '../src/**/*.stories.@(js|jsx|mjs|ts|tsx)',
  ],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',
  ],
  framework: {
    name: '@storybook/react-webpack5',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
};

export default config;
"""

    def _generate_storybook_main_vue(self) -> str:
        """Generate Storybook main config for Vue"""
        return """
import type { StorybookConfig } from '@storybook/vue3-webpack5';

const config: StorybookConfig = {
  stories: [
    '../src/**/*.mdx',
    '../src/**/*.stories.@(js|jsx|mjs|ts|tsx)',
  ],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',
  ],
  framework: {
    name: '@storybook/vue3-webpack5',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
};

export default config;
"""

    def _generate_storybook_main_angular(self) -> str:
        """Generate Storybook main config for Angular"""
        return """
import type { StorybookConfig } from '@storybook/angular';

const config: StorybookConfig = {
  stories: [
    '../src/**/*.mdx',
    '../src/**/*.stories.@(js|jsx|mjs|ts|tsx)',
  ],
  addons: [
    '@storybook/addon-links',
    '@storybook/addon-essentials',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',
  ],
  framework: {
    name: '@storybook/angular',
    options: {},
  },
  docs: {
    autodocs: 'tag',
  },
};

export default config;
"""

    def _generate_angular_module(self, components: List[str]) -> str:
        """Generate Angular module with all components"""
        imports = [
            "import { NgModule } from '@angular/core';",
            "import { CommonModule } from '@angular/common';",
            "import { ReactiveFormsModule } from '@angular/forms';",
            "import { ButtonComponent } from './button.component';",
            "import { FormComponent } from './form.component';",
            "import { InputComponent } from './input.component';",
            "import { AlertComponent } from './alert.component';",
        ]

        exports = [
            "ButtonComponent",
            "FormComponent",
            "InputComponent",
            "AlertComponent",
        ]

        return f"""
{chr(10).join(imports)}

@NgModule({{
  declarations: [
    {', '.join([c for c in exports])}
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
  ],
  exports: [
    {', '.join([c for c in exports])}
  ],
}})
export class ComponentsModule {{ }}
"""

    def generate_package_json(self, framework: str) -> Dict[str, Any]:
        """Generate package.json for component library"""
        base = {
            "name": f"@{self.project_name}/{framework}-components",
            "version": "1.0.0",
            "description": f"{framework.capitalize()} component library",
            "main": "dist/index.js",
            "types": "dist/index.d.ts",
            "scripts": {
                "dev": self._get_dev_script(framework),
                "build": self._get_build_script(framework),
                "test": self._get_test_script(framework),
                "storybook": "storybook dev -p 6006",
                "build-storybook": "storybook build",
                "lint": "eslint src --ext .ts,.tsx,.vue",
            },
            "dependencies": self._get_framework_deps(framework),
            "devDependencies": self._get_dev_deps(framework),
        }
        return base

    def _get_dev_script(self, framework: str) -> str:
        if framework == "react":
            return "vite"
        elif framework == "vue":
            return "vite"
        elif framework == "angular":
            return "ng serve"
        return "vite"

    def _get_build_script(self, framework: str) -> str:
        if framework == "react":
            return "vite build"
        elif framework == "vue":
            return "vite build"
        elif framework == "angular":
            return "ng build"
        return "vite build"

    def _get_test_script(self, framework: str) -> str:
        if framework == "react":
            return "jest"
        elif framework == "vue":
            return "vitest"
        elif framework == "angular":
            return "ng test"
        return "jest"

    def _get_framework_deps(self, framework: str) -> Dict[str, str]:
        if framework == "react":
            return {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
            }
        elif framework == "vue":
            return {
                "vue": "^3.3.0",
            }
        elif framework == "angular":
            return {
                "@angular/common": "^15.0.0",
                "@angular/core": "^15.0.0",
                "rxjs": "^7.8.0",
            }
        return {}

    def _get_dev_deps(self, framework: str) -> Dict[str, str]:
        base = {
            "typescript": "^5.0.0",
            "eslint": "^8.0.0",
            "@typescript-eslint/eslint-plugin": "^5.0.0",
            "storybook": "^7.0.0",
        }

        if framework == "react":
            base.update({
                "jest": "^29.0.0",
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^5.0.0",
                "@storybook/react": "^7.0.0",
                "@storybook/react-webpack5": "^7.0.0",
                "vite": "^4.0.0",
            })
        elif framework == "vue":
            base.update({
                "vitest": "^0.34.0",
                "@vue/test-utils": "^2.4.0",
                "@storybook/vue3": "^7.0.0",
                "@storybook/vue3-webpack5": "^7.0.0",
                "vite": "^4.0.0",
                "@vitejs/plugin-vue": "^4.0.0",
            })
        elif framework == "angular":
            base.update({
                "jasmine": "^4.0.0",
                "karma": "^6.0.0",
                "@storybook/angular": "^7.0.0",
                "@angular/cli": "^15.0.0",
            })

        return base


def generate_phase5_libraries() -> Dict[str, Dict[str, str]]:
    """Generate all Phase 5 UI component libraries"""
    orchestrator = UIComponentOrchestrator("one-shot", "./phase5_output")

    output = {
        "react": orchestrator.generate_react_library(),
        "vue": orchestrator.generate_vue_library(),
        "angular": orchestrator.generate_angular_library(),
    }

    # Add package.json for each framework
    for framework in ["react", "vue", "angular"]:
        output[framework][f"{framework}/package.json"] = json.dumps(
            orchestrator.generate_package_json(framework),
            indent=2
        )

    return output


if __name__ == "__main__":
    libraries = generate_phase5_libraries()
    print(f"Generated {sum(len(files) for files in libraries.values())} files across 3 frameworks")
    for framework, files in libraries.items():
        print(f"  {framework}: {len(files)} files")
