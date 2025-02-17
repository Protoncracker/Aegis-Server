# User Guide for the Remote Code Editing Sandbox Server

## Aegis Sandbox
*Remote Code Editing and Command Execution Server*

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Installation and Setup](#installation-and-setup)
4. [Server Details and Commands](#server-details-and-commands)
    - [Authentication and Token Generation](#authentication-and-token-generation)
    - [Command Execution](#command-execution)
    - [Session Management](#session-management)
    - [Dangerous Command Handling](#dangerous-command-handling)
    - [Built-in Commands](#built-in-commands)
5. [Logging and Monitoring](#logging-and-monitoring)
6. [Testing Suite](#testing-suite)
7. [Security Considerations](#security-considerations)
8. [Troubleshooting and FAQ](#troubleshooting-and-faq)
9. [Future Enhancements](#future-enhancements)
10. [Contact and Support](#contact-and-support)

---

## Overview

The Aegis Sandbox server provides a secure, sandboxed environment where artificial intelligences can remotely edit code and perform system-level operations. This controlled setup allows remote interactions with the server while maintaining strict security measures.

Key objectives of the server:
- **Remote Code Editing:** Allow AI agents to modify and execute code remotely.
- **Secure Command Execution:** Enable execution of both system commands and arbitrary Python code within a sandbox.
- **Extensive Logging:** Record every session and command execution to facilitate auditing and troubleshooting.
- **Controlled Access:** Rely on token-based authentication, manual dangerous command approval, and session management to limit access.

---

## System Architecture

### Server Components

- **server.py:**  
  The main backend script which:
  - Listens for TCP connections.
  - Authenticates clients using an identifier and token.
  - Processes commands (basic shell commands, arbitrary code execution, etc.).
  - Enforces dangerous command checks requiring admin approval.
  - Manages session timeouts and logs all activities.

- **test_server.py:**  
  A comprehensive testing suite that:
  - Sends both valid and invalid commands to the server.
  - Verifies session timeout, token generation, and dangerous command handling.
  - Logs each interaction into `test_log.log` along with a final summary of the tests.

- **USER_GUIDE.md:**  
  This document, providing detailed instructions on setup, configuration, usage, and security practices.

### Metadata (Embedded in server.py)

- **Version:** 1.0.0
- **Author/Maintainer:** ProtonCracker
- **License:** Private - All Rights Reserved
- **Status:** Production
- **Program Name:** Aegis Sandbox

---

## Installation and Setup

### Prerequisites

- **Python 3.6+** is required.
- **Colorama:**  
  For colored logging output. If Colorama is not installed, the server uses dummy classes.
  
  To install Colorama, run:
  ```bash
  pip install colorama
  ```

- **Ngrok (optional):**  
  Ngrok can be used to expose your local server over the Internet. Configure the `NGROK_COMMAND` variable as needed in server.py.

### Running the Server

1. Install all necessary dependencies.
2. Run the server using:
   ```bash
   python server.py
   ```
3. The server will start on `127.0.0.1:8080`. An ASCII art shield and the program metadata will be displayed on startup.
4. If configured, Ngrok will start automatically to expose the server externally.

### Running the Tests

To run the complete testing suite:
```bash
python test_server.py
```
This executes all unit tests, logs every transaction in `test_log.log`, and prints a summary at the end.

---

## Server Details and Commands

### Authentication and Token Generation

- The server now requires a 14-character base64 string as the identifier. This value is loaded from a local file called `AEGIS.env`. The file must include a line in the following format:
  ```
  ID=<your_14_character_base64_string>
  ```
- Additionally, the command used to start ngrok is loaded from `AEGIS.env` via the `NGROK_COMMAND` variable. For example:
  ```
  NGROK_COMMAND=ngrok http 8080
  ```
- At startup, both values are logged. Any connection providing an identifier that does not exactly match the loaded value is rejected.
- The command JSON structure still requires the `"token"` field for session management. In case an invalid token is provided, a new valid token is generated and returned.

### Command Execution

#### Safe Commands

- **Basic System Commands:**  
  Commands such as `echo`, directory changes (`cd`), and checking server uptime (`hows alive`) are supported.
  
  Example:
  ```json
  {
    "id": "Jarvis",
    "token": "your_token_here",
    "command": "echo Hello"
  }
  ```

#### Arbitrary Code Execution (Run Command)

- Use the `"run"` command with an extra `"code"` field to execute Python code.
  
  Example:
  ```json
  {
    "id": "Jarvis",
    "token": "your_token_here",
    "command": "run",
    "code": "print('Hello from run')"
  }
  ```
  
- **Security Note:**  
  This capability is powerful and should be restricted to verified users only, as it can potentially be exploited if credentials are compromised.

#### Dangerous Command Handling

- **Admin Approval Required:**  
  Commands that include dangerous substrings (e.g., `rm -rf`, `del /f`) trigger an admin prompt. The server logs the command and asks for manual approval.
  - **If approval is denied:** The command is not executed, and an error message is returned.
  
  Example dangerous command:
  ```json
  {
    "id": "Jarvis",
    "token": "your_token_here",
    "command": "rm -rf /dummy"
  }
  ```
  Response:
  ```json
  {
    "error": "Dangerous command execution denied by admin."
  }
  ```

### Session Management

- **Timeout:**  
  Sessions are disconnected after 60 seconds of inactivity.
- **Token Persistence:**  
  Valid tokens remain active during the session. Upon invalidation of a token, a new one is issued.
- **Disconnection:**  
  The `"exit"` command allows clients to terminate their session gracefully.

### Built-in Commands

- **hows alive:**  
  Returns the server's uptime.
- **cd [directory]:**  
  Changes the current working directory.
- **shutdown:**  
  Shuts down the server after logging the shutdown command.
- **exit:**  
  Terminates the client connection with a farewell message.

---

## Logging and Monitoring

### Logging Features

- **Server Logging:**  
  Activities such as client authentication, command execution, errors, and session activity are logged into `server.log` with appropriate timestamps and log levels (INFO, DEBUG, WARNING, ERROR).

- **Test Logging:**  
  All test interactions are recorded in `test_log.log`.
  
- **Console Output:**  
  If Colorama is installed, console logging is color-formatted to facilitate easier debugging.

---

## Testing Suite

### Features in test_server.py

- **Command & Response Tracking:**  
  Every command sent and response received is recorded for auditability.
- **Security Tests:**  
  These tests simulate remote code execution vulnerabilities, bypass attempts, dangerous command invocations, and measure proper session handling.
- **Session Tests:**  
  Validate token regeneration, session timeout behavior, and proper handling of both valid and invalid credentials.

### Running the Tests

Execute the following command in your terminal:
```bash
python test_server.py
```
After running, review `test_log.log` for a detailed summary of test interactions and outcomes.

---

## Security Considerations

### Strengths

- **Controlled Environment:**  
  Strict token-based authentication and manual approval for dangerous commands help secure the system.
- **Comprehensive Logging:**  
  Detailed logs aid in auditing and troubleshooting, helping detect any unauthorized actions.
- **Defined Sandbox:**  
  The ability to execute arbitrary code is limited to verified users to prevent misuse.

### Caveats

- **Arbitrary Code Execution Risk:**  
  While useful, allowing the execution of arbitrary code is inherently risky. For production, consider using containerized sandboxes or further restricting execution environments.
- **Token-Based Authentication Limitations:**  
  Enhancing the current authentication mechanism with more robust protocols is recommended.
- **Additional Security Measures:**  
  Implement rate limiting, advanced input validation, and anomaly detection to further harden the server.

---

## Troubleshooting and FAQ

### Common Issues

- **Colorama Module Missing:**  
  If you encounter issues with colored logging, install Colorama via:
  ```bash
  pip install colorama
  ```
  The server will function with plain output if Colorama is absent.
  
- **Session Timeouts:**  
  If sessions disconnect unexpectedly, ensure that activity occurs within the 60-second timeout window.
  
- **Dangerous Command Denial:**  
  Verify that your commands do not inadvertently trigger dangerous command checks. Provide proper admin approval if necessary.

### Frequently Asked Questions

- **Can I modify the session timeout?**  
  Yes, modify the `SESSION_TIMEOUT` parameter in server.py as required.
  
- **How can I allow a command flagged as dangerous?**  
  You must provide manual admin approval when prompted. For automated environments, consider adjusting the dangerous command handler.
  
- **How do I update the ASCII art or the metadata in the banner?**  
  The ASCII art in the `print_banner()` function of server.py can be edited manually, and the metadata is declared at the top of the file.

---

## Future Enhancements

- **Enhanced Sandbox Environments:**  
  Consider deploying containerization (e.g., Docker) for improved isolation of code execution.
- **Improved Authentication:**  
  Integration with OAuth or other security frameworks may offer higher security.
- **Rate Limiting:**  
  Implement request rate limiting to mitigate potential abuse.
- **Advanced Monitoring:**  
  Develop real-time alerting mechanisms for unusual activities and potential security breaches.

---

## Contact and Support

For further assistance or updates regarding Aegis Sandbox, please reach out to:

- **Author/Maintainer:** ProtonCracker
- **Email:** tryme.freefall963@passinbox.com

*Happy and secure coding!*

