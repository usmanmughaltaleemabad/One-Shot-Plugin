"""
Advanced Vue 3 Components - Data display, overlays, and layout
"""

from typing import Dict, Any


class VueAdvancedComponentGenerator:
    """Generate advanced Vue components"""

    def generate_table_component(self) -> str:
        """Generate data table with sorting"""
        return """
<template>
  <div class="table-wrapper">
    <table class="table">
      <thead>
        <tr>
          <th v-if="selectable" class="checkbox-col">
            <input
              type="checkbox"
              :checked="selectedRows.size === data.length && data.length > 0"
              @change="selectAll"
              aria-label="Select all rows"
            />
          </th>
          <th
            v-for="col in columns"
            :key="String(col.key)"
            :style="{ width: col.width }"
            :class="{ sortable: col.sortable }"
            @click="col.sortable && handleSort(col.key)"
          >
            <div class="header-content">
              {{ col.label }}
              <span v-if="sortKey === col.key" class="sort-icon">
                {{ sortOrder === 'asc' ? '↑' : '↓' }}
              </span>
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in sortedData"
          :key="row.id"
          :class="{ selected: selectedRows.has(row.id) }"
          @click="onRowClick?.(row)"
        >
          <td v-if="selectable" class="checkbox-col">
            <input
              type="checkbox"
              :checked="selectedRows.has(row.id)"
              @change="selectRow(row.id)"
              @click.stop
            />
          </td>
          <td v-for="col in columns" :key="String(col.key)">
            <slot :name="`cell-${String(col.key)}`" :value="row[col.key]" :row="row">
              {{ row[col.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts" generic="T extends { id: string | number }">
import { ref, computed } from 'vue';

export interface Column<T> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  width?: string;
}

interface Props<T> {
  data: T[];
  columns: Column<T>[];
  selectable?: boolean;
  onRowClick?: (row: T) => void;
}

interface Emits<T> {
  selectionChange: [selected: T[]];
}

const props = withDefaults(defineProps<Props<T>>(), {
  selectable: false,
});

const emit = defineEmits<Emits<T>>();

const sortKey = ref<keyof T | null>(null);
const sortOrder = ref<'asc' | 'desc' | null>(null);
const selectedRows = ref(new Set<string | number>());

const sortedData = computed(() => {
  if (!sortKey.value || !sortOrder.value) return props.data;

  return [...props.data].sort((a, b) => {
    const aVal = a[sortKey.value as keyof T];
    const bVal = b[sortKey.value as keyof T];

    if (aVal < bVal) return sortOrder.value === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortOrder.value === 'asc' ? 1 : -1;
    return 0;
  });
});

const handleSort = (key: keyof T) => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : sortOrder.value === 'desc' ? null : 'asc';
    if (sortOrder.value === null) sortKey.value = null;
  } else {
    sortKey.value = key;
    sortOrder.value = 'asc';
  }
};

const selectRow = (id: string | number) => {
  selectedRows.value.has(id) ? selectedRows.value.delete(id) : selectedRows.value.add(id);
  emit('selectionChange', sortedData.value.filter(r => selectedRows.value.has(r.id)));
};

const selectAll = () => {
  if (selectedRows.value.size === sortedData.value.length) {
    selectedRows.value.clear();
    emit('selectionChange', []);
  } else {
    selectedRows.value = new Set(sortedData.value.map(r => r.id));
    emit('selectionChange', sortedData.value);
  }
};
</script>

<style scoped>
.table-wrapper {
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

.header-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sort-icon {
  font-size: 12px;
}

.checkbox-col {
  width: 40px;
  padding: 8px;
  text-align: center;
}
</style>
"""

    def generate_modal_component(self) -> str:
        """Generate modal dialog"""
        return """
<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="backdrop" @click="close">
        <div
          class="modal"
          :class="`modal--${size}`"
          @click.stop
          role="dialog"
          :aria-labelledby="title ? 'modal-title' : undefined"
          aria-modal="true"
        >
          <div v-if="title || closeButton" class="header">
            <h2 v-if="title" id="modal-title" class="title">{{ title }}</h2>
            <button
              v-if="closeButton"
              class="close-button"
              @click="close"
              aria-label="Close modal"
            >
              ✕
            </button>
          </div>
          <div class="content">
            <slot />
          </div>
          <div v-if="$slots.footer" class="footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { watch, Teleport, Transition } from 'vue';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg';
  closeButton?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  closeButton: true,
});

const close = () => props.onClose();

watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    } else {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'auto';
    }
  }
);

const handleEscape = (e: KeyboardEvent) => {
  if (e.key === 'Escape') close();
};
</script>

<style scoped>
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
}

.modal {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  overflow: hidden;

  &.modal--sm {
    width: 90%;
    max-width: 400px;
  }

  &.modal--md {
    width: 90%;
    max-width: 600px;
  }

  &.modal--lg {
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

.close-button {
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

.modal-enter-active, .modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from {
  opacity: 0;
}

.modal-enter-from .modal {
  transform: scale(0.95);
}
</style>
"""

    def generate_card_component(self) -> str:
        """Generate card component"""
        return """
<template>
  <div
    :class="['card', { 'card--hoverable': hoverable }]"
    :role="onClick ? 'button' : undefined"
    :tabindex="onClick ? 0 : undefined"
    @click="onClick"
    @keypress.enter="onClick"
  >
    <div v-if="title || subtitle" class="header">
      <h3 v-if="title" class="title">{{ title }}</h3>
      <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
    </div>
    <div class="content">
      <slot />
    </div>
    <div v-if="$slots.footer" class="footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title?: string;
  subtitle?: string;
  hoverable?: boolean;
  onClick?: () => void;
}

withDefaults(defineProps<Props>(), {
  hoverable: false,
});
</script>

<style scoped>
.card {
  background: white;
  border: 1px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s ease;

  &.card--hoverable {
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
</style>
"""


def generate_vue_advanced_components(component_type: str) -> Dict[str, str]:
    """Generate Vue advanced components"""
    generator = VueAdvancedComponentGenerator()
    output = {}

    if component_type == "table":
        output["Table.vue"] = generator.generate_table_component()

    elif component_type == "modal":
        output["Modal.vue"] = generator.generate_modal_component()

    elif component_type == "card":
        output["Card.vue"] = generator.generate_card_component()

    return output
