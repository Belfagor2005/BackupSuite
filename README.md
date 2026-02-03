
![](https://komarev.com/ghpvc/?username=Belfagor2005) [![Python package](https://github.com/Belfagor2005/BackupSuite/actions/workflows/pylint.yml/badge.svg)](https://github.com/Belfagor2005/BackupSuite/actions/workflows/pylint.yml)

---

<!-- Icona plugin -->
<p align="center">
  <img src="https://github.com/Belfagor2005/BackupSuite/blob/main/usr/lib/enigma2/python/Plugins/Extensions/BackupSuite/plugin.png?raw=true" height="120">
</p>

## 📺 Screenshots

### **Main**
<p align="center">
  <img src="https://github.com/Belfagor2005/BackupSuite/blob/main/screen/00.png?raw=true" height="220">
</p>

### **On USB**
<p align="center">
  <img src="https://github.com/Belfagor2005/BackupSuite/blob/main/screen/11.png?raw=true" height="220">
  <img src="https://github.com/Belfagor2005/BackupSuite/blob/main/screen/22.png?raw=true" height="220">
</p>

### **On Net**
<p align="center">
  <img src="https://github.com/Belfagor2005/BackupSuite/blob/main/screen/33.png?raw=true" height="220">
</p>

### **On MMC**
<p align="center">
  <img src="https://github.com/Belfagor2005/BackupSuite/blob/main/screen/mmc1.png?raw=true" height="220">
  <img src="https://github.com/Belfagor2005/BackupSuite/blob/main/screen/mmc2.png?raw=true" height="220">
</p>

### **Info**
<p align="center">
  <img src="https://github.com/Belfagor2005/BackupSuite/blob/main/screen/info.png?raw=true" height="220">
</p>

### **Help**
<p align="center">
  <img src="https://github.com/Belfagor2005/BackupSuite/blob/main/screen/help.png?raw=true" height="220">
</p>

---

### **Device List**

* Use **UP/DOWN** buttons to navigate through backup options
* Press **OK** to select an option

---

### **Backup Options**

* **HDD Backup**: Full system backup to internal hard drive
* **USB Backup**: Create a bootable USB recovery stick
* **MMC Backup**: Backup to internal storage (eMMC)
* **NET Backup**: Backup to network storage (NAS/SMB)
* **Barry Allen**: Multiboot backup (if installed)
* **Restore**: Flash a previously created backup or image

---

### **Button Functions**

* **GREEN**: Start backup for selected device
* **YELLOW**: Start restore process
* **BLUE**: Show this help screen
* **RED**: Close BackupSuite

---

### **NET Backup Instructions**

1. **Mount your network share first**:

   * Go to **Main Menu > Setup > System > Storage Manager**
   * Select **"Network Storage"** and add your NAS/SMB share
   * Enter server IP, share name, username and password
   * Mount the share and assign a name (e.g., `NET_BACKUP`)

2. **Select "NET Backup"** from the device list

3. **Choose** your mounted network share

4. **Confirm** and start the backup process

---

Restore from Network Procedure:
Select "Restore Backup" from the main menu

* Choose the network share (all mounted shares should be listed)
* Navigate to the folder where you saved your backups (e.g., /media/net/MODEMTIM/backup/)
* Select the ZIP backup file you want to restore
* Follow the guided steps to complete the restore process
---


### **Best Practices**

* Keep regular backups of your system
* Verify you have enough free storage space
* Never interrupt backup/restore processes
* Use quality USB drives for recovery sticks
* For network backups, use wired connection instead of Wi-Fi

---

### **Technical Notes**

* **HDD backups**: Stored in `/media/hdd/backup`
* **USB backups**: Require FAT32-formatted drive with `backupstick` file
* **NET backups**: Require mounted CIFS/NFS share with write permissions
* **Restore**: Works from HDD, USB, NET or MMC storage
* Always choose **"Standard (root and kernel)"** when restoring

---

### **Troubleshooting NET Backup**

* Ensure NAS is powered on and accessible
* Verify username/password are correct
* Check share permissions (read/write)
* Test connection with `ping` command
* Use IP address instead of hostname if DNS fails

---

