#!/bin/bash
# Setup early VFIO binding so GPU is claimed before nvidia driver loads

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo"
    exit 1
fi

echo "=== Setting Up Early VFIO Binding ==="

# Your NVIDIA GPU IDs
NVIDIA_VGA_ID="10de:2582"
NVIDIA_AUDIO_ID="10de:2291"

echo "GPU IDs to bind:"
echo "  VGA: $NVIDIA_VGA_ID"
echo "  Audio: $NVIDIA_AUDIO_ID"

# 1. Add vfio-pci.ids to kernel parameters
echo "Updating GRUB configuration..."

if grep -q "vfio-pci.ids=" /etc/default/grub; then
    echo "⚠️  vfio-pci.ids already in GRUB config"
    echo "Current line:"
    grep "vfio-pci.ids=" /etc/default/grub
    echo ""
    echo "Replace it? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 0
    fi
    sed -i '/vfio-pci.ids=/d' /etc/default/grub
fi

# Add to GRUB
sed -i "s/GRUB_CMDLINE_LINUX_DEFAULT=\"/GRUB_CMDLINE_LINUX_DEFAULT=\"vfio-pci.ids=$NVIDIA_VGA_ID,$NVIDIA_AUDIO_ID /" /etc/default/grub

# 2. Blacklist nvidia driver
echo "Blacklisting NVIDIA driver..."

cat > /etc/modprobe.d/vfio-nvidia.conf << EOF
# Blacklist NVIDIA so VFIO can claim GPU at boot
blacklist nvidia
blacklist nvidia_drm
blacklist nvidia_modeset
blacklist nvidia_uvm
blacklist nouveau

# Load VFIO modules first
softdep nvidia pre: vfio vfio_pci
EOF

# 3. Update VFIO modules config
cat > /etc/modprobe.d/vfio.conf << EOF
# VFIO configuration for GPU passthrough
options vfio-pci ids=$NVIDIA_VGA_ID,$NVIDIA_AUDIO_ID
options vfio-pci disable_vga=1
EOF

# 4. Update initramfs
echo "Updating initramfs..."
update-initramfs -u

# 5. Update GRUB
echo "Updating GRUB..."
update-grub

echo ""
echo "=== Setup Complete ==="
echo ""
echo "⚠️  You MUST reboot for changes to take effect!"
echo ""
echo "After reboot:"
echo "  - NVIDIA GPU will be bound to VFIO at boot"
echo "  - Desktop will use AMD GPU automatically"
echo "  - NVIDIA will be ready for VM passthrough"
echo ""
echo "To verify after reboot:"
echo "  lspci -k -s 10:00.0"
echo "  Should show: Kernel driver in use: vfio-pci"
echo ""
echo "Reboot now? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    reboot
fi
