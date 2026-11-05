/** Italian texts. The keys of this file define the type that `en.ts` must satisfy. */
export const it = {
  "common.loading": "Caricamento…",
  "common.somethingWrong": "Qualcosa è andato storto. Riprova.",
  "lang.label": "Lingua",
  "lang.it": "Italiano",
  "lang.en": "Inglese",
  "header.logoAlt": "Cissone",
  "home.register": "Iscriviti al camp",
  "notFound.title": "Pagina non trovata",
  "notFound.home": "Torna alla home",
} as const;

export type MessageKey = keyof typeof it;
