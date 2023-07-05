import struct
import sys

class packet:

    def __init__(self):
        pass

    # serialize the flags and payload_data into a byte array of the ultravox message
    # The first and second bytes are always 0x5A and 0x00 which are sync and reserved
    # The third and fourth bytes are the flags
    # The fifth and sixth bytes are the length of the payload_data
    # The the rest of the bytes are the payload_data
    # The last byte is the null terminator
    def serialize(flags, payload_data):
        # initialize the ultravox_message
        ultravox_message = b'\x5A\x00\x00\x00\x00\x00'
        ultravox_message = bytearray(ultravox_message)

        # get the lenght of the payload_data
        length_bytes = struct.pack("<h", len(payload_data))

        # if the system is little endian, reverse the bytes of the length
        if sys.byteorder == "little":
            # reverse the bytes of the flags
            flag_bytes = struct.pack("<h", flags)[::-1]
            flags = struct.unpack("<h", flag_bytes)[0]

        # we append the flags to the third and fourth bytes of the ultravox_message
        ultravox_message[2:4] = flag_bytes

        # if the length of the payload_data is greater than 255, we append the length to the fifth and sixth bytes
        # else we append the length to the sixth byte
        if len(payload_data) > 255:
            ultravox_message[4:6] = length_bytes
        else:
            ultravox_message[5] = len(payload_data)

        # initialize the final_bytes
        final_bytes = bytearray((len(ultravox_message) + len(payload_data) + 1))

        # copy the contents of the ultravox_message into the final_bytes
        final_bytes[0:len(ultravox_message)] = ultravox_message
        # then copy the contents of the payload_data into the final_bytes
        final_bytes[len(ultravox_message):len(ultravox_message) + len(payload_data)] = payload_data
        # then add the null terminator
        final_bytes[len(ultravox_message) + len(payload_data)] = 0x00

        # then we reset the ultravox_message
        ultravox_message = bytearray([0x5A, 0x0, 0x0, 0x0, 0x0, 0x0])

        return final_bytes
