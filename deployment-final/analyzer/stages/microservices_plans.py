# microservices_plans.py
from pathlib import Path
import json

def infer_build_commands(svc: dict, repo: Path) -> list[str]:
    """Enhanced build commands based on runtime and framework"""
    p = repo / svc["path"]
    rt = svc["runtime"]
    fw = svc.get("framework", "")
    
    if rt == "node":
        if "nextjs" in fw:
            if "static" in fw:
                return ["npm ci", "npm run build", "npm run export"]
            else:  # SSR
                return ["npm ci", "npm run build"]
        return ["npm ci"]
        
    elif rt == "python":
        if (p/"pyproject.toml").exists(): 
            return ["pip install -U pip", "pip install ."]
        return ["pip install -U pip", "pip install -r requirements.txt"]
        
    elif rt == "dotnet":
        csproj = list(p.glob("*.csproj"))[:1]
        if csproj:
            return [f"dotnet restore {csproj[0].name}", f"dotnet publish {csproj[0].name} -c Release -o out"]
        return ["dotnet restore", "dotnet publish -c Release -o out"]
        
    elif rt == "java":
        if (p/"mvnw").exists() or (p/"pom.xml").exists(): 
            return ["./mvnw -q -DskipTests package" if (p/"mvnw").exists() else "mvn -q -DskipTests package"]
        if list(p.glob("**/build.gradle*")): 
            return ["./gradlew build -x test" if (p/"gradlew").exists() else "gradle build -x test"]
        return ["mvn -q -DskipTests package"]
        
    elif rt == "golang":
        return ["go mod tidy", "go build -o app ."]
        
    elif rt == "php":
        return ["composer install --no-dev", "php artisan config:cache"]
        
    return []

def infer_artifact(svc: dict) -> dict:
    """Enhanced artifact detection"""
    rt = svc["runtime"]
    fw = svc.get("framework", "")
    
    if rt == "node":
        if "nextjs-static" in fw:
            return {"path": "out", "type": "static"}
        elif "nextjs" in fw:
            return {"path": ".next", "type": "server"}
        return {"path": ".", "type": "server"}
        
    elif rt in ("python", "golang", "php"): 
        return {"path": ".", "type": "server"}
        
    elif rt == "dotnet": 
        return {"path": "out", "type": "server"}
        
    elif rt == "java": 
        if "gradle" in str(svc.get("build", {}).get("commands", [])):
            return {"path": "build/libs", "type": "server"}
        return {"path": "target", "type": "server"}
        
    return {"path": ".", "type": "server"}

def infer_patch_plan(svc: dict, repo: Path) -> list[dict]:
    """Enhanced patch plan with health checks and env setup"""
    p = repo / svc["path"]
    rt = svc["runtime"]
    fw = svc.get("framework", "")
    plan = []
    
    # Ensure health endpoint with framework-specific path
    health_path = svc.get("health", {}).get("path", "/healthz")
    plan.append({
        "action": "ensure_health_endpoint",
        "framework": fw or rt,
        "file_hint": None,
        "pattern": health_path
    })
    
    # Ensure env example with PORT and framework-specific vars
    env_content = f"PORT={svc['ports'][0]}\n"
    if rt == "java":
        env_content += "SPRING_PROFILES_ACTIVE=production\nJAVA_OPTS=-Xmx512m\n"
    elif rt == "dotnet":
        env_content += "ASPNETCORE_ENVIRONMENT=Production\n"
    elif rt == "node":
        env_content += "NODE_ENV=production\n"
    elif rt == "python":
        env_content += "PYTHONPATH=.\n"
    
    if not (p/".env.example").exists():
        plan.append({
            "action": "create_if_missing",
            "file": ".env.example",
            "contents": env_content
        })
    
    # Ensure Dockerfile
    if not svc.get("dockerfile") and not (p/"Dockerfile").exists():
        plan.append({
            "action": "add_optional",
            "file": "Dockerfile", 
            "template_id": f"{rt}.docker.minimal"
        })
    
    # Runtime-specific patches
    if rt == "node":
        if (p/"package.json").exists():
            if "nextjs" in fw:
                if "static" in fw:
                    plan.append({"action": "ensure_script", "file": "package.json", "key": "export", "value": "next export"})
                else:
                    plan.append({"action": "ensure_script", "file": "package.json", "key": "start", "value": "next start"})
            else:
                plan.append({"action": "ensure_script", "file": "package.json", "key": "start", "value": "node server.js"})
                if not (p/"server.js").exists():
                    plan.append({"action": "create_if_missing", "file": "server.js", "template_id": f"{fw or 'express'}.minimal.server"})
    
    return plan

def map_runtime_to_blueprint(rt: str, fw: str = None) -> str:
    """Enhanced blueprint mapping"""
    if rt == "node":
        if fw == "nextjs-static":
            return "aws.s3_cloudfront.next.export.v1"
        elif fw == "nextjs-ssr" or fw == "nextjs":
            return "aws.ecs.fargate.node.alb.v2"
        elif fw == "react":
            return "aws.s3_cloudfront.static.v2"
        return "aws.ecs.fargate.node.alb.v2"
        
    elif rt == "python":
        return "aws.ecs.fargate.python.alb.v2"
        
    elif rt == "dotnet":
        return "aws.ecs.fargate.dotnet.alb.v1"
        
    elif rt == "java":
        return "aws.ecs.fargate.java.alb.v1"
        
    elif rt == "golang":
        return "aws.ecs.fargate.golang.alb.v1"
        
    elif rt == "php":
        return "aws.ecs.fargate.php.alb.v1"
        
    return "aws.ecs.fargate.generic.alb.v1"

def generate_routing_rules(services: list[dict]) -> list[dict]:
    """Generate ALB routing rules for app services"""
    rules = []
    
    # API services get /api/{service}/* patterns
    api_services = []
    frontend_service = None
    
    for svc in services:
        svc_id = svc["id"]
        fw = svc.get("framework", "")
        
        # Check if it's a frontend
        if any(name in svc_id for name in ["storefront", "frontend", "web", "ui"]) or "nextjs" in fw or "react" in fw:
            frontend_service = svc_id
        elif svc_id not in ["gateway", "nginx", "proxy"]:
            api_services.append(svc_id)
    
    # Generate API rules
    for svc_id in sorted(api_services):
        rules.append({
            "path": f"/api/{svc_id}/*",
            "service": svc_id,
            "priority": 100
        })
    
    # Media/uploads rule
    if any("media" in s["id"] for s in services):
        rules.append({
            "path": "/media/*",
            "service": "media",
            "priority": 90
        })
    
    # Catch-all frontend rule (lowest priority)
    if frontend_service:
        rules.append({
            "path": "/*",
            "service": frontend_service,
            "priority": 1
        })
    
    return rules
