import socket
from packet import packet
from encrypt import encrypt
import struct
import sys


class broadcast:
    username = ""
    password = ""
    serverAddr = ""
    port = 0
    streamid = 0
    socket = None
    authenticated = False
    connected = False
    XTEAKey = ""
    mimeType = ""
    negotiatedbuffersize = 0
    bitrate = 0
    IcyName = ""
    IcyGenre = ""
    IcyPub = False
    IcyUrl = ""
    incoming_buffer = bytearray(128)
    def __init__(self):
        pass


    # Initialize the broadcast class with the username, password, server address, port, and stream id
    # also creates a new socket and connects to the server
    # returns true if the connection was successful
    def bc(self, username, password, serverAddr, port, streamid):
        if len(username) > 8:
            username = username[:8]

        self.username = username
        self.password = password
        self.serverAddr = serverAddr
        self.port = port
        self.streamid = streamid

        # Create a new socket
        self.socket = socket.socket(type = socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.connect((self.serverAddr, self.port))

        return True

    # Then we need to tell the server we are a broadcaster of version 2.1
    # Then we need to serialize the packet and send it to the server
    # The packet is a cipher packet with the message flag 4105, which in hex is 0x1009
    # A detailed information of the flags can be found on the wiki page
    # http://wiki.winamp.com/wiki/SHOUTcast_2_(Ultravox_2.1)_Protocol_Details
    def authenticateStream(self):
        request_payload = "2.1".encode()
        cipher_packet = packet.serialize(4105, request_payload)
        # Send the packet
        self.socket.send(cipher_packet)
        response = self.receive_ack(self)
        # If the response is empty, then the server has closed the connection
        if response == "":
            self.authenticated = False
            self.connected = False
            return False
        # If the response is not empty, then the server has responded with the XTEA key
        self.XTEAKey = response[1].rstrip('\0')
        incoming_buffer = bytearray(128)
        # then we use that key to encrypt the username and password
        x = encrypt()
        XTeaEncryptedUsername = x.encrypt(self.username, self.XTEAKey).lower()
        XTeaEncryptedPassword = x.encrypt(self.password, self.XTEAKey).lower()

        # then we create the authentication string in the format of 2.1:streamid:username:password<NULL>
        authentication_string = "2.1" + ":" + str(self.streamid) + ":" + XTeaEncryptedUsername + ":" + XTeaEncryptedPassword + "\0"
        # then we encode the string to bytes and send it to the server with the message flag 4097 in hex 0x1001
        auth_bytes = authentication_string.encode()
        serialized_packet = packet.serialize(4097, auth_bytes)
        # Send the packet
        self.socket.send(serialized_packet)
        # then we wait for the server to respond with the message "Allow"
        # if the server responds with "Allow" then we are authenticated
        response = self.receive_ack(self)
        if response[2] == "Allow":
            self.authenticated = True
            self.connected = True
            return True

    # We need to send the server the message flag 4160 in hex 0x1040
    def SetMimeType(self, mimeType):
        self.mimeType = mimeType
        self.socket.send(packet.serialize(4160, mimeType.encode()))
        response = self.receive_ack(self)
        return True;

    # We need to send the server the message flag 4098 in hex 0x1002
    # The bitrate is in kbps so we need to multiply it by 1000
    # The format of the payload is average:maximum
    def setBitrate(self, average, maximum):
        bitratepayload = str(average * 1000) + ":" + str(maximum * 1000)
        self.socket.send(packet.serialize(4098, bitratepayload.encode()))

        try:
            response = self.receive_ack(self)
        except ex as Exception:
            return False
        self.bitrate = average
        return True

    # We negotiate the buffer size with the server if needed the server will respond with the negotiated buffer size
    # We need to send the server the message flag 4099 in hex 0x1003
    # The format of the payload is desired:minimum
    # The maximum buffer size is 16771 bytes
    def NegotiateBufferSize(self, desired_buffer_size, minimun_buffer_size):
        negotiation_payload = str(desired_buffer_size) + ":" + str(minimun_buffer_size)
        self.socket.send(packet.serialize(4099, negotiation_payload.encode()))
        negotiated_size = self.receive_ack(self)[1]
        self.negotiatedbuffersize = negotiated_size
        return True

    # We need to send the server the message flag 4101 in hex 0x1005
    # The format of the payload is desired:minimum
    def NegotiatePayloadSize(self, desired_payload_size, minimum_payload_size):
        negotiation_payload = str(desired_payload_size) + ":" + str(minimum_payload_size)
        self.socket.send(packet.serialize(4101, negotiation_payload.encode()))
        negotiated_size = self.receive_ack(self)[1]
        self.negotiatedbuffersize = negotiated_size
        return True


    # Then once we have negotiated the buffer size we need to send the server the message flag 4100 in hex 0x1004
    # Which means we are ready to start sending data
    # The payload is empty
    def Standby(self):
        self.socket.send(packet.serialize(4100, "".encode()))
        response = self.receive_ack(self)[1]
        if response == "Data transfer mode":
            self.connected = True
            return True
        return False

    # Then we can send the name, genre, url and public flag to the server
    def confIcyData(self, icyName, icyGenre, icyUrl, icyPub):
        self.confICYName(self,icyName)
        self.confICYGenre(self,icyGenre)
        self.confICYUrl(self,icyUrl)
        self.confICYPub(self,icyPub)
        return True

    def confICYName(self, icyName):
        self.IcyName = icyName
        self.socket.send(packet.serialize(4352, icyName.encode()))
        reponse = self.receive_ack(self)
        return True
    
    def confICYGenre(self, icyGenre):
        self.IcyGenre = icyGenre
        self.socket.send(packet.serialize(4353, icyGenre.encode()))
        response = self.receive_ack(self)
        return True
    
    def confICYUrl(self, IcyUrl):
        self.IcyUrl = IcyUrl
        self.socket.send(packet.serialize(4354, IcyUrl.encode()))
        response = self.receive_ack(self)
        return True

    def confICYPub(self, icyPub):
        self.IcyPub = icyPub
        if icyPub:
            self.socket.send(packet.serialize(4355, b'1'))
        else:
            self.socket.send(packet.serialize(4355, b'0'))
        response = self.receive_ack(self)
        return True

    # If we need to add an intro or a backup audio we can do that here by first sending the fileTransferBegin message
    # The flag for this message is 4176 in hex 0x1040
    # The payload is the type of file and the size of the file in bytes
    def fileTransferBegin(self, filesize, type):
        filetransferpayload = type + ":" + str(filesize)
        self.socket.send(packet.serialize(4176, filetransferpayload.encode()))
        response = self.receive_ack(self)
        return True

    # Then we can send the data to the server
    def fileTransferData(self, data):
        print("Sending Data")
        self.socket.send(packet.serialize(4177, data))

    # We can now send the audio as a byte array
    # The flag for this message is 28672 in hex 0x7000 for MP3
    # The flag for this message is 32772 in hex 0x8004 for Vorbis
    # The flag for this message is 36865 in hex 0x9001 for Headless Vorbis
    # The payload is the audio data in bytes
    # The maximum size of the payload is 16771 bytes
    def sendAudioData(self, data, type):
        if type == "MP3":
            self.socket.send(packet.serialize(28672, data))
        elif type == "Vorbis":
            self.socket.send(packet.serialize(32772,data))
        elif type == "Headless Vorbis":
            self.socket.send(packet.serialize(36865, data))
    
    # When we are ready to disconnect we can send the server the message flag 4101 in hex 0x1005
    # The payload is empty
    def broadcastDisconnect(self):
        self.socket.send(packet.serialize(4101, "".encode()))
        response = self.receive_ack(self)
        self.socket.close()
        return True

    # Receive the response from the server
    # the response is a 128 byte buffer
    # The first byte is the sync code 0x5A
    # The second byte is reserved
    # The third and fourth bytes are the flags
    # The fifth and sixth bytes are the length of the payload
    # The rest of the buffer is the payload
    # And then the server sends a null byte to terminate the message
    def receive_ack(self):
        self.socket.recv_into(self.incoming_buffer)

        flags = struct.unpack("<h", self.incoming_buffer[2:4])[0]
        response_length = struct.unpack("<h", self.incoming_buffer[4:6])[0]

        if sys.byteorder == "little":
            flags = struct.unpack("<h", self.incoming_buffer[2:4][::-1])[0]
            response_length = struct.unpack("<h", self.incoming_buffer[4:6][::-1])[0]


        response = self.incoming_buffer[6:6+response_length].decode("utf-8").rstrip('\0').split(':')

        # NAK Handling
        if response[0] == "NAK":
            reason = response[2] if response[1] == "2.1" else response[1]

            if reason == "Parse Error":
                raise Exception("There was a parse error in the request.")

            if reason == "Sequence Error":
                raise Exception("The sequence number was incorrect.")

            if reason == "Deny":
                if flags != MessageFlag.SetMimeType:
                    authenticated = False
                    self.broadcastDisconnect()
                    raise Exception("The username or password was incorrect.")

            if reason == "Version Error":
                raise Exception("The version of the protocol is not supported.")

            if reason == "Stream Moved":
                raise Exception("The stream has moved.")

            if reason == "Buffer Size Error":
                raise Exception("The buffer size is invalid.")

            if reason == "Bit Rate Error":
                raise Exception("The bit rate is invalid.")

            if reason == "Compatibility mode not enabled":
                raise Exception("The server does not support compatibility mode.")

            if reason == "Configuration Error":
                raise Exception("The configuration is invalid.")

            if reason == "Stream In Use":
                raise Exception("The stream is already in use.")

            raise Exception(response[2])

        # Clear the buffer
        self.incoming_buffer = bytearray(128)

        return response