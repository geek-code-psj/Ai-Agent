"""Quick verification script to test the framework setup."""

import sys
import os

def check_file_exists(filepath, name):
    """Check if a file exists."""
    if os.path.exists(filepath):
        print(f"✅ {name}")
        return True
    else:
        print(f"❌ {name} - NOT FOUND")
        return False

def main():
    """Run verification checks."""
    print("=" * 60)
    print("AI Agent Framework - Verification Script")
    print("=" * 60)
    
    checks_passed = 0
    total_checks = 0
    
    # Check core files
    print("\n📁 Core Files:")
    files = [
        ("requirements.txt", "Requirements file"),
        (".env.example", "Environment template"),
        (".gitignore", "Git ignore"),
        ("README.md", "Documentation"),
        ("docker-compose.yml", "Docker Compose"),
    ]
    
    for file, name in files:
        total_checks += 1
        if check_file_exists(file, name):
            checks_passed += 1
    
    # Check app structure
    print("\n📦 Application Structure:")
    dirs = [
        ("app", "App directory"),
        ("app/agents", "Agents"),
        ("app/tools", "Tools"),
        ("app/chains", "Chains"),
        ("app/memory", "Memory"),
        ("app/models", "Models"),
        ("app/middleware", "Middleware"),
        ("app/core", "Core"),
    ]
    
    for dir_path, name in dirs:
        total_checks += 1
        if check_file_exists(dir_path, name):
            checks_passed += 1
    
    # Check Docker files
    print("\n🐳 Docker:")
    docker_files = [
        ("docker/Dockerfile", "Dockerfile"),
    ]
    
    for file, name in docker_files:
        total_checks += 1
        if check_file_exists(file, name):
            checks_passed += 1
    
    # Check Kubernetes files
    print("\n☸️  Kubernetes:")
    k8s_files = [
        ("k8s/namespace.yaml", "Namespace"),
        ("k8s/configmap.yaml", "ConfigMap"),
        ("k8s/secret.yaml", "Secret"),
        ("k8s/deployment.yaml", "Deployment"),
        ("k8s/service.yaml", "Service"),
        ("k8s/hpa.yaml", "HPA"),
        ("k8s/ingress.yaml", "Ingress"),
    ]
    
    for file, name in k8s_files:
        total_checks += 1
        if check_file_exists(file, name):
            checks_passed += 1
    
    # Check key Python files
    print("\n🐍 Key Python Files:")
    py_files = [
        ("app/api.py", "FastAPI application"),
        ("app/main.py", "Entry point"),
        ("app/agents/base_agent.py", "Base agent"),
        ("app/tools/web_search.py", "Web search tool"),
        ("app/memory/persistent_memory.py", "Persistent memory"),
    ]
    
    for file, name in py_files:
        total_checks += 1
        if check_file_exists(file, name):
            checks_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Verification Complete: {checks_passed}/{total_checks} checks passed")
    print("=" * 60)
    
    if checks_passed == total_checks:
        print("\n✅ All files present! Framework is ready.")
        print("\nNext steps:")
        print("1. Set your OPENAI_API_KEY in .env")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run locally: python app/main.py")
        print("4. Visit: http://localhost:8000/docs")
        return 0
    else:
        print(f"\n⚠️  {total_checks - checks_passed} file(s) missing.")
        print("Please check the project structure.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
