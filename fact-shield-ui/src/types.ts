export type Claim = {
  id: string;
  claim?: string;       // some endpoints return 'claim'
  claim_text?: string;  // others return 'claim_text'
  status: "pending" | "true" | "false" | "escalated_manual" | "unknown";
  explanation?: string | null;
  truth_count?: number;
  false_count?: number;
};

export type SignInResponse = {
  access_token: string;
  user: { id: string; email: string; name: string; org: string; role: string };
};