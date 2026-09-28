"""Keep demo host ports separate from existing services; container ports stay conventional."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
for name in ["README.md","docs/api.md","docs/demo-guide.md","scripts/demo.py","frontend/playwright.config.ts","frontend/vite.config.ts"]:
    path=root/name
    source=path.read_text(encoding="utf-8")
    source=source.replace("localhost:8000","localhost:18000").replace("localhost:8080","localhost:18080")
    if name=="README.md":
        source=source.replace("ports 8080, 8000, 15432","ports 18080, 18000, 15432").replace("--port 8000","--port 18000").replace("proxies to port 8000","proxies to port 18000")
    path.write_text(source,encoding="utf-8")
path=root/"docker-compose.yml"
path.write_text(path.read_text(encoding="utf-8").replace("127.0.0.1:8000:8000","127.0.0.1:18000:8000").replace("127.0.0.1:8080:80","127.0.0.1:18080:80"),encoding="utf-8")
