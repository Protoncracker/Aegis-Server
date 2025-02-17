# Aegis Sandbox

Aegis Sandbox is a secure remote command-line interface designed for AI agents. Born from the rise of intelligent agents like those powered by OpenAI, the primary goal of this project is to provide a controlled environment where AI systems (e.g., GPT-4) can execute commands and modify code as if they were operating on their own machine.

> **Warning:** Due to the inherent risks of giving agents the ability to execute arbitrary code, it is **highly recommended** to run Aegis Sandbox within a virtual machine (VM) or another sandboxed environment.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [How It Works](#how-it-works)
- [Installation and Setup](#installation-and-setup)
- [Use Cases](#use-cases)
- [Future Enhancements](#future-enhancements)
- [Security Considerations](#security-considerations)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Introduction

The rapid advancement of AI agents, particularly from OpenAI, has inspired this project. Aegis Sandbox provides a way for AI agents to interact with your system's command line securely. You have two options for using the system:

1. **Create Your Own Agent:** Hardcode a custom identifier (a 14-character base64 string) within your agent for authentication.
2. **Use a Third-Party Agent:** (Not recommended) Supply the identifier for an external agent.

*Note:* The base64 string required is completely custom — it is **not generated automatically** by the program. We recommend that you use your own personal favorite 14-character-long base64 string.

## Features

- **Remote Control:** Execute shell commands, run arbitrary Python code, and modify files remotely.
- **Token-Based Authentication:** Secure your sessions with token generation and validation.
- **Customizable Identifier:** Authenticate connections using a custom 14-character base64 identifier loaded from an environment file (`AEGIS.env`).
- **Ngrok Integration:** Easily expose your local server to the internet via a configurable Ngrok command.
- **Robust Logging:** All activities, including command executions and session information, are logged for auditing.
- **Secure Command Execution:** Dangerous commands trigger admin approval to prevent unwanted system changes.
- **Future Enhancements:** Plans include challenge-based authentication using public and private encryption, mouse and keyboard emulation, and image recognition.

## How It Works

- **Authentication:**  
  The server checks for an allowed identifier (a custom 14-character base64 string) as specified in the `AEGIS.env` file. Any connection that doesn't provide the exact identifier will be rejected.

- **Command Execution:**  
  The system supports safe commands (e.g., `echo`, `cd`) and arbitrary Python code execution via a `"run"` command. Commands containing dangerous operations (e.g., `rm -rf`) require manual admin approval.

- **Session Management:**  
  Sessions time out after 60 seconds of inactivity, and tokens ensure that only authorized actions are executed.

## Installation and Setup

1. **Prerequisites:**
   - Python 3.6 or later.
   - [Colorama](https://pypi.org/project/colorama/) for colored logging output.
   - [Ngrok](https://ngrok.com/) (optional) to expose your local server externally.

2. **Environment Configuration:**
   - Create an `AEGIS.env` file in the project root with the following entries:
     ```
     ID=<your_14_character_base64_string>
     NGROK_COMMAND=ngrok http 8080
     ```
   - *Note:* The ID you provide must be a custom, 14-character-long base64 string that you choose. The program itself does not generate this value.

3. **Installation:**
   - Install the required dependencies by running:
     ```bash
     pip install -r requirements.txt
     ```

4. **Running the Server:**
   - Start the server with:
     ```bash
     python server.py
     ```
   - On startup, an ASCII art shield and the program metadata will be displayed, and the server will begin listening on `127.0.0.1:8080`.

5. **Running the Tests:**
   - Execute the comprehensive testing suite using:
     ```bash
     python test_server.py
     ```
   - All interactions will be logged and a final summary will be displayed.

## Use Cases

Aegis Sandbox empowers AI agents by providing a direct way to interact with a system:

- **Custom Agent Development:** Build your own agent with the identifier hardcoded for secure authentication.
- **Third-Party Agent Integration:** Alternatively, supply an identifier to allow an external agent to interface with the system (less secure and not recommended).

## Future Enhancements

- **Challenge-Based Authentication:**  
  Future iterations may include enhanced security via challenge-response mechanisms. In this approach, the server would send cryptographic challenges to the AI agent, which must be answered using a private key (hardcoded in the agent) instead of a simple ID. This method leverages public and private encryption to establish a secure connection, optionally requiring an additional ID or manual admin intervention.

- **Sandbox Enhancements:**  
  Planned features include mouse emulation, image recognition, and keyboard emulation to enable full-scale interaction akin to a real user.

## Security Considerations

- **Current Security:**  
  The system uses token-based authentication and a custom, 14-character base64 identifier to control access. Dangerous commands trigger an admin approval prompt to prevent unauthorized or harmful operations.

- **Important Note:**  
  The required base64 string is custom; the program does not generate it. We recommend you use your own personal favorite 14-character-long base64 string to ensure secure and unique authentication.

- **Looking Forward:**  
  Additional security measures, such as challenge-response authentication using public/private key pairs, are planned to further enhance the system's integrity. These mechanisms will provide an extra layer of verification before granting access.

## Contributing

Contributions, suggestions, and bug reports are welcome! Please submit issues or pull requests to help improve Aegis Sandbox and enhance its security and functionality.

## License

This project is licensed under a proprietary license. All rights are reserved by ProtonCracker.

## Contact

For support or inquiries, please reach out to:

- **Author/Maintainer:** ProtonCracker
- **Email:** tryme.freefall963@passinbox.com

---

Happy and secure coding!
