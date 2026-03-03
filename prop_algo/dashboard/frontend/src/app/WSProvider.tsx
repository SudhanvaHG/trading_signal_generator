'use client';
import { useWebSocket } from '@/hooks/useWebSocket';

export function WSProvider() {
  useWebSocket();
  return null;
}
