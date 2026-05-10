"""
Advanced Angular Components - Data display, overlays, and layout
"""

from typing import Dict, Any


class AngularAdvancedComponentGenerator:
    """Generate advanced Angular components"""

    def generate_table_component(self) -> str:
        """Generate data table component"""
        return """
import { Component, Input, Output, EventEmitter } from '@angular/core';

export interface TableColumn<T> {
  key: keyof T;
  label: string;
  sortable?: boolean;
  width?: string;
}

@Component({
  selector: 'app-table',
  template: `
    <div class="table-wrapper">
      <table class="table">
        <thead>
          <tr>
            <th
              *ngFor="let col of columns"
              [style.width]="col.width"
              [class.sortable]="col.sortable"
              (click)="col.sortable && handleSort(col.key)"
            >
              <div class="header-content">
                {{ col.label }}
                <span *ngIf="sortKey === col.key" class="sort-icon">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let row of sortedData" (click)="onRowClick.emit(row)">
            <td *ngFor="let col of columns">
              {{ row[col.key as string] }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  `,
  styles: [`
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
  `]
})
export class TableComponent<T extends { id: string | number }> {
  @Input() data: T[] = [];
  @Input() columns: TableColumn<T>[] = [];
  @Output() onRowClick = new EventEmitter<T>();

  sortKey: keyof T | null = null;
  sortOrder: 'asc' | 'desc' | null = null;
  sortedData: T[] = [];

  ngOnInit() {
    this.updateSortedData();
  }

  ngOnChanges() {
    this.updateSortedData();
  }

  handleSort(key: keyof T) {
    if (this.sortKey === key) {
      this.sortOrder = this.sortOrder === 'asc' ? 'desc' : this.sortOrder === 'desc' ? null : 'asc';
      if (this.sortOrder === null) this.sortKey = null;
    } else {
      this.sortKey = key;
      this.sortOrder = 'asc';
    }
    this.updateSortedData();
  }

  private updateSortedData() {
    if (!this.sortKey || !this.sortOrder) {
      this.sortedData = [...this.data];
      return;
    }

    this.sortedData = [...this.data].sort((a, b) => {
      const aVal = a[this.sortKey as keyof T];
      const bVal = b[this.sortKey as keyof T];

      if (aVal < bVal) return this.sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return this.sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }
}
"""

    def generate_modal_component(self) -> str:
        """Generate modal component"""
        return """
import { Component, Input, Output, EventEmitter, HostListener } from '@angular/core';

@Component({
  selector: 'app-modal',
  template: `
    <div *ngIf="isOpen" class="backdrop" (click)="close()">
      <div
        class="modal"
        [class]="'modal--' + size"
        (click)="$event.stopPropagation()"
        role="dialog"
        aria-modal="true"
      >
        <div *ngIf="title || closeButton" class="header">
          <h2 *ngIf="title" class="title">{{ title }}</h2>
          <button
            *ngIf="closeButton"
            class="close-button"
            (click)="close()"
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>
        <div class="content">
          <ng-content></ng-content>
        </div>
        <div class="footer">
          <ng-content select="[modal-footer]"></ng-content>
        </div>
      </div>
    </div>
  `,
  styles: [`
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
  `]
})
export class ModalComponent {
  @Input() isOpen = false;
  @Input() title?: string;
  @Input() size: 'sm' | 'md' | 'lg' = 'md';
  @Input() closeButton = true;
  @Output() onClose = new EventEmitter<void>();

  @HostListener('document:keydown.escape', ['$event'])
  handleEscape(event: KeyboardEvent) {
    if (this.isOpen) this.close();
  }

  close() {
    this.onClose.emit();
  }

  ngOnChanges() {
    if (this.isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
  }
}
"""

    def generate_card_component(self) -> str:
        """Generate card component"""
        return """
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-card',
  template: `
    <div class="card" [class.card--hoverable]="hoverable">
      <div *ngIf="title || subtitle" class="header">
        <h3 *ngIf="title" class="title">{{ title }}</h3>
        <p *ngIf="subtitle" class="subtitle">{{ subtitle }}</p>
      </div>
      <div class="content">
        <ng-content></ng-content>
      </div>
      <div class="footer">
        <ng-content select="[card-footer]"></ng-content>
      </div>
    </div>
  `,
  styles: [`
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
  `]
})
export class CardComponent {
  @Input() title?: string;
  @Input() subtitle?: string;
  @Input() hoverable = false;
}
"""


def generate_angular_advanced_components(component_type: str) -> Dict[str, str]:
    """Generate Angular advanced components"""
    generator = AngularAdvancedComponentGenerator()
    output = {}

    if component_type == "table":
        output["table.component.ts"] = generator.generate_table_component()

    elif component_type == "modal":
        output["modal.component.ts"] = generator.generate_modal_component()

    elif component_type == "card":
        output["card.component.ts"] = generator.generate_card_component()

    return output
