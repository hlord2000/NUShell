# NUShell

NUShell is a Python-based terminal emulator for interacting with devices using the Nordic UART Service (NUS) over Bluetooth Low Energy (BLE). It allows you to send and receive data to and from BLE devices that implement the NUS, rendering all control codes, color codes, and characters correctly in your terminal.

## Requirements

- Bluetooth Low Energy (BLE) adapter
- Terminal that supports ANSI escape codes (for color rendering)

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/nushell.git
   cd nushell
   ```

2. **Install Dependencies***

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Usage

   ```bash
   python3 nushell.py
   ```

