# infra/

Dağıtım tanımları: `docker/` (docker-compose, Dockerfile'lar), `k8s/` (manifestler — k8s Secret varsayılan base64'tür, şifreli değildir, bkz. [docs/repo-conventions.md](../docs/repo-conventions.md)), `railway/` (Railway servis konfigürasyonu).

Yerel geliştirme her zaman `docker/docker-compose.yml` ile tek komutla ayağa kalkabilmelidir.
