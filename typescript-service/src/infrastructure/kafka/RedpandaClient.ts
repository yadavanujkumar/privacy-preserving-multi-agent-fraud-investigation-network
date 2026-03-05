import { Kafka, Producer } from 'kafkajs';
import { IEventPublisher } from '../../domain/interfaces/IEventPublisher';

export class RedpandaClient implements IEventPublisher {
  private kafka: Kafka;
  private producer: Producer;

  constructor(brokers: string[]) {
    this.kafka = new Kafka({ clientId: 'ts-service', brokers });
    this.producer = this.kafka.producer();
  }

  async connect(): Promise<void> {
    await this.producer.connect();
  }

  async publish(topic: string, data: any): Promise<void> {
    await this.producer.send({
      topic,
      messages: [{ value: JSON.stringify(data) }]
    });
  }
}