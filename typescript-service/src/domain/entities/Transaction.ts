export class Transaction {
  constructor(
    public readonly id: string,
    public readonly amount: number,
    public readonly sourceAccountHash: string,
    public readonly targetAccountHash: string,
    public readonly timestamp: Date
  ) {}

  isHighValue(): boolean {
    return this.amount > 10000;
  }
}