import express, { Request, Response, NextFunction } from 'express';
import { RedpandaClient } from './infrastructure/kafka/RedpandaClient';
import { AnalyzeTransactionUseCase } from './usecases/AnalyzeTransactionUseCase';
import { Transaction } from './domain/entities/Transaction';
import { correlationIdMiddleware } from './middleware/correlationId';
import { requestLogger } from './middleware/requestLogger';
import { errorHandler } from './middleware/errorHandler';
import { TransactionSchema } from './schemas/TransactionSchema';
import { logger } from './middleware/logger';

const app = express();
app.use(express.json());
app.use(correlationIdMiddleware);
app.use(requestLogger);

const PORT = parseInt(process.env.PORT || '3000', 10);
const brokers = (process.env.KAFKA_BROKER || 'localhost:9093').split(',');
const redpandaClient = new RedpandaClient(brokers);
const analyzeUseCase = new AnalyzeTransactionUseCase(redpandaClient);

let isReady = false;

app.get('/health/live', (_req: Request, res: Response) => {
  res.status(200).json({ status: 'alive' });
});

app.get('/health/ready', (_req: Request, res: Response) => {
  if (isReady) {
    res.status(200).json({ status: 'ready' });
  } else {
    res.status(503).json({ status: 'not ready' });
  }
});

app.post('/api/transactions', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const parsed = TransactionSchema.parse(req.body);
    const tx = new Transaction(parsed.id, parsed.amount, parsed.source, parsed.target, new Date());
    await analyzeUseCase.execute(tx);
    logger.info('transaction_accepted', {
      correlationId: req.correlationId,
      transactionId: tx.id,
      amount: tx.amount
    });
    res.status(202).json({ status: 'Accepted', correlationId: req.correlationId });
  } catch (error) {
    next(error);
  }
});

app.use(errorHandler);

async function start(): Promise<void> {
  await redpandaClient.connect();
  isReady = true;
  const server = app.listen(PORT, () =>
    logger.info('server_started', { port: PORT })
  );

  const shutdown = async (signal: string): Promise<void> => {
    logger.info('shutdown_initiated', { signal });
    isReady = false;
    server.close(async () => {
      await redpandaClient.disconnect();
      logger.info('shutdown_complete');
      process.exit(0);
    });
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}

start().catch(err => {
  logger.error('startup_failed', { error: err.message, stack: err.stack });
  process.exit(1);
});