import type { ChatResponse } from './types';

export async function sendMessage(userId: string, message: string): Promise<ChatResponse> {
  const response = await fetch("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: userId,
      message,
    }),
  });

  if (!response.ok) {
    throw new Error(await response.text() || response.statusText);
  }

  return response.json();
}

export async function resetUser(userId: string): Promise<void> {
  const response = await fetch("/reset", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: userId,
    }),
  });

  if (!response.ok) {
    throw new Error(await response.text() || response.statusText);
  }
}
