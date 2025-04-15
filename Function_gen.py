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

    def set(self, protocol: str, vendor_id: int, product_id: int, sn: str, interface_id: int = 0):
        self.Protocol: str = protocol
        self.VendorID: int = vendor_id
        self.ProductID: int = product_id
        self.SN: str = sn
        self.InterfaceID: int = interface_id

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

    # def __eq__(self, other):
    #     if not isinstance(other, Device):
    #         return NotImplemented
    #     return (self.Protocol == other.Protocol and
    #             self.VendorID == other.VendorID and
    #             self.ProductID == other.ProductID and
    #             self.SN == other.SN and
    #             self.InterfaceID == other.InterfaceID)

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
        logging.debug(f'Sending "{msg}"')

    def query(self, msg: str) -> str:
        if not self.instrument:
            raise ValueError("Instrument is not connected.")
        logging.debug(f'Sending "{msg}"')
        answer = str(self.instrument.query(msg))
        logging.debug(f'Answer: "{answer.strip()}"')
        return answer


class Function_Gen:
    """Responsible for tracking the state of the function generator"""

    def __init__(self, visa_instance: VISA_Connection, vpp: float, offset: float, pulse_width: float):
        self.visa = visa_instance
        self.output: bool
        self._set_outp(False, soft=False)
        #  Frequency
        self.freq: int = 1000
        self.configure_freq(self.freq)
        #  Voltage
        self.volt: float = vpp
        self.configure_vpp(self.volt)
        #  Pulse width
        self.width = pulse_width
        self.configure_pulse_width(self.width)
        #  Offset
        self.offset: float = offset
        self.configure_offset(self.offset)

        self.freq = int(float(self.visa.query("SOUR1:FREQ?")))
        print(self.freq)

    def configure_vpp(self, vpp: float):
        self.visa.write(f"VOLT {vpp}")

    def configure_offset(self, offset: float):
        self.visa.write(f"VOLT:OFFS {offset}")

    def configure_pulse_width(self, pulse_width: float):
        # self.visa.write(f"FUNC:PULS:WIDT {pulse_width:.3e}")
        self.visa.write(f"FUNC:PULS:WIDT {pulse_width}")

    def configure_freq(self, freq:int):
        self.visa.write(f'SOUR1:FREQ {freq}')
        self.freq = freq
        # self.visa.write(f'SOUR1:FREQ {freq:.3e}')

    def play_tone(self, freq: int, duration: float, stop: bool = True, wait: bool = True,
                  soft_stop: bool = True) -> None:
        """Sends VISA SCPI commands to the Function Generator, to produce a tone.

        :param soft_stop: Should the output be shut down with a relay click, or just brought to 0v quietly?
        :type soft_stop:
        :param freq: Tone, in Hz
        :type freq:
        :param duration: Duration, in seconds
        :type duration:
        :param stop: Should the tone be stopped at the end of the duration? (Obsolete without wait)
        :type stop:
        :param wait: Should the function wait the duration period or exit immediately? (Fire & Forget)
        :type wait:
        """
        # self.visa.write(f"SOUR1:FREQ {freq}")
        self.configure_freq(freq)
        self._set_outp(True)
        logging.debug(f"Setting freq to {freq}.")
        if wait:
            sleep(duration)
            if stop:
                self._set_outp(False, soft=soft_stop)

    def _set_outp(self, output: bool, soft: bool = True):
        if soft:
            # outp_v_msg = str(self.volt) if output else "0.1"
            # outp_o_msg = str(self.offset) if output else "0"
            # self.visa.write(f"VOLT {outp_v_msg}")
            # self.visa.write(f"VOLT:OFFS {outp_o_msg}")
            outp_f_msg = str(self.freq) if output else "1"
            self.visa.write(f'SOUR1:FREQ {outp_f_msg}')
            self.visa.write("OUTP1 ON")
        else:
            outp_msg = "ON" if output else "OFF"
            self.visa.write(f"OUTP1 {outp_msg}")
        self.output = output

    def stop(self):
        self._set_outp(False, soft=False)


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
                fg = Function_Gen(visa_instance=VISA, offset=1.15, vpp=2.3, pulse_width=186e-6)
                fg.play_tone(500, 0.2, stop=False)
                fg.play_tone(800, 0.8, soft_stop=False)
                fg.stop()
        except Exception as e:
            print(f"An error occurred during the main execution: {e}")
    else:
        logging.warning("No devices matching the filter...")
        devices = scan_visa()
        if devices:
            logging.info(f"Available devices ({len(devices)}):")
            for device in devices:
                logging.info(f"{device}")
        else:
            print("No available devices found")
