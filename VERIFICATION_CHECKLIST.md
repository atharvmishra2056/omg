# GPU Passthrough Verification Checklist

Use this checklist to verify your GPU passthrough setup is working correctly.

## ☑️ Pre-Setup Checklist

### Hardware
- [ ] CPU supports virtualization (Intel VT-x / AMD-V)
- [ ] CPU supports IOMMU (Intel VT-d / AMD-Vi)
- [ ] System has both iGPU and dGPU
- [ ] Monitor can connect to iGPU port (usually on motherboard)

### BIOS Settings
- [ ] Virtualization enabled (VT-x / AMD-V)
- [ ] IOMMU enabled (VT-d / AMD-Vi)
- [ ] iGPU enabled (not disabled)
- [ ] Primary display set to iGPU (or Auto)

### Linux Kernel
- [ ] IOMMU kernel parameter added to GRUB
  ```bash
  cat /proc/cmdline | grep -E '(intel_iommu|amd_iommu)'
  # Should show: intel_iommu=on or amd_iommu=on
  ```
- [ ] System rebooted after GRUB update

---

## ☑️ Setup Verification

### Run Setup Script
```bash
sudo ./scripts/setup_gpu_passthrough.sh
```

- [ ] Script completed without errors
- [ ] IOMMU check passed
- [ ] VFIO modules loaded
- [ ] Libvirt hooks installed
- [ ] Libvirtd restarted successfully

### Verify IOMMU
```bash
dmesg | grep -i iommu
```
- [ ] Shows "IOMMU enabled" or similar
- [ ] No IOMMU-related errors

### Verify VFIO Modules
```bash
lsmod | grep vfio
```
- [ ] `vfio_pci` present
- [ ] `vfio_iommu_type1` present
- [ ] `vfio` present

### Verify Libvirt Hook
```bash
ls -l /etc/libvirt/hooks/qemu
```
- [ ] File exists
- [ ] File is executable (`-rwxr-xr-x`)

### Verify Log Directory
```bash
ls -l /var/log/libvirt/qemu-hook.log
```
- [ ] File exists
- [ ] File is writable

---

## ☑️ Component Testing

### Run Test Suite
```bash
python3 scripts/test_gpu_passthrough.py
```

Expected output:
- [ ] `SYSTEM: ✓ PASS`
- [ ] `GPU_DETECTION: ✓ PASS`
- [ ] `VFIO: ✓ PASS`
- [ ] `LIBVIRT: ✓ PASS`
- [ ] `CONFIGURATOR: ✓ PASS`

### GPU Detection
- [ ] At least one GPU detected
- [ ] At least one GPU marked for passthrough
- [ ] GPU PCI addresses shown
- [ ] IOMMU groups displayed

### Libvirt Connection
- [ ] Connected to libvirt
- [ ] VMs listed (if any exist)
- [ ] No connection errors

---

## ☑️ GPU Activation Test

### Before Activation

Check GPU driver:
```bash
lspci -k | grep -A 3 VGA
```
- [ ] dGPU shows `Kernel driver in use: nvidia` or `amdgpu`

### Activate GPU

In VirtFlow:
1. [ ] Start VirtFlow: `python3 src/main.py`
2. [ ] Select a VM from the list
3. [ ] Click "🎮 Activate GPU" button
4. [ ] Progress bar appears
5. [ ] "Waiting for guest agent..." (or skip if not needed)
6. [ ] "Verifying VirtIO drivers..." (or skip if not needed)
7. [ ] "Stopping VM and binding GPU to VFIO..."
8. [ ] "GPU passthrough enabled successfully!"
9. [ ] No errors in progress dialog

### After Activation

Check GPU driver:
```bash
lspci -k | grep -A 3 VGA
```
- [ ] dGPU shows `Kernel driver in use: vfio-pci`

Check VM XML:
```bash
virsh dumpxml YourVMName | grep hostdev
```
- [ ] Shows `<hostdev type='pci'>` entries

Check no graphics:
```bash
virsh dumpxml YourVMName | grep -E '(graphics|audio|sound)'
```
- [ ] No `<graphics>` elements
- [ ] No `<audio>` elements
- [ ] No `<sound>` elements

Check logs:
```bash
tail -20 app_debug.log
```
- [ ] Shows "GPU successfully bound to VFIO"
- [ ] Shows "GPU passthrough enabled"
- [ ] No errors or exceptions

---

## ☑️ VM Start Test

### Start VM

In VirtFlow:
1. [ ] Click "▶ Start" button
2. [ ] VM starts without errors
3. [ ] No libvirt errors in logs

### Host Display
- [ ] Host display still working
- [ ] Host using iGPU (check with `nvidia-smi` or `radeontop` - should show no processes)

### VM Display
- [ ] Can connect to VM (via physical monitor on dGPU or via VNC initially)
- [ ] Windows boots normally

### Check Logs
```bash
# VirtFlow log
tail -f app_debug.log

# Libvirt hook log
sudo tail -f /var/log/libvirt/qemu-hook.log
```
- [ ] Hook shows "VM starting - GPU should already be bound to VFIO"
- [ ] No errors in either log

### In Windows VM

Open Device Manager:
- [ ] GPU appears under "Display adapters"
- [ ] GPU shows as unknown device (before driver install) or working (after driver install)

Install GPU drivers:
- [ ] Download NVIDIA/AMD drivers
- [ ] Install drivers in Windows
- [ ] Reboot Windows VM
- [ ] GPU shows as working in Device Manager
- [ ] Can run GPU-accelerated applications

---

## ☑️ VM Stop Test

### Stop VM

In VirtFlow:
1. [ ] Click "⏹ Stop" button
2. [ ] VM shuts down gracefully
3. [ ] No errors in UI

### Check Logs
```bash
tail -20 app_debug.log
```
- [ ] Shows "VM has GPU passthrough, will restore GPU to host"
- [ ] Shows "Waiting for VM to stop..."
- [ ] Shows "VM stopped, restoring GPU to host..."
- [ ] Shows "Restoring [GPU name] to host driver..."
- [ ] Shows "GPU successfully restored to host"

### After Stop

Check GPU driver:
```bash
lspci -k | grep -A 3 VGA
```
- [ ] dGPU shows `Kernel driver in use: nvidia` or `amdgpu` (restored!)

Check host can use GPU:
```bash
# For NVIDIA
nvidia-smi

# For AMD
radeontop
```
- [ ] GPU is accessible from host
- [ ] No errors

---

## ☑️ Full Cycle Test

### Complete Workflow
1. [ ] Activate GPU (one-time)
2. [ ] Start VM → dGPU disconnects from host
3. [ ] Use VM with GPU acceleration
4. [ ] Stop VM → dGPU reconnects to host
5. [ ] Start VM again → dGPU disconnects again
6. [ ] Stop VM again → dGPU reconnects again

### Verify Automation
- [ ] No manual commands needed
- [ ] GPU binding/unbinding is automatic
- [ ] Host display stays on iGPU throughout
- [ ] VM gets full GPU access

---

## ☑️ Error Handling Test

### Test Error Cases

1. **Start VM without activation:**
   - [ ] VM starts normally with virtual graphics
   - [ ] No GPU passthrough

2. **Activate GPU while VM running:**
   - [ ] VirtFlow stops VM first
   - [ ] Then activates GPU
   - [ ] No errors

3. **Stop VM forcefully:**
   - [ ] GPU still restored to host
   - [ ] No stuck VFIO binding

---

## ☑️ Performance Test

### In Windows VM with GPU

Run a GPU benchmark:
- [ ] GPU is detected
- [ ] GPU shows correct model
- [ ] Benchmark runs at expected performance
- [ ] No stuttering or artifacts

Run a game or GPU application:
- [ ] Application uses GPU
- [ ] Performance is good
- [ ] No crashes

---

## ☑️ Troubleshooting Verification

### If Something Fails

Check each component:

1. **IOMMU:**
   ```bash
   dmesg | grep -i iommu
   ```
   - [ ] IOMMU is enabled

2. **VFIO modules:**
   ```bash
   lsmod | grep vfio
   ```
   - [ ] All modules loaded

3. **GPU binding:**
   ```bash
   lspci -k | grep -A 3 VGA
   ```
   - [ ] Correct driver for current state

4. **VM XML:**
   ```bash
   virsh dumpxml YourVMName
   ```
   - [ ] Hostdev present when activated
   - [ ] No conflicting devices

5. **Logs:**
   ```bash
   tail -50 app_debug.log
   sudo tail -50 /var/log/libvirt/qemu-hook.log
   ```
   - [ ] No errors or exceptions

---

## ✅ Final Verification

### All Systems Go!

If all items above are checked:
- ✅ **Setup is complete**
- ✅ **GPU passthrough is working**
- ✅ **Automation is functional**
- ✅ **Your vision is achieved!**

### Success Criteria
- [x] iGPU powers host
- [x] dGPU disconnects when VM starts
- [x] dGPU reconnects when VM stops
- [x] Fully automated
- [x] No manual intervention needed

**Congratulations! Your GPU passthrough system is fully operational!** 🎉

---

## 📝 Notes

Record any observations:
- GPU model: ________________
- VM name: ________________
- Host OS: ________________
- Guest OS: ________________
- Any issues encountered: ________________
- Resolution: ________________

---

## 🆘 If Issues Persist

1. Review `FIXES_SUMMARY.md` for detailed fix information
2. Check `GPU_PASSTHROUGH_GUIDE.md` for troubleshooting
3. Run `python3 scripts/test_gpu_passthrough.py` for diagnostics
4. Check all logs for error messages
5. Verify BIOS settings again
6. Ensure kernel parameters are correct

**Everything should work if all checklist items pass!**
