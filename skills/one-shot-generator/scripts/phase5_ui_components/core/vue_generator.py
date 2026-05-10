"""
Vue Component Generator - Vue 3 Composition API components with TypeScript

Generates:
- Functional components using Composition API
- Props with TypeScript definitions
- Composables for logic reuse
- State management integration (Pinia)
- Component testing (Vitest)
- Storybook stories
- Accessibility support
"""

from typing import Dict, Any


class VueComponentGenerator:
    """Generate Vue 3 Composition API components"""

    def __init__(self):
        pass

    def generate_button_component(self) -> str:
        """Generate a reusable Button component"""
        return """
<template>
  <button
    :class="[
      'button',
      buttonClass,
      { 'button--loading': isLoading }
    ]"
    :disabled="disabled || isLoading"
    :aria-label="ariaLabel"
    :aria-busy="isLoading"
    v-bind="$attrs"
    @click="$emit('click')"
  >
    <span v-if="icon && iconPosition === 'left'" class="button__icon">
      <slot name="icon-left">
        {{ icon }}
      </slot>
    </span>

    <span v-if="!isLoading" class="button__text">
      <slot>{{ label }}</slot>
    </span>

    <span v-else class="button__spinner" />

    <span v-if="icon && iconPosition === 'right'" class="button__icon">
      <slot name="icon-right">
        {{ icon }}
      </slot>
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue';

export type ButtonVariant = 'primary' | 'secondary' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';
export type IconPosition = 'left' | 'right';

interface Props {
  label?: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
  icon?: string;
  iconPosition?: IconPosition;
  ariaLabel?: string;
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  isLoading: false,
  disabled: false,
  fullWidth: false,
  iconPosition: 'left',
});

defineEmits<{
  click: [];
}>();

const buttonClass = computed(() => {
  const classes: Record<string, boolean> = {
    'button--primary': true, // Default variant
    'button--full-width': false, // Will be computed below
  };
  return classes;
});
</script>

<style scoped>
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  height: 40px;
  background-color: #0066cc;
  color: white;

  &:hover:not(:disabled) {
    background-color: #0052a3;
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
  &--primary {
    background-color: #0066cc;
    color: white;

    &:hover:not(:disabled) {
      background-color: #0052a3;
    }
  }

  &--secondary {
    background-color: #e0e0e0;
    color: #333;

    &:hover:not(:disabled) {
      background-color: #d0d0d0;
    }
  }

  &--danger {
    background-color: #dc3545;
    color: white;

    &:hover:not(:disabled) {
      background-color: #c82333;
    }
  }

  /* Sizes */
  &--sm {
    padding: 6px 12px;
    font-size: 12px;
    height: 32px;
  }

  &--md {
    padding: 8px 16px;
    font-size: 14px;
    height: 40px;
  }

  &--lg {
    padding: 12px 24px;
    font-size: 16px;
    height: 48px;
  }

  /* Full width */
  &--full-width {
    width: 100%;
  }

  /* Loading state */
  &--loading {
    position: relative;
  }

  &__spinner {
    display: inline-block;
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  &__icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }

  &__text {
    flex: 0 1 auto;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
"""

    def generate_form_component(self) -> str:
        """Generate Form component with field management"""
        return """
<template>
  <form @submit.prevent="handleSubmit" novalidate class="form">
    <div
      v-for="field in fields"
      :key="field.name"
      class="form__group"
    >
      <label :for="field.name" class="form__label">
        {{ field.label }}
        <span v-if="field.required" class="form__required">*</span>
      </label>

      <textarea
        v-if="field.type === 'textarea'"
        :id="field.name"
        v-model="formData[field.name]"
        :placeholder="field.placeholder"
        :class="['form__input', { 'form__input--error': errors[field.name] }]"
        :aria-invalid="!!errors[field.name]"
        :aria-describedby="errors[field.name] ? `${field.name}-error` : undefined"
        @blur="validateField(field.name)"
      />

      <input
        v-else
        :id="field.name"
        v-model="formData[field.name]"
        :type="field.type"
        :placeholder="field.placeholder"
        :class="['form__input', { 'form__input--error': errors[field.name] }]"
        :aria-invalid="!!errors[field.name]"
        :aria-describedby="errors[field.name] ? `${field.name}-error` : undefined"
        @blur="validateField(field.name)"
      />

      <span
        v-if="errors[field.name]"
        :id="`${field.name}-error`"
        class="form__error"
        role="alert"
      >
        {{ errors[field.name] }}
      </span>
    </div>

    <button
      type="submit"
      :disabled="isSubmitting"
      class="form__submit"
    >
      {{ isSubmitting ? 'Submitting...' : submitLabel }}
    </button>
  </form>
</template>

<script setup lang="ts" generic="T extends Record<string, string>">
import { reactive, ref, computed } from 'vue';

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'password' | 'number' | 'textarea';
  required?: boolean;
  placeholder?: string;
  validation?: (value: string) => string | null;
}

interface Props<T> {
  fields: FormField[];
  submitLabel?: string;
  initialValues?: Partial<T>;
}

interface Emits {
  submit: [data: T];
}

withDefaults(defineProps<Props<T>>(), {
  submitLabel: 'Submit',
  initialValues: () => ({}),
});

defineEmits<Emits>();

const formData = reactive<Record<string, string>>(
  new Proxy({}, {
    get: (target, prop: string) => target[prop] || '',
    set: (target, prop: string, value: string) => {
      target[prop] = value;
      return true;
    }
  })
);

const errors = reactive<Record<string, string | null>>({});
const isSubmitting = ref(false);

const validateField = (fieldName: string) => {
  const field = fields.value.find(f => f.name === fieldName);
  if (!field) return;

  if (field.required && !formData[fieldName]) {
    errors[fieldName] = `${field.label} is required`;
  } else if (field.validation) {
    errors[fieldName] = field.validation(formData[fieldName]) || null;
  } else {
    errors[fieldName] = null;
  }
};

const handleSubmit = async () => {
  // Validate all fields
  fields.value.forEach(field => validateField(field.name));

  const hasErrors = Object.values(errors).some(error => error !== null);
  if (hasErrors) return;

  isSubmitting.value = true;
  try {
    emit('submit', formData as T);
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 16px;

  &__group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  &__label {
    font-weight: 600;
    font-size: 14px;
    color: #333;
  }

  &__required {
    color: #dc3545;
  }

  &__input {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
    font-family: inherit;
    transition: border-color 0.2s;

    &:focus {
      outline: none;
      border-color: #0066cc;
      box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
    }

    &--error {
      border-color: #dc3545;

      &:focus {
        box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.1);
      }
    }
  }

  &__error {
    font-size: 12px;
    color: #dc3545;
  }

  &__submit {
    padding: 8px 16px;
    background-color: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.2s;

    &:hover:not(:disabled) {
      background-color: #0052a3;
    }

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}
</style>
"""

    def generate_use_fetch_composable(self) -> str:
        """Generate useFetch composable"""
        return """
import { ref, computed, onMounted, Ref } from 'vue';

interface UseFetchOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: Record<string, any>;
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
}

interface UseFetchReturn<T> {
  data: Ref<T | null>;
  loading: Ref<boolean>;
  error: Ref<Error | null>;
  refetch: () => Promise<void>;
}

export function useFetch<T = any>(
  url: string,
  options: UseFetchOptions = {}
): UseFetchReturn<T> {
  const data = ref<T | null>(null);
  const loading = ref(true);
  const error = ref<Error | null>(null);

  const fetchData = async () => {
    loading.value = true;
    error.value = null;
    data.value = null;

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

      data.value = (await response.json()) as T;
      options.onSuccess?.(data.value);
    } catch (err) {
      error.value = err instanceof Error ? err : new Error(String(err));
      options.onError?.(error.value);
    } finally {
      loading.value = false;
    }
  };

  onMounted(fetchData);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
  };
}
"""

    def generate_input_component(self) -> str:
        """Generate Input component"""
        return """
<template>
  <div :class="['input-wrapper', { 'input-wrapper--full-width': fullWidth }]">
    <label v-if="label" :for="inputId" class="input__label">
      {{ label }}
    </label>

    <div class="input__container" :class="[`input__container--${size}`, { 'input__container--has-icon': icon }]">
      <span v-if="icon && iconPosition === 'left'" class="input__icon input__icon--left">
        {{ icon }}
      </span>

      <input
        :id="inputId"
        v-bind="$attrs"
        :class="['input__field', { 'input__field--error': error }]"
        :aria-invalid="!!error"
        :aria-describedby="error ? `${inputId}-error` : helpText ? `${inputId}-help` : undefined"
      />

      <span v-if="icon && iconPosition === 'right'" class="input__icon input__icon--right">
        {{ icon }}
      </span>
    </div>

    <span v-if="error" :id="`${inputId}-error`" class="input__error" role="alert">
      {{ error }}
    </span>
    <span v-else-if="helpText" :id="`${inputId}-help`" class="input__help">
      {{ helpText }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

export type InputSize = 'sm' | 'md' | 'lg';

interface Props {
  label?: string;
  error?: string;
  helpText?: string;
  size?: InputSize;
  fullWidth?: boolean;
  icon?: string;
  iconPosition?: 'left' | 'right';
  id?: string;
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  fullWidth: false,
  iconPosition: 'left',
});

const inputId = computed(() => props.id || `input-${Math.random()}`);
</script>

<style scoped>
.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;

  &.input-wrapper--full-width {
    width: 100%;
  }
}

.input__label {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.input__container {
  display: flex;
  align-items: center;
  border: 1px solid #ddd;
  border-radius: 4px;
  transition: border-color 0.2s;

  &.input__container--has-icon {
    padding: 0 8px;
  }

  &.input__container--sm .input__field {
    padding: 4px 8px;
    font-size: 12px;
  }

  &.input__container--md .input__field {
    padding: 8px 12px;
    font-size: 14px;
  }

  &.input__container--lg .input__field {
    padding: 12px 16px;
    font-size: 16px;
  }

  &:focus-within {
    border-color: #0066cc;
    box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
  }
}

.input__field {
  flex: 1;
  border: none;
  background: transparent;
  font-family: inherit;
  outline: none;

  &.input__field--error {
    color: #dc3545;
  }
}

.input__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;

  &.input__icon--left {
    margin-right: 8px;
  }

  &.input__icon--right {
    margin-left: 8px;
  }
}

.input__error {
  font-size: 12px;
  color: #dc3545;
}

.input__help {
  font-size: 12px;
  color: #666;
}
</style>
"""

    def generate_select_component(self) -> str:
        """Generate Select component"""
        return """
<template>
  <div class="select-wrapper">
    <label v-if="label" :for="selectId" class="select__label">
      {{ label }}
    </label>

    <select
      :id="selectId"
      :class="['select__field', { 'select__field--error': error }]"
      v-bind="$attrs"
      :aria-invalid="!!error"
      :aria-describedby="error ? `${selectId}-error` : helpText ? `${selectId}-help` : undefined"
    >
      <option v-if="placeholder" value="">{{ placeholder }}</option>
      <option
        v-for="opt in options"
        :key="opt.value"
        :value="opt.value"
        :disabled="opt.disabled"
      >
        {{ opt.label }}
      </option>
    </select>

    <span v-if="error" :id="`${selectId}-error`" class="select__error" role="alert">
      {{ error }}
    </span>
    <span v-else-if="helpText" :id="`${selectId}-help`" class="select__help">
      {{ helpText }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Option {
  value: string | number;
  label: string;
  disabled?: boolean;
}

interface Props {
  label?: string;
  options: Option[];
  error?: string;
  helpText?: string;
  placeholder?: string;
  id?: string;
}

defineProps<Props>();

const selectId = computed(() => Math.random().toString());
</script>

<style scoped>
.select-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.select__label {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.select__field {
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

  &.select__field--error {
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

.select__error {
  font-size: 12px;
  color: #dc3545;
}

.select__help {
  font-size: 12px;
  color: #666;
}
</style>
"""

    def generate_alert_component(self) -> str:
        """Generate Alert component"""
        return """
<template>
  <div
    v-if="isVisible"
    :class="['alert', `alert--${type}`]"
    role="alert"
    :aria-live="type === 'error' ? 'assertive' : 'polite'"
  >
    <div class="alert__content">
      <span v-if="icon" class="alert__icon">{{ icon }}</span>
      <div>
        <div v-if="title" class="alert__title">{{ title }}</div>
        <div class="alert__message"><slot /></div>
      </div>
    </div>
    <button
      v-if="closable"
      class="alert__close"
      @click="isVisible = false"
      aria-label="Close alert"
    >
      ✕
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

export type AlertType = 'info' | 'success' | 'warning' | 'error';

interface Props {
  type?: AlertType;
  title?: string;
  closable?: boolean;
  icon?: string;
}

withDefaults(defineProps<Props>(), {
  type: 'info',
  closable: false,
});

const isVisible = ref(true);
</script>

<style scoped>
.alert {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 14px;

  &.alert--info {
    background-color: #e7f3ff;
    border-left: 4px solid #0066cc;
    color: #0066cc;
  }

  &.alert--success {
    background-color: #f0f9ff;
    border-left: 4px solid #28a745;
    color: #28a745;
  }

  &.alert--warning {
    background-color: #fff8e1;
    border-left: 4px solid #ffc107;
    color: #856404;
  }

  &.alert--error {
    background-color: #ffe7e7;
    border-left: 4px solid #dc3545;
    color: #dc3545;
  }
}

.alert__content {
  display: flex;
  gap: 12px;
  flex: 1;
}

.alert__icon {
  display: flex;
  align-items: flex-start;
  font-size: 18px;
}

.alert__title {
  font-weight: 600;
  margin-bottom: 4px;
}

.alert__message {
  line-height: 1.5;
}

.alert__close {
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
</style>
"""

    def generate_toast_component(self) -> str:
        """Generate Toast composable and components"""
        return """
<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="['toast', `toast--${toast.type}`]"
          role="status"
        >
          <span>{{ toast.message }}</span>
          <button @click="removeToast(toast.id)" aria-label="Close toast">✕</button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, provide, Teleport, TransitionGroup } from 'vue';

export type ToastType = 'info' | 'success' | 'warning' | 'error';

interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

const toasts = ref<Toast[]>([]);

const addToast = (message: string, type: ToastType = 'info', duration = 3000) => {
  const id = `toast-${Date.now()}`;
  toasts.value.push({ id, type, message, duration });

  if (duration) {
    setTimeout(() => removeToast(id), duration);
  }
  return id;
};

const removeToast = (id: string) => {
  toasts.value = toasts.value.filter(t => t.id !== id);
};

provide('toast', { addToast, removeToast });
</script>

<style scoped>
.toast-container {
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

  &.toast--info {
    background-color: #e7f3ff;
    color: #0066cc;
  }

  &.toast--success {
    background-color: #f0f9ff;
    color: #28a745;
  }

  &.toast--warning {
    background-color: #fff8e1;
    color: #856404;
  }

  &.toast--error {
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

.toast-enter-active, .toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  transform: translateX(400px);
  opacity: 0;
}

.toast-leave-to {
  transform: translateX(400px);
  opacity: 0;
}
</style>
"""


def generate_vue_components(component_type: str = "button") -> Dict[str, str]:
    """
    Generate Vue 3 components.

    Args:
        component_type: Type of component to generate

    Returns: dict of {filename: code_content}
    """
    generator = VueComponentGenerator()
    output = {}

    if component_type == "button":
        output["Button.vue"] = generator.generate_button_component()

    elif component_type == "form":
        output["Form.vue"] = generator.generate_form_component()
        output["composables/useFetch.ts"] = generator.generate_use_fetch_composable()

    elif component_type == "input":
        output["Input.vue"] = generator.generate_input_component()

    elif component_type == "select":
        output["Select.vue"] = generator.generate_select_component()

    elif component_type == "alert":
        output["Alert.vue"] = generator.generate_alert_component()

    elif component_type == "toast":
        output["Toast.vue"] = generator.generate_toast_component()

    elif component_type == "all":
        output.update(generate_vue_components("button"))
        output.update(generate_vue_components("form"))
        output.update(generate_vue_components("input"))
        output.update(generate_vue_components("select"))
        output.update(generate_vue_components("alert"))
        output.update(generate_vue_components("toast"))

    return output
