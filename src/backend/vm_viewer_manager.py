"""
VM Viewer Manager - Handles external SPICE/VNC viewer integration
Automatically launches virt-viewer when VM starts
"""

import subprocess
import time
import xml.etree.ElementTree as ET
from typing import Optional, Tuple
from pathlib import Path

import libvirt

from utils.logger import logger


class VMViewerManager:
    """Manages VM display viewer (virt-viewer/remote-viewer)"""
    
    def __init__(self):
        self.viewer_processes = {}  # vm_name -> subprocess.Popen
        self._check_viewer_available()
    
    def _check_viewer_available(self) -> bool:
        """Check if virt-viewer or remote-viewer is available"""
        import shutil
        
        self.viewer_binary = None
        
        # Try virt-viewer first (preferred)
        if shutil.which('virt-viewer'):
            self.viewer_binary = 'virt-viewer'
            logger.info("Found virt-viewer")
            return True
        
        # Fallback to remote-viewer
        if shutil.which('remote-viewer'):
            self.viewer_binary = 'remote-viewer'
            logger.info("Found remote-viewer")
            return True
        
        logger.warning("No SPICE/VNC viewer found (virt-viewer or remote-viewer)")
        return False
    
    def get_vm_display_info(self, domain: libvirt.virDomain) -> Optional[Tuple[str, str, int]]:
        """
        Get VM display connection info
        
        Args:
            domain: libvirt domain object
            
        Returns:
            Tuple of (protocol, host, port) or None
        """
        try:
            xml_desc = domain.XMLDesc(0)
            root = ET.fromstring(xml_desc)
            
            # Find graphics element
            graphics = root.find('.//devices/graphics')
            
            if graphics is not None:
                protocol = graphics.get('type')  # 'spice' or 'vnc'
                host = graphics.get('listen', '127.0.0.1')
                port = graphics.get('port', 'auto')
                
                # Handle autoport
                if port == 'auto' or port == '-1':
                    # Get actual port from QEMU monitor
                    port = self._get_actual_port(domain, protocol)
                
                logger.info(f"VM display: {protocol}://{host}:{port}")
                return (protocol, host, int(port) if port else 0)
            
        except Exception as e:
            logger.error(f"Failed to get display info: {e}")
        
        return None
    
    def _get_actual_port(self, domain: libvirt.virDomain, protocol: str) -> Optional[int]:
        """Get actual SPICE/VNC port assigned by libvirt"""
        try:
            # Use virsh domdisplay to get connection URI
            result = subprocess.run(
                ['virsh', 'domdisplay', domain.name()],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                uri = result.stdout.strip()
                # Parse URI: spice://127.0.0.1:5900 or vnc://127.0.0.1:5901
                if '://' in uri and ':' in uri:
                    port_str = uri.split(':')[-1]
                    return int(port_str)
        except Exception as e:
            logger.debug(f"Failed to get actual port: {e}")
        
        return None
    
    def launch_viewer(
        self,
        vm_name: str,
        domain: libvirt.virDomain,
        wait_for_vm: bool = True,
        fullscreen: bool = False
    ) -> bool:
        """
        Launch external SPICE/VNC viewer for VM
        
        Args:
            vm_name: VM name
            domain: libvirt domain object
            wait_for_vm: Wait for VM to start before launching viewer
            fullscreen: Launch viewer in fullscreen mode
            
        Returns:
            bool: Success status
        """
        if not self.viewer_binary:
            logger.error("No viewer binary available")
            return False
        
        # Check if viewer already running for this VM
        if vm_name in self.viewer_processes:
            proc = self.viewer_processes[vm_name]
            if proc.poll() is None:  # Still running
                logger.info(f"Viewer already running for '{vm_name}'")
                return True
        
        logger.info(f"Launching viewer for VM '{vm_name}'...")
        
        try:
            # Build viewer command
            cmd = [
                self.viewer_binary,
                '--connect', 'qemu:///system',
                '--wait' if wait_for_vm else '--reconnect',
                vm_name
            ]
            
            if fullscreen:
                cmd.append('--full-screen')
            
            # Launch viewer as separate process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Detach from parent
            )
            
            self.viewer_processes[vm_name] = process
            logger.info(f"Viewer launched for '{vm_name}' (PID: {process.pid})")
            return True
            
        except FileNotFoundError:
            logger.error(f"Viewer binary not found: {self.viewer_binary}")
            return False
        except Exception as e:
            logger.error(f"Failed to launch viewer: {e}")
            return False
    
    def close_viewer(self, vm_name: str) -> bool:
        """
        Close viewer for a VM
        
        Args:
            vm_name: VM name
            
        Returns:
            bool: Success status
        """
        if vm_name not in self.viewer_processes:
            return True
        
        process = self.viewer_processes[vm_name]
        
        try:
            if process.poll() is None:  # Still running
                logger.info(f"Closing viewer for '{vm_name}'...")
                process.terminate()
                
                # Wait for graceful termination
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    process.kill()
                    process.wait()
            
            del self.viewer_processes[vm_name]
            logger.info(f"Viewer closed for '{vm_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to close viewer: {e}")
            return False
    
    def is_viewer_running(self, vm_name: str) -> bool:
        """Check if viewer is running for a VM"""
        if vm_name not in self.viewer_processes:
            return False
        
        process = self.viewer_processes[vm_name]
        return process.poll() is None
    
    def close_all_viewers(self):
        """Close all running viewers"""
        vm_names = list(self.viewer_processes.keys())
        for vm_name in vm_names:
            self.close_viewer(vm_name)
