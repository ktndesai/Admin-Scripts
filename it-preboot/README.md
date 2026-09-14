# IT Preboot Environment — Starter Project

A custom Debian 13 (Trixie) Live ISO starter with:

- Automatic hardware summary: manufacturer/model/serial, CPU, RAM, disks and IPs
- NetworkManager networking
- L2TP/IPsec VPN support
- Azure Blob image repository using AzCopy
- Clonezilla + Partclone restore tools
- Simple Python/Tk GUI that boots automatically
- Guarded destructive restore workflow

> **Important:** This is a starter/lab build. Test it against disposable VMs before using it on production PCs. Clonezilla restore operations destroy data on the selected target disk.

## 1. Build machine

Use a Debian 13 or Ubuntu Linux VM with internet access. Debian 13 is recommended.

```bash
sudo apt update
sudo apt install -y live-build
unzip it-preboot.zip
cd it-preboot
sudo ./build.sh
```

The output should be:

```text
build/IT-Preboot-v1.iso
```

## 2. Configuration

Edit:

```text
config/includes.chroot/etc/it-preboot/preboot.conf
```

Set at least:

```bash
COMPANY_NAME="Your Company"
VPN_SERVER="vpn.example.com"
AZURE_CONTAINER_URL="https://STORAGE.blob.core.windows.net/CONTAINER"
```

For an initial lab test, copy:

```text
config/includes.chroot/etc/it-preboot/secrets.env.example
```

to:

```text
config/includes.chroot/etc/it-preboot/secrets.env
```

and fill:

```bash
AZURE_SAS_TOKEN="sv=..."
VPN_USERNAME="..."
VPN_PASSWORD="..."
VPN_IPSEC_PSK="..."
```

**Do not distribute a production ISO containing long-lived secrets.** A later revision should inject site/user secrets at boot, use short-lived SAS credentials, or use another appropriate identity flow.

## 3. Azure container layout

The starter expects a `manifest.json` in the root of the Blob container.

Example:

```text
machine-images/
├── manifest.json
└── win11-qa-24h2/
    ├── Info-dmi.txt
    ├── Info-img-id.txt
    ├── parts
    ├── sda-pt.parted
    ├── sda1.ntfs-ptcl-img.zst.aa
    ├── ... normal Clonezilla image files ...
    └── SHA256SUMS
```

See `examples/manifest.json`.

The `blob_prefix` value is the Azure folder/prefix to download. `clonezilla_image` must match the local Clonezilla image directory name after download.

## 4. SHA256 verification

Inside each image folder, generate a checksum file before uploading it to Azure:

```bash
cd win11-qa-24h2
find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
```

The GUI verifies this file when it is present and referenced by the manifest.

## 5. Azure access

Give the preboot system only the access it needs. For SAS-based lab use, prefer container-level read/list access and a short lifetime. The GUI downloads the selected image into a local cache before Clonezilla starts.

Default cache:

```text
/var/tmp/it-preboot-images
```

That is normally RAM/overlay-backed in a live session and may be unsuitable for large images. For realistic images, mount a sufficiently large USB SSD or temporary storage and change `IMAGE_CACHE_ROOT` accordingly.

## 6. L2TP/IPsec

The Connect VPN button creates a NetworkManager L2TP connection using:

- VPN server from `preboot.conf`
- username/password from `secrets.env`
- IPsec PSK from `secrets.env`

The exact NetworkManager properties can vary with the VPN server. Treat the supplied configuration as the baseline and adjust it to match your server's authentication/cipher requirements.

## 7. Restore safety

The GUI asks for confirmation before opening the restore workflow. The restore helper then requires the technician to type the target disk name (for example `nvme0n1`) before Clonezilla is called.

The current Clonezilla command is intentionally conservative and leaves the machine running after restoration so the technician can inspect the output.

## 8. Test in a VM first

Recommended sequence:

1. Build ISO.
2. Boot it in Hyper-V, VMware, VirtualBox or Proxmox.
3. Attach a disposable virtual disk.
4. Validate hardware display and networking.
5. Validate L2TP.
6. Validate Azure manifest listing and image download.
7. Restore a Clonezilla image to the disposable disk.
8. Only then test on physical hardware.

## 9. USB

The ISO is an `iso-hybrid` image and can be written with tools such as Rufus, balenaEtcher, `dd`, or placed on a Ventoy USB for lab use.

## Known starter limitations

- Secure Boot is not explicitly configured/tested yet.
- AzCopy is downloaded at build time from Microsoft's current v10 Linux download rather than pinned to a specific version.
- Secrets injection is lab-oriented in v1.
- Azure image cache capacity must be planned for large images.
- The GUI is intentionally simple and should be hardened before broad deployment.
- Clonezilla flags and disk-layout policy should be validated against your actual image format and hardware fleet.
