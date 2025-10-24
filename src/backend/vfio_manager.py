"""
VFIO Manager - Crash-safe GPU binding using isolated worker subprocess
"""

import subprocess
import time
from pathlib import Path
from typing import Optional

from backend.gpu_detector import GPU
from utils.logger import logger


class VFIOManager:
    """Manages VFIO driver binding using isolated worker process"""
    
    def __init__(self):
        self.worker_path = Path(__file__).parent / "gpu_worker.py"
        if not self.worker_path.exists():
            logger.error(f"GPU worker not found at {self.worker_path}")
        self._check_vfio_available()
    
    def _check_vfio_available(self) -> bool:
        """Check if VFIO modules are loaded"""
        try:
            result = subprocess.run(['lsmod'], capture_output=True, text=True, timeout=5)
            has_vfio = 'vfio_pci' in result.stdout
            
            if not has_vfio:
                logger.info("Loading VFIO modules...")
                modules = ['vfio', 'vfio_iommu_type1', 'vfio_pci']
                for module in modules:
                    subprocess.run(['sudo', 'modprobe', module], timeout=5)
                logger.info("VFIO modules loaded")
            
            return True
        except Exception as e:
            logger.error(f"Failed to check VFIO: {e}")
            return False
    
    def bind_gpu_to_vfio(self, gpu: GPU) -> bool:
        """
        Bind GPU to VFIO using isolated worker subprocess
        CRASH-SAFE: If worker crashes, main app continues
        """
        logger.info(f"Binding {gpu.full_name} to VFIO via worker...")
        
        try:
            # Build device list arguments
            device_args = []
            for device in gpu.all_devices:
                arg = f"{device.address}|{device.vendor_id}|{device.device_id}"
                device_args.append(arg)
            
            # Launch worker subprocess
            cmd = ['python3', str(self.worker_path), 'bind'] + device_args
            
            logger.info(f"Launching worker: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=60)
                
                # Log worker output
                for line in stdout.strip().split('\n'):
                    if line:
                        logger.info(f"Worker: {line}")
                
                if process.returncode == 0:
                    logger.info(f"Successfully bound {gpu.full_name} to VFIO")
                    return True
                else:
                    logger.error(f"Worker failed with code {process.returncode}")
                    if stderr:
                        logger.error(f"Worker error: {stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.error("Worker timed out after 60 seconds")
                process.kill()
                return False
                
        except Exception as e:
            logger.exception(f"Failed to launch worker: {e}")
            return False
    
    def unbind_gpu_from_vfio(self, gpu: GPU) -> bool:
        """
        Unbind GPU from VFIO using isolated worker subprocess
        """
        logger.info(f"Unbinding {gpu.full_name} from VFIO via worker...")
        
        try:
            # Determine host driver
            if gpu.vendor == "NVIDIA":
                host_driver = "nvidia"
            elif gpu.vendor == "AMD":
                host_driver = "amdgpu"
            else:
                host_driver = "nouveau"
            
            # Build arguments
            device_addrs = [device.address for device in gpu.all_devices]
            cmd = ['python3', str(self.worker_path), 'unbind', host_driver] + device_addrs
            
            logger.info(f"Launching worker: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for completion
            try:
                stdout, stderr = process.communicate(timeout=60)
                
                for line in stdout.strip().split('\n'):
                    if line:
                        logger.info(f"Worker: {line}")
                
                if process.returncode == 0:
                    logger.info(f"Successfully restored {gpu.full_name} to host")
                    return True
                else:
                    logger.error(f"Worker failed with code {process.returncode}")
                    if stderr:
                        logger.error(f"Worker error: {stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.error("Worker timed out after 60 seconds")
                process.kill()
                return False
                
        except Exception as e:
            logger.exception(f"Failed to launch worker: {e}")
            return False
    
    def is_bound_to_vfio(self, pci_address: str) -> bool:
        """Check if device is bound to vfio-pci"""
        try:
            driver_path = Path(f"/sys/bus/pci/devices/{pci_address}/driver")
            if driver_path.exists():
                driver_name = driver_path.resolve().name
                return driver_name == "vfio-pci"
        except Exception:
            pass
        return False
