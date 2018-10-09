import OVLFile
import OVL_COMPRESSED_DATA
from ByteIO import ByteIO

import sys
import re


def unescape_sequence(matchobj):
    escape_char = matchobj.group(1)
    if escape_char == 'r':
        return '\r'
    elif escape_char == 'n':
        return '\n'
    else:
        assert escape_char == '\\'
        return '\\'


def unescape_string(string: str):
    return re.sub(r'\\(r|n|\\)', unescape_sequence, string)


if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <path to OVL file>")
    print("Text will be read from a plain text file next to the OVL with .txt extension added")
    sys.exit(1)

ovl_path = sys.argv[1]
localization_entries = []
with open(ovl_path + '.txt', 'r', encoding='utf-8') as textfile:
    for line in textfile:
        line = line.rstrip('\r\n')
        line = unescape_string(line)
        equals_index = line.index('=')
        localization_entry = OVL_COMPRESSED_DATA.LocalizationEntry()
        name = line[:equals_index]
        localization_entry.text = line[equals_index+1:]
        exclamation_index = name.rfind('!')
        if exclamation_index >= 0:
            localization_entry.name = name[:exclamation_index]
            localization_entry.extra_int = int(name[exclamation_index+1:])
        else:
            localization_entry.name = name
        localization_entries.append(localization_entry)
parsed_ovl = OVLFile.OVL(ovl_path)
parsed_ovl.read()
compressed = OVL_COMPRESSED_DATA.OVLCompressedData(parsed_ovl, parsed_ovl.static_archive)
compressed.read(ByteIO(byte_object=parsed_ovl.static_archive.uncompressed_data))
compressed.update_localization_data(localization_entries)
new_compressed_data = ByteIO()
compressed.write(new_compressed_data)
new_compressed_data.seek(0)
parsed_ovl.static_archive.uncompressed_data = new_compressed_data.read_bytes()
replaced_file = ByteIO(path=ovl_path, mode='w')
parsed_ovl.write(replaced_file)
replaced_file.close()