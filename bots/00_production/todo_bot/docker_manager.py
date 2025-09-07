#!/usr/bin/env python3
"""
Docker Container Manager for Discord Bots
- Überprüft laufende Container
- Aktualisiert Container mit neuester Version
- Startet Todo-Bot Container
- Managed Container-Lifecycle
"""

import os
import sys
import subprocess
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('docker_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DockerManager')

class DockerManager:
    """Manages Docker containers for Discord bots"""
    
    def __init__(self):
        self.docker_compose_file = Path("/home/pi/Documents/discord/docker-compose.yml")
        self.todo_compose_file = Path("/home/pi/Documents/discord/bots/00_production/todo_bot/docker-compose.todo.yml")
        self.image_name = "discord-bots"
        self.todo_image_name = "discord-todo-bot"
        
    def run_command(self, cmd: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
        """Execute shell command and return result"""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=cwd,
                timeout=300
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, f"Command failed: {e}"
    
    def get_running_containers(self) -> Dict[str, Dict]:
        """Get information about running Discord bot containers"""
        success, output = self.run_command(['docker', 'ps', '--format', 'json'])
        
        if not success:
            logger.error(f"Failed to get container list: {output}")
            return {}
        
        containers = {}
        for line in output.strip().split('\n'):
            if line.strip():
                try:
                    container = json.loads(line)
                    # Filter für Discord Bot Container
                    if any(name in container.get('Names', '') for name in ['discord', 'bot']):
                        containers[container['Names']] = {
                            'id': container['ID'],
                            'image': container['Image'],
                            'status': container['Status'],
                            'created': container.get('CreatedAt', ''),
                            'ports': container.get('Ports', '')
                        }
                except json.JSONDecodeError:
                    continue
        
        return containers
    
    def get_image_version(self, image_name: str) -> Optional[str]:
        """Get image creation date as version identifier"""
        success, output = self.run_command(['docker', 'images', '--format', 'json', image_name])
        
        if not success:
            return None
        
        for line in output.strip().split('\n'):
            if line.strip():
                try:
                    image = json.loads(line)
                    if image['Repository'] == image_name:
                        return image.get('CreatedAt', 'unknown')
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def build_main_bot_image(self) -> bool:
        """Build the main Discord bots image"""
        logger.info("🔨 Building main Discord bots image...")
        
        success, output = self.run_command(
            ['docker', 'build', '-t', self.image_name, '.'],
            cwd="/home/pi/Documents/discord"
        )
        
        if success:
            logger.info("✅ Main bot image built successfully")
            return True
        else:
            logger.error(f"❌ Failed to build main bot image: {output}")
            return False
    
    def build_todo_bot_image(self) -> bool:
        """Build the Todo bot image"""
        logger.info("🔨 Building Todo bot image...")
        
        success, output = self.run_command(
            ['docker', 'build', '-t', self.todo_image_name, '.'],
            cwd="/home/pi/Documents/discord/bots/00_production/todo_bot"
        )
        
        if success:
            logger.info("✅ Todo bot image built successfully")
            return True
        else:
            logger.error(f"❌ Failed to build Todo bot image: {output}")
            return False
    
    def stop_container(self, container_name: str) -> bool:
        """Stop a specific container"""
        logger.info(f"🛑 Stopping container: {container_name}")
        
        success, output = self.run_command(['docker', 'stop', container_name])
        
        if success:
            logger.info(f"✅ Container {container_name} stopped")
            return True
        else:
            logger.error(f"❌ Failed to stop container {container_name}: {output}")
            return False
    
    def start_main_bots(self) -> bool:
        """Start main Discord bots using docker-compose"""
        logger.info("🚀 Starting main Discord bots...")
        
        if not self.docker_compose_file.exists():
            logger.error(f"❌ Docker compose file not found: {self.docker_compose_file}")
            return False
        
        success, output = self.run_command(
            ['docker-compose', 'up', '-d'],
            cwd=self.docker_compose_file.parent
        )
        
        if success:
            logger.info("✅ Main Discord bots started")
            return True
        else:
            logger.error(f"❌ Failed to start main bots: {output}")
            return False
    
    def start_todo_bot(self) -> bool:
        """Start Todo bot container"""
        logger.info("🚀 Starting Todo bot...")
        
        # Erstelle Docker Compose für Todo Bot falls nicht vorhanden
        if not self.todo_compose_file.exists():
            self.create_todo_docker_compose()
        
        success, output = self.run_command(
            ['docker-compose', '-f', 'docker-compose.todo.yml', 'up', '-d'],
            cwd=self.todo_compose_file.parent
        )
        
        if success:
            logger.info("✅ Todo bot started")
            return True
        else:
            logger.error(f"❌ Failed to start Todo bot: {output}")
            return False
    
    def create_todo_docker_compose(self):
        """Create Docker Compose file for Todo bot"""
        compose_content = """version: '3.8'

services:
  todo-bot:
    build: .
    container_name: discord-todo-bot
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - TODOIST_API_KEY=${TODOIST_API_KEY}
      - WEEKLY_PLANNING_CHANNEL_ID=${WEEKLY_PLANNING_CHANNEL_ID}
      - PYTHONPATH=/app
      - PYTHONUNBUFFERED=1
    env_file:
      - ../../.env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - todo-network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "python", "health_check.py"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 30s

networks:
  todo-network:
    driver: bridge

volumes:
  logs:
  data:
"""
        
        self.todo_compose_file.write_text(compose_content)
        logger.info(f"✅ Created Todo bot Docker Compose: {self.todo_compose_file}")
    
    def update_container(self, container_name: str, is_todo_bot: bool = False) -> bool:
        """Update a specific container with latest image"""
        logger.info(f"🔄 Updating container: {container_name}")
        
        # Stop container
        if not self.stop_container(container_name):
            return False
        
        # Wait a bit
        time.sleep(2)
        
        # Rebuild image
        if is_todo_bot:
            if not self.build_todo_bot_image():
                return False
        else:
            if not self.build_main_bot_image():
                return False
        
        # Start container
        if is_todo_bot:
            return self.start_todo_bot()
        else:
            return self.start_main_bots()
    
    def check_container_health(self, container_name: str) -> Tuple[bool, str]:
        """Check container health status"""
        success, output = self.run_command(['docker', 'inspect', container_name, '--format', '{{.State.Health.Status}}'])
        
        if success:
            health = output.strip()
            return health == "healthy", health
        else:
            return False, "unhealthy"
    
    def get_container_logs(self, container_name: str, tail: int = 50) -> str:
        """Get recent container logs"""
        success, output = self.run_command(['docker', 'logs', '--tail', str(tail), container_name])
        return output if success else f"Failed to get logs: {output}"
    
    def cleanup_old_images(self) -> bool:
        """Remove dangling images to save space"""
        logger.info("🧹 Cleaning up old Docker images...")
        
        success, output = self.run_command(['docker', 'image', 'prune', '-f'])
        
        if success:
            logger.info("✅ Docker cleanup completed")
            return True
        else:
            logger.error(f"❌ Docker cleanup failed: {output}")
            return False
    
    def full_deployment(self) -> bool:
        """Complete deployment process"""
        logger.info("🚀 Starting full Docker deployment...")
        
        # 1. Get current running containers
        containers = self.get_running_containers()
        logger.info(f"📊 Found {len(containers)} running bot containers")
        
        for name, info in containers.items():
            logger.info(f"  - {name}: {info['status']}")
        
        # 2. Build new images
        logger.info("🔨 Building latest images...")
        
        main_built = self.build_main_bot_image()
        todo_built = self.build_todo_bot_image()
        
        if not (main_built and todo_built):
            logger.error("❌ Failed to build images")
            return False
        
        # 3. Update existing containers
        updated_containers = []
        
        for container_name in containers.keys():
            if 'todo' in container_name.lower():
                success = self.update_container(container_name, is_todo_bot=True)
            else:
                success = self.update_container(container_name, is_todo_bot=False)
            
            if success:
                updated_containers.append(container_name)
            else:
                logger.error(f"❌ Failed to update {container_name}")
        
        # 4. Start Todo bot if not running
        if not any('todo' in name.lower() for name in containers.keys()):
            logger.info("🎯 Todo bot not running, starting it...")
            if self.start_todo_bot():
                updated_containers.append("discord-todo-bot")
        
        # 5. Cleanup
        self.cleanup_old_images()
        
        # 6. Health check
        logger.info("🏥 Performing health checks...")
        time.sleep(30)  # Wait for containers to start
        
        all_healthy = True
        for container in updated_containers:
            healthy, status = self.check_container_health(container)
            logger.info(f"  {container}: {status}")
            
            if not healthy:
                all_healthy = False
                logger.warning(f"❌ {container} is not healthy, checking logs...")
                logs = self.get_container_logs(container)
                logger.warning(f"Recent logs:\n{logs[-500:]}")  # Last 500 chars
        
        if all_healthy:
            logger.info("🎉 Full deployment completed successfully!")
            return True
        else:
            logger.warning("⚠️ Deployment completed with some issues")
            return False
    
    def status_report(self) -> Dict:
        """Generate status report of all containers"""
        containers = self.get_running_containers()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'containers': {},
            'images': {},
            'summary': {
                'total_containers': len(containers),
                'healthy_containers': 0,
                'unhealthy_containers': 0
            }
        }
        
        # Container status
        for name, info in containers.items():
            healthy, health_status = self.check_container_health(name)
            
            report['containers'][name] = {
                'status': info['status'],
                'health': health_status,
                'image': info['image'],
                'created': info['created']
            }
            
            if healthy:
                report['summary']['healthy_containers'] += 1
            else:
                report['summary']['unhealthy_containers'] += 1
        
        # Image versions
        for image in [self.image_name, self.todo_image_name]:
            version = self.get_image_version(image)
            report['images'][image] = version
        
        return report

def main():
    """Main entry point"""
    manager = DockerManager()
    
    print("🐳 Docker Container Manager für Discord Bots")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python docker_manager.py deploy     # Full deployment")
        print("  python docker_manager.py status     # Status report")  
        print("  python docker_manager.py todo       # Start Todo bot only")
        print("  python docker_manager.py update     # Update all containers")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "deploy":
        success = manager.full_deployment()
        sys.exit(0 if success else 1)
    
    elif command == "status":
        report = manager.status_report()
        print(json.dumps(report, indent=2))
    
    elif command == "todo":
        success = manager.start_todo_bot()
        sys.exit(0 if success else 1)
    
    elif command == "update":
        containers = manager.get_running_containers()
        success = True
        
        for name in containers.keys():
            is_todo = 'todo' in name.lower()
            if not manager.update_container(name, is_todo):
                success = False
        
        sys.exit(0 if success else 1)
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
