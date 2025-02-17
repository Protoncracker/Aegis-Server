#!/usr/bin/env python3

__version__ = "1.0.0"
__author__ = "ProtonCracker"
__license__ = "Private - All Rights Reserved"
__copyright__ = "Copyright © 2025 ProtonCracker™"
__maintainer__ = "ProtonCracker"
__email__ = "tryme.freefall963@passinbox.com"
__status__ = "Production"
__program_name__ = "Aegis Sandbox"

import socket
import subprocess
import os
import time
import json
import secrets
import signal
from datetime import datetime, timedelta

try:
    from colorama import Fore, Style, init  # type: ignore
    init()
except ImportError:
    class Fore:
        RED = ""
        GREEN = ""
        YELLOW = ""
        CYAN = ""
        WHITE = ""
    class Style:
        RESET_ALL = ""
    def init():
        pass
    init()

import threading
from queue import Queue
import io
import contextlib

# Logging function should be defined before using it.
def log_message(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    with open("server.log", "a") as log_file:
        log_file.write(log_entry + "\n")
    if level == "INFO":
        color = Fore.CYAN
    elif level == "WARNING":
        color = Fore.YELLOW
    elif level == "ERROR":
        color = Fore.RED
    elif level == "DEBUG":
        color = Fore.GREEN
    else:
        color = Fore.WHITE
    print(color + log_entry + Style.RESET_ALL)

# ASCII Art Logo and Information Header
def print_banner():
    banner = r"""
           .-~~~~~~~~~~~~-.
         .'                '.
        /                    \
       |                      |
       |      ##########      |
       |     ############     |
        \    ############    /
         '.   ##########   .'
           '-.__________.-'
    """
    info = f"""
    Program Name : {__program_name__}
    Version      : {__version__}
    Author       : {__author__}
    License      : {__license__}
    Copyright    : {__copyright__}
    Maintainer   : {__maintainer__}
    Email        : {__email__}
    Status       : {__status__}
    """
    print(Fore.CYAN + banner + Style.RESET_ALL)
    print(info)

# Load allowed identifier and ngrok command from AEGIS.env file.
ALLOWED_ID = None
NGROK_COMMAND = None
try:
    with open("AEGIS.env", "r") as env_file:
        for line in env_file:
            line = line.strip()
            if line.startswith("ID="):
                ALLOWED_ID = line.split("=", 1)[1].strip()
            elif line.startswith("NGROK_COMMAND="):
                NGROK_COMMAND = line.split("=", 1)[1].strip()
    if ALLOWED_ID is None or len(ALLOWED_ID) != 14:
        raise ValueError("Loaded identifier is not a 14-character string.")
    if NGROK_COMMAND is None:
        NGROK_COMMAND = "ngrok http 8080"
    log_message("Allowed identifier loaded from AEGIS.env: " + ALLOWED_ID, "INFO")
    log_message("Ngrok command loaded from AEGIS.env: " + NGROK_COMMAND, "INFO")
except Exception as e:
    print(f"Error loading configuration from AEGIS.env: {e}")
    exit(1)

# Configuration
HOST = '127.0.0.1'
PORT = 8080
LOG_FILE = 'server.log'
AUTHORIZED_TOKENS = set()
SERVER_START_TIME = datetime.now()
SESSION_TIMEOUT = timedelta(minutes=1)
MAX_THREADS = 10
VALID_IDENTIFIERS = ("Jarvis",)

# Global shutdown event to control graceful shutdown
SHUTDOWN_EVENT = threading.Event()

# Thread pool and task queue
thread_pool = []
task_queue = Queue()

# Define dangerous command keywords
DANGEROUS_KEYWORDS = ["rm -rf", "del /f", "mkfs", "dd if=", "reboot", "poweroff", "halt"]

# Global admin approval function (can be overridden for tests)
ADMIN_APPROVAL_FUNC = input

def is_dangerous_command(command):
    """Check if the command contains dangerous keywords."""
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in command:
            return True
    return False

def generate_token():
    """Generate a random token to uniquely identify a session."""
    token = secrets.token_hex(16)
    AUTHORIZED_TOKENS.add(token)
    log_message(f"Generated new token: '{token}'", "DEBUG")
    return token

def start_ngrok():
    """Start ngrok using the specified command in a separate, invisible window."""
    log_message("Starting ngrok...", "INFO")
    try:
        if os.name == 'nt':
            # For Windows: create a new process group and hide the window.
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            ngrok_process = subprocess.Popen(
                NGROK_COMMAND.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags
            )
        else:
            # For Unix-like systems: set the process group id so that children can be terminated
            ngrok_process = subprocess.Popen(
                NGROK_COMMAND.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
        time.sleep(5)  # Give ngrok time to initialize
        log_message("Ngrok started successfully.", "INFO")
        return ngrok_process
    except Exception as e:
        log_message(f"Failed to start ngrok: {e}", "ERROR")
        raise

def validate_client(client_socket):
    """Ensure client provides a valid identifier and token for authentication."""
    try:
        credentials = client_socket.recv(4096).decode('utf-8').strip()
        try:
            data = json.loads(credentials)
        except json.JSONDecodeError:
            client_socket.sendall(json.dumps({"error": "Invalid JSON format."}).encode('utf-8'))
            return None, None

        identifier = data.get('id')
        token = data.get('token')

        if not identifier or not token:
            client_socket.sendall(json.dumps({"error": "Missing 'id' or 'token' fields."}).encode('utf-8'))
            return None, None

        if identifier not in VALID_IDENTIFIERS:
            # Only pre-approved identifiers are allowed for connections.
            log_message(f"Invalid identifier: {identifier}", "WARNING")
            client_socket.sendall(json.dumps({"error": "Invalid identifier."}).encode('utf-8'))
            return None, None

        log_message(f"Received identifier: {identifier}, token: {token}", "INFO")

        if token in AUTHORIZED_TOKENS:
            # Reuse previously authorized tokens.
            log_message(f"Token '{token}' already authorized.", "DEBUG")
            return identifier, token

        log_message(f"Token '{token}' not recognized. Generating new token.", "INFO")
        new_token = generate_token()
        client_socket.sendall(json.dumps({"new_token": new_token}).encode('utf-8'))
        return identifier, new_token

    except Exception as e:
        # Handle unexpected validation errors.
        log_message(f"Error during client validation: {e}", "ERROR")
        client_socket.sendall(json.dumps({"error": "Server error during validation."}).encode('utf-8'))
        return None, None

def handle_client(client_socket, client_address):
    """Process client commands after successful authentication."""
    log_message(f"Connection received from {client_address}", "INFO")

    identifier, token = validate_client(client_socket)
    if not identifier or not token:
        log_message(f"Client {client_address} failed validation.", "WARNING")
        client_socket.close()
        return

    session_start_time = datetime.now()
    last_activity_time = datetime.now()

    # Set a short timeout on the socket so the loop can periodically check for timeouts.
    client_socket.settimeout(1)

    try:
        while True:
            try:
                # Try to read data from the client.
                input_data = client_socket.recv(4096).decode('utf-8').strip()
            except socket.timeout:
                current_time = datetime.now()
                # If no data is received, check for timeouts.
                if current_time - session_start_time > SESSION_TIMEOUT:
                    try:
                        client_socket.sendall(
                            json.dumps({"error": "Session timed out."}).encode('utf-8')
                        )
                        client_socket.shutdown(socket.SHUT_WR)
                        time.sleep(0.1)
                    except Exception as exc:
                        log_message(f"Error sending session timeout message: {exc}", "ERROR")
                    log_message(f"Session for {client_address} timed out.", "WARNING")
                    break
                if current_time - last_activity_time > SESSION_TIMEOUT:
                    try:
                        client_socket.sendall(
                            json.dumps({"error": "Idle timeout reached."}).encode('utf-8')
                        )
                        client_socket.shutdown(socket.SHUT_WR)
                        time.sleep(0.1)
                    except Exception as exc:
                        log_message(f"Error sending idle timeout message: {exc}", "ERROR")
                    log_message(f"Session for {client_address} idle too long.", "WARNING")
                    break
                continue

            # If the client closed the connection.
            if not input_data:
                break

            current_time = datetime.now()
            # Check timeouts after data arrives.
            if current_time - session_start_time > SESSION_TIMEOUT:
                try:
                    client_socket.sendall(
                        json.dumps({"error": "Session timed out."}).encode('utf-8')
                    )
                    client_socket.shutdown(socket.SHUT_WR)
                    time.sleep(0.1)
                except Exception as exc:
                    log_message(f"Error sending session timeout message: {exc}", "ERROR")
                log_message(f"Session for {client_address} timed out after receiving data.", "WARNING")
                break

            if current_time - last_activity_time > SESSION_TIMEOUT:
                try:
                    client_socket.sendall(
                        json.dumps({"error": "Idle timeout reached."}).encode('utf-8')
                    )
                    client_socket.shutdown(socket.SHUT_WR)
                    time.sleep(0.1)
                except Exception as exc:
                    log_message(f"Error sending idle timeout message: {exc}", "ERROR")
                log_message(f"Session for {client_address} idle too long after receiving data.", "WARNING")
                break

            last_activity_time = current_time

            try:
                data = json.loads(input_data)
            except json.JSONDecodeError:
                client_socket.sendall(
                    json.dumps({"error": "Invalid JSON format."}).encode('utf-8')
                )
                continue

            recv_id = data.get('id')
            recv_token = data.get('token')
            command = data.get('command')

            if not recv_id or not recv_token or not command:
                client_socket.sendall(
                    json.dumps({"error": "Missing required fields ('id', 'token', 'command')."}).encode('utf-8')
                )
                continue

            if recv_id != identifier or recv_token != token:
                log_message(f"Invalid credentials from {client_address}: {recv_id}, {recv_token}", "WARNING")
                client_socket.sendall(
                    json.dumps({"error": "Invalid credentials."}).encode('utf-8')
                )
                break

            # Shutdown command
            if command.lower() == "shutdown":
                log_message(f"Shutdown command received from {client_address}", "INFO")
                client_socket.sendall(
                    json.dumps({"message": "Server is shutting down."}).encode('utf-8')
                )
                SHUTDOWN_EVENT.set()
                break

            # Change directory command.
            if command.lower().startswith("cd "):
                try:
                    directory = command[3:].strip()
                    os.chdir(directory)
                    new_dir = os.getcwd()
                    response = {"output": f"Changed directory to {new_dir}"}
                    log_message(f"Changed directory to {new_dir} for {client_address}", "INFO")
                except Exception as e:
                    response = {"output": f"Failed to change directory: {e}"}
                    log_message(f"Failed to change directory for {client_address}: {e}", "ERROR")
                client_socket.sendall(json.dumps(response).encode('utf-8'))
                continue

            # Exit command – send a goodbye message before closing.
            if command.lower() == "exit":
                log_message(f"Client {client_address} disconnected.", "INFO")
                client_socket.sendall(
                    json.dumps({"message": "Goodbye"}).encode('utf-8')
                )
                time.sleep(0.1)
                break

            # 'hows alive' command.
            if command.lower() == "hows alive":
                uptime = datetime.now() - SERVER_START_TIME
                response = {"uptime": str(uptime).split('.')[0]}
                client_socket.sendall(json.dumps(response).encode('utf-8'))
                continue

            # Arbitrary Code Execution: 'run' command uses the code field.
            if command.lower() == "run":
                if 'code' not in data or not data.get('code'):
                    client_socket.sendall(json.dumps({"error": "Missing code for execution."}).encode('utf-8'))
                    continue
                code_to_run = data.get('code')
                log_message(f"Executing arbitrary code from {recv_id} at {client_address}.", "DEBUG")
                try:
                    stdout_capture = io.StringIO()
                    with contextlib.redirect_stdout(stdout_capture):
                        exec(code_to_run, {})
                    code_output = stdout_capture.getvalue()
                except Exception as e:
                    code_output = str(e)
                    log_message(f"Error executing arbitrary code: {e}", "ERROR")
                response = {"output": code_output}
                client_socket.sendall(json.dumps(response).encode('utf-8'))
                continue

            # For other commands, check if it is dangerous.
            if is_dangerous_command(command):
                log_message(f"Dangerous command detected from {recv_id} at {client_address}: {command}", "WARNING")
                admin_approval = ADMIN_APPROVAL_FUNC(f"Approve dangerous command from {recv_id} @ {client_address}: {command}\nApprove? (Y/N): ")
                if admin_approval.strip().lower() != 'y':
                    client_socket.sendall(json.dumps({"error": "Dangerous command execution denied by admin."}).encode('utf-8'))
                    log_message("Dangerous command execution denied by admin.", "WARNING")
                    continue
                else:
                    log_message("Admin approved dangerous command execution.", "INFO")

            log_message(f"Received command: {command} from {recv_id}", "INFO")
            try:
                output = subprocess.check_output(
                    command, shell=True, stderr=subprocess.STDOUT, text=True
                )
            except subprocess.CalledProcessError as e:
                output = e.output
                log_message(f"Command execution error: {output}", "ERROR")

            response = {"output": output}
            client_socket.sendall(json.dumps(response).encode('utf-8'))
    except Exception as e:
        log_message(f"Error handling client {client_address}: {e}", "ERROR")
        try:
            client_socket.sendall(
                json.dumps({"error": "Server error while handling command."}).encode('utf-8')
            )
        except Exception:
            pass
    finally:
        client_socket.close()
        log_message(f"Closed connection with {client_address}", "INFO")

def worker():
    """Thread worker to manage client requests in the queue."""
    while True:
        client_socket, client_address = task_queue.get()
        try:
            handle_client(client_socket, client_address)
        finally:
            task_queue.task_done()

def clean_exit(server_socket, ngrok_process):
    """Clean up resources and stop network activities."""
    log_message("Cleaning up resources...", "INFO")
    if ngrok_process:
        try:
            if os.name == 'nt':
                ngrok_process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(os.getpgid(ngrok_process.pid), signal.SIGTERM)
            ngrok_process.wait(timeout=5)  # Wait for process to terminate
            log_message("Ngrok process terminated.", "INFO")
        except subprocess.TimeoutExpired:
            log_message("Ngrok process did not terminate. Attempting force kill...", "WARNING")
            try:
                ngrok_process.kill()
            except Exception as kill_exception:
                log_message(f"Failed to kill ngrok process: {kill_exception}", "ERROR")
    if server_socket:
        server_socket.close()
        log_message("Server socket closed.", "INFO")

def start_server():
    """Launch the server and initialize the thread pool for client handling."""
    log_message(f"Starting server on {HOST}:{PORT}...", "INFO")
    ngrok_process = None
    server_socket = None

    try:
        ngrok_process = start_ngrok()  # Ensure ngrok is running
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        server_socket.settimeout(1.0)  # Timeout chosen for responsiveness to interrupts
        log_message("Server is listening for connections...", "INFO")

        # Create and start thread pool
        for _ in range(MAX_THREADS):
            thread = threading.Thread(target=worker, daemon=True)
            thread_pool.append(thread)
            thread.start()

        while not SHUTDOWN_EVENT.is_set():
            try:
                client_socket, client_address = server_socket.accept()
                task_queue.put((client_socket, client_address))
            except socket.timeout:
                continue

    except KeyboardInterrupt:
        log_message("Interrupt received. Preparing to shut down.", "INFO")
    finally:
        clean_exit(server_socket, ngrok_process)

if __name__ == '__main__':
    print_banner()  # Display ASCII logo and metadata
    log_message("Server initialization...", "INFO")
    start_server()
