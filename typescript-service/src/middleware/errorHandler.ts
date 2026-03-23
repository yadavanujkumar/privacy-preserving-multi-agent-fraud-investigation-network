import { Request, Response, NextFunction } from 'express';
import { ZodError } from 'zod';
import { logger } from './logger';

export class AppError extends Error {
  constructor(
    public readonly statusCode: number,
    message: string
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  _next: NextFunction
): void {
  if (err instanceof ZodError) {
    logger.warn('validation_error', {
      correlationId: req.correlationId,
      errors: err.errors
    });
    res.status(400).json({
      error: 'Validation Error',
      details: err.errors.map(e => ({ path: e.path.join('.'), message: e.message }))
    });
    return;
  }

  if (err instanceof AppError) {
    logger.warn('app_error', {
      correlationId: req.correlationId,
      statusCode: err.statusCode,
      message: err.message
    });
    res.status(err.statusCode).json({ error: err.message });
    return;
  }

  logger.error('unhandled_error', {
    correlationId: req.correlationId,
    error: err.message,
    stack: err.stack
  });
  res.status(500).json({ error: 'Internal Server Error' });
}
