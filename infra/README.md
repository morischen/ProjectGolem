# infra/

Local development infrastructure (ARCHITECTURE.md §2).

```bash
docker compose -f infra/docker-compose.yml up -d     # start
docker compose -f infra/docker-compose.yml down      # stop (keep data)
docker compose -f infra/docker-compose.yml down -v   # stop + wipe volumes
```

| Service | Purpose | Ports | Dev creds |
|---------|---------|-------|-----------|
| neo4j | Knowledge graph | 7474 (browser), 7687 (bolt) | neo4j / devpassword |
| qdrant | Vector store | 6333 (http), 6334 (grpc) | — |
| postgres | Metadata / canonical records | 5432 | eip / devpassword (db: eip) |
| minio | S3-compatible object storage | 9000 (api), 9001 (console) | eip / devpassword |

**Dev only.** These are throwaway local credentials. Production uses managed,
secret-managed instances — never these values.
