import { z } from 'zod';

export const TransactionSchema = z.object({
  id: z.string().uuid({ message: 'id must be a valid UUID' }),
  amount: z.number().positive({ message: 'amount must be a positive number' }),
  source: z.string().min(1, { message: 'source account hash is required' }),
  target: z.string().min(1, { message: 'target account hash is required' })
});

export type TransactionInput = z.infer<typeof TransactionSchema>;
