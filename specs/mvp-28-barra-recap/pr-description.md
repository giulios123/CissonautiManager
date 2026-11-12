## Cosa cambia per gli organizzatori

- La barra in alto del modulo d'iscrizione (quota e «Iscriviti») ha fondo pieno al posto del vetro trasparente, una riga gialla sotto, importo più grande e pulsante comodo da toccare.
- Il riquadro del riepilogo a destra ha fondo bianco e una riga gialla in alto; scorre con la pagina, non resta fisso.
- Se un campo ha un errore, la pagina lo porta in vista sotto la barra, non dietro.

Nessuna formula di quota, nessun testo e nessun dato cambiano.

## Checklist di test manuali (per gli organizzatori)

Vedi [test-manuali.md](test-manuali.md) (8 passi): desktop, telefono, sito Google (iframe), zoom al 200%, inglese.

## Dettagli tecnici

- Solo `styles.css`, un effetto in `Registration.tsx` (le variabili `--registration-sticky-offset` e `--registration-bar-height` ora stanno sul form) e test; guida partecipante IT/EN.
- Nessuna migrazione né API. Branch impilato sul 27 (PR #30) e sul 26 (PR #29).
- Verificato in locale: frontend 469 test, lint, TypeScript, build; screenshot headless desktop e telefono dell'inizio pagina. Da verificare: scorrimento reale, iframe, zoom 200%, collaudo.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
