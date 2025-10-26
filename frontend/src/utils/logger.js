// Logger utility wrapper
// Re-exports logger from services for backward compatibility

import { logger, log } from '../services/logger';

export { logger, log };
export default logger;
