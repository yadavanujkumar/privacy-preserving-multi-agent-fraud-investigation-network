import { Transaction } from '../domain/entities/Transaction';
import { IEventPublisher } from '../domain/interfaces/IEventPublisher';

export class AnalyzeTransactionUseCase {
  constructor(private eventPublisher: IEventPublisher) {}

  async execute(transaction: Transaction): Promise<void> {
    if (transaction.isHighValue()) {
      await this.eventPublisher.publish('high-value-transactions', transaction);
    }
    await this.eventPublisher.publish('all-transactions', transaction);
  }
}