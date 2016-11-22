#! /usr/bin/python

import struct
import sys

import amfast
import json

from amfast.decoder import Decoder
from amfast.encoder import Encoder

#sys.argv.append('/home/tyler/GlitchPacketLogs/MoveStreet')
fileName = sys.argv[1]
outName = fileName + "_parsed"
headerLen = 66

inFile = open(fileName, 'r')
outFile = open(outName, 'w')

mainHeader = inFile.read(24)

partialPacketBuffer = ''
targetLen = 0
midPacket = False
packetCount = 0

while True:
    packetHeader = inFile.read(16)
    if len(packetHeader) < 16:
        break
    
    parsedHeader = struct.unpack('IIII', packetHeader)
    
    packetLength = parsedHeader[2]
    packet = inFile.read(packetLength)
    packet = packet[66:]
    if targetLen == 0:
        targetLen = len(packet)
    if ord(packet[0]) == 0 and len(partialPacketBuffer) == 0:
        targetLen = struct.unpack('>I', packet[:4])[0]
        packet = packet[4:]
    partialPacketBuffer += packet
    while True:
        if len(partialPacketBuffer) < targetLen:
            break
        elif len(partialPacketBuffer) == targetLen:
            packetToParse = partialPacketBuffer
            decoder = Decoder(amf3 = True)
            data = decoder.decode(packetToParse)
            if data == None:
                print("Null!")
            outFile.write('Length = ' + str(len(packetToParse)) + '\n' + json.dumps(data, indent=3) + '\n\n')
            packetCount += 1
            targetLen = 0
            partialPacketBuffer = ''
            break
        elif len(partialPacketBuffer) > targetLen:
            packet = partialPacketBuffer[:targetLen]
            partialPacketBuffer = partialPacketBuffer[targetLen:]
            decoder = Decoder(amf3 = True)
            data = decoder.decode(packet)
            if data == None:
                print("Null!")
            outFile.write('Length = ' + str(len(packetToParse)) + '\n' + json.dumps(data, indent=3) + '\n\n')
            packetCount += 1
            if ord(partialPacketBuffer[0]) == 0:
                targetLen = struct.unpack('>I', partialPacketBuffer[:4])[0]
                partialPacketBuffer = partialPacketBuffer[4:]
            else:
                matchCount = 0
                counter = 0
                for ch in partialPacketBuffer:
                    if matchCount == 0 and ord(ch) == 10:
                        matchCount += 1
                    elif matchCount == 1 and ord(ch) == 11:
                        matchCount += 1
                    elif matchCount == 2 and ord(ch) == 1:
                        targetLen = counter
                        break
                    else:
                        matchCount = 0
                    counter += 1
outFile.close()
inFile.close()
print("Parsed " + str(packetCount) + " packets.")
