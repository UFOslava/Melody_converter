import logging
from time import sleep
import pyvisa


def scan_visa(backend: str = "@py", resource_filter: str = "USB") -> list[str]:
    rm = pyvisa.ResourceManager(backend)  # '@py' for pyvisa-py backend
    # rm = pyvisa.ResourceManager()
    resources = list()
    logging.info(f"Scanning VISA devices...")
    try:
        resources = rm.list_resources(query=resource_filter)
    except Exception as e:
        print(f"Error listing resources: {e}")
    finally:
        rm.close()
        return list(resources)


class Device:
    """Class to hold device info
    USB0::2391::9479::MY52102525::0::INSTR"""

    def __init__(self, resource_name: str):
        self.resource_name = resource_name
        self.parts = self.resource_name.split('::')
        self.Protocol = self.parts[0]

    def res(self) -> str:
        return self.resource_name


class USB_Device(Device):
    def __init__(self, resource_name: str):
        super().__init__(resource_name)
        try:
            self.VendorID = int(self.parts[1])
            self.ProductID = int(self.parts[2])
            self.SN = self.parts[3]
            self.InterfaceID = int(self.parts[4]) if len(self.parts) == 6 else 0
        except ValueError:
            print(f"Error: Could not parse numeric IDs from '{resource_name}'")
            self.VendorID = None
            self.ProductID = None
            self.InterfaceID = None

    def set(self, Protocol: str, VendorID: int, ProductID: int, SN: str, InterfaceID: int = 0):
        self.Protocol: str = Protocol
        self.VendorID: int = VendorID
        self.ProductID: int = ProductID
        self.SN: str = SN
        self.InterfaceID: int = InterfaceID

    def __repr__(self):
        return (f"Device(ResourceName='{self.ResourceName}', "
                f"Protocol='{self.Protocol}', "
                f"VendorID={self.VendorID}, "
                f"ProductID={self.ProductID}, "
                f"SN='{self.SN}', "
                f"InterfaceID={self.InterfaceID})")

    def __str__(self):
        return (f"{self.Protocol} Device: VendorID=0x{self.VendorID:04X},"
                f" ProductID=0x{self.ProductID:04X},"
                f" SN='{self.SN}'")

    def __eq__(self, other):
        if not isinstance(other, Device):
            return NotImplemented
        return (self.Protocol == other.Protocol and
                self.VendorID == other.VendorID and
                self.ProductID == other.ProductID and
                self.SN == other.SN and
                self.InterfaceID == other.InterfaceID)

    def __hash__(self):
        return hash((self.Protocol, self.VendorID, self.ProductID, self.SN, self.InterfaceID))


def device_factory(resource_name: str) -> Device:
    parts = resource_name.split("::")
    if parts:
        protocol = parts[0].lower()
        if protocol.startswith("usb"):
            return USB_Device(resource_name)
        else:
            return Device(resource_name)
    else:
        return Device(resource_name)


class VISA_Connection:
    instrument: pyvisa.Resource

    def __init__(self, visa_device: Device):
        self.visa_device = visa_device
        self.resource_manager = pyvisa.ResourceManager('@py')  # Initialize here
        self.instrument = None

    def __enter__(self):
        print(f"Connecting to {self.visa_device.resource_name}...")

        try:
            self.instrument = self.resource_manager.open_resource(self.visa_device.resource_name)
            print(f"Successfully connected to: {self.instrument.resource_name}")

            # Query the instrument's identification
            identification = self.instrument.query('*IDN?')
            print(f"Instrument identification: {identification.strip()}")

            # You can now send other commands to control the instrument
            # For example, to set the output to a sine wave at 1 kHz with 1 Vpp:
            # instrument.write('SOUR1:FUNC SIN')
            # instrument.write('SOUR1:FREQ 1000')
            # instrument.write('SOUR1:VOLT 1VP')
            # self.instrument.write('OUTP1 ON')
            # sleep(0.5)
            # self.instrument.write('OUTP1 OFF')
            return self  # Return self to allow use with 'as'

        except pyvisa.VisaIOError as e:
            print(f"Error communicating with the instrument: {e}")
            self.__exit__(None, None, None)  # Ensure cleanup even on connect fail
            raise  # Re-raise the exception to stop execution
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.__exit__(None, None, None)
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.instrument:  # Check if instrument is valid
                self.instrument.close()
            if self.resource_manager:
                self.resource_manager.close()
            print("Instrument connection closed.")
        except Exception as e:
            print(f"Error during cleanup: {e}")

    def write(self, msg: str):
        if not self.instrument:
            raise ValueError("Instrument is not connected.")
        self.instrument.write(msg)
        logging.info(f'Sending "{msg}"')

    def query(self, msg: str) -> str:
        if not self.instrument:
            raise ValueError("Instrument is not connected.")
        logging.info(f'Sending "{msg}"')
        answer = str(self.instrument.query(msg))
        logging.info(f'Answer: "{answer}"')
        return answer


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    device_filter: str = "2391::9479"
    logging.info(f'Device Filter: "{device_filter}"')
    # devices = scan_visa(resource_filter=device_filter)
    devices = scan_visa()
    if devices:
        device = Device(devices[0])
        try:
            with VISA_Connection(device) as VISA:
                VISA.write('SOUR1:FREQ 1000')
                VISA.write('OUTP1 ON')
                sleep(0.5)
                VISA.write('OUTP1 OFF')
        except Exception as e:
            print(f"An error occurred during the main execution: {e}")
    else:
        logging.warning("No devices matching the filter...")
        devices = scan_visa()
        if devices:
            logging.info(f"Available devices ({len(devices)}):")
            for device in devices:
                logging.info(f"{device}")
