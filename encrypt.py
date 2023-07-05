import struct
import sys
import ctypes
import os
import subprocess

class encrypt:
    @staticmethod
    # we take the input string and the key string and pass it to the encrypt.exe file
    # or the encrypt file depending on the platform
    # we then return the encrypted string
    def encrypt(input_string, key_string):
        if sys.platform == "win32":
            result = subprocess.run(["encrypt.exe", input_string, key_string], capture_output=True, text=True)
        elif sys.platform == "linux":
            result = subprocess.run(["./encrypt", input_string, key_string], capture_output=True, text=True)

        encrypted_string = result.stdout.strip()
        result = encrypted_string
        return result