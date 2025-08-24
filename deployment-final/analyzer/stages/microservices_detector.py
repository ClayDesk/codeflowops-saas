# microservices_detector.py
from pathlib import Path
import json, re
try:
    import yaml  # pip install pyyaml
except Exception:
    yaml = None

RUNTIME_DEFAULT_PORT = {"node": 3000, "python": 8000, "dotnet": 8080, "java": 8080, "generic": 8080}

# Shared resource classifications
SHARED_DB = {"postgres", "mysql", "mariadb", "postgresql", "mongodb"}
SHARED_CACHE = {"redis", "memcached"}
SHARED_SEARCH = {"elasticsearch", "opensearch", "elastic"}
SHARED_MESSAGING = {"kafka", "rabbitmq", "zookeeper", "kafka-connect", "kafka-ui"}
OBSERVABILITY = {"prometheus", "grafana", "loki", "tempo", "jaeger", "otel-collector", "collector"}
AUTH = {"keycloak", "auth", "identity"}
GATEWAY = {"nginx", "traefik", "envoy", "haproxy"}
ADMIN_TOOLS = {"pgadmin", "swagger-ui", "adminer"}

def classify_shared_or_observability(name: str):
    """Classify service as shared resource vs app service"""
    n = name.lower()
    if any(db in n for db in SHARED_DB): return ("database", n)
    if any(cache in n for cache in SHARED_CACHE): return ("cache", n) 
    if any(search in n for search in SHARED_SEARCH): return ("search", n)
    if any(msg in n for msg in SHARED_MESSAGING): return ("messaging", n)
    if any(obs in n for obs in OBSERVABILITY): return ("observability", n)
    if any(auth in n for auth in AUTH) or "identity" in n: return ("auth", n)
    if any(gw in n for gw in GATEWAY): return ("gateway", n)
    if any(admin in n for admin in ADMIN_TOOLS): return ("admin", n)
    return None

def normalize_id(s: str) -> str:
    """Normalize service IDs"""
    return s.strip().lower().replace("_", "-")

def choose_port(svc, compose_port=None, k8s_port=None, exposed_port=None, runtime_default=None):
    """Choose canonical port from various sources"""
    for p in (compose_port, k8s_port, exposed_port):
        if p: return p
    return runtime_default or 8080

def dedupe_services(services):
    """De-duplicate services and fix ports"""
    out, seen = [], set()
    for s in services:
        sid = normalize_id(s["id"])
        key = (sid, s.get("path", ""))
        if key in seen: continue
        seen.add(key)
        s["id"] = sid
        
        # Fix port to one canonical port
        canonical = choose_port(
            s, 
            s.get("compose_port"), 
            s.get("k8s_port"),
            s.get("exposed_port"), 
            RUNTIME_DEFAULT_PORT.get(s["runtime"], 8080)
        )
        s["ports"] = [int(canonical)]
        out.append(s)
    return out

def detect_next_variant(service_dir: Path):
    """Detect Next.js SSR vs static"""
    pj = service_dir / "package.json"
    if not pj.exists(): return None
    
    try:
        data = json.loads(pj.read_text(encoding="utf-8", errors="ignore"))
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        if "next" not in deps: return None
        
        # Check for SSR markers in code
        ssr_markers = [
            "getServerSideProps", "headers()", "cookies()", 
            "export const dynamic = 'force-dynamic'", "revalidate: 0", 
            "cache: 'no-store'", "notFound()", "redirect()"
        ]
        
        for f in list(service_dir.rglob("**/*.tsx")) + list(service_dir.rglob("**/*.ts")) + \
                 list(service_dir.rglob("**/*.js")) + list(service_dir.rglob("**/*.jsx")):
            try:
                t = f.read_text(encoding="utf-8", errors="ignore")
                if any(m in t for m in ssr_markers): return "ssr"
            except Exception: pass
        
        # Check scripts for export
        scripts = data.get("scripts", {})
        if any("next export" in v for v in scripts.values()): return "static"
        if any("next build" in v and "export" in v for v in scripts.values()): return "static"
        
        # Default to static for safety
        return "static"
    except Exception:
        return None

def detect_health_path(svc):
    """Detect health check path based on framework"""
    framework = svc.get("framework", "")
    runtime = svc.get("runtime", "")
    
    if "spring" in framework: return "/actuator/health"
    if "aspnet" in framework or "dotnet" in runtime: return "/health"
    if framework in ["express", "fastify", "nest"]: return "/healthz"
    if framework in ["fastapi", "flask", "django"]: return "/healthz"
    return "/healthz"  # default

def _runtime_from_dockerfile(df_txt: str) -> str:
    """Enhanced runtime detection from Dockerfile"""
    s = df_txt.lower()
    if " from " not in s: return "generic"
    
    # More comprehensive detection
    if any(pattern in s for pattern in [" node:", " from node", "node.js", "nodejs"]): 
        return "node"
    if any(pattern in s for pattern in [" python:", " from python", "python3"]): 
        return "python"
    if any(pattern in s for pattern in ["aspnet", "dotnet", "mcr.microsoft.com/dotnet"]): 
        return "dotnet"
    if any(pattern in s for pattern in ["openjdk", "temurin", "corretto", "amazoncorretto", " maven:", " gradle:"]): 
        return "java"
    if any(pattern in s for pattern in [" golang:", " from golang", " go:", " from go"]): 
        return "golang"
    if any(pattern in s for pattern in [" php:", " from php"]): 
        return "php"
    
    return "generic"

def _infer_framework(runtime: str, text: str, service_path: Path = None) -> str | None:
    """Enhanced framework detection"""
    t = text.lower()
    
    if runtime == "node":
        if "nestjs" in t or "@nestjs" in t: return "nest"
        if "express" in t: return "express"
        if '"next"' in t or "'next'" in t: 
            # Check for Next.js variant if we have the path
            if service_path and detect_next_variant(service_path):
                variant = detect_next_variant(service_path)
                return f"nextjs-{variant}"
            return "nextjs"
        if "fastify" in t: return "fastify"
        if "react" in t and "next" not in t: return "react"
        if "vue" in t: return "vue"
        
    elif runtime == "python":
        if "fastapi" in t: return "fastapi"
        if "flask" in t: return "flask"
        if "django" in t: return "django"
        if "starlette" in t: return "starlette"
        
    elif runtime == "dotnet":
        if "blazor" in t: return "blazor"
        return "aspnet"
        
    elif runtime == "java":
        if "spring-boot" in t or "org.springframework.boot" in t: return "spring-boot"
        if "org.springframework" in t: return "spring"
        if "quarkus" in t: return "quarkus"
        if "micronaut" in t: return "micronaut"
        
    elif runtime == "golang":
        if "gin" in t: return "gin"
        if "echo" in t: return "echo"
        if "fiber" in t: return "fiber"
        
    elif runtime == "php":
        if "laravel" in t: return "laravel"
        if "symfony" in t: return "symfony"
        if "slim" in t: return "slim"
    
    return None

def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def services_from_compose(repo: Path) -> list[dict]:
    """Enhanced Docker Compose service detection"""
    out = []
    if yaml is None: return out
    
    for f in list(repo.glob("docker-compose*.yml")) + list(repo.glob("docker-compose*.yaml")):
        try:
            doc = yaml.safe_load(f.read_text())
        except Exception:
            continue
            
        for name, svc in (doc.get("services") or {}).items():
            build = svc.get("build")
            context_dir, dockerfile = None, None
            
            if isinstance(build, dict):
                context_dir = build.get("context")
                dockerfile = build.get("dockerfile")
            elif isinstance(build, str):
                context_dir = build
                
            ctx = (repo / (context_dir or ".")).resolve()
            df_path = (ctx / (dockerfile or "Dockerfile"))
            
            # Enhanced runtime detection
            runtime = "generic"
            if df_path.exists():
                df_txt = _read_text(df_path)
                runtime = _runtime_from_dockerfile(df_txt)
            
            # Get ports from compose
            ports = []
            for p in (svc.get("ports") or []):
                ps = str(p)
                try:
                    cont = ps.split(":")[-1].split("/")[0]
                    ports.append(int(cont))
                except Exception:
                    pass
            
            # Use compose port as canonical if available
            compose_port = ports[0] if ports else None
            ports = ports or [RUNTIME_DEFAULT_PORT[runtime]]
            
            # Enhanced framework detection
            framework = None
            if (ctx / "package.json").exists():
                pkg_txt = _read_text(ctx / "package.json")
                framework = _infer_framework(runtime, pkg_txt, ctx)
            
            out.append({
                "id": name, 
                "path": str(ctx.relative_to(repo)),
                "runtime": runtime, 
                "framework": framework,
                "ports": ports, 
                "compose_port": compose_port,
                "dockerfile": str(df_path.relative_to(repo)) if df_path.exists() else None,
                "source": "compose", 
                "health": {"path": None, "expect": 200}
            })
    return out

def services_from_k8s(repo: Path) -> list[dict]:
    out = []
    if yaml is None: return out
    for yml in repo.rglob("*.y*ml"):
        txt = _read_text(yml)
        if "kind: Deployment" not in txt: continue
        try:
            for doc in yaml.safe_load_all(txt):
                if not isinstance(doc, dict) or doc.get("kind") != "Deployment":
                    continue
                meta = doc.get("metadata", {}) or {}
                name = meta.get("name") or yml.stem
                c = (((doc.get("spec") or {}).get("template") or {}).get("spec") or {}).get("containers") or []
                if not c: continue
                c0 = c[0]
                image = c0.get("image","").lower()
                ports = [p.get("containerPort") for p in (c0.get("ports") or []) if p.get("containerPort")]
                if "node" in image: runtime = "node"
                elif "python" in image: runtime = "python"
                elif "dotnet" in image or "aspnet" in image: runtime = "dotnet"
                elif any(j in image for j in ["openjdk","temurin","corretto","java"]): runtime = "java"
                else: runtime = "generic"
                out.append({
                    "id": name, "path": ".", "runtime": runtime, "framework": None,
                    "ports": ports or [RUNTIME_DEFAULT_PORT[runtime]],
                    "source": "k8s", "health": {"path": None, "expect": 200}
                })
        except Exception:
            pass
    return out

def services_from_folders(repo: Path) -> list[dict]:
    """Enhanced folder-based service detection"""
    out = []
    roots = [repo/"services", repo/"apps", repo/"src", repo/"packages", repo/"modules"]
    candidates = []
    
    for r in roots:
        if r.exists():
            for d in r.iterdir():
                if d.is_dir():
                    candidates.append(d)
    
    for d in candidates:
        runtime, framework = None, None
        
        # Enhanced detection with framework inference
        if list(d.glob("*.csproj")):
            runtime = "dotnet"
            framework = "aspnet"
        elif (d/"pom.xml").exists() or list(d.glob("**/build.gradle*")):
            runtime = "java"
            # Check for Spring Boot
            if (d/"pom.xml").exists():
                pom_txt = _read_text(d/"pom.xml")
                framework = _infer_framework(runtime, pom_txt, d) or "spring"
            else:
                framework = "spring"
        elif (d/"package.json").exists():
            runtime = "node"
            pj_txt = _read_text(d/"package.json")
            framework = _infer_framework(runtime, pj_txt, d)
        elif (d/"pyproject.toml").exists() or (d/"requirements.txt").exists():
            runtime = "python"
            if (d/"requirements.txt").exists():
                req_txt = _read_text(d/"requirements.txt")
                framework = _infer_framework(runtime, req_txt, d)
            elif (d/"manage.py").exists():
                framework = "django"
        elif (d/"go.mod").exists():
            runtime = "golang"
            go_txt = _read_text(d/"go.mod")
            framework = _infer_framework(runtime, go_txt, d)
        elif (d/"composer.json").exists():
            runtime = "php"
            composer_txt = _read_text(d/"composer.json")
            framework = _infer_framework(runtime, composer_txt, d)
            
        if runtime:
            # Check for Dockerfile to override runtime detection
            dockerfile_path = d / "Dockerfile"
            if dockerfile_path.exists():
                df_txt = _read_text(dockerfile_path)
                detected_runtime = _runtime_from_dockerfile(df_txt)
                if detected_runtime != "generic":
                    runtime = detected_runtime
            
            out.append({
                "id": d.name, 
                "path": str(d.relative_to(repo)), 
                "runtime": runtime,
                "framework": framework, 
                "ports": [RUNTIME_DEFAULT_PORT[runtime]],
                "source": "folders", 
                "health": {"path": None, "expect": 200}
            })
    return out

def merge_services(*lists: list[list[dict]]) -> list[dict]:
    """Merge and classify services vs shared resources"""
    all_services = []
    for lst in lists:
        all_services.extend(lst)
    
    # De-duplicate services
    services = dedupe_services(all_services)
    
    # Separate app services from shared resources
    app_services = []
    shared_resources = {
        "databases": [],
        "caches": [],
        "search": [],
        "messaging": [],
        "auth": [],
        "observability": [],
        "gateway": [],
        "admin": []
    }
    
    for svc in services:
        classification = classify_shared_or_observability(svc["id"])
        if classification:
            category, name = classification
            # Map to managed services where appropriate
            managed_deployments = {
                "database": {
                    "postgres": "aws.rds.postgres.v1",
                    "mysql": "aws.rds.mysql.v1", 
                    "mariadb": "aws.rds.mariadb.v1"
                },
                "cache": {
                    "redis": "aws.elasticache.redis.v1",
                    "memcached": "aws.elasticache.memcached.v1"
                },
                "search": {
                    "elasticsearch": "aws.opensearch.v1",
                    "opensearch": "aws.opensearch.v1"
                },
                "messaging": {
                    "kafka": "aws.msk.v1",
                    "rabbitmq": "aws.mq.rabbitmq.v1"
                },
                "observability": {
                    "prometheus": "aws.amp.v1",
                    "grafana": "aws.amg.v1",
                    "default": "aws.otel.cloudwatch.v1"
                }
            }
            
            deployment = "self-hosted"
            if category in managed_deployments:
                if name in managed_deployments[category]:
                    deployment = managed_deployments[category][name]
                elif "default" in managed_deployments[category]:
                    deployment = managed_deployments[category]["default"]
            
            resource_key = category if category in shared_resources else "admin"
            shared_resources[resource_key].append({
                "name": name,
                "deployment": deployment,
                "original_service": svc["id"]
            })
        else:
            # This is an app service - enhance it
            svc["health"]["path"] = detect_health_path(svc)
            app_services.append(svc)
    
    return app_services, shared_resources
