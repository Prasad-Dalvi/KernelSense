import subprocess
import time

from database.database import save_command


def execute_command(command, risk="safe"):
    """
    Execute a Linux command without using a shell
    and save the execution result to SQLite.
    """

    start_time = time.perf_counter()

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=False
        )

        execution_time_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2
        )

        success = result.returncode == 0
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        save_command(
            command=" ".join(command),
            risk=risk,
            status="success" if success else "failed",
            output=stdout if success else stderr
        )

        return {
            "command": command,
            "success": success,
            "return_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "execution_time_ms": execution_time_ms
        }

    except subprocess.TimeoutExpired:

        execution_time_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2
        )

        save_command(
            command=" ".join(command),
            risk=risk,
            status="timeout",
            output="Command timed out"
        )

        return {
            "command": command,
            "success": False,
            "return_code": None,
            "stdout": "",
            "stderr": "Command timed out",
            "execution_time_ms": execution_time_ms
        }

    except FileNotFoundError:

        execution_time_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2
        )

        save_command(
            command=" ".join(command),
            risk=risk,
            status="failed",
            output="Command not found"
        )

        return {
            "command": command,
            "success": False,
            "return_code": None,
            "stdout": "",
            "stderr": "Command not found",
            "execution_time_ms": execution_time_ms
        }

    except OSError as error:

        execution_time_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2
        )

        save_command(
            command=" ".join(command),
            risk=risk,
            status="failed",
            output=str(error)
        )

        return {
            "command": command,
            "success": False,
            "return_code": None,
            "stdout": "",
            "stderr": str(error),
            "execution_time_ms": execution_time_ms
        }
