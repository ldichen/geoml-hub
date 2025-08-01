/**
 * Form validation utilities
 */

/**
 * Validation rules
 */
export const rules = {
  required: (value) => {
    if (typeof value === 'string') {
      return value.trim().length > 0 || 'This field is required';
    }
    return value != null || 'This field is required';
  },

  email: (value) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return !value || emailRegex.test(value) || 'Please enter a valid email address';
  },

  minLength: (min) => (value) => {
    return !value || value.length >= min || `Minimum length is ${min} characters`;
  },

  maxLength: (max) => (value) => {
    return !value || value.length <= max || `Maximum length is ${max} characters`;
  },

  min: (min) => (value) => {
    const num = Number(value);
    return isNaN(num) || num >= min || `Minimum value is ${min}`;
  },

  max: (max) => (value) => {
    const num = Number(value);
    return isNaN(num) || num <= max || `Maximum value is ${max}`;
  },

  pattern: (regex, message = 'Invalid format') => (value) => {
    return !value || regex.test(value) || message;
  },

  username: (value) => {
    const usernameRegex = /^[a-zA-Z0-9_-]+$/;
    return !value || (
      usernameRegex.test(value) && 
      value.length >= 3 && 
      value.length <= 20
    ) || 'Username must be 3-20 characters and contain only letters, numbers, underscores, and hyphens';
  },

  password: (value) => {
    if (!value) return true;
    
    const hasLower = /[a-z]/.test(value);
    const hasUpper = /[A-Z]/.test(value);
    const hasNumber = /\d/.test(value);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(value);
    const isLongEnough = value.length >= 8;

    if (!isLongEnough) return 'Password must be at least 8 characters long';
    if (!hasLower) return 'Password must contain at least one lowercase letter';
    if (!hasUpper) return 'Password must contain at least one uppercase letter';
    if (!hasNumber) return 'Password must contain at least one number';
    if (!hasSpecial) return 'Password must contain at least one special character';

    return true;
  },

  confirmPassword: (originalPassword) => (value) => {
    return !value || value === originalPassword || 'Passwords do not match';
  },

  url: (value) => {
    if (!value) return true;
    try {
      new URL(value);
      return true;
    } catch {
      return 'Please enter a valid URL';
    }
  },

  fileSize: (maxSizeInMB) => (file) => {
    if (!file) return true;
    const maxBytes = maxSizeInMB * 1024 * 1024;
    return file.size <= maxBytes || `File size must be less than ${maxSizeInMB}MB`;
  },

  fileType: (allowedTypes) => (file) => {
    if (!file) return true;
    const allowed = Array.isArray(allowedTypes) ? allowedTypes : [allowedTypes];
    return allowed.includes(file.type) || `File type must be one of: ${allowed.join(', ')}`;
  }
};

/**
 * Validate a single field
 * @param {any} value - Field value to validate
 * @param {Array} validators - Array of validation functions
 * @returns {string|null} - Error message or null if valid
 */
export function validateField(value, validators = []) {
  for (const validator of validators) {
    const result = validator(value);
    if (result !== true) {
      return result;
    }
  }
  return null;
}

/**
 * Validate an entire form
 * @param {Object} values - Form values object
 * @param {Object} schema - Validation schema
 * @returns {Object} - Errors object
 */
export function validateForm(values, schema) {
  const errors = {};

  for (const [field, validators] of Object.entries(schema)) {
    const error = validateField(values[field], validators);
    if (error) {
      errors[field] = error;
    }
  }

  return errors;
}

/**
 * Create a validation schema
 * @param {Object} config - Schema configuration
 * @returns {Object} - Validation schema
 */
export function createSchema(config) {
  const schema = {};

  for (const [field, fieldConfig] of Object.entries(config)) {
    schema[field] = [];

    if (fieldConfig.required) {
      schema[field].push(rules.required);
    }

    if (fieldConfig.email) {
      schema[field].push(rules.email);
    }

    if (fieldConfig.minLength) {
      schema[field].push(rules.minLength(fieldConfig.minLength));
    }

    if (fieldConfig.maxLength) {
      schema[field].push(rules.maxLength(fieldConfig.maxLength));
    }

    if (fieldConfig.min !== undefined) {
      schema[field].push(rules.min(fieldConfig.min));
    }

    if (fieldConfig.max !== undefined) {
      schema[field].push(rules.max(fieldConfig.max));
    }

    if (fieldConfig.pattern) {
      schema[field].push(rules.pattern(fieldConfig.pattern, fieldConfig.patternMessage));
    }

    if (fieldConfig.username) {
      schema[field].push(rules.username);
    }

    if (fieldConfig.password) {
      schema[field].push(rules.password);
    }

    if (fieldConfig.url) {
      schema[field].push(rules.url);
    }

    if (fieldConfig.custom) {
      schema[field].push(...fieldConfig.custom);
    }
  }

  return schema;
}

/**
 * Form validation store factory
 */
export function createFormValidator(initialValues = {}, schema = {}) {
  let values = { ...initialValues };
  let errors = {};
  let touched = {};
  let isValid = true;

  function validate() {
    errors = validateForm(values, schema);
    isValid = Object.keys(errors).length === 0;
    return { errors, isValid };
  }

  function setValue(field, value) {
    values[field] = value;
    touched[field] = true;

    // Validate single field
    const fieldValidators = schema[field] || [];
    const fieldError = validateField(value, fieldValidators);
    
    if (fieldError) {
      errors[field] = fieldError;
    } else {
      delete errors[field];
    }

    isValid = Object.keys(errors).length === 0;
  }

  function setTouched(field, isTouched = true) {
    touched[field] = isTouched;
  }

  function reset(newValues = initialValues) {
    values = { ...newValues };
    errors = {};
    touched = {};
    isValid = true;
  }

  function getFieldError(field) {
    return touched[field] ? errors[field] : null;
  }

  return {
    get values() { return values; },
    get errors() { return errors; },
    get touched() { return touched; },
    get isValid() { return isValid; },
    setValue,
    setTouched,
    validate,
    reset,
    getFieldError
  };
}

// Common validation schemas
export const schemas = {
  login: createSchema({
    email: { required: true, email: true },
    password: { required: true }
  }),

  register: createSchema({
    username: { required: true, username: true },
    email: { required: true, email: true },
    password: { required: true, password: true },
    confirmPassword: { required: true }
  }),

  repository: createSchema({
    name: { required: true, minLength: 1, maxLength: 100 },
    description: { maxLength: 500 },
    visibility: { required: true }
  }),

  profile: createSchema({
    full_name: { maxLength: 100 },
    bio: { maxLength: 500 },
    location: { maxLength: 100 },
    website: { url: true }
  })
};