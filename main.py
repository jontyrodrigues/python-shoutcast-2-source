from broadcast import broadcast
import time
import threading
from mutagen.mp3 import MP3
import pyaudio
from pydub import AudioSegment
import io
import subprocess
import os
import wave



def main():
    b = broadcast
    stream_from_file = False
    # the username can be anything in case of a stream
    # the password is the password of the stream
    # the ip is the ip of the server
    # the port is the port of the server
    # the stream id is the id of the stream
    b.bc(b, "username", "password", "192.168.0.1", 8000, 1)
    b.authenticateStream(b)
    if(b.authenticated):
        print("Authenticated")
    else:
        return False
    b.SetMimeType(b, "audio/mpeg")
    if b.setBitrate(b, 128, 128):
        print("Bitrate set")
    else:
        print("Bitrate not set")
        return False
    b.NegotiateBufferSize(b, 1, 2)
    # b.NegotiatePayloadSize(b, 16377, 16377)
    b.confIcyData(b, "Test", "Test", "http://shoutcast.com/stream", True)

    b.Standby(b)

    if b.connected:
        print("Connected")
    else:
        return False

    # we open the audio file
    audio_file = open("audio.mp3", "rb")
    # we read the audio file as bytes
    audio_bytes = audio_file.read()
    # we close the audio file
    audio_file.close()
    # we get the duration of the audio file
    audio = MP3("crowd.mp3")
    duration = audio.info.length
    # we calculate the bitrate of the audio file
    bitrate = len(audio_bytes) / duration * 8
    # the chunk size is the number of bytes to send to the server
    chunk_size = 25
    # we calculate the target chunk duration ie the time it takes to send the chunk to the server
    target_chunk_duration = chunk_size * 8 / (bitrate * 1000)

        # we start the timer
    start_time = time.time()
    elapsed_time = 0
        
    try:
        # Then in a loop we send the audio data
        while True:
            print("Sending audio data")
            bytesSent = 0
            # we send the audio data in chunks of n bytes defined by chunk_size
            for i in range(0, len(audio_bytes), chunk_size):
                # this is the actual sending of the audio data via the broadcast class
                b.sendAudioData(b, audio_bytes[i:i+chunk_size], "MP3")
                # then we calculate the elapsed time
                elapsed_time = time.time() - start_time
                # then we calculate the target time ie the time it should take to send the chunk
                target_time = i * target_chunk_duration
                # then we calculate the sleep time ie the time to sleep to send the chunk in the target time
                sleep_time = target_time - elapsed_time

                # if the sleep time is negative we don't sleep
                if sleep_time > 0:
                    time.sleep(sleep_time)

            # Calculate the remaining time to sleep at the end
            total_duration = len(audio_bytes) * target_chunk_duration
            remaining_sleep_time = total_duration - elapsed_time

            # if the remaining sleep time is negative we don't sleep
            if remaining_sleep_time > 0:
                time.sleep(remaining_sleep_time)
    # if the user presses ctrl+c we disconnect
    except KeyboardInterrupt:
        print("Disconnecting")
        b.broadcastDisconnect(b)
        print("Disconnected")
            

if __name__ == "__main__":
    main()
