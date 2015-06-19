#!/usr/bin/env python
# Copyright (C) 2015 Swift Navigation Inc.
# Contact: Colin Beighley <colin@swift-nav.com>
#
# This source is subject to the license found in the file 'LICENSE' which must
# be be distributed together with this source. All other rights reserved.
#
# THIS CODE AND INFORMATION IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND,
# EITHER EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND/OR FITNESS FOR A PARTICULAR PURPOSE.

import serial_link
import time
import struct
import yaml

from sbp.client.handler import *
from sbp.settings       import *
from sbp.msg            import *
from sbp.logging        import SBP_MSG_PRINT

DIAGNOSTICS_FILENAME = "diagnostics.yaml"

class Diagnostics(object):
  """
  Diagnostics

  The :class:`Diagnostics` class collects devices diagnostics.
  """
  def __init__(self, link):
    self.diagnostics = {}
    self.diagnostics['settings'] = {}
    self.settings_received = False
    self.link = link
    self.link.add_callback(self._read_callback, SBP_MSG_SETTINGS_READ_BY_INDEX)
    self.link.send_msg(MsgSettingsReadByIndex(index=0))
    while not self.settings_received:
      time.sleep(0.1)

  def _read_callback(self, sbp_msg):
    if not sbp_msg.payload:
      self.settings_received = True
    else:
      section, setting, value, format_type = sbp_msg.payload[2:].split('\0')[:4]
      if not self.diagnostics['settings'].has_key(section):
        self.diagnostics['settings'][section] = {}
      self.diagnostics['settings'][section][setting] = value

      index = struct.unpack('<H', sbp_msg.payload[:2])[0]
      self.link.send_msg(MsgSettingsReadByIndex(index=index+1))

def get_args():
  """
  Get and parse arguments.
  """
  import argparse
  parser = argparse.ArgumentParser(description='Acquisition Monitor')
  parser.add_argument("-f", "--ftdi",
                      help="use pylibftdi instead of pyserial.",
                      action="store_true")
  parser.add_argument('-p', '--port',
                      default=[serial_link.SERIAL_PORT], nargs=1,
                      help='specify the serial port to use.')
  parser.add_argument("-b", "--baud",
                      default=[serial_link.SERIAL_BAUD], nargs=1,
                      help="specify the baud rate to use.")
  parser.add_argument("-o", "--diagnostics-filename",
                      default=[DIAGNOSTICS_FILENAME], nargs=1,
                      help="file to write diagnostics to.")
  return parser.parse_args()

def main():
  """
  Get configuration, get driver, and build handler and start it.
  """
  args = get_args()
  port = args.port[0]
  baud = args.baud[0]
  diagnostics_filename = args.diagnostics_filename[0]
  # Driver with context
  with serial_link.get_driver(args.ftdi, port, baud) as driver:
    with Handler(driver.read, driver.write) as link:
      diagnostics = Diagnostics(link).diagnostics
      with open(diagnostics_filename, 'w') as diagnostics_file:
        yaml.dump(diagnostics, diagnostics_file, default_flow_style=False)

if __name__ == "__main__":
  main()
