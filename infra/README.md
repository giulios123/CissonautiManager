# Infrastruttura Azure

Un solo gruppo di risorse con: Container App (si spegne quando nessuno la usa), database Azure SQL tier Basic, Log Analytics. L'immagine sta su GitHub Container Registry. Tutto è in `main.bicep`.

> Stato: scritto ma **non ancora validato né provato** (nessun accesso ad Azure in fase di sviluppo). Il primo deploy serve anche a questo: parti da `what-if`.

## Costi e spegnimento

- **Container App**: zero repliche quando non è usata, quindi non si paga il calcolo. Il primo accesso dopo una pausa impiega qualche secondo. Controlla che resti `minReplicas: 0`.
- **Database Basic**: circa 5 € al mese (stima, da verificare nel calcolatore Azure), sempre acceso, non si mette in pausa. Se l'evento è finito e non serve più, esporta i dati ed elimina il database o l'intero gruppo di risorse.
- **Log**: 30 giorni di conservazione, ben sotto la quota gratuita mensile.

## Prima configurazione (una volta sola)

Servono Azure CLI e i permessi sull'abbonamento.

```bash
az login
az account set --subscription <ID_ABBONAMENTO>
az group create --name cisonauti-rg --location westeurope
```

Utenza per GitHub Actions, con login senza password (OIDC) e permessi solo su quel gruppo:

```bash
APP_ID=$(az ad app create --display-name cisonauti-deploy --query appId -o tsv)
az ad sp create --id "$APP_ID"
az role assignment create --assignee "$APP_ID" --role Contributor \
  --scope /subscriptions/<ID_ABBONAMENTO>/resourceGroups/cisonauti-rg
az ad app federated-credential create --id "$APP_ID" --parameters '{
  "name": "github-production",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:giulios123/CissonautiManager:environment:production",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

Su GitHub crea l'ambiente `production` (Settings, Environments) e imposta:

| Tipo | Nome | Valore |
|---|---|---|
| Variabile | `AZURE_CLIENT_ID` | l'`APP_ID` di sopra |
| Variabile | `AZURE_TENANT_ID` | `az account show --query tenantId -o tsv` |
| Variabile | `AZURE_SUBSCRIPTION_ID` | l'ID dell'abbonamento |
| Variabile | `AZURE_RESOURCE_GROUP` | `cisonauti-rg` |
| Variabile | `APP_NAME` | nome breve, ad esempio `cisonauti-booking` |
| Variabile | `ADMIN_EMAIL` | email del primo admin |
| Segreto | `SQL_ADMIN_PASSWORD` | password lunga del database (maiuscole, minuscole, numeri, simboli) |
| Segreto | `SECRET_KEY` | stringa casuale lunga |
| Segreto | `ADMIN_PASSWORD` | facoltativa: password iniziale del primo admin |

Se il repository o il pacchetto su GitHub sono privati, aggiungi anche la variabile `GHCR_USERNAME` e il segreto `GHCR_TOKEN` (token con permesso `read:packages`). Se sono pubblici non servono.

## Deploy

Ogni push su `main` esegue `deploy.yml`: costruisce l'immagine, la pubblica su GHCR, applica `main.bicep` e aggiorna la Container App. Le migrazioni del database partono da sole all'avvio del container. Si può lanciare anche a mano da Actions (Run workflow).

Per provare prima senza modificare nulla:

```bash
export IMAGE=ghcr.io/<proprietario>/<repo>:<tag> ADMIN_EMAIL=... SQL_ADMIN_PASSWORD=... SECRET_KEY=...
az deployment group what-if --resource-group cisonauti-rg \
  --template-file infra/main.bicep --parameters infra/main.bicepparam
```

Dopo il deploy `GET <url>/api/health` deve rispondere 200. L'indirizzo è nell'output `url`.

## Da sapere

- Finché non c'è l'invio email reale (MVP 2) i magic link compaiono solo nei log (Log Analytics). L'admin entra con email e password.
- Il database accetta connessioni dai servizi Azure. L'accesso con identità gestita al posto della password è un'evoluzione possibile.
