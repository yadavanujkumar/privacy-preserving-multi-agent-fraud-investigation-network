import { AnalyzeTransactionUseCase } from '../src/usecases/AnalyzeTransactionUseCase';
import { Transaction } from '../src/domain/entities/Transaction';
import { IEventPublisher } from '../src/domain/interfaces/IEventPublisher';
import { TransactionSchema } from '../src/schemas/TransactionSchema';

class MockPublisher implements IEventPublisher {
  published: { topic: string; data: unknown }[] = [];
  async publish(topic: string, data: unknown): Promise<void> {
    this.published.push({ topic, data });
  }
  async disconnect(): Promise<void> {}
}

describe('AnalyzeTransactionUseCase', () => {
  it('should publish to high-value-transactions if amount > 10000', async () => {
    const publisher = new MockPublisher();
    const useCase = new AnalyzeTransactionUseCase(publisher);
    const tx = new Transaction('1', 15000, 'src', 'tgt', new Date());

    await useCase.execute(tx);

    expect(publisher.published.length).toBe(2);
    expect(publisher.published[0].topic).toBe('high-value-transactions');
  });

  it('should only publish to all-transactions for low-value transactions', async () => {
    const publisher = new MockPublisher();
    const useCase = new AnalyzeTransactionUseCase(publisher);
    const tx = new Transaction('2', 500, 'src', 'tgt', new Date());

    await useCase.execute(tx);

    expect(publisher.published.length).toBe(1);
    expect(publisher.published[0].topic).toBe('all-transactions');
  });
});

describe('TransactionSchema', () => {
  it('should reject a transaction with a non-UUID id', () => {
    const result = TransactionSchema.safeParse({ id: 'not-a-uuid', amount: 100, source: 'A', target: 'B' });
    expect(result.success).toBe(false);
  });

  it('should reject a transaction with a negative amount', () => {
    const result = TransactionSchema.safeParse({
      id: '550e8400-e29b-41d4-a716-446655440000',
      amount: -1,
      source: 'A',
      target: 'B'
    });
    expect(result.success).toBe(false);
  });

  it('should accept a valid transaction', () => {
    const result = TransactionSchema.safeParse({
      id: '550e8400-e29b-41d4-a716-446655440000',
      amount: 250,
      source: 'A',
      target: 'B'
    });
    expect(result.success).toBe(true);
  });
});