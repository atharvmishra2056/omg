# 🚀 START HERE - VirtFlow GPU Passthrough - Quick Start

## ⚡ LATEST UPDATE: All Critical Issues Fixed!

✅ **No more Python crashes**  
✅ **No need to start VM before activation**  
✅ **App restarts work perfectly**  
✅ **Test script doesn't hang**  

See `LATEST_FIXES.md` for details!

---

## 🚀 Get Started in 3 Steps

All issues have been fixed. Your vision is implemented. Let's get you started!

---

## ⚡ Quick Start (Choose Your Path)

### 🏃 Path 1: Just Want It Working (Fastest)
```bash
# 1. Run setup
sudo ./scripts/setup_gpu_passthrough.sh

# 2. Start VirtFlow
python3 src/main.py

# 3. In UI: Select VM → Click "Activate GPU" → Click "Start"
```
**Time: 5 minutes**

### 🧪 Path 2: Test First, Then Use
```bash
# 1. Run setup
sudo ./scripts/setup_gpu_passthrough.sh

# 2. Run tests
python3 scripts/test_gpu_passthrough.py

# 3. Start VirtFlow
python3 src/main.py

# 4. In UI: Select VM → Click "Activate GPU" → Click "Start"
```
**Time: 10 minutes**

### 📖 Path 3: Read Everything First
1. Read `QUICKSTART.md` (3 min)
2. Read `GPU_PASSTHROUGH_GUIDE.md` (10 min)
3. Run setup and tests
4. Use VirtFlow
**Time: 20 minutes**

---

## 📚 Documentation Guide

### For Getting Started
- **START_HERE.md** ← You are here!
- **QUICKSTART.md** ← 3-step quick start guide
- **VERIFICATION_CHECKLIST.md** ← Test everything works

### For Understanding
- **README_GPU_PASSTHROUGH.md** ← Overview of the solution
- **GPU_PASSTHROUGH_GUIDE.md** ← Complete user guide
- **COMPLETE_GPU_PASSTHROUGH_SOLUTION.md** ← Technical details

### For Troubleshooting
- **FIXES_SUMMARY.md** ← What was broken and how it was fixed
- **VERIFICATION_CHECKLIST.md** ← Systematic testing
- **GPU_PASSTHROUGH_GUIDE.md** ← Troubleshooting section

---

## 🎯 What You're Getting

### Your Vision (Now Reality!)
✅ **iGPU powers host** - Your desktop stays on integrated graphics  
✅ **dGPU disconnects when VM starts** - Dedicated GPU goes to Windows  
✅ **dGPU reconnects when VM stops** - GPU returns to host automatically  
✅ **Fully automated** - No manual commands needed  

### What Was Fixed
1. ✅ AttributeError with LibvirtManager
2. ✅ Spice audio configuration error
3. ✅ Missing VFIO GPU binding
4. ✅ No GPU restoration on shutdown
5. ✅ Incomplete automation

### What You Get
- 🎮 Full GPU passthrough to Windows VM
- 🖥️ Host continues using iGPU
- 🔄 Automatic GPU switching
- 📊 Complete logging and monitoring
- 🛠️ One-command setup
- 📖 Comprehensive documentation

---

## 🔧 Prerequisites (Check These First)

### Hardware
- [ ] CPU with VT-d/AMD-Vi support
- [ ] Motherboard with IOMMU
- [ ] Both iGPU and dGPU present
- [ ] Monitor can connect to iGPU port

### BIOS
- [ ] Virtualization enabled
- [ ] IOMMU/VT-d enabled
- [ ] iGPU enabled

### Linux
- [ ] IOMMU kernel parameter added
  ```bash
  # Check with:
  cat /proc/cmdline | grep -E '(intel_iommu|amd_iommu)'
  ```
- [ ] System rebooted after GRUB update

**If any are missing, see `GPU_PASSTHROUGH_GUIDE.md` Prerequisites section**

---

## 🚀 Installation

### One-Command Setup
```bash
sudo ./scripts/setup_gpu_passthrough.sh
```

This will:
1. ✓ Check IOMMU is enabled
2. ✓ Load VFIO kernel modules
3. ✓ Configure modules for boot
4. ✓ Install libvirt hooks
5. ✓ Restart libvirtd

**Takes ~2 minutes**

---

## ✅ Verification

### Quick Test
```bash
python3 scripts/test_gpu_passthrough.py
```

**Expected output:**
```
SYSTEM:         ✓ PASS
GPU_DETECTION:  ✓ PASS
VFIO:           ✓ PASS
LIBVIRT:        ✓ PASS
CONFIGURATOR:   ✓ PASS

✓ All tests passed! GPU passthrough is ready to use.
```

**If any fail, see `VERIFICATION_CHECKLIST.md`**

---

## 🎮 Usage

### First Time (Per VM)
```bash
# 1. Start VirtFlow
python3 src/main.py

# 2. In the UI:
#    - Select your VM
#    - Click "🎮 Activate GPU" button
#    - Wait for progress bar to complete
#    - GPU is now activated!

# 3. Start the VM:
#    - Click "▶ Start" button
#    - VM boots with dGPU
#    - Host uses iGPU

# 4. In Windows:
#    - Install NVIDIA/AMD drivers
#    - Reboot Windows
#    - Enjoy full GPU acceleration!
```

### Daily Use
```bash
# Just start and stop the VM normally!
# - Start VM → dGPU disconnects from host
# - Stop VM → dGPU reconnects to host
# All automatic!
```

---

## 🔍 How to Verify It's Working

### Before VM Start
```bash
lspci -k | grep -A 3 VGA
# dGPU should show: Kernel driver in use: vfio-pci
```

### During VM Run
```bash
# Host should be using iGPU
# VM should have full dGPU access
# Check in Windows Device Manager
```

### After VM Stop
```bash
lspci -k | grep -A 3 VGA
# dGPU should show: Kernel driver in use: nvidia (or amdgpu)
```

---

## 📊 File Structure

```
/home/atharv/virtflow/
│
├── START_HERE.md                    ← You are here!
├── QUICKSTART.md                    ← 3-step guide
├── README_GPU_PASSTHROUGH.md        ← Overview
├── GPU_PASSTHROUGH_GUIDE.md         ← Complete guide
├── COMPLETE_GPU_PASSTHROUGH_SOLUTION.md
├── FIXES_SUMMARY.md                 ← What was fixed
├── VERIFICATION_CHECKLIST.md        ← Test checklist
│
├── scripts/
│   ├── setup_gpu_passthrough.sh     ← Run this first!
│   ├── install_libvirt_hooks.sh
│   └── test_gpu_passthrough.py      ← Run this second!
│
└── src/
    ├── main.py                       ← Start VirtFlow
    ├── backend/
    │   ├── vm_gpu_configurator.py   ← GPU passthrough logic
    │   ├── vm_controller.py         ← Auto-restore
    │   ├── vfio_manager.py          ← VFIO binding
    │   └── gpu_worker.py            ← GPU operations
    └── ui/
        └── gpu_activation_dialog.py ← Activation UI
```

---

## 🐛 If Something Goes Wrong

### Step 1: Check Logs
```bash
# VirtFlow log
tail -f app_debug.log

# Libvirt hook log
sudo tail -f /var/log/libvirt/qemu-hook.log
```

### Step 2: Run Tests
```bash
python3 scripts/test_gpu_passthrough.py
```

### Step 3: Check Checklist
See `VERIFICATION_CHECKLIST.md` for systematic debugging

### Step 4: Review Guide
See `GPU_PASSTHROUGH_GUIDE.md` Troubleshooting section

---

## 💡 Common Questions

**Q: Do I need to activate GPU every time?**  
A: No! Only once per VM. After that, just start/stop normally.

**Q: Will my host display stop working?**  
A: No! Host switches to iGPU automatically.

**Q: Can I use dGPU on host after VM stops?**  
A: Yes! It automatically reconnects.

**Q: What if I want to remove GPU passthrough?**  
A: Use `configurator.disable_gpu_passthrough()` or just delete the VM.

**Q: Is this safe?**  
A: Yes! GPU operations run in isolated worker process.

---

## 🎯 Success Criteria

You'll know it's working when:
- ✅ "Activate GPU" completes without errors
- ✅ VM starts with GPU hardware
- ✅ Windows Device Manager shows your GPU
- ✅ GPU drivers install successfully
- ✅ GPU-accelerated apps work in Windows
- ✅ VM stops and GPU returns to host
- ✅ Host can use GPU after VM stops

---

## 🚀 Ready to Go?

### Recommended Path:
```bash
# 1. Setup (2 min)
sudo ./scripts/setup_gpu_passthrough.sh

# 2. Test (1 min)
python3 scripts/test_gpu_passthrough.py

# 3. Use (5 min)
python3 src/main.py
# → Select VM
# → Click "Activate GPU"
# → Click "Start"
# → Install drivers in Windows
# → Enjoy!
```

---

## 📞 Need Help?

1. **Quick issues:** Check `VERIFICATION_CHECKLIST.md`
2. **Understanding:** Read `GPU_PASSTHROUGH_GUIDE.md`
3. **Technical details:** See `COMPLETE_GPU_PASSTHROUGH_SOLUTION.md`
4. **What was fixed:** Read `FIXES_SUMMARY.md`

---

## 🎉 You're All Set!

Everything is ready. All issues are fixed. Your vision is implemented.

**Just run the setup script and start using it!**

```bash
sudo ./scripts/setup_gpu_passthrough.sh
python3 src/main.py
```

**Welcome to seamless GPU passthrough!** 🚀

---

*Built with ❤️ to make GPU passthrough simple and automatic*
