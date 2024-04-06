import subprocess
import zipfile
import os
from time import sleep
import requests
from tkinter import filedialog
import shutil
import argparse


####################
# SYSTEM ARGUMENTS #
####################

parser = argparse.ArgumentParser(description="A handmade script to automate repeating chores of flashing Android images.\n\nGApps and debloater script is powered by NikGapps debloater script.")

parser.add_argument('-r', '--root', action='store_true', help='Include ROOT')
parser.add_argument('-g', '--google', action='store_true', help='Flash Google Apps (right now only support Android 13).')
parser.add_argument('-d', '--debloatgoogle', action='store_true', help='Debloat Google Apps (Applicable if you coming from Pixel-like ROMs, or Stock ROM with google Bloat). REMINDER: This script WILL NOT remove Google core binaries (GSF, GPlayServices, Phonesky - PlayStore, Velvet - Google Main App.')
parser.add_argument('-a', '--debloataosp', action='store_true', help='Debloat AOSP ROM (Applicable if you annoyyed with AOSP included apps like Recorder, Browser, Aosp Keyboard, Calendar, Calculator, Camera, etc.). REMINDER: Script has been tested on LineageOS and ArrowOS, other ROMs may remove some if not none.')
parser.add_argument('-k', '--apkreplacement', action='store_true', help='Addendum to the above, I like to replace those with my own preferred APK utilities replacement. Feature of inserting your own list of APK is Coming Soon(TM)')
parser.add_argument('-s', '--settings', action='store_true', help='My own preferred way of setting the phone, automatedly (EXPERIMENTAL!).')
parser.add_argument('-v', '--verbose', action='store_true', help='Disables clear() function.')
parser.add_argument('-m', '--magisk_module', action='store_true', help='Push to the device some of useful magisk modules that I collect.')
parser.add_argument('--skip_rom', action='store_true', help='Skip ROM installation function.')
parser.add_argument('--download_replace', action='store_true', help='Re-download all required assets.')
parser.add_argument('--hzk', action='store_true', help='My own setting.')

args = parser.parse_args()


###################
# GLOBAL VARIABLE #
###################

typeZIP = (('ROM ZIP Files', '*.zip'), ('All files', '*.*'))
typeCONFIG = (('Nikgapps CONFIG File', '*.config'), ('All files', '*.*'))
assetFolder = (os.path.expanduser('~') + "\\py-android-flash-tool")


#####################
# GENERAL FUNCTIONS #
#####################


if args.hzk:
  args.root = True
  args.debloatgoogle = True
  args.apkreplacement = True
  args.settings = True
  args.verbose = True

def clear():
  if not args.verbose:
    os.system('cls' if os.name == 'nt' else 'clear')

def download(link: str, filename: str):

    if not os.path.exists(assetFolder):
        os.makedirs(assetFolder)
    
    clear()
    print("Gathering latest", filename + "...")

    if not os.path.exists(assetFolder + '\\' + filename):
      response = requests.get(link)
      with open(assetFolder + '\\' + filename, 'wb') as file:
          file.write(response.content)
      print(filename, 'downloaded successfully.')
    else:
      print(filename, 'already downloaded.')

def countdown(message: str, seconds: int):
    # how many seconds you want to wait
    while seconds >= 1:
        print(message, str(seconds) + '...', end='\r')
        sleep(1)
        seconds = seconds - 1

def phoneState(mode: str):
  if (mode == 'adb'):
    output = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    outputArr = (output.stdout).split()  
    while len(outputArr) <  6:
      outputArr.append(None)
    if (outputArr[5] == 'recovery'):   return 'recovery'
    elif (outputArr[5] == 'sideload'): return 'sideload'
    elif (outputArr[5] == 'device'):   return 'device'
    else:                              return 'intermediary'
  elif (mode == 'fastboot'):
    output = subprocess.run(["fastboot", "devices"], capture_output=True, text=True)
    outputArr = (output.stdout).split()  
    while len(outputArr) <  2:
      outputArr.append(None)
    if (outputArr[1] == 'fastboot'): return 'fastboot'
    else:                            return "intermediary"
  elif (mode == 'lock'):
    output = subprocess.run(["adb", "shell", 'ls', '/sdcard'], capture_output=True, text=True)
    outputArr = (output.stdout).split()
    for i in outputArr:
      if (i == 'Android'): return 'unlocked'


def compileDebloater(mode: str):
  
  if mode == "custom":
    print("Open NikGapps debloater.config file")
    debloatConfig = filedialog.askopenfilename(filetypes=typeCONFIG, title="Open NikGapps debloater.config file")
    print(f"File selected: {debloatConfig}")
  elif mode == "aospBloat":
    download('https://raw.githubusercontent.com/HaiziIzzudin/py-android-flash-tool/main/debloater-aosp/debloater.config','debloater.config')
    debloatConfig = assetFolder + '\\debloater.config'


  debloatDirPath = assetFolder + "\\debloater"
  

  if os.path.exists(debloatDirPath):
    print("Removing and readding debloater folder...")
    shutil.rmtree(debloatDirPath)
    os.makedirs(debloatDirPath)
  else:
    print("Making debloater folder...")
    os.makedirs(debloatDirPath)

  print("Extracting debloater file...")
  with zipfile.ZipFile(assetFolder + "\\debloater.zip", 'r') as zip_ref:
    zip_ref.extractall(debloatDirPath)

  print("Integrating debloater config file...")
  shutil.copy2(debloatConfig, debloatDirPath + "\\afzc\\debloater.config")



  # Open the file in read mode and read all lines into a list
  with open(debloatDirPath + "\\afzc\\nikgapps.config", 'r') as file:
      lines = file.readlines()

  # Modify the line at index 30 (line 31)
  lines[30] = 'use_zip_config=1\n'

  # Open the file in write mode and overwrite it with the modified lines
  with open(debloatDirPath + "\\afzc\\nikgapps.config", 'w') as file:
      file.writelines(lines)



  print("Re-zipping debloater.zip file...")
  with zipfile.ZipFile((debloatDirPath + "_mod.zip"), 'w') as zipf:
    for root, dirs, files in os.walk(debloatDirPath):
      for file in files:
        file_path = os.path.join(root, file)
        zipf.write(file_path, os.path.relpath(file_path, debloatDirPath))


def flash(whatToFlash: str):
  
  if not (phoneState('adb') == 'recovery'):
    subprocess.run(["adb", "reboot", 'recovery'])

  countdown('Giving some time in', 3)
  
  print("In your recovery, enable ADB sideload.")

  while True:
    if not (phoneState('adb') == 'sideload'):
      print('Waiting for sideload mode', end='\r')
    else:
      if (whatToFlash == 'rom'):
        k = ROMfile
      elif (whatToFlash == 'fdroid'):
        k = assetFolder + "\\fdroid-ota.zip"
      elif (whatToFlash == 'google'):
        k = assetFolder + "\\nikgapps-13.zip"
      elif (whatToFlash == 'debloater'):
        k = assetFolder + "\\debloater_mod.zip"
        
      print("Flashing", k, "...")
      subprocess.run(["adb", "sideload", k])
      break


def rooting():

  # Open the zip file
  with zipfile.ZipFile(ROMfile, 'r') as zip_ref:
    # Extract the specified file
    zip_ref.extract("boot.img", assetFolder) # what-file, what-directory

  # push boot.img to android
  subprocess.run(["adb", "push", assetFolder + "\\" + "boot.img", "/sdcard/Download"])
  subprocess.run(["adb", "shell", "am", "start", "io.github.huskydg.magisk/com.topjohnwu.magisk.ui.MainActivity"])

  clear()
  print('On your phone screen rn, the Magisk app has been opened for you.\n(1) Please click "Install" button of the 1st card,\n(2) then select "Select and Patch a File",\n(3) then select the file "boot.img" in the "Downloads" folder.\n(4) Press "Let\'s go ->"\n\nPlease wait for a while for Magisk to finish patching, this program will auto fetch the file for you.')

  loop = True
  while (loop == True):
  
    output = ((subprocess.run(["adb", "shell", 'ls', '/sdcard/Download'], capture_output=True, text=True)).stdout).split()

    for file in output:
      if file.startswith('magisk_patched'):
        output = file
        loop = False
      else:
        print('Waiting for magisk_patched file...', end='\r')
    sleep(.25)

  countdown('Pulling patched image in', 20)
  subprocess.run(["adb", "pull", "/sdcard/Download/" + output , assetFolder])
  subprocess.run(['adb', 'shell', 'rm', '/sdcard/Download/' + output])
  subprocess.run(["adb", "reboot", "bootloader"])

  clear()

  while True:
    if not (phoneState('fastboot') == 'fastboot'):
      print('Waiting for fastboot mode ready...', end='\r')
    else:
      subprocess.run(["fastboot", "flash", "boot", assetFolder + "\\" + output])
      subprocess.run(["fastboot", "reboot"])
      break
  
  clear()
  
  countdown('Waiting for phone to boot in', 7)
  print("After your phone has booted, unlock it.\n\n")

  while True:
    if not (phoneState('lock') == 'unlocked'):
      print('Waiting for user to unlock the device...', end='\r')
    else:
      print('Device has unlocked...')
      break
    sleep(.25)

  subprocess.run(["adb", "shell", "am", "start", "io.github.huskydg.magisk/com.topjohnwu.magisk.ui.MainActivity"])

  clear()
  print("Your devices may prompt to reboot to finish ROOT setup. Press OK. \nWait until your device has booted.\n\n")

  while True:
    if (phoneState('adb') == 'device'):
      print('Waiting for user to reboot...', end='\r')
    else:
      print('\nUser has rebooted...')
      break
    sleep(.25)

  sleep(5)
  while True:
    if (phoneState('adb') == 'intermediary'):
      print('Detecting reboot method...', end='\r')
    elif (phoneState('adb') == 'recovery'):
      countdown('Detected booting to recovery. Booting to system in', 5)
      subprocess.run(['adb', 'reboot'])
      break
    elif (phoneState('adb') == 'device'):
      break
    sleep(.25)
  
  countdown('Waiting for phone to boot in', 7)
  print("After your phone has booted, unlock it.\n\n")

  while True:
    if not (phoneState('lock') == 'unlocked'):
      print('Waiting for user to unlock the device...', end='\r')
    else:
      print('Device has unlocked...')
      break
    sleep(.25)

  clear()
  subprocess.run(["adb", "shell", "am", "start", "io.github.huskydg.magisk/com.topjohnwu.magisk.ui.MainActivity"])
  print("Magisk has been opened for you. Press settings icon at the top of the Magisk main page, \nscroll down to Magisk section, and enable\n(i) Zygisk\n(ii) MagiskHide\n(iii) Enforce SuList\n\nAfter finished toggling, do REBOOT FROM RECOVERY from MAGISK (at the top of the main Magisk page, circular arrow button).\n\n")

  while True:
    if not (phoneState('adb') == 'recovery'):
      print('Waiting for booting to recovery...', end='\r')
    else:
      print('\nPhone has booted to recovery...')
      break
    sleep(.25)




def downloadNinstallAPK(index: int):

  apkName = [
    "huskydg-magisk.apk",
    "revanced.apk", 
    'fdroid.apk',
    'zarchiver.apk',
  ]

  downloadLink = [
    "https://github.com/HuskyDG/magisk-files/releases/download/v26.4-kitsune-2/26.4-kitsune-2.apk",
    "https://github.com/ReVanced/revanced-manager/releases/download/v1.18.0/revanced-manager-v1.18.0.apk",
    'https://f-droid.org/F-Droid.apk',
    'https://github.com/HaiziIzzudin/py-android-flash-tool/raw/main/mirrored-apk/ru.zdevs.zarchiver_1.0.9-10925.apk',
  ]

  download(downloadLink[index], apkName[index])
  subprocess.run(["adb", "install", assetFolder + "\\" + apkName[index]])



def MySettingsforNewROM():
  subprocess.run(["adb", "shell", "cmd", "bluetooth_manager", "disable"])
  subprocess.run(["adb", "shell", "settings", "put", "system", "screen_off_timeout", "1800000"])


##############################
# ACTUAL PROGRAM STARTS HERE #
##############################

clear()

if args.google: download("https://nchc.dl.sourceforge.net/project/nikgapps/Releases/NikGapps-T/10-Feb-2024/NikGapps-core-arm64-13-20240210-signed.zip", "nikgapps-13.zip")
if (args.debloatgoogle or args.debloataosp): download("https://nchc.dl.sourceforge.net/project/nikgapps/Releases/Debloater/10-Feb-2024/Debloater-20240210-signed.zip", "debloater.zip")

if not ((phoneState('adb') == 'device') or (phoneState('adb') == 'recovery')):

  print('ADB debugging is not detected. Open Device info in Settings. Tap many times on Build number/ MIUI version until the toast say "You are now a developer!/ You have enabled development settings!"\n\nThen, go to developer options, and enable USB debugging. \n\nAfter done, run the program again.\n\nExiting...')

else:
    
  if args.skip_rom:
    print('Flags --skip_rom specified. Skipping ROM flashing...')
  else:
    print("Open your ROM ZIP file")
    ROMfile = filedialog.askopenfilename(filetypes=typeZIP, title="Open your ROM ZIP file")
    
    if not ROMfile:
      print('No ROM selected. Exiting...')
      exit()
    else:
      print(f"File selected: {ROMfile}")
      ROMdir = os.path.dirname(ROMfile)
      
      subprocess.run(["adb", "reboot", "recovery"])
      
      while True:
        if not (phoneState('adb') == 'recovery'): print('Waiting for phone to boot to recovery', end='\r')
        else:
          input('Many custom ROM (and stock ROM) have some encryption in place. Therefore, please do "FACTORY RESET" first.\n(DATA WIPE IMMINENT AND UNRECOVERABLE!!! BACK UP YOUR DATA FIRST!!!)\n\nAfter done, press [ENTER] to continue.')
          flash('rom')
          break


  if args.google: flash('google')


  if args.root:
    while True:
      sleep(.25)
      if not (phoneState('adb') == 'recovery'):
        print('Waiting for recovery mode', end='\r')
      else:
        print("Rebooting to system...")
        subprocess.run(["adb", "reboot"])
        break
    
    print("Once your phone has rebooted, do initial setup, test functionality, and set lockscreen.")
    print('Now, open Device info in Settings. Tap many times on Build number until the toast say "You are now a developer!/ You have enabled development settings!"\n\nThen, go to developer options, and enable USB debugging. \n\nPlease authorize the debugging, and wait until further instructions.\n\n')
    
    while True:
      sleep(.25)
      if not (phoneState('adb') == 'device'):
        print('Waiting for authorized ADB mode...', end='\r')
      else:
        print("Installing huskydg magisk...")
        downloadNinstallAPK(0) # dl and install magsik
        rooting()
        break



  if args.debloatgoogle:
    compileDebloater("custom")
    flash('debloater')

  if args.debloataosp:
    compileDebloater("aospBloat")
    flash('debloater')

  countdown('Continuing in', 10)

  if args.apkreplacement:
    
    while True:
      sleep(.25)
      if not (phoneState('adb') == 'recovery'):
        print('Waiting for device ready...', end='\r')
      else:
        subprocess.run(["adb", "reboot"])
        break
    
    while True:
      if not (phoneState('lock') == 'unlocked'):
        print('Waiting for user to unlock the device...', end='\r')
      else:
        print('Device has unlocked...')
        print("Installing replacement APKs...")
        for i in range(1, 4):
          downloadNinstallAPK(i)
        break
      sleep(.25)
  


  if args.magisk_module:
    download('https://github.com/LSPosed/LSPosed/releases/download/v1.9.2/LSPosed-v1.9.2-7024-zygisk-release.zip','lsposed-zygisk.zip')
    download('https://github.com/chiteroman/PlayIntegrityFix/releases/download/v15.8/PlayIntegrityFix_v15.8.zip','PIF.zip')
    subprocess.run(['adb', 'push', assetFolder + '\\' + 'lsposed-zygisk.zip', '/sdcard/Download'])
    subprocess.run(['adb', 'push', assetFolder + '\\' + 'PIF.zip', '/sdcard/Download'])
    
    


  if args.settings:
    MySettingsforNewROM()