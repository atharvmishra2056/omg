# VirtFlow GPU Passthrough - Quick Start

## 🚀 Get Started in 3 Steps

### Step 1: Setup (One-time, ~2 minutes)
```bash
cd /home/atharv/virtflow
sudo ./scripts/setup_gpu_passthrough.sh
```

This will:
- ✓ Check IOMMU is enabled
- ✓ Load VFIO kernel modules
- ✓ Install libvirt hooks
- ✓ Configure system for GPU passthrough

### Step 2: Test (Optional but recommended)
```bash
python3 scripts/test_gpu_passthrough.py
```

This verifies:
- ✓ GPU detection works
- ✓ VFIO manager ready
- ✓ Libvirt connection active
- ✓ All components functional

### Step 3: Use GPU Passthrough
```bash
# Start VirtFlow
python3 src/main.py
```

**In the UI:**
1. Select your VM
2. Click **"🎮 Activate GPU"** button
3. Wait for activation to complete
4. Click **"▶ Start"** to boot VM
5. Install GPU drivers in Windows
6. Enjoy full GPU acceleration!

**When done:**
- Click **"⏹ Stop"** button
- GPU automatically returns to host
- No manual steps needed!

---

## ⚡ What Happens

### When You Activate GPU:
```
1. VM stops (if running)
2. dGPU unbinds from nvidia/amdgpu driver
3. dGPU binds to vfio-pci driver
4. VM XML updated with GPU hostdev
5. Ready to start!
```

### When You Start VM:
```
1. VM boots with dGPU hardware
2. Host display switches to iGPU
3. Windows sees dGPU
4. Install drivers → Full acceleration!
```

### When You Stop VM:
```
1. VM shuts down
2. VirtFlow detects GPU passthrough
3. dGPU unbinds from vfio-pci
4. dGPU rebinds to nvidia/amdgpu
5. Host can use dGPU again!
```

---

## 🔧 Prerequisites

**Before running setup, ensure:**

1. **BIOS Settings:**
   - ✓ Intel VT-d or AMD-Vi enabled
   - ✓ IOMMU enabled
   - ✓ Virtualization enabled

2. **Kernel Parameters:**
   Add to `/etc/default/grub`:
   ```bash
   # Intel CPU
   GRUB_CMDLINE_LINUX="intel_iommu=on iommu=pt"
   
   # AMD CPU
   GRUB_CMDLINE_LINUX="amd_iommu=on iommu=pt"
   ```
   
   Then:
   ```bash
   sudo update-grub
   sudo reboot
   ```

3. **Hardware:**
   - ✓ iGPU (integrated graphics) for host
   - ✓ dGPU (dedicated graphics) for VM

---

## 📋 Quick Verification

After setup, verify everything:

```bash
# Check IOMMU
dmesg | grep -i iommu
# Should show: "IOMMU enabled"

# Check VFIO modules
lsmod | grep vfio
# Should show: vfio_pci, vfio_iommu_type1, vfio

# Check hook installed
ls -l /etc/libvirt/hooks/qemu
# Should exist and be executable
```

---

## 🐛 Common Issues

### "IOMMU not enabled"
**Fix:**
1. Enable in BIOS
2. Add kernel parameter to GRUB
3. Update GRUB and reboot

### "No GPUs available for passthrough"
**Fix:**
1. Check GPU is not primary display
2. Verify IOMMU groups: `scripts/test_gpu_passthrough.py`
3. Ensure iGPU is enabled in BIOS

### "Spice audio error"
**Status:** ✅ FIXED in latest code
- Audio devices now removed before graphics
- Should not occur anymore

---

## 📚 Full Documentation

- **Complete Guide:** `GPU_PASSTHROUGH_GUIDE.md`
- **Full Solution:** `COMPLETE_GPU_PASSTHROUGH_SOLUTION.md`
- **Test Script:** `scripts/test_gpu_passthrough.py`
- **Setup Script:** `scripts/setup_gpu_passthrough.sh`

---

## 🎯 Your Goal: ACHIEVED

✅ **iGPU powers host**
✅ **dGPU disconnects when VM starts**
✅ **dGPU reconnects when VM stops**
✅ **Fully automated**
✅ **No manual intervention needed**

**Ready to go? Run the setup script above!** 🚀
