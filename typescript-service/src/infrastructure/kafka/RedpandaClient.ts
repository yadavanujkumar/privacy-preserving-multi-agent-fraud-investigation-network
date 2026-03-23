import { Kafka, Producer, logLevel } from 'kafkajs';
import { IEventPublisher } from '../../domain/interfaces/IEventPublisher';

export class RedpandaClient implements IEventPublisher {
  private kafka: Kafka;
  private producer: Producer;

  constructor(brokers: string[]) {
    this.kafka = new Kafka({
      clientId: 'fraud-investigation-api',
      brokers,
      logLevel: logLevel.WARN,
      retry: {
        initialRetryTime: 300,
        retries: 10
      }
    });
    this.producer = this.kafka.producer({
      allowAutoTopicCreation: false,
      idempotent: true
    });
  }

  async connect(): Promise<void> {
    await this.producer.connect();
  }

  async disconnect(): Promise<void> {
    await this.producer.disconnect();
  }

  async publish(topic: string, data: unknown): Promise<void> {
    await this.producer.send({
      topic,
      messages: [{ value: JSON.stringify(data) }]
    });
  }
}