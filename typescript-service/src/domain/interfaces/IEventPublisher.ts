export interface IEventPublisher {
  publish(topic: string, data: any): Promise<void>;
}