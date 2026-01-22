/**
 * Setup para testes Jest
 */

// Mock de localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock de showNotification (função global do app)
global.showNotification = jest.fn();

// Mock de IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor(callback, options) {
    this.callback = callback;
    this.options = options;
  }
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Configurações globais do app
global.CONFIG = {
  API_URL: 'http://localhost:5000'
};

// LazyLoadConfig global
global.LazyLoadConfig = {
  PAGE_SIZE: 50,
  BUFFER_SIZE: 20,
  CACHE_TTL: 300000,  // 5 minutos
  SCROLL_THRESHOLD: 0.8,
  MAX_CACHED_PAGES: 10
};

// Suprimir console.log em testes (opcional)
// global.console = {
//   ...console,
//   log: jest.fn(),
//   debug: jest.fn(),
//   info: jest.fn(),
// };
