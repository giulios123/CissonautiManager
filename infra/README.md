# Infrastruttura Azure

Un solo gruppo di risorse con: Container App (si spegne quando nessuno la usa), database Azure SQL tier Basic, Azure Communication Services per le email, un job orario per i promemoria di pagamento, Log Analytics. L'immagine sta su GitHub Container Registry. Tutto è in `main.bicep`.

> Stato: scritto ma **non ancora validato né provato** (nessun accesso ad Azure in fase di sviluppo). Il primo deploy serve anche a questo: parti da `what-if`.

## Costi e spegnimento

- **Container App**: zero repliche quando non è usata, quindi non si paga il calcolo. Il primo accesso dopo una pausa impiega qualche secondo. Controlla che resti `minReplicas: 0`.
- **Database Basic**: circa 5 € al mese (stima, da verificare nel calcolatore Azure), sempre acceso, non si mette in pausa. Se l'evento è finito e non serve più, esporta i dati ed elimina il database o l'intero gruppo di risorse.
- **Email**: Azure Communication Services con dominio gestito Azure, gratuito; si paga solo l'invio (frazioni di centesimo a messaggio, per un camp di poche decine di persone è trascurabile).
- **Job promemoria**: parte ogni ora, gira pochi secondi e si spegne.
- **Log**: 30 giorni di conservazione, ben sotto la quota gratuita mensile.

## Prima configurazione (una volta sola)

**Via rapida**: da Azure Cloud Shell (Bash), dopo `gh auth login`, lancia `./infra/bootstrap.sh`. Fa in un colpo tutto quello che segue (gruppo di risorse, utenza di deploy, ambiente GitHub, variabili e segreti) e non stampa nessun segreto. I passi sotto sono la stessa cosa fatta a mano, per riferimento.

Servono Azure CLI e i permessi sull'abbonamento.

```bash
az login
az account set --subscription <ID_ABBONAMENTO>
az group create --name cissonauti-rg --location westeurope
```

Poi, **nello stesso abbonamento appena selezionato**, registra i provider di risorse che il Bicep usa. L'identità di deploy ha permessi solo sul gruppo di risorse e non può farlo da sola (`bootstrap.sh` lo fa già):

```bash
for provider in Microsoft.App Microsoft.Communication Microsoft.OperationalInsights Microsoft.Sql; do
  az provider register --namespace "$provider" --wait
done
```

Utenza per GitHub Actions, con login senza password (OIDC) e permessi solo su quel gruppo:

```bash
APP_ID=$(az ad app create --display-name cissonauti-deploy --query appId -o tsv)
az ad sp create --id "$APP_ID"
az role assignment create --assignee "$APP_ID" --role Contributor \
  --scope /subscriptions/<ID_ABBONAMENTO>/resourceGroups/cissonauti-rg
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
| Variabile | `AZURE_RESOURCE_GROUP` | `cissonauti-rg` |
| Variabile | `APP_NAME` | nome breve, ad esempio `cissonauti-booking` |
| Variabile | `ADMIN_EMAIL` | email del primo admin |
| Segreto | `SQL_ADMIN_PASSWORD` | password lunga del database (maiuscole, minuscole, numeri, simboli) |
| Segreto | `SECRET_KEY` | stringa casuale lunga |
| Segreto | `ADMIN_PASSWORD` | facoltativa: password iniziale del primo admin |

Se il repository o il pacchetto su GitHub sono privati, aggiungi anche la variabile `GHCR_USERNAME` e il segreto `GHCR_TOKEN` (token con permesso `read:packages`). Se sono pubblici non servono.

## Se il deploy dice MissingSubscriptionRegistration

Il messaggio `The subscription is not registered to use namespace 'Microsoft.Communication'` (o un altro `Microsoft.*`) vuol dire che l'abbonamento non ha registrato quel provider, e le email (Azure Communication Services) non partono. Si risolve una volta sola, con permessi sull'abbonamento:

```bash
az provider register --namespace Microsoft.Communication --wait
```

Poi rilancia il deploy dalla scheda Actions («Re-run jobs»): non serve nessuna modifica al codice. Un ambiente creato prima dell'MVP 2 con `bootstrap.sh` non aveva questo provider.

## Se il server SQL non si crea (RegionDoesNotAllowProvisioning)

Alcuni abbonamenti non possono creare nuovi server SQL in certe regioni. Il resto dell'app può restare dove è: basta mettere il database in un'altra regione europea. Per sapere dove si può creare, prova a creare un server vuoto (non costa nulla) in alcune regioni:

```bash
for r in westeurope francecentral germanywestcentral swedencentral uksouth italynorth; do
  n="probe-$RANDOM$RANDOM"
  if az sql server create -g cissonauti-rg -n "$n" -l "$r" -u probeadmin -p "$(openssl rand -hex 12)Aa1" -o none 2>/dev/null; then
    echo "$r: ok"; az sql server delete -g cissonauti-rg -n "$n" --yes
  else
    echo "$r: no"
  fi
done
```

Poi imposta la regione scelta come variabile dell'ambiente `production` (`SQL_LOCATION`) e rilancia il deploy:

```bash
gh variable set SQL_LOCATION --env production --repo giulios123/CissonautiManager --body westeurope
```

Se un deploy precedente ha lasciato un server in stato Failed, eliminalo prima: `az sql server delete -g cissonauti-rg -n <nome> --yes`.

## Se il login a Azure fallisce (AADSTS700213)

Azure confronta il `subject` della credenziale con quello che GitHub presenta. Il messaggio d'errore nel log del workflow riporta il subject esatto. Alcuni repository lo presentano nel formato con gli ID numerici (`repo:proprietario@ID/repo@ID:environment:production`): in quel caso serve una seconda credenziale con quel subject. `bootstrap.sh` le crea entrambe. A mano:

```bash
az ad app federated-credential create --id <APP_ID> --parameters '{
  "name": "github-production-id",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "<SUBJECT_DAL_LOG>",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

## Deploy

Ogni push su `main` esegue `deploy.yml`: costruisce l'immagine, la pubblica su GHCR, applica `main.bicep` e aggiorna la Container App. Le migrazioni del database partono da sole all'avvio del container. Si può lanciare anche a mano da Actions (Run workflow).

Per provare prima senza modificare nulla:

```bash
export IMAGE=ghcr.io/<proprietario>/<repo>:<tag> ADMIN_EMAIL=... SQL_ADMIN_PASSWORD=... SECRET_KEY=...
az deployment group what-if --resource-group cissonauti-rg \
  --template-file infra/main.bicep --parameters infra/main.bicepparam
```

Dopo il deploy `GET <url>/api/health` deve rispondere 200. L'indirizzo è nell'output `url`.

Il dominio pubblico è `https://app.cissonesummercamp.it`. `main.bicep` lo associa al certificato gestito già presente nell'ambiente Container Apps e usa lo stesso indirizzo per i link delle email e dei promemoria. Se ricrei il certificato, aggiorna il parametro `appCertificateName` nel Bicep. L'output `azureUrl` conserva anche l'indirizzo tecnico di Container Apps.

## Da sapere

- **Email**: con `EMAIL_PROVIDER=acs` (default) le email partono dall'indirizzo `DoNotReply@<id>.azurecomm.net`, visibile nell'output `emailSender` del deploy. Il dominio gestito ha limiti di invio bassi (alcune decine di messaggi al minuto) e può finire nella posta indesiderata: se succede, la strada è un dominio proprio da collegare al servizio email. Per tornare ai log basta `EMAIL_PROVIDER=console` (parametro `emailProvider`).
- **Promemoria**: il job `<app>-reminders` (Container Apps Job) gira ogni ora (`0 * * * *`, orario UTC) con la stessa immagine e il comando `python -m app.jobs.send_reminders`. Per vedere cosa ha fatto: portale Azure, risorsa del job, "Execution history" e i log (riga `Reminders: examined=... mid=... final=...`). Per lanciarlo subito: `az containerapp job start -g <gruppo> -n <app>-reminders`.
- **Migrazioni**: partono all'avvio dell'app. Dopo ogni deploy il workflow chiama `/api/health` per svegliarla, così le migrazioni sono applicate prima che il job giri con il nuovo codice.
- Il database accetta connessioni dai servizi Azure. L'accesso con identità gestita al posto della password è un'evoluzione possibile.
