class Msg:
    def __init__(self, magic_cookie, msg_type):
        self.magic_cookie = magic_cookie
        self.msg_type = msg_type
        # self.msg = msg

    def __str__(self):
        return "Msg: magic_cookie=%d, msg_type=%d, msg=%s" % (self.magic_cookie, self.msg_type, self.msg)
    
    def encode(self, msg):
        arr = bytearray()
        arr.extend(self.magic_cookie.to_bytes(4, 'big'))
        arr.extend(self.msg_type.to_bytes(1, 'big'))
        arr.extend(msg)
        return arr
    
    # decode the message from the given data
    def decode(self, data):
        # error checking
        if len(data) < 5:
            raise Exception("Invalid message length")

        self.magic_cookie = int.from_bytes(data[:4], 'big')
        self.msg_type = int.from_bytes(data[4:5], 'big')
        self.msg = data[5:]
        return self
    
offerMsgCookie = 0xabcddcba
offerMsgType = 0x2
class OfferMsg(Msg):
    def __init__(self):
        super().__init__(offerMsgCookie, offerMsgType)

    def encode(self, serverUDPPort, serverTCPPort):
        # error checking
        # TODO: check if port is valid
        if serverUDPPort < 0 or serverTCPPort < 0:
            raise Exception("Invalid port number")
        
        self.serverUDPPort = serverUDPPort
        self.serverTCPPort = serverTCPPort
        arr = bytearray()
        arr.extend(serverUDPPort.to_bytes(2, 'big'))
        arr.extend(serverTCPPort.to_bytes(2, 'big'))
        return super().encode(arr)

    # decode the message from the given data
    def decode(self, data):
        # error checking
        if len(data) < 4:
            raise Exception("Invalid message length")

        self = super().decode(data)
        self.serverUDPPort = int.from_bytes(self.msg[:2], 'big')
        self.serverTCPPort = int.from_bytes(self.msg[2:4], 'big')

        # TODO: check if ports are valid

        return self

requestMsgCookie = 0xabcddcba
requestMsgType = 0x3
class RequestMsg(Msg):
    def __init__(self):
        super().__init__(requestMsgCookie, requestMsgType)

    def encode(self, fileSize):
        # error checking
        if fileSize < 0:
            raise Exception("Invalid file size")
        
        self.fileSize = fileSize

        arr = bytearray()
        arr.extend(self.fileSize.to_bytes(8, 'big'))
        return super().encode(arr)
    
    def decode(self, data):
        # error checking
        if len(data) < 8:
            raise Exception("Invalid message length")

        self = super().decode(data)
        self.fileSize = int.from_bytes(self.msg, 'big')
        return self

payloadMsgCookie = 0xabcddcba
payloadMsgType = 0x4
class PayloadMsg(Msg):
    def __init__(self):
        super().__init__(payloadMsgCookie, payloadMsgType)

    def encode(self, totalSegmentCount, currentSegmentCount, payload):
        # error checking
        if totalSegmentCount < 0 or currentSegmentCount < 0 or currentSegmentCount > totalSegmentCount:
            raise Exception("Invalid segment count")
        if len(payload) < 0:
            raise Exception("Invalid payload")

        self.totalSegmentCount = totalSegmentCount
        self.currentSegmentCount = currentSegmentCount
        self.payload = payload

        arr = bytearray()
        arr.extend(totalSegmentCount.to_bytes(8, 'big'))
        arr.extend(currentSegmentCount.to_bytes(8, 'big'))
        payload_len = len(payload)  # make sure payload is an array of bytes
        arr.extend(payload)
        return super().encode(arr)

    def decode(self, data):
        # error checking
        if len(data) < 16:
            raise Exception("Invalid message length")

        self = super().decode(data)
        self.totalSegmentCount = int.from_bytes(self.msg[:8], 'big')
        self.currentSegmentCount = int.from_bytes(self.msg[8:16], 'big')
        self.payload = self.msg[16:]
        return self