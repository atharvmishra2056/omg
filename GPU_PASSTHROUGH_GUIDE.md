# GPU Passthrough Guide for VirtFlow

## Overview

This guide explains how to use VirtFlow's GPU passthrough feature to:
- **Use iGPU for host display** (your desktop stays on integrated graphics)
- **Pass dGPU to VM** (dedicated GPU disconnects from host and connects to Windows VM)
- **Automatic GPU restoration** (when VM stops, dGPU returns to host)

## Architecture

### GPU Passthrough Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    GPU ACTIVATION PHASE                      │
│  (Click "Activate GPU" button in VirtFlow)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Stop VM (if running)                                     │
│ 2. Bind dGPU to VFIO driver (unbind from nvidia/amdgpu)    │
│ 3. Modify VM XML:                                           │
│    - Remove virtual graphics (Spice/VNC)                    │
│    - Remove audio devices                                    │
│    - Add PCI hostdev for dGPU                               │
│ 4. Redefine VM configuration                                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      VM START PHASE                          │
│  (Click "Start" button or start VM)                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Libvirt starts VM                                        │
│ 2. QEMU passes dGPU hardware to VM                          │
│ 3. Host display switches to iGPU                            │
│ 4. Windows detects dGPU hardware                            │
│ 5. Install NVIDIA/AMD drivers in Windows                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      VM RUNNING                              │
│  - Host uses iGPU for display                               │
│  - VM uses dGPU for graphics                                │
│  - Full GPU acceleration in Windows                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      VM STOP PHASE                           │
│  (Click "Stop" button or shutdown Windows)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. VM shuts down                                            │
│ 2. VirtFlow detects GPU passthrough                         │
│ 3. Unbind dGPU from VFIO                                    │
│ 4. Rebind dGPU to host driver (nvidia/amdgpu)              │
│ 5. Host display can use dGPU again                          │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### 1. Hardware Requirements
- **CPU**: Intel VT-d or AMD-Vi support
- **Motherboard**: IOMMU support
- **GPUs**: 
  - iGPU (integrated graphics) - for host display
  - dGPU (dedicated graphics) - for VM passthrough

### 2. BIOS Settings
Enable the following in BIOS:
- **Intel VT-d** or **AMD-Vi**
- **IOMMU**
- **Virtualization** (Intel VT-x / AMD-V)

### 3. Linux Kernel Parameters
Add to `/etc/default/grub`:
```bash
# For Intel CPU
GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt"

# For AMD CPU
GRUB_CMDLINE_LINUX="amd_iommu=on iommu=pt"
```

Then update GRUB:
```bash
sudo update-grub
sudo reboot
```

## Setup

### Quick Setup (Recommended)
Run the automated setup script:
```bash
sudo ./scripts/setup_gpu_passthrough.sh
```

This script will:
1. Check IOMMU status
2. Load VFIO kernel modules
3. Configure modules to load at boot
4. Install libvirt hooks
5. Configure libvirt for GPU passthrough
6. Restart libvirtd

### Manual Setup
If you prefer manual setup, see `scripts/setup_gpu_passthrough.sh` for individual commands.

## Usage

### Activating GPU Passthrough

1. **Open VirtFlow**
   ```bash
   cd /home/atharv/virtflow
   python3 src/main.py
   ```

2. **Select Your VM**
   - Click on the VM in the list

3. **Click "Activate GPU" Button**
   - VirtFlow will:
     - Check guest agent is ready
     - Verify VirtIO drivers
     - Bind dGPU to VFIO
     - Modify VM XML
   - Progress bar shows each step

4. **Start the VM**
   - Click "Start" button
   - VM will boot with dGPU
   - Host display switches to iGPU

5. **Install GPU Drivers in Windows**
   - Download NVIDIA/AMD drivers
   - Install normally in Windows
   - Reboot Windows VM
   - GPU is now fully functional!

### Stopping the VM

When you stop the VM:
1. Click "Stop" button in VirtFlow
2. VM shuts down gracefully
3. **VirtFlow automatically**:
   - Detects GPU passthrough
   - Waits for VM to fully stop
   - Unbinds dGPU from VFIO
   - Restores dGPU to host driver
4. Host can use dGPU again

### Deactivating GPU Passthrough

To permanently remove GPU passthrough:
```python
# In VirtFlow, or via Python:
from backend.libvirt_manager import LibvirtManager
from backend.vm_gpu_configurator import VMGPUConfigurator
from backend.gpu_detector import GPUDetector

manager = LibvirtManager()
configurator = VMGPUConfigurator(manager)
detector = GPUDetector()

gpu = detector.get_passthrough_gpus()[0]
configurator.disable_gpu_passthrough("YourVMName", gpu)
```

This will:
- Remove GPU hostdev from XML
- Restore virtual graphics (VNC)
- Unbind GPU from VFIO
- Return GPU to host

## Troubleshooting

### VM Won't Start After GPU Activation

**Error**: `Spice audio is not supported without spice graphics`

**Solution**: This is now fixed. VirtFlow removes ALL audio devices before removing graphics.

If you still see this:
```bash
# Check VM XML
virsh dumpxml YourVMName | grep -E '(audio|sound|graphics)'

# Should show NO audio/sound devices and NO graphics devices
```

### GPU Not Binding to VFIO

**Check VFIO modules**:
```bash
lsmod | grep vfio
# Should show: vfio_pci, vfio_iommu_type1, vfio
```

**Check GPU driver**:
```bash
lspci -k | grep -A 3 VGA
# Look for "Kernel driver in use: vfio-pci"
```

**Manually bind GPU** (for testing):
```bash
# Find GPU PCI address
lspci | grep VGA

# Example: 0000:01:00.0
echo "0000:01:00.0" | sudo tee /sys/bus/pci/devices/0000:01:00.0/driver/unbind
echo "vfio-pci" | sudo tee /sys/bus/pci/devices/0000:01:00.0/driver_override
echo "0000:01:00.0" | sudo tee /sys/bus/pci/drivers_probe
```

### GPU Not Returning to Host After VM Stop

**Check logs**:
```bash
# VirtFlow logs
tail -f app_debug.log

# Libvirt hook logs
sudo tail -f /var/log/libvirt/qemu-hook.log
```

**Manually restore GPU**:
```bash
# Unbind from VFIO
echo "0000:01:00.0" | sudo tee /sys/bus/pci/devices/0000:01:00.0/driver/unbind

# Bind to nvidia/amdgpu
echo "0000:01:00.0" | sudo tee /sys/bus/pci/drivers/nvidia/bind
# OR for AMD:
echo "0000:01:00.0" | sudo tee /sys/bus/pci/drivers/amdgpu/bind

# Reload driver
sudo modprobe nvidia  # or amdgpu
```

### Display Issues

**Black screen on host after VM start**:
- This is normal! Host is using iGPU now
- Check if iGPU is enabled in BIOS
- Connect monitor to iGPU port (usually on motherboard)

**No display in VM**:
- GPU drivers not installed in Windows yet
- Use VNC/Spice to access VM initially
- Install GPU drivers, then reboot VM
- Physical monitor connected to dGPU will work after driver install

### IOMMU Groups

**Check IOMMU groups**:
```bash
#!/bin/bash
for d in /sys/kernel/iommu_groups/*/devices/*; do
    n=${d#*/iommu_groups/*}; n=${n%%/*}
    printf 'IOMMU Group %s ' "$n"
    lspci -nns "${d##*/}"
done
```

**GPU must be in its own IOMMU group** or with only its audio device.

## Files Modified by VirtFlow

### VM XML Changes
- **Removed**: `<graphics>`, `<video>`, `<audio>`, `<sound>`, `<channel>`, `<redirdev>`, `<smartcard>`
- **Added**: `<hostdev>` entries for GPU PCI devices

### System Files
- `/etc/libvirt/hooks/qemu` - Libvirt hook script
- `/etc/modules-load.d/vfio.conf` - VFIO modules to load at boot
- `/var/log/libvirt/qemu-hook.log` - Hook execution log

## Performance Tips

1. **CPU Pinning**: Pin VM vCPUs to physical cores for better performance
2. **Huge Pages**: Enable huge pages for VM memory
3. **I/O Threads**: Use dedicated I/O threads for disk operations
4. **MSI/MSI-X**: Ensure GPU uses MSI interrupts (usually automatic)

## Security Notes

- GPU passthrough requires root privileges for VFIO binding
- VirtFlow uses a separate worker process for GPU operations
- Worker process is isolated to prevent crashes affecting main app
- All operations are logged for audit

## Support

For issues or questions:
1. Check `app_debug.log` for VirtFlow errors
2. Check `/var/log/libvirt/qemu-hook.log` for hook errors
3. Check `dmesg` for kernel/IOMMU errors
4. Verify IOMMU is enabled: `dmesg | grep IOMMU`

## Advanced: Manual Hook Installation

If automatic setup fails, manually install hooks:
```bash
sudo mkdir -p /etc/libvirt/hooks
sudo cp scripts/install_libvirt_hooks.sh /tmp/
sudo bash /tmp/install_libvirt_hooks.sh
```

## License

VirtFlow GPU Passthrough - Part of VirtFlow VM Manager
