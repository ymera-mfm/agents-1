export const sanitizeInput = (input) => {
  if (typeof input !== 'string') {
    return input;
  }
  return input.replace(/[<>]/g, '').trim();
};

export const validateEmail = (email) => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
};

export const debounce = (func, wait) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};
