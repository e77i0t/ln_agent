#!/usr/bin/env python3
import sys
import subprocess
import venv
from pathlib import Path
import platform
import time
import socket
import os

def check_python_version():
    """Check if Python version meets requirements."""
    if sys.version_info < (3, 11):
        print("Error: Python 3.11 or higher is required")
        sys.exit(1)
    print(f"✓ Python version {platform.python_version()} OK")

def create_virtual_environment():
    """Create a virtual environment if it doesn't exist."""
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        venv.create(venv_path, with_pip=True)
        print("✓ Virtual environment created")
    else:
        print("✓ Virtual environment already exists")
    return venv_path

def install_dependencies(venv_path):
    """Install project dependencies."""
    pip_path = venv_path / "bin" / "pip"
    
    print("Installing dependencies...")
    subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
    subprocess.run([str(pip_path), "install", "-r", "requirements-dev.txt"], check=True)
    print("✓ Dependencies installed")

def setup_env_file():
    """Set up .env file if it doesn't exist."""
    if not Path(".env").exists():
        print("Creating .env file from example...")
        subprocess.run(["cp", "env.example", ".env"], check=True)
        print("✓ .env file created")
    else:
        print("✓ .env file already exists")

def check_docker():
    """Check if Docker is running."""
    try:
        subprocess.run(["docker", "info"], check=True, capture_output=True)
        print("✓ Docker is running")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: Docker is not running or not installed")
        return False

def start_docker_services():
    """Start Docker services using docker-compose."""
    print("Starting Docker services...")
    subprocess.run(["docker-compose", "up", "-d"], check=True)
    print("✓ Docker services started")

def wait_for_service(host, port, service_name, timeout=30):
    """Wait for a service to become available."""
    start_time = time.time()
    while True:
        try:
            socket.create_connection((host, port), timeout=1)
            print(f"✓ {service_name} is ready")
            return True
        except (socket.timeout, socket.error):
            if time.time() - start_time > timeout:
                print(f"Error: {service_name} did not become available")
                return False
            time.sleep(1)

def main():
    """Main setup function."""
    try:
        # Change to project root directory
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        
        print("Starting development environment setup...")
        
        # Run checks and setup
        check_python_version()
        venv_path = create_virtual_environment()
        install_dependencies(venv_path)
        setup_env_file()
        
        if check_docker():
            start_docker_services()
            # Wait for services to be ready
            wait_for_service("localhost", 27017, "MongoDB")
            wait_for_service("localhost", 6379, "Redis")
        
        print("\nSetup completed successfully! 🎉")
        print("\nNext steps:")
        print("1. Activate the virtual environment:")
        print("   source venv/bin/activate")
        print("2. Start the development server:")
        print("   flask run")
        
    except Exception as e:
        print(f"Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 