# Platform-specific SFP transceiver interface for SONiC
#

try:
    import time
    from sonic_sfp.sfputilbase import SfpUtilBase
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


class SfpUtil(SfpUtilBase):
    """Platform-specific SfpUtil class"""

    PORT_START = 0
    PORT_END = 53
    PORTS_IN_BLOCK = 53
    QSFP_START = 48
    QSFP_END = 53

    _port_to_eeprom_mapping = {}

    @property
    def port_start(self):
        return self.PORT_START

    @property
    def port_end(self):
        return self.PORT_END

    @property
    def qsfp_ports(self):
        return list(range(self.QSFP_START, self.QSFP_END + 1))

    @property
    def port_to_eeprom_mapping(self):
        return self._port_to_eeprom_mapping

    def __init__(self):
        # Override port_to_eeprom_mapping for class initialization
        eeprom_path = '/sys/bus/i2c/devices/i2c-{0}/{0}-0050/eeprom'

        for x in range(self.PORT_START, self.PORT_END + 1):
            if self.port_start == 1:
                self.port_to_eeprom_mapping[x] = eeprom_path.format((x - 1) + 26)
            else:
                self.port_to_eeprom_mapping[x] = eeprom_path.format(x + 26)
        SfpUtilBase.__init__(self)

    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        try:
            reg_file = open("/sys/devices/platform/redstone_xp_cpld/port_presence", "r")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        content = reg_file.readline().rstrip()

        # content is a string containing the hex representation of the register
        reg_value = int(content, 16)

        # Determind if port_num start from 1 or 0
        if self.port_start == 1:
            bit_index = port_num - 1
        else:
            bit_index = port_num

        # Mask off the bit corresponding to our port
        mask = (1 << bit_index)

        # ModPrsL is active low
        if reg_value & mask == 0:
            return True

        return False

    def get_low_power_mode(self, port_num):
        # Check for invalid port_num
        if port_num not in self.qsfp_ports:
            return False

        try:
            reg_file = open("/sys/devices/platform/redstone_xp_cpld/qsfp_lpmode", "r")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        content = reg_file.readline().rstrip()

        # content is a string containing the hex representation of the register
        reg_value = int(content, 16)

        # Determind if port_num start from 1 or 0
        bit_index = port_num - 48

        # Mask off the bit corresponding to our port
        mask = (1 << bit_index)

        # LPMode is active high
        if reg_value & mask == 0:
            return False

        return True

    def set_low_power_mode(self, port_num, lpmode):
        # Check for invalid port_num
        if port_num not in self.qsfp_ports:
            return False

        try:
            reg_file = open("/sys/devices/platform/redstone_xp_cpld/qsfp_lpmode", "r+")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        content = reg_file.readline().rstrip()

        # content is a string containing the hex representation of the register
        reg_value = int(content, 16)

        # Determind if port_num start from 1 or 0
        bit_index = port_num - 48

        # Mask off the bit corresponding to our port
        mask = (1 << bit_index)

        # LPMode is active high; set or clear the bit accordingly
        if lpmode is True:
            reg_value = reg_value | mask
        else:
            reg_value = reg_value & ~mask

        # Convert our register value back to a hex string and write back
        content = hex(reg_value).strip('L')

        reg_file.seek(0)
        reg_file.write(content)
        reg_file.close()

        return True

    def reset(self, port_num):
        # Check for invalid port_num
        if port_num not in self.qsfp_ports:
            return False

        try:
            reg_file = open("/sys/devices/platform/redstone_xp_cpld/qsfp_reset", "r+")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        content = reg_file.readline().rstrip()

        # File content is a string containing the hex representation of the
        # register
        reg_value = int(content, 16)

        # Determind if port_num start from 1 or 0
        bit_index = port_num - 48

        # Mask off the bit corresponding to our port
        mask = (1 << bit_index)

        # ResetL is active low
        reg_value = reg_value & ~mask

        # Convert our register value back to a hex string and write back
        reg_file.seek(0)
        reg_file.write(hex(reg_value).rstrip('L'))
        reg_file.close()

        # Sleep 1 second to allow it to settle
        time.sleep(1)

        # Flip the bit back high and write back to the register to take port
        # out of reset
        try:
            reg_file = open("/sys/devices/platform/redstone_xp_cpld/qsfp_reset", "w")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = reg_value | mask
        reg_file.seek(0)
        reg_file.write(hex(reg_value).rstrip('L'))
        reg_file.close()

        return True

    def get_transceiver_change_event(self, timeout=0):
        raise NotImplementedError
