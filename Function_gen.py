import pyvisa


def scan_visa(backend: str = "@py"):
    rm = pyvisa.ResourceManager(backend)  # '@py' for pyvisa-py backend
    # rm = pyvisa.ResourceManager()
    try:
        resources = rm.list_resources()
        if resources:
            print("Available VISA resources:")
        for resource in resources:
            print(resource)
        if not resources:
            print("No VISA resources available.")
    except Exception as e:
        print(f"Error listing resources: {e}")
    finally:
        rm.close()


def test_func_gen_connection():
    resource_manager = pyvisa.ResourceManager('@py')
    instrument_address = 'USB0::2391::9479::MY52102525::0::INSTR'  # Replace with your actual address

    try:
        instrument = resource_manager.open_resource(instrument_address)
        print(f"Successfully connected to: {instrument.resource_name}")

        # Query the instrument's identification
        identification = instrument.query('*IDN?')
        print(f"Instrument identification: {identification.strip()}")

        # You can now send other commands to control the instrument
        # For example, to set the output to a sine wave at 1 kHz with 1 Vpp:
        instrument.write('SOUR1:FUNC SIN')
        instrument.write('SOUR1:FREQ 1000')
        instrument.write('SOUR1:VOLT 1VP')
        instrument.write('OUTP1 ON')

    except pyvisa.VisaIOError as e:
        print(f"Error communicating with the instrument: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'instrument' in locals() and instrument.is_open:
            instrument.close()
            resource_manager.close()
            print("Instrument connection closed.")
        elif 'resource_manager' in locals():
            resource_manager.close()


class Device:
    """Class to hold device info
    USB0::2391::9479::MY52102525::0::INSTR"""
    def __init__(self, ResourceName: str):
        parts = ResourceName.split('::')
        if len(parts) == 5 or len(parts) == 6:
            self.Protocol = parts[0]
            try:
                self.VendorID = int(parts[1])
                self.ProductID = int(parts[2])
                self.SN = parts[3]
                self.InterfaceID = int(parts[4]) if len(parts) == 6 else 0
            except ValueError:
                print(f"Error: Could not parse numeric IDs from '{ResourceName}'")
                self.VendorID = None
                self.ProductID = None
                self.InterfaceID = None
        else:
            print(f"Error: Invalid resource name format: '{ResourceName}'")
            self.Protocol = None
            self.VendorID = None
            self.ProductID = None
            self.SN = None
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
        return f"{self.Protocol} Device: VendorID=0x{self.VendorID:04X}, ProductID=0x{self.ProductID:04X}, SN='{self.SN}'"

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


# class WaveformGenerator_33500B:
#     def __init__(self, ):
#
#
# test_func_gen_connection()

device = Device()
