import unittest
import socket
import json
import time
import logging
from unittest.mock import patch

# Configure test logging
TEST_LOG_FILENAME = "test_log.log"
logging.basicConfig(
    filename=TEST_LOG_FILENAME,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration for testing
TEST_HOST = '127.0.0.1'
TEST_PORT = 8080
# Our server SESSION_TIMEOUT is 60 seconds; tests use 60 seconds as well.
SESSION_TIMEOUT = 60

def log_test(message):
    logging.debug(message)
    print(message)  # also print to console, if desired

class TestServer(unittest.TestCase):
    command_history = []  # records tuples (sent, received)

    def setUp(self):
        """Setup a new connection to the server for each test."""
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((TEST_HOST, TEST_PORT))
        log_test("Connected to server")

    def tearDown(self):
        """Close the connection after each test."""
        try:
            self.client_socket.close()
        except Exception:
            pass
        log_test("Closed connection to server")

    def send_and_receive(self, data):
        """Send JSON data to the server, log the command and response, and return the response."""
        command = json.dumps(data)
        log_test(f"Sending command: {command}")
        self.client_socket.sendall(command.encode('utf-8'))
        try:
            response = self.client_socket.recv(4096)
        except ConnectionAbortedError:
            response = b'{"error": "Session timed out."}'
        decoded_response = response.decode('utf-8')
        log_test(f"Received response: {decoded_response}")
        # Record this command-response pair
        self.__class__.command_history.append((command, decoded_response))
        if decoded_response:
            try:
                return json.loads(decoded_response)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON in response"}
        return {}

    @classmethod
    def tearDownClass(cls):
        """After all tests, write a summary to the test log."""
        summary_lines = ["Test Summary:"]
        for i, (sent, received) in enumerate(cls.command_history, start=1):
            summary_lines.append(f"#{i} Sent: {sent} | Received: {received}")
        summary = "\n".join(summary_lines)
        log_test(summary)

    def test_invalid_json(self):
        """Test the server response to invalid JSON data."""
        self.client_socket.sendall(b"Invalid JSON")
        response = self.client_socket.recv(4096).decode('utf-8')
        log_test(f"Raw response for invalid JSON: {response}")
        data = json.loads(response)
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Invalid JSON format.")

    def test_missing_fields(self):
        """Test the response when required fields are missing."""
        data = {"id": "Jarvis"}
        response = self.send_and_receive(data)
        self.assertIn("error", response)
        self.assertEqual(response["error"], "Missing 'id' or 'token' fields.")

    def test_invalid_identifier(self):
        """Test the server response when an invalid identifier is used."""
        data = {"id": "InvalidID", "token": "1234"}
        response = self.send_and_receive(data)
        self.assertIn("error", response)
        self.assertEqual(response["error"], "Invalid identifier.")

    def test_token_generation(self):
        """Test that a new token is generated for an invalid token."""
        data = {"id": "Jarvis", "token": "invalid_token"}
        response = self.send_and_receive(data)
        self.assertIn("new_token", response)

    def test_execute_command(self):
        """Test the execution of a valid system command."""
        auth_data = {"id": "Jarvis", "token": "invalid_token"}
        auth_response = self.send_and_receive(auth_data)
        token = auth_response.get("new_token")
        command_data = {"id": "Jarvis", "token": token, "command": "echo Hello"}
        response = self.send_and_receive(command_data)
        self.assertIn("output", response)
        # The echo output may have trailing newline characters
        self.assertEqual(response["output"].strip(), "Hello")

    def test_hows_alive_command(self):
        """Test that the 'hows alive' command returns the server uptime."""
        auth_data = {"id": "Jarvis", "token": "invalid_token"}
        auth_response = self.send_and_receive(auth_data)
        token = auth_response.get("new_token")
        command_data = {"id": "Jarvis", "token": token, "command": "hows alive"}
        response = self.send_and_receive(command_data)
        self.assertIn("uptime", response)
        self.assertTrue(isinstance(response["uptime"], str))

    def test_exit_command(self):
        """Test that the 'exit' command closes the connection."""
        auth_data = {"id": "Jarvis", "token": "invalid_token"}
        auth_response = self.send_and_receive(auth_data)
        token = auth_response.get("new_token")
        command_data = {"id": "Jarvis", "token": token, "command": "exit"}
        self.send_and_receive(command_data)
        with self.assertRaises(Exception):
            self.send_and_receive({"id": "Jarvis", "token": token, "command": "echo test"})

    def test_invalid_credentials_during_session(self):
        """Test using an incorrect token during an active session."""
        auth_data = {"id": "Jarvis", "token": "invalid_token"}
        auth_response = self.send_and_receive(auth_data)
        token = auth_response.get("new_token")
        command_data = {"id": "Jarvis", "token": "wrong_token", "command": "echo test"}
        response = self.send_and_receive(command_data)
        self.assertIn("error", response)
        self.assertEqual(response["error"], "Invalid credentials.")

    def test_session_timeout(self):
        """Test that the session times out after inactivity."""
        auth_data = {"id": "Jarvis", "token": "invalid_token"}
        auth_response = self.send_and_receive(auth_data)
        token = auth_response.get("new_token")
        time.sleep(SESSION_TIMEOUT + 1)
        command_data = {"id": "Jarvis", "token": token, "command": "echo After Timeout"}
        response = self.send_and_receive(command_data)
        self.assertIn("error", response)
        self.assertEqual(response["error"], "Session timed out.")

    def test_run_command(self):
        """Test arbitrary code execution using the 'run' command."""
        auth_data = {"id": "Jarvis", "token": "invalid_token"}
        auth_response = self.send_and_receive(auth_data)
        token = auth_response.get("new_token")
        run_data = {
            "id": "Jarvis",
            "token": token,
            "command": "run",
            "code": "print('Hello from run')"
        }
        response = self.send_and_receive(run_data)
        self.assertIn("output", response)
        self.assertEqual(response["output"].strip(), "Hello from run")

    def test_rce_vulnerability(self):
        """Test to see if arbitrary code execution can read server files (RCE).
           This simulates an attacker trying to bypass restrictions.
        """
        malicious_code = (
            "import os\n"
            "print('Files:', os.listdir('.'))"
        )
        auth_data = {"id": "Jarvis", "token": "invalid_token"}
        auth_response = self.send_and_receive(auth_data)
        token = auth_response.get("new_token")
        run_data = {
            "id": "Jarvis",
            "token": token,
            "command": "run",
            "code": malicious_code
        }
        response = self.send_and_receive(run_data)
        self.assertIn("output", response)
        # Even if the command succeeds, note that allowing arbitrary directory listing may be undesirable.
        self.assertTrue("Files:" in response["output"])

    @patch('server.ADMIN_APPROVAL_FUNC', lambda prompt: "n")
    def test_dangerous_command_denied(self):
        """Test that a dangerous command is denied when admin does not approve."""
        auth_data = {"id": "Jarvis", "token": "invalid_token"}
        auth_response = self.send_and_receive(auth_data)
        token = auth_response.get("new_token")
        dangerous_data = {"id": "Jarvis", "token": token, "command": "rm -rf /dummy"}
        response = self.send_and_receive(dangerous_data)
        self.assertIn("error", response)
        self.assertEqual(response["error"], "Dangerous command execution denied by admin.")

    @patch('server.ADMIN_APPROVAL_FUNC', lambda prompt: "y")
    def test_dangerous_command_approved(self):
        """Test that a dangerous command is executed when admin approves.
           Note: We use a harmless command containing the dangerous keyword.
        """
        auth_data = {"id": "Jarvis", "token": "invalid_token"}
        auth_response = self.send_and_receive(auth_data)
        token = auth_response.get("new_token")
        dangerous_data = {
            "id": "Jarvis",
            "token": token,
            "command": "echo rm -rf approved"
        }
        response = self.send_and_receive(dangerous_data)
        self.assertIn("output", response)
        self.assertIn("rm -rf approved", response["output"])

    def test_bypass_attempt(self):
        """Simulate an attempt to bypass authentication by sending extra fields."""
        # Even if additional fields are sent or the command is modified,
        # proper verification should prevent bypassing security controls.
        auth_data = {
            "id": "Jarvis", 
            "token": "invalid_token",
            "extra_field": "malicious_payload"
        }
        auth_response = self.send_and_receive(auth_data)
        token = auth_response.get("new_token")
        # Try to bypass dangerous command approval by appending a benign command to a dangerous one
        bypass_data = {
            "id": "Jarvis",
            "token": token,
            "command": "rm -rf /dummy && echo bypass"
        }
        response = self.send_and_receive(bypass_data)
        # With admin approval required, the dangerous part should trigger denial if not approved.
        self.assertIn("error", response)
        self.assertEqual(response["error"], "Dangerous command execution denied by admin.")

if __name__ == '__main__':
    unittest.main()
