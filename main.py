from initial_setup import createAuthFile
import subprocess
import sys

if not createAuthFile():
    print('make sure you run the code in a pendrive')
else:
    command = ['pyinstaller', '--onefile', '--windowed', 'app.py']
    print(f"Running command: {' '.join(command)}")
    subprocess.call(command)    
    print("\nBuild process completed successfully!")