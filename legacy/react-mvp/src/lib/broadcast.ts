import type { BroadcastMessage } from '../types';

export const CHANNEL_NAME = 'sports-video-logger';

export function createBroadcastChannel(): BroadcastChannel {
  return new BroadcastChannel(CHANNEL_NAME);
}

export function postMessage(channel: BroadcastChannel, message: BroadcastMessage): void {
  channel.postMessage(message);
}

export function subscribe(
  channel: BroadcastChannel,
  handler: (message: BroadcastMessage) => void,
): () => void {
  const listener = (event: MessageEvent<BroadcastMessage>) => {
    handler(event.data);
  };
  channel.addEventListener('message', listener);
  return () => channel.removeEventListener('message', listener);
}
