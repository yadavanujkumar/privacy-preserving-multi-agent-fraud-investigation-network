import express from 'express';
import { RedpandaClient } from './infrastructure/kafka/RedpandaClient';
import { AnalyzeTransactionUseCase } from './usecases/AnalyzeTransactionUseCase';
import { Transaction } from './domain/entities/Transaction';

const app = express();
app.use(express.json());

const brokers = [process.env.KAFKA_BROKER || 'localhost:9093'];
const redpandaClient = new RedpandaClient(brokers);
const analyzeUseCase = new AnalyzeTransactionUseCase(redpandaClient);

app.post('/api/transactions', async (req, res) => {
  try {
    const { id, amount, source, target } = req.body;
    const tx = new Transaction(id, amount, source, target, new Date());
    await analyzeUseCase.execute(tx);
    res.status(202).json({ status: 'Accepted' });
  } catch (error) {
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

async function start() {
  await redpandaClient.connect();
  app.listen(3000, () => console.log('TS Service listening on port 3000'));
}

start();