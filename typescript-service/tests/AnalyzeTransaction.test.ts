import { AnalyzeTransactionUseCase } from '../src/usecases/AnalyzeTransactionUseCase';
import { Transaction } from '../src/domain/entities/Transaction';
import { IEventPublisher } from '../src/domain/interfaces/IEventPublisher';

class MockPublisher implements IEventPublisher {
  published: { topic: string; data: any }[] = [];
  async publish(topic: string, data: any): Promise<void> {
    this.published.push({ topic, data });
  }
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
});