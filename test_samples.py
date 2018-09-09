#!/usr/bin/env python

import os
import json
import traceback
import unittest

import uefi_firmware
from uefi_firmware.utils import flatten_firmware_objects


class SamplesTest(unittest.TestCase):
    class Status(object):
        def __init__(self, code, firmware=None):
            self.code = code
            self.firmware = firmware

    def __init__(self, methodName='runTest'):
        # The types set bins various folder representing firmware types
        # to the expected 'detected' type from the parser code.
        with open('TYPES.json', 'r') as fh:
            self.TYPES = json.loads(fh.read())

        # The files set binds explicit file names to the number of ojects
        # detected. Modifications to the codebase should have expected changes
        # in the addition/removal of objects.
        with open('OBJECTS.json', 'r') as fh:
            self.OBJECTS = json.loads(fh.read())

        return super(SamplesTest, self).__init__(methodName)

    @staticmethod
    def get_files(dir):
        files = []
        for base, dirnames, filenames in os.walk(dir):
            for filename in filenames:
                files.append(os.path.join(base, filename).replace(os.path.sep, '/'))
        return files

    def _test_file(self, sample, type_name):
        with open(sample, "rb") as fh:
            sample_data = fh.read()
        parser = uefi_firmware.AutoParser(sample_data)
        if parser.type() is None:
            print("Cannot parse (%s): No matched type." % sample)
            return self.Status(1)
        if parser.type() != type_name:
            print("Problem parsing (%s): mismatched type " +
                "expected %s, got %s") % (sample, parser.type(), type_name)
            return self.Status(1)
        try:
            firmware = parser.parse()
        except Exception as e:
            # Wrap 'process' in exception handling for a pretty print.
            print("Exception parsing (%s): (%s)." % (sample, str(e)))
            return self.Status(1)

        # Check that 'process' does not encounter invalid formats/errors.
        if firmware is None:
            print("Error parsing (%s): failure in process." % (sample))
            return self.Status(1)

        # Attempt to iterate each of the nested/parsed objects.
        try:
            for _object in firmware.iterate_objects():
                pass
        except Exception as e:
            print("Exception iterating (%s): (%s)." % (sample, str(e)))
            print(traceback.print_exc())
            return self.Status(1)

        print("Parsing (%s): success" % (sample))
        return self.Status(0, firmware)

    def _test_items(self, sample, firmware):
        if sample not in self.OBJECTS:
            return self.Status(0)
        objects = firmware.iterate_objects()
        all_objects = flatten_firmware_objects(objects)
        num_objects = len(all_objects)
        self.assertEqual(num_objects, self.OBJECTS[sample],
            "Inconsistency parsing (%s): expected %d objects, found: %d\n" \
            "This 'may' be expected if this change improves the object " \
            "discovery/parsing logic.\n\n" % (sample, self.OBJECTS[sample], num_objects))
        print("Listing (%s): item count: %d" % (sample, num_objects))
        return self.Status(0)

    def test_with_samples(self):
        for type_name, samples_dir in self.TYPES.items():
            sample_files = self.get_files(samples_dir)
            for sample in sample_files:
                status = self._test_file(sample, type_name)
                self.assertEqual(status.code, 0)
                status = self._test_items(sample, status.firmware)
                self.assertEqual(status.code, 0)


if __name__ == "__main__":
    unittest.main()
