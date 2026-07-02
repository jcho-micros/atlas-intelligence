import subprocess
import sys
from app.utils.settings import Settings


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    if command == "research":
        subprocess.run([sys.executable, "main.py"], check=True)
    elif command == "dashboard":
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app/dashboard/dashboard.py", "--server.port", str(Settings.DASHBOARD_PORT)], check=True)
    elif command == "help":
        print("Atlas commands: research | dashboard")
    else:
        raise SystemExit(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
