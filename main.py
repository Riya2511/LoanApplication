from initial_setup import createAuthFile
import subprocess
import os
import sys
import logging
import traceback

# Configure detailed logging
def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging to write to both file and console
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'pyinstaller_build.log'), mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def add_to_defender_exclusion(executable_path):
    """
    Add an executable to Windows Defender exclusion list
    Requires administrative privileges
    """
    try:
        # Ensure full path is used
        full_path = os.path.abspath(executable_path)
        
        # PowerShell command to add exclusion
        cmd = [
            'powershell', 
            '-Command', 
            f'Add-MpPreference -ExclusionPath "{full_path}"'
        ]
        
        # Run with admin privileges
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            shell=True
        )
        
        # Check for success
        if result.returncode == 0:
            print(f"Successfully added {full_path} to Windows Defender exclusions.")
            return True
        else:
            print("Failed to add exclusion. Error:")
            print(result.stderr)
            return False
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def run_pyinstaller():
    try:
        if not createAuthFile():
            logging.error('Failed to create auth file. Ensure you are running on a pendrive.')
            return False
        # command = fr'pyinstaller --onefile --windowed --distpath . --add-data=".auth;.auth" --add-data="{font_file_path};fonts\DejaVuSans.ttf" --name LoanApplication app.py'
        # command = fr'pyinstaller --onefile --windowed --distpath . --add-data="{font_file_path};fonts\DejaVuSans.ttf" --name LoanApplication app.py'
        command = fr'pyinstaller --onefile --windowed --distpath final/ --name LoanApplication app.py'
        result = subprocess.run(command, capture_output=True, text=True)
        
        # Log stdout and stderr
        logging.info("STDOUT: " + result.stdout)
        logging.error("STDERR: " + result.stderr)

        # Test running the generated executable
        exe_path = os.path.join('dist', 'LoanApplication.exe')
        logging.info(f"Executable Path: {exe_path}")
        add_to_defender_exclusion(exe_path)
        
        if os.path.exists(exe_path):
            logging.info("Executable created successfully")
            try:
                exe_result = subprocess.run([exe_path], capture_output=True, text=True, timeout=10)
                logging.info("Executable Run STDOUT: " + exe_result.stdout)
                logging.error("Executable Run STDERR: " + exe_result.stderr)
            except subprocess.TimeoutExpired:
                logging.warning("Executable run timed out")
            except Exception as exe_error:
                logging.error(f"Error running executable: {exe_error}")
                logging.error(traceback.format_exc())
        else:
            logging.error("Executable was not created")

        return True

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        logging.error(traceback.format_exc())
        return False

def main():
    setup_logging()
    try:
        run_pyinstaller()
    except Exception as e:
        logging.error(f"Main process error: {e}")
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()
