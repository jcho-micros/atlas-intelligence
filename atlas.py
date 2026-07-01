import argparse
import subprocess
import sys

from main import main as run_research


def dashboard() -> None:
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app/dashboard/dashboard.py"], check=True)


def cli() -> None:
    parser = argparse.ArgumentParser(description="Atlas Intelligence CLI")
    parser.add_argument("command", choices=["research", "dashboard"], help="Command to run")
    args = parser.parse_args()
    if args.command == "research":
        run_research()
    elif args.command == "dashboard":
        dashboard()


if __name__ == "__main__":
    cli()
