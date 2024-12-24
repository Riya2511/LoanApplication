import os
import wmi
import win32api
import win32file
import hashlib
import ctypes


def hashSerialNumber(serialNumber: str):
    dataEncoded = str(serialNumber).encode("utf-8")
    sha256Hash = hashlib.sha256()
    sha256Hash.update(dataEncoded)
    return sha256Hash.hexdigest()

def getPendriveSerialNumber():
    try:
        current_drive = os.path.splitdrive(os.path.abspath(__file__))[0] + "\\"
        drive_type = win32file.GetDriveType(current_drive)
        if drive_type != 2:
            print("Current drive is not a removable drive")
            return None
        c = wmi.WMI()
        for disk in c.Win32_LogicalDisk(DeviceID=current_drive.replace("\\", "")):
            if hasattr(disk, "VolumeSerialNumber"):
                return disk.VolumeSerialNumber

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def createAuthFile(serialNumber=None):
    try:
        if serialNumber is None:
            serialNumber = getPendriveSerialNumber()
        
        if not serialNumber: 
            print('Please run this file in a pendrive')
            return None
        hashedSerial = hashSerialNumber(serialNumber)
        
        if hashedSerial is None:
            print("Could not create auth file: No serial number found")
            return False
        # current_drive = os.path.splitdrive(os.path.abspath(__file__))[0] + "\\"
        auth_file_path = os.path.join(os.getcwd() + '\\', ".auth")
        with open(auth_file_path, 'w') as f:
            f.write(hashedSerial)
        ctypes.windll.kernel32.SetFileAttributesW(auth_file_path, 0x2)
        
        print("Authentication file created successfully")
        return True
    except PermissionError:
        return True
    except Exception as e:
        print(f"Error creating auth file: {e}")
        return False

if __name__ == "__main__":
    serial_number = getPendriveSerialNumber()
    if serial_number:
        print("Pendrive Serial Number:", serial_number)
        print("Hashed Serial Number:", hashSerialNumber(serial_number))
        createAuthFile(serial_number)