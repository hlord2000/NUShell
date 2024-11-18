import simplepyble
import sys
import threading
import time
import platform
import select

# NUS Service UUID and Characteristic UUIDs
NUS_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
NUS_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"  # Write
NUS_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"  # Notify

def main():
    # Get BLE adapter
    adapters = simplepyble.Adapter.get_adapters()
    if not adapters:
        print("No Bluetooth adapters found.")
        sys.exit(1)
    adapter = adapters[0]
    print(f"Using adapter: {adapter.identifier()}")

    # Scan for devices
    print("Scanning for devices...")
    adapter.scan_for(5000)
    peripherals = adapter.scan_get_results()

    # Filter devices that advertise the NUS service
    nus_peripherals = []
    for peripheral in peripherals:
        service_uuids = peripheral.services()
        if isinstance(service_uuids, list):
            for service_uuid in service_uuids:
                if NUS_SERVICE_UUID.lower() == service_uuid.uuid().lower():
                    nus_peripherals.append(peripheral)
                    break  
        elif isinstance(service_uuids, str):
            if NUS_SERVICE_UUID.lower() == service_uuids.lower():
                nus_peripherals.append(peripheral)

    if not nus_peripherals:
        print("No devices advertising the Nordic UART Service found.")
        sys.exit(1)

    # Display the list of devices
    print("\nDevices advertising NUS service:")
    for idx, peripheral in enumerate(nus_peripherals):
        name = peripheral.identifier() or "Unknown"
        address = peripheral.address()
        print(f"{idx + 1} {name} [{address}]")

    # Ask the user to select a device
    while True:
        try:
            selection = int(input("\nSelect a device by number (or 0 to exit): "))
            if selection == 0:
                sys.exit(0)
            if 1 <= selection <= len(nus_peripherals):
                selected_peripheral = nus_peripherals[selection - 1]
                break
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")

    target_peripheral = selected_peripheral

    # Connect to the device
    print(f"\nConnecting to {target_peripheral.identifier()} ({target_peripheral.address()})...")
    target_peripheral.connect()
    print("Connected successfully!")

    # Discover services and characteristics
    services = target_peripheral.services()
    nus_service = None
    for service in services:
        if service.uuid().lower() == NUS_SERVICE_UUID.lower():
            nus_service = service
            break

    if not nus_service:
        print("NUS service not found on the device.")
        target_peripheral.disconnect()
        sys.exit(1)

    # Check if characteristics are available
    rx_char = None
    tx_char = None
    for char in nus_service.characteristics():
        if NUS_RX_CHAR_UUID.lower() in char.uuid().lower():
            rx_char = char
        if NUS_TX_CHAR_UUID.lower() in char.uuid().lower():
            tx_char = char

    if not rx_char or not tx_char:
        print("Required characteristics not found.")
        target_peripheral.disconnect()
        sys.exit(1)

    # Set up notification handler
    stop_event = threading.Event()

    def notification_handler(data):
        # Data received from the device
        data_bytes = bytes(data)
        print(data_bytes.decode('utf-8', errors='replace'), end='', flush=True)

    try:
        target_peripheral.notify(nus_service.uuid(), tx_char.uuid(), notification_handler)
    except Exception as e:
        print(f"Failed to subscribe to notifications: {str(e)}")
        target_peripheral.disconnect()
        sys.exit(1)

    # Start thread to read user input and send to device
    def read_user_input():
        try:
            if platform.system() == 'Windows':
                import msvcrt
                while not stop_event.is_set():
                    if msvcrt.kbhit():
                        c = msvcrt.getwch()
                        if c == '\r':
                            c = '\n'
                            print('', flush=True)
                        target_peripheral.write_request(nus_service.uuid(), rx_char.uuid(), c.encode('utf-8'))
            else:
                import sys
                import termios
                import tty
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                tty.setcbreak(fd)
                while not stop_event.is_set():
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        c = sys.stdin.read(1)
                        if c == '\x03':  
                            stop_event.set()
                            break
                        target_peripheral.write_request(nus_service.uuid(), rx_char.uuid(), c.encode('utf-8'))
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception as e:
            print(f"Error reading user input: {str(e)}")
            stop_event.set()

    input_thread = threading.Thread(target=read_user_input)
    input_thread.daemon = True
    input_thread.start()

    print("\nTerminal started. Press Ctrl+C to exit.")

    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_event.set()

    print("\nExiting...")
    target_peripheral.disconnect()

if __name__ == "__main__":
    main()
