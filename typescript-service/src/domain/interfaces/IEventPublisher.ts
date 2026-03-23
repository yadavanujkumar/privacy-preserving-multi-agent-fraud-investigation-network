export interface IEventPublisher {
  publish(topic: string, data: unknown): Promise<void>;
  disconnect(): Promise<void>;
}