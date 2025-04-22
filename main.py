# udp_server.py
import socket
import struct
import time 
MESSAGE_IDX = 0

def hex_dump(data: bytes) -> str:
    return ' '.join(f'{b:02x}' for b in data)




def decode_data(data: bytes,s, addr) -> str:
    # we need to extract the first byte, and based on that we will 
    # find the type of the message
    global MESSAGE_IDX
    first_byte = data[0]
    type = "Unknown"

    # we send confirm back 
    if(first_byte != 0x00):
        x = bytes([0x00])
        ref_message_id = int.from_bytes(data[1:3], byteorder='big')
        packet = bytes([0x00]) + ref_message_id.to_bytes(2, byteorder='big')
        s.sendto(packet, addr)
        print(f"SERVER Sent CONFIRM to {addr}\n")

    match first_byte:
        case 0x00:
            type = "CONFIRM"
            message_id = int.from_bytes(data[1:3], byteorder='big')
            return f'CONFIRM | MESSAGEID: {message_id}'
        case 0x01:
            type = "REPLY"
            return type
        case 0x02:
            type = "AUTH"
            message_id = int.from_bytes(data[1:3], byteorder='big')
            #find the next null byte in data
            null_index = data.find(b'\x00', 3)
            name = (data[3:null_index]).decode('utf-8')
            #find the next null byte in data
            null_index_2 = data.find(b'\x00', null_index + 1)
            display_name = (data[null_index + 1 : null_index_2]).decode('utf-8')
            #skip next null byte and find secret
            secret = data[null_index_2 + 1 :].decode('utf-8')

            # SEND POSITIVE REPLY
            """
              1 byte       2 bytes       1 byte       2 bytes      
            +--------+--------+--------+--------+--------+--------+--------~~---------+---+
            |  0x01  |    MessageID    | Result |  Ref_MessageID  |  MessageContents  | 0 |
            +--------+--------+--------+--------+--------+--------+--------~~---------+---+
            """
            flag = 0x01
            m_id = struct.pack('!H', MESSAGE_IDX)
            MESSAGE_IDX += 1
            result = 0x01
            ref_message_id = struct.pack('!H', message_id)
            message_contents = b'OK'
            message = bytes([flag]) + m_id + bytes([result]) + ref_message_id + message_contents
            # send the message back
            s.sendto(message, addr)
            print(f"🚀SERVER Sent AUTH REPLY to {addr}\n")
            time.sleep(0.1)
            s.sendto(message, addr)
            print(f"🚀SERVER Sent AUTH REPLY to {addr} second time\n")
            return f'AUTH | USERNAME : {name} | DISPLAYNAME : {display_name} | SECRET : {secret}'
        case 0x03:
            type = "JOIN"
            message_id = int.from_bytes(data[1:3], byteorder='big')
            #find the next null byte in data
            null_index = data.find(b'\x00', 3)
            channel_name = (data[3:null_index]).decode('utf-8')
            #find the next null byte in data
            null_index_2 = data.find(b'\x00', null_index + 1)
            display_name = data[null_index + 1 : null_index_2].decode('utf-8')
            return f'JOIN | MESSAGEID : {message_id} | CHANNEL : {channel_name} | DISPLAYNAME : {display_name}'
        case 0x04:
            """
              1 byte       2 bytes      
            +--------+--------+--------+-------~~------+---+--------~~---------+---+
            |  0x04  |    MessageID    |  DisplayName  | 0 |  MessageContents  | 0 |
            +--------+--------+--------+-------~~------+---+--------~~---------+---+
            """



            type = "MSG"
            message_id = int.from_bytes(data[1:3], byteorder='big')
            #find the next null byte in data
            null_index = data.find(b'\x00', 3)
            channel_name = (data[3:null_index]).decode('utf-8')
            #find the next null byte in data
            null_index_2 = data.find(b'\x00', null_index + 1)
            display_name = data[null_index + 1 : null_index_2].decode('utf-8')
            #find the next null byte in data
            null_index_3 = data.find(b'\x00', null_index_2 + 1)
            message = data[null_index_2 + 1 : null_index_3].decode('utf-8')
            testing_seeing_message = 1
            if(testing_seeing_message == 1):
                new_mess_i = MESSAGE_IDX
                
                first_byte = bytes([0x04])
                mew_mess_two_bytes = new_mess_i.to_bytes(2, byteorder='big')
                packet = first_byte + mew_mess_two_bytes + display_name + bytes([0x00]) + message + b'\x00'
            return f'MSG | MESSAGEID : {message_id} | DISPLAYNAME : {display_name} | MESSAGE : {message}'
        case 0xFD:
            type = "PING"
            return type
        case 0xFE:
            type = "ERR"
            message_id = int.from_bytes(data[1:3], byteorder='big')
            #find the next null byte in data
            null_index = data.find(b'\x00', 3)
            display_name = (data[3:null_index]).decode('utf-8')
            #find the next null byte in data
            null_index_2 = data.find(b'\x00', null_index + 1)
            error_message = data[null_index + 1 : null_index_2].decode('utf-8')
            return f'ERR | MESSAGEID : {message_id} | DISPLAYNAME : {display_name} | ERROR : {error_message}'
        case 0xFF:
            type = "BYE"
            message_id = int.from_bytes(data[1:3], byteorder='big')
            #find the next null byte in data
            null_index = data.find(b'\x00', 3)
            display_name = (data[3:null_index]).decode('utf-8')
            return f'BYE | MESSAGEID : {message_id} | DISPLAYNAME : {display_name}'
        case _:
            type = "Unknown"
    

        




def runServer(host='127.0.0.1', port=54331):
   
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind((host, port))
        print(f"🚀 SERVER BOOTED | Listening on {host}:{port}\n")

        active_users = set()

        while True:
            try:
                data, addr = s.recvfrom(60001)
            except Exception as e:
                print(f"recvfrom() error: {e}")
                continue

            print(f"\nGot {len(data)} bytes from {addr}\n")
            if len(data) < 3:
                print("⚠️  Dropping—too short.\n")
                continue
            
            if addr not in active_users:
                active_users.add(addr)
                print(f"🆕  New client: {addr}\n")

            print(f"SERVER Sent CONFIRM to {addr}\n")
            text = decode_data(data, s, addr)
            print(f"🧾 RECIEVED: {text} \n\n")


if __name__ == "__main__":
    runServer()
