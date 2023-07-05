#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <sstream>
#include <iomanip>

std::string ToHexString(uint32_t value) {
    std::stringstream stream;
    stream << std::hex << std::setw(8) << std::setfill('0') << value;
    return stream.str();
}

/*
    This is a C++ implementation of the Tiny Encryption Algorithm (TEA) according to the
    specification in http://wiki.winamp.com/wiki/SHOUTcast_2_(Ultravox_2.1)_Protocol_Details
    This magic is written by copilot and chatGPT
    This code is derived from the C# implementation by chatGPT
    The code always encrypts for a little endian system
    The code can be found here: https://github.com/hqkirkland/Netshout
*/
std::string Encrypt(const std::string& InputString, const std::string& KeyString) {
    std::vector<uint8_t> DataStrBytes(InputString.begin(), InputString.end());
    std::vector<uint8_t> DataBytes;

    if (DataStrBytes.size() % 8 > 0) {
        DataBytes.resize(DataStrBytes.size() + (8 - (DataStrBytes.size() % 8)));
    }
    else {
        DataBytes.resize(DataStrBytes.size());
    }

    std::copy(DataStrBytes.begin(), DataStrBytes.end(), DataBytes.begin());

    std::vector<uint32_t> DataArray(DataBytes.size() / 4);

    for (size_t i = 0; i < DataArray.size(); i++) {
            std::reverse(DataBytes.begin() + i * 4, DataBytes.begin() + (i + 1) * 4);
        DataArray[i] = *reinterpret_cast<uint32_t*>(&DataBytes[i * 4]);
    }

    std::vector<uint8_t> KeyBytes(16);
    std::copy(KeyString.begin(), KeyString.end(), KeyBytes.begin());

    std::vector<uint32_t> KeyArray(4);

    for (int i = 0; i < 4; i++) {
            std::reverse(KeyBytes.begin() + i * 4, KeyBytes.begin() + (i + 1) * 4);
        KeyArray[i] = *reinterpret_cast<uint32_t*>(&KeyBytes[i * 4]);
    }

    uint32_t Y = DataArray[0];
    uint32_t Z = DataArray[1];

    uint32_t Sum = 0;
    uint32_t Delta = 0x9E3779B9;
    uint32_t N = 32;

    while (N-- > 0) {
        Y += (Z << 4 ^ Z >> 5) + Z ^ Sum + KeyArray[Sum & 3];
        Sum += Delta;
        Z += (Y << 4 ^ Y >> 5) + Y ^ Sum + KeyArray[Sum >> 11 & 3];
    }

    DataArray[0] = Y;
    DataArray[1] = Z;

    std::string Result = ToHexString(DataArray[0]) + ToHexString(DataArray[1]);

    if (DataBytes.size() > 8) {
        uint32_t A = DataArray[2];
        uint32_t B = DataArray[3];

        Sum = 0;
        N = 32;

        while (N-- > 0) {
            A += (B << 4 ^ B >> 5) + B ^ Sum + KeyArray[Sum & 3];
            Sum += Delta;
            B += (A << 4 ^ A >> 5) + A ^ Sum + KeyArray[Sum >> 11 & 3];
        }

        DataArray[2] = A;
        DataArray[3] = B;

        Result += ToHexString(DataArray[2]) + ToHexString(DataArray[3]);
    }

    return Result;
}

int main(int argc, char* argv[]) {
    std::string InputString = argv[1];
    std::string KeyString = argv[2];

    std::cout << Encrypt(InputString, KeyString) << std::endl;

    return 0;
}