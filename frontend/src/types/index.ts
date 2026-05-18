export interface ChatResponse {
  reply: string;
  matched_products: string[];
  requires_more_info: boolean;
  missing_fields: string[];
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  meta?: ChatResponse;
}
