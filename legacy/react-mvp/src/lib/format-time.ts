export function formatTimestamp(seconds: number): string {
  const total = Math.floor(seconds);
  const minutes = Math.floor(total / 60);
  const secs = total % 60;
  return `${minutes}-${secs < 10 ? '0' : ''}${secs}`;
}
