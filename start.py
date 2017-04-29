import sys
import subprocess

def run():
    command = (sys.executable, "simc.py")
    while True:
        try:
            code = subprocess.call(command)
        except KeyboardInterrupt:
            code = 0
            break
        else:
            if code == 0:
                break
            else:
                print("Restarting. Exit code: %d" % code)
                continue
    print("Shutdown. Exit code: %d" % code)

run()