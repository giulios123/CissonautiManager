export type GuestMeal = { date: string; kind: "lunch" | "dinner" };
export type GuestActivity = {
  id: number;
  title: string;
  date: string;
  period: "morning" | "afternoon" | "evening";
};
export type Payer = "paying" | "non_paying";

export type GuestMovement = {
  id: number;
  kind: "payment" | "refund";
  amount_cents: number;
  channel: string;
  paid_on: string;
  note: string | null;
  created_at: string;
  voided_at: string | null;
  void_reason: string | null;
};
export type GuestItem = { label: string; price_cents: number; collectable_cents: number };

/** An external guest: a person without an account, added by an admin. */
export type Guest = {
  id: number;
  first_name: string;
  last_name: string;
  payer: Payer;
  phone: string | null;
  reference: string | null;
  internal_note: string | null;
  diet: "omnivore" | "vegetarian" | "vegan" | null;
  allergies: string | null;
  allergies_consent_at: string | null;
  meals: GuestMeal[];
  activities: GuestActivity[];
  // Money: read from the current prices; movements are the register of the guest.
  due_cents: number;
  paid_cents: number;
  refunded_cents: number;
  balance_cents: number;
  items: GuestItem[];
  movements: GuestMovement[];
  warning?: string | null;
};

/** What the form sends. `confirm_duplicate` is set only after the admin said it is another person. */
export type GuestInput = {
  first_name: string;
  last_name: string;
  payer: Payer;
  phone: string | null;
  reference: string | null;
  internal_note: string | null;
  diet: Guest["diet"];
  allergies: string | null;
  allergies_consent: boolean;
  confirm_duplicate?: boolean;
};

export const emptyGuest: GuestInput = {
  first_name: "",
  last_name: "",
  payer: "paying",
  phone: null,
  reference: null,
  internal_note: null,
  diet: null,
  allergies: null,
  allergies_consent: false,
};

export const guestInput = (guest: Guest): GuestInput => ({
  first_name: guest.first_name,
  last_name: guest.last_name,
  payer: guest.payer,
  phone: guest.phone,
  reference: guest.reference,
  internal_note: guest.internal_note,
  diet: guest.diet,
  allergies: guest.allergies,
  allergies_consent: guest.allergies_consent_at !== null,
});
