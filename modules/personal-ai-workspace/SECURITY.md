# Security Policy

## Secrets

Do not commit `.env`, API keys, personal documents, private notes, or generated databases. Use `.env.example` as the public template and keep real values in local environment variables or private deployment secrets.

## API Exposure

FastAPI authentication is disabled by default for local development. Enable it before exposing the service outside localhost:

```yaml
server:
  api_auth_enabled: true
  api_token_env: PERSONAL_AI_API_TOKEN
```

Set `PERSONAL_AI_API_TOKEN` in `.env` or your deployment secret manager.

## Data Handling

The project is designed for local-first personal data workflows. Review `examples/` before publishing screenshots or sample data. Keep real personal materials outside the public repository.

## Reporting Issues

If you discover a vulnerability, open a private security advisory or contact the repository owner. Do not publish exploit details before a fix is available.
