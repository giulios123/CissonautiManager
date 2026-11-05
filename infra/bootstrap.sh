#!/usr/bin/env bash
# One-time setup for the Azure deployment (see infra/README.md).
#
# What it does, in order:
#   1. creates the resource group and registers the Azure providers needed
#   2. creates the deploy identity (service principal) with rights ONLY on that group,
#      and a passwordless GitHub login (OIDC) for the `production` environment
#   3. creates the GitHub environment `production` and sets every variable and secret
#
# Run it from Azure Cloud Shell (Bash) after `az login` is already done (Cloud Shell does it)
# and `gh auth login` (token with `repo` scope). Safe to run again: existing items are reused.
# No secret is printed or saved on disk: generated passwords go straight to GitHub.

set -euo pipefail

REPO="${REPO:-giulios123/CissonautiManager}"
RG="${RG:-cisonauti-rg}"
LOCATION="${LOCATION:-westeurope}"
APP_NAME="${APP_NAME:-cisonauti-booking}"
IDENTITY_NAME="${IDENTITY_NAME:-cisonauti-deploy}"
ENVIRONMENT="production"

for tool in az gh openssl; do
  command -v "$tool" >/dev/null || { echo "Missing tool: $tool" >&2; exit 1; }
done
az account show >/dev/null 2>&1 || { echo "Run 'az login' first." >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Run 'gh auth login' first." >&2; exit 1; }

SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
TENANT_ID="$(az account show --query tenantId -o tsv)"
SCOPE="/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RG}"

echo "Repository:     ${REPO}"
echo "Subscription:   $(az account show --query name -o tsv) (${SUBSCRIPTION_ID})"
echo "Resource group: ${RG} in ${LOCATION}"
echo "App name:       ${APP_NAME}"
read -r -p "Continue? [y/N] " answer
[[ "$answer" =~ ^[Yy]$ ]] || exit 0

read -r -p "Email of the first admin: " ADMIN_EMAIL
[[ "$ADMIN_EMAIL" == *@*.* ]] || { echo "Invalid email." >&2; exit 1; }
read -r -s -p "Initial admin password (at least 12 characters, hidden): " ADMIN_PASSWORD; echo
read -r -s -p "Repeat it: " ADMIN_PASSWORD_2; echo
[[ "$ADMIN_PASSWORD" == "$ADMIN_PASSWORD_2" ]] || { echo "Passwords differ." >&2; exit 1; }
[[ ${#ADMIN_PASSWORD} -ge 12 ]] || { echo "Password too short." >&2; exit 1; }

echo "1/3 Resource group and providers"
for provider in Microsoft.App Microsoft.OperationalInsights Microsoft.Sql; do
  az provider register --namespace "$provider" --wait >/dev/null
done
az group create --name "$RG" --location "$LOCATION" --output none

echo "2/3 Deploy identity (rights only on ${RG})"
APP_ID="$(az ad app list --display-name "$IDENTITY_NAME" --query "[0].appId" -o tsv)"
if [[ -z "$APP_ID" ]]; then
  APP_ID="$(az ad app create --display-name "$IDENTITY_NAME" --query appId -o tsv)"
fi
az ad sp show --id "$APP_ID" >/dev/null 2>&1 || az ad sp create --id "$APP_ID" --output none
if [[ -z "$(az role assignment list --assignee "$APP_ID" --scope "$SCOPE" --role Contributor --query "[0].id" -o tsv)" ]]; then
  az role assignment create --assignee "$APP_ID" --role Contributor --scope "$SCOPE" --output none
fi
if [[ -z "$(az ad app federated-credential list --id "$APP_ID" --query "[?name=='github-${ENVIRONMENT}'].name" -o tsv)" ]]; then
  az ad app federated-credential create --id "$APP_ID" --parameters "{
    \"name\": \"github-${ENVIRONMENT}\",
    \"issuer\": \"https://token.actions.githubusercontent.com\",
    \"subject\": \"repo:${REPO}:environment:${ENVIRONMENT}\",
    \"audiences\": [\"api://AzureADTokenExchange\"]
  }" --output none
fi

echo "3/3 GitHub environment, variables and secrets"
gh api --method PUT "repos/${REPO}/environments/${ENVIRONMENT}" --silent

set_var() { gh variable set "$1" --env "$ENVIRONMENT" --repo "$REPO" --body "$2"; }
set_secret() { printf '%s' "$2" | gh secret set "$1" --env "$ENVIRONMENT" --repo "$REPO"; }

set_var AZURE_CLIENT_ID "$APP_ID"
set_var AZURE_TENANT_ID "$TENANT_ID"
set_var AZURE_SUBSCRIPTION_ID "$SUBSCRIPTION_ID"
set_var AZURE_RESOURCE_GROUP "$RG"
set_var APP_NAME "$APP_NAME"
set_var ADMIN_EMAIL "$ADMIN_EMAIL"

# Generated here and sent straight to GitHub. The suffix guarantees Azure SQL password complexity.
set_secret SQL_ADMIN_PASSWORD "$(openssl rand -base64 24 | tr -d '=+/')Aa1!"
set_secret SECRET_KEY "$(openssl rand -base64 48)"
set_secret ADMIN_PASSWORD "$ADMIN_PASSWORD"

cat <<DONE

Done. Nothing secret was printed.
- Variables set on '${ENVIRONMENT}': AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID,
  AZURE_RESOURCE_GROUP, APP_NAME, ADMIN_EMAIL
- Secrets set on '${ENVIRONMENT}': SQL_ADMIN_PASSWORD, SECRET_KEY, ADMIN_PASSWORD
- If the GitHub package is private, also set GHCR_USERNAME (variable) and GHCR_TOKEN (secret).
- The SQL admin password exists only in GitHub. To reset it later:
  az sql server update -g ${RG} -n <server> --admin-password <new>

Next: merge to main (or run the 'Deploy' workflow) to create everything.
DONE
