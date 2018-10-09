import OVLFile
import OVL_COMPRESSED_DATA
from ByteIO import ByteIO

import sys


def escape_string(string: str):
    return string.replace('\\', '\\\\').replace('\r', '\\r').replace('\n', '\\n')


if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <path to OVL file>")
    print("Text will be extracted to a plain text file next to the OVL with .txt extension added")
    sys.exit(1)

ovl_path = sys.argv[1]
parsed_ovl = OVLFile.OVL(ovl_path)
parsed_ovl.read()
compressed = OVL_COMPRESSED_DATA.OVLCompressedData(parsed_ovl, parsed_ovl.static_archive)
compressed.read(ByteIO(byte_object=parsed_ovl.static_archive.uncompressed_data))
texts = compressed.get_localization_data()
with open(ovl_path + ".txt", 'w', encoding='utf-8') as out:
    for localization_entry in texts:
        out.write(localization_entry.name)
        if localization_entry.extra_int is not None:
            out.write('!')
            out.write(str(localization_entry.extra_int))
        out.write('=')
        out.write(escape_string(localization_entry.text))
        out.write('\n')
