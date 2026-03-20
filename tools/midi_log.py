#!/usr/bin/env python3.13
"""Monitor SysEx debug messages from Spaluter over USB MIDI.

Usage:
    python3.13 tools/midi_log.py

Connect the disting NT via USB before running. The script will
auto-detect the device and print decoded log messages in real time.
Press Ctrl+C to stop.
"""

import mido
import sys

def find_disting():
    """Find the disting NT MIDI input port."""
    for name in mido.get_input_names():
        if 'disting' in name.lower() or 'expert' in name.lower():
            return name
    return None

def decode_sysex(data):
    """Decode our debug SysEx format: F0 7D <stage> <ascii...> F7"""
    if len(data) < 2 or data[0] != 0x7D:
        return None
    stage = data[1]
    msg = ''.join(chr(b) for b in data[2:] if 32 <= b < 127)
    return stage, msg

def main():
    port_name = find_disting()
    if not port_name:
        print("Available MIDI inputs:")
        for name in mido.get_input_names():
            print(f"  {name}")
        print("\nDisting NT not found. Connect via USB and retry.")
        print("Or specify port name as argument:")
        print("  python3.13 tools/midi_log.py 'Port Name'")
        if len(sys.argv) > 1:
            port_name = sys.argv[1]
        else:
            sys.exit(1)

    print(f"Listening on: {port_name}")
    print("Waiting for SysEx debug messages... (Ctrl+C to stop)\n")

    with mido.open_input(port_name) as port:
        for msg in port:
            if msg.type == 'sysex':
                result = decode_sysex(msg.data)
                if result:
                    stage, text = result
                    print(f"  STAGE {stage:2d}: {text}")
                else:
                    print(f"  SysEx: {bytes(msg.data).hex()}")
            # Also show any other MIDI for completeness
            elif msg.type not in ('clock', 'active_sensing'):
                print(f"  MIDI: {msg}")

if __name__ == '__main__':
    main()
