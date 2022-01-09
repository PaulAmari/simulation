#!/usr/bin/env python
# -*-coding:utf-8 -*-
'''Generate electrical netlist.cir file for SPICE simulation

TODO : create a class for device with add_instance and update methods
'''

import io           # To use TextIOWrapper text stream
import datetime     # To get current date and time

# Constants
_END_OF_LINE = '\n'
_ZFILL_WIDTH = 5


class NetList:
    """Electrical netlist class containing subcircuits and devices

    Parameters
    ----------
    filepath : str
        Complete file path where netlist is saved

    Attributes
    ----------
    filepath : str
        Complete file path where netlist is saved
    subcircuits : list of SubCircuit
        Subcircuits present in NetList
    devices : list
        Devices present in NetList
    __count_device_dict : dict
        Count of specific devices in NetList
    __count_device_total : int
        Total count of all devices in NetList
    """

    def __init__(self, filepath=''):
        """Constructor for NetList class

        Parameters
        ----------
        filepath : str, optional
            Complete file path where netlist is saved, by default ''
        """
        self.filepath = filepath
        self.subcircuits = []
        self.devices = []
        self.__count_device_dict = {
            'R': 0, 'C': 0, 'L': 0
        }
        self.__count_device_total = int(0)

    @property
    def count_device_dict(self):
        return self.__count_device_dict

    @property
    def count_device_total(self):
        return self.__count_device_total

    def get_subcircuit_names(self):
        return [subcircuit.name for subcircuit in self.subcircuits]

    def add_subcircuit(self, subcircuit):
        """Add a subcircuit to NetList and initialize subcircuit counter to 0

        Parameters
        ----------
        subcircuit : SubCircuit
            subcircuit is a netlist in a netlist which might be instantiate as a specific device like R, L, C

        Raises
        ------
        TypeError
            if subcircuit is not a SubCircuit
        """
        if isinstance(subcircuit, SubCircuit):
            self.subcircuits.append(subcircuit)
            self.__count_device_dict[subcircuit.name] = 0
        else:
            raise TypeError('subcircuit must be a SubCircuit')

    def rlc_instance(self, device: str, nodes: list, value: float):
        """Create new RLC device instance in NetList with specific nodes.

        Parameters
        ----------
        device : str
            Name of the device to insert, must be R, L or C
            R = Resistance, value in Ohm
            L = Inductance, value in Henry
            C = Capacitance, value in Farad
        nodes : list
            nodes of the RLC instance
        value : float
            value of the RLC instance

        Raises
        ------
        ValueError
            if device is not an RLC component
        """
        if device in ['R', 'L', 'C']:
            self.__count_device_total += 1         # Increment total counter
            self.__count_device_dict[device] += 1  # Increment rlc counter
            new_line = ('%s%d %s %.6e%s') % (
                device, self.__count_device_dict[device],
                ' '.join(nodes),
                value, _END_OF_LINE
            )
            self.devices.append(new_line)
        else:
            raise ValueError("device must be in ['R', 'L', 'C']")

    def subcircuit_instance(self, subcircuit, nodes: list):
        """Create new subcircuit instance in NetList with specific nodes.

        Parameters
        ----------
        subcircuit : SubCircuit

        nodes : list
            nodes of the subcircuit instance

        Raises
        ------
        ValueError
            if subcircuit is not available in the netlist
        TypeError
            if subcircuit is not a SubCircuit
        """
        # FIXME: fix isinstance check to match SubCircuit
        # if isinstance(subcircuit, SubCircuit):
        if subcircuit.name in self.get_subcircuit_names():
            # Increment total and specific device counter
            self.__count_device_total += 1
            self.__count_device_dict[subcircuit.name] += 1
            __subcircuit_number = str(
                self.__count_device_dict[subcircuit.name]).zfill(
                _ZFILL_WIDTH
            )
            new_line = ('X_%s_%s %s %s%s') % (
                subcircuit.suffix,
                __subcircuit_number,
                ' '.join(nodes),
                subcircuit.name,
                _END_OF_LINE
            )
            self.devices.append(new_line)
        else:
            raise ValueError(
                ('%s does not exist as a subcircuit') %
                (subcircuit.name)
            )
            print(
                'Tips : use add_subcircuit method to add a new subcircuit in the netlist.\n')
        # else:
        #     raise TypeError('subcircuit must be a SubCircuit')

    def _write_comment(self, f: io.TextIOWrapper, comment: str = ''):
        """Write comment in a file using text stream f

        Parameters
        ----------
        f : io.TextIOWrapper
            text stream where comment is written
        comment : str, optional
            comment to write in the file, by default ''

        Raises
        ------
        TypeError
            if f is not an io.TextIOWrapper
        """
        if len(comment):
            if isinstance(f, io.TextIOWrapper):
                comment_line = ('*** %s%s') % (comment, _END_OF_LINE)
                f.write(comment_line)
            else:
                raise TypeError('f must be an io.TextIOWrapper')

    def _write_header(self):
        """Write netlist file header with few comments in netlist file
        """
        with open(self.filepath, 'w') as f:
            self._write_comment(f, 'Generated for: SPICE')
            self._write_comment(f, 'By: simulation.spice python package')
            # Get current date and time
            __date_today = datetime.date.today().strftime("%d/%m/%Y")
            __time_now = datetime.datetime.now().strftime("%H:%M:%S")
            # Write current date and time
            self._write_comment(f, ('On: %s') % (__date_today))
            self._write_comment(f, ('At: %s') % (__time_now))
            self._write_comment(f, ' ')

    def _write_subcircuits(self):
        """Write subcircuits in netlist file
        """
        try:
            with open(self.filepath, 'a+') as f:
                print('subcircuits below will be written in the netlist :')
                print(self.get_subcircuit_names())
                self._write_comment(f, 'subcircuits')
                for subcircuit in self.subcircuits:
                    subcircuit._write_subcircuit(f)
        finally:
            print('subcircuits from netlist successfully written.\n')

    def _write_instances(self):
        """Write instances in netlist file
        """
        try:
            with open(self.filepath, 'a+') as f:
                comment = 'Instances'
                self._write_comment(f, comment)
                for device in self.devices:
                    f.write(device)
        finally:
            print('Instances from netlist successfully written.\n')

    def write_in_fpath(self):
        """Write header, subcircuits and instances in netlist file
        """
        self._write_header()
        self._write_subcircuits()
        self._write_instances()


class SubCircuit(NetList):
    """Child class inherited from NetList representing a subcircuit

    Parameters
    ----------
    NetList : NetList
        netlist containing subcircuits and devices

    Attributes
    ----------
    name : str, optional
        name of the subcircuit, by default ''
    external_nodes : list, optional
        external nodes of the subcircuit to connect with other devices, by default []
    suffix : str, optional
        suffix to use while instantiating the subcircuit, by default ''

    """

    def __init__(self, name: str = '', external_nodes=[],
                 suffix: str = '', comment: str = ''):
        """Constructor of SubCircuit class

        Initiate subcircuit using super class constructor and parameters.

        Parameters
        ----------
        name : str, optional
            name of the subcircuit, by default ''
        external_nodes : list, optional
            external nodes of the subcircuit to connect with other devices, by default []
        suffix : str, optional
            suffix to use while instantiating the subcircuit, by default ''
        comment : str, optional
            comment about the subcircuit will be written in netlist, by default ''
        """
        super().__init__()
        self.name = name
        self.ext_nodes = external_nodes
        self.suffix = suffix
        self.comment = comment
        self._update_start_line()
        self._update_end_line()

    def _update_start_line(self):
        """Update starting line in SPICE format based on subcircuit attributes
        """
        self.start_line = ('.SUBCIRCUIT %s %s%s') % (
            self.name, ' '.join(self.ext_nodes), _END_OF_LINE)

    def _update_end_line(self):
        """Update ending line in SPICE format based on subcircuit attributes
        """
        self.end_line = ('.ENDS %s%s') % (self.name, _END_OF_LINE)

    def load_from_file(
            self, subcircuit_filepath, external_nodes: list = [],
            name: str = '', suffix: str = ''):
        """ Load subcircuit from subcircuit_filepath .cir file

        Parameters
        ----------
        subcircuit_filepath : str
            subcircuit filepath to load from
        external_nodes : list, optional
            external nodes of the subcircuit, by default []
        name : str, optional
            name of the sub circuit, by default ''
        suffix : str, optional
            suffix to use while instantiating the subcircuit
        """
        # Update SubCircuit attributes based on parameters
        self.subcircuit_filepath = subcircuit_filepath
        self.ext_nodes = external_nodes
        self.name = name
        self.suffix = suffix
        # Read the file and updates subcircuit accordingly
        with open(subcircuit_filepath, 'r') as f:
            # Read first line
            line = f.readline()
            split_line = line.split()
            k = 0
            # If name is empty, update name, starting and ending line based on first line of the file
            if not name:
                self.name = split_line[1]
                self._update_start_line()
                self._update_end_line()
            # If ext_nodes is empty update it based on first line of the file
            if not self.ext_nodes:
                self.ext_nodes = split_line[2:]
            print(('subcircuit %s will be loaded from file to the netlist.')
                  % (self.name))
            # Retrieve information line by line and update instances
            while line:
                k += 1
                line = f.readline()
                split_line = line.split()
                first_char = split_line[0][0]
                # Check first character to identify device
                if first_char in ['R', 'L', 'C']:
                    value = float(split_line[-1])
                    self.rlc_instance(first_char, split_line[1:-1], value)
                elif first_char == 'X':
                    self.subcircuit_instance(split_line[-1], split_line[1:-1])
                elif first_char in ['.']:
                    if split_line[0] == '.ENDS':
                        print('New subcircuit .\n')
                        break
                else:
                    print(('Line %d : Unidentified component.') % (k))

    def _write_subcircuit(self, f: io.TextIOWrapper):
        """Write subcircuit and nested subcircuit using text stream f

        Parameters
        ----------
        f : io.TextIOWrapper
            text stream where subcircuit is written

        Raises
        ------
        ValueError
            if text stream f is closed
        TypeError
            if f is not an 
        """
        if isinstance(f, io.TextIOWrapper):
            if f.closed:
                raise ValueError('Write operation on closed file.')
            else:
                self._update_start_line()
                self._update_end_line()
                lines = ''.join(self.devices)
                # Write subcircuit in file using text stream f
                self._write_comment(f, self.comment)
                f.write(self.start_line)
                f.write(lines)
                # Write subcircuits nested in subcircuit
                for subcircuit in self.subcircuits:
                    self._write_comment(f, ' ')
                    self._write_comment(f, 'Inner subcircuit')
                    if hasattr(subcircuit, 'subcircuit_filepath'):
                        self._write_comment(
                            f, ('subcircuit loaded from : %s') %
                            (subcircuit.subcircuit_filepath)
                        )
                    subcircuit._write_subcircuit(f)
                f.write(self.end_line)
        else:
            raise TypeError('f must be an io.TextIOWrapper')
