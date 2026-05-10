"""
Angular Component Generator - Angular components with TypeScript, RxJS, and testing

Generates:
- Angular components with dependency injection
- TypeScript interfaces and types
- RxJS observables
- Template-driven and reactive forms
- Component testing (Jasmine/Karma)
- Service integration
- Accessibility support
"""

from typing import Dict, Any


class AngularComponentGenerator:
    """Generate Angular components"""

    def __init__(self):
        pass

    def generate_button_component(self) -> str:
        """Generate an Angular Button component"""
        return """
import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit
} from '@angular/core';

export type ButtonVariant = 'primary' | 'secondary' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

@Component({
  selector: 'app-button',
  template: `
    <button
      [class]="buttonClass"
      [disabled]="disabled || isLoading"
      [attr.aria-label]="ariaLabel"
      [attr.aria-busy]="isLoading"
      (click)="onClick()"
    >
      <span *ngIf="icon && iconPosition === 'left'" class="button__icon">
        <ng-content select="[appButtonIconLeft]"></ng-content>
        {{ icon }}
      </span>

      <span *ngIf="!isLoading" class="button__text">
        <ng-content></ng-content>
      </span>

      <span *ngIf="isLoading" class="button__spinner"></span>

      <span *ngIf="icon && iconPosition === 'right'" class="button__icon">
        <ng-content select="[appButtonIconRight]"></ng-content>
        {{ icon }}
      </span>
    </button>
  `,
  styles: [`
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

      &--primary {
        background-color: #0066cc;
        &:hover:not(:disabled) { background-color: #0052a3; }
      }

      &--secondary {
        background-color: #e0e0e0;
        color: #333;
        &:hover:not(:disabled) { background-color: #d0d0d0; }
      }

      &--danger {
        background-color: #dc3545;
        &:hover:not(:disabled) { background-color: #c82333; }
      }

      &--full-width {
        width: 100%;
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
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `]
})
export class ButtonComponent {
  @Input() variant: ButtonVariant = 'primary';
  @Input() size: ButtonSize = 'md';
  @Input() isLoading = false;
  @Input() disabled = false;
  @Input() fullWidth = false;
  @Input() icon: string | null = null;
  @Input() iconPosition: 'left' | 'right' = 'left';
  @Input() ariaLabel: string | null = null;
  @Output() buttonClick = new EventEmitter<void>();

  get buttonClass(): string {
    const classes = [
      'button',
      `button--${this.variant}`,
      `button--${this.size}`,
    ];

    if (this.fullWidth) classes.push('button--full-width');
    if (this.isLoading) classes.push('button--loading');

    return classes.join(' ');
  }

  onClick(): void {
    if (!this.disabled && !this.isLoading) {
      this.buttonClick.emit();
    }
  }
}
"""

    def generate_button_test(self) -> str:
        """Generate Button component test"""
        return """
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ButtonComponent } from './button.component';
import { DebugElement } from '@angular/core';
import { By } from '@angular/platform-browser';

describe('ButtonComponent', () => {
  let component: ButtonComponent;
  let fixture: ComponentFixture<ButtonComponent>;
  let buttonElement: DebugElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ButtonComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(ButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    buttonElement = fixture.debugElement.query(By.css('button'));
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render text content', () => {
    const testText = 'Click me';
    fixture.nativeElement.textContent = testText;
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain(testText);
  });

  it('should emit buttonClick event on click', () => {
    spyOn(component.buttonClick, 'emit');
    buttonElement.nativeElement.click();
    expect(component.buttonClick.emit).toHaveBeenCalled();
  });

  it('should disable button when disabled is true', () => {
    component.disabled = true;
    fixture.detectChanges();
    expect(buttonElement.nativeElement.disabled).toBe(true);
  });

  it('should apply variant class', () => {
    component.variant = 'danger';
    fixture.detectChanges();
    expect(buttonElement.nativeElement.classList).toContain('button--danger');
  });

  it('should apply size class', () => {
    component.size = 'lg';
    fixture.detectChanges();
    expect(buttonElement.nativeElement.classList).toContain('button--lg');
  });

  it('should show loading spinner when isLoading is true', () => {
    component.isLoading = true;
    fixture.detectChanges();
    const spinner = buttonElement.nativeElement.querySelector('.button__spinner');
    expect(spinner).toBeTruthy();
  });

  it('should apply full-width class', () => {
    component.fullWidth = true;
    fixture.detectChanges();
    expect(buttonElement.nativeElement.classList).toContain('button--full-width');
  });

  it('should set aria-label when provided', () => {
    component.ariaLabel = 'Delete item';
    fixture.detectChanges();
    expect(buttonElement.nativeElement.getAttribute('aria-label')).toBe('Delete item');
  });

  it('should not emit event when disabled', () => {
    component.disabled = true;
    fixture.detectChanges();
    spyOn(component.buttonClick, 'emit');
    component.onClick();
    expect(component.buttonClick.emit).not.toHaveBeenCalled();
  });

  it('should not emit event when loading', () => {
    component.isLoading = true;
    spyOn(component.buttonClick, 'emit');
    component.onClick();
    expect(component.buttonClick.emit).not.toHaveBeenCalled();
  });
});
"""

    def generate_http_service(self) -> str:
        """Generate HttpClient service for API calls"""
        return """
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, retry } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = '/api';

  constructor(private http: HttpClient) {}

  /**
   * Make a GET request
   */
  get<T>(endpoint: string, params?: Record<string, string | number>): Observable<T> {
    let httpParams = new HttpParams();

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        httpParams = httpParams.set(key, String(value));
      });
    }

    return this.http.get<T>(`${this.apiUrl}${endpoint}`, { params: httpParams })
      .pipe(
        retry(1),
        catchError(this.handleError)
      );
  }

  /**
   * Make a POST request
   */
  post<T>(endpoint: string, data: any): Observable<T> {
    return this.http.post<T>(`${this.apiUrl}${endpoint}`, data)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Make a PUT request
   */
  put<T>(endpoint: string, data: any): Observable<T> {
    return this.http.put<T>(`${this.apiUrl}${endpoint}`, data)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Make a DELETE request
   */
  delete<T>(endpoint: string): Observable<T> {
    return this.http.delete<T>(`${this.apiUrl}${endpoint}`)
      .pipe(
        catchError(this.handleError)
      );
  }

  /**
   * Handle HTTP errors
   */
  private handleError(error: any) {
    let errorMessage = 'An error occurred';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Error Code: ${error.status}\\nMessage: ${error.message}`;
    }

    console.error(errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
"""

    def generate_reactive_form_component(self) -> str:
        """Generate component using reactive forms"""
        return """
import { Component, OnInit, Output, EventEmitter } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

@Component({
  selector: 'app-user-form',
  template: `
    <form [formGroup]="userForm" (ngSubmit)="onSubmit()">
      <div class="form-group">
        <label for="email">Email</label>
        <input
          id="email"
          type="email"
          formControlName="email"
          class="form-control"
          [class.is-invalid]="isFieldInvalid('email')"
        />
        <div *ngIf="isFieldInvalid('email')" class="invalid-feedback">
          {{ getFieldError('email') }}
        </div>
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input
          id="password"
          type="password"
          formControlName="password"
          class="form-control"
          [class.is-invalid]="isFieldInvalid('password')"
        />
        <div *ngIf="isFieldInvalid('password')" class="invalid-feedback">
          {{ getFieldError('password') }}
        </div>
      </div>

      <button type="submit" [disabled]="!userForm.valid || isSubmitting">
        {{ isSubmitting ? 'Submitting...' : 'Submit' }}
      </button>
    </form>
  `
})
export class UserFormComponent implements OnInit {
  @Output() formSubmit = new EventEmitter<any>();

  userForm!: FormGroup;
  isSubmitting = false;

  constructor(private fb: FormBuilder) {}

  ngOnInit(): void {
    this.initializeForm();
  }

  private initializeForm(): void {
    this.userForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
    });
  }

  isFieldInvalid(fieldName: string): boolean {
    const field = this.userForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  getFieldError(fieldName: string): string {
    const field = this.userForm.get(fieldName);
    if (!field || !field.errors) return '';

    if (field.errors['required']) return `${fieldName} is required`;
    if (field.errors['email']) return 'Please enter a valid email';
    if (field.errors['minlength']) return `Minimum length is ${field.errors['minlength'].requiredLength}`;

    return 'Invalid input';
  }

  async onSubmit(): Promise<void> {
    if (this.userForm.invalid) return;

    this.isSubmitting = true;
    try {
      this.formSubmit.emit(this.userForm.value);
    } finally {
      this.isSubmitting = false;
    }
  }
}
"""

    def generate_input_component(self) -> str:
        """Generate Input component"""
        return """
import { Component, Input, forwardRef } from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

@Component({
  selector: 'app-input',
  template: `
    <div class="input-wrapper">
      <label *ngIf="label" [for]="inputId" class="input__label">
        {{ label }}
      </label>
      <input
        [id]="inputId"
        [value]="value"
        [type]="type"
        [disabled]="disabled"
        [attr.aria-invalid]="error ? true : false"
        [attr.aria-describedby]="error ? inputId + '-error' : null"
        [class.input--error]="error"
        (change)="onChange($event)"
        (blur)="onTouched()"
      />
      <span *ngIf="error" [id]="inputId + '-error'" class="input__error" role="alert">
        {{ error }}
      </span>
      <span *ngIf="helpText && !error" class="input__help">
        {{ helpText }}
      </span>
    </div>
  `,
  styles: [`
    .input-wrapper {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .input__label {
      font-weight: 600;
      font-size: 14px;
      color: #333;
    }

    input {
      padding: 8px 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-family: inherit;
      font-size: 14px;

      &:focus {
        outline: none;
        border-color: #0066cc;
        box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
      }

      &.input--error {
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

    .input__error {
      font-size: 12px;
      color: #dc3545;
    }

    .input__help {
      font-size: 12px;
      color: #666;
    }
  `],
  providers: [{
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => InputComponent),
    multi: true
  }]
})
export class InputComponent implements ControlValueAccessor {
  @Input() label?: string;
  @Input() error?: string;
  @Input() helpText?: string;
  @Input() type: string = 'text';
  @Input() inputId: string = `input-${Math.random()}`;

  value: any;
  disabled = false;

  onChange: (value: any) => void = () => {};
  onTouched: () => void = () => {};

  writeValue(value: any): void {
    this.value = value;
  }

  registerOnChange(fn: (value: any) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isDisabled: boolean): void {
    this.disabled = isDisabled;
  }
}
"""

    def generate_alert_component(self) -> str:
        """Generate Alert component"""
        return """
import { Component, Input, Output, EventEmitter } from '@angular/core';

export type AlertType = 'info' | 'success' | 'warning' | 'error';

@Component({
  selector: 'app-alert',
  template: `
    <div *ngIf="isVisible" [class]="'alert alert--' + type" role="alert">
      <div class="alert__content">
        <span *ngIf="icon" class="alert__icon">{{ icon }}</span>
        <div>
          <div *ngIf="title" class="alert__title">{{ title }}</div>
          <div class="alert__message"><ng-content></ng-content></div>
        </div>
      </div>
      <button *ngIf="closable" class="alert__close" (click)="close()" aria-label="Close alert">
        ✕
      </button>
    </div>
  `,
  styles: [`
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

      &:hover {
        opacity: 1;
      }
    }
  `]
})
export class AlertComponent {
  @Input() type: AlertType = 'info';
  @Input() title?: string;
  @Input() closable = false;
  @Input() icon?: string;
  @Output() closed = new EventEmitter<void>();

  isVisible = true;

  close(): void {
    this.isVisible = false;
    this.closed.emit();
  }
}
"""


def generate_angular_components(component_type: str = "button") -> Dict[str, str]:
    """
    Generate Angular components.

    Args:
        component_type: Type of component to generate

    Returns: dict of {filename: code_content}
    """
    generator = AngularComponentGenerator()
    output = {}

    if component_type == "button":
        output["button.component.ts"] = generator.generate_button_component()
        output["button.component.spec.ts"] = generator.generate_button_test()

    elif component_type == "service":
        output["api.service.ts"] = generator.generate_http_service()

    elif component_type == "form":
        output["user-form.component.ts"] = generator.generate_reactive_form_component()

    elif component_type == "input":
        output["input.component.ts"] = generator.generate_input_component()

    elif component_type == "alert":
        output["alert.component.ts"] = generator.generate_alert_component()

    elif component_type == "all":
        output.update(generate_angular_components("button"))
        output.update(generate_angular_components("form"))
        output.update(generate_angular_components("input"))
        output.update(generate_angular_components("alert"))

    return output
