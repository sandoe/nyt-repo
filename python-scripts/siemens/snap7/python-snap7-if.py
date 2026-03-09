# Velkommen til denne video hvor vi vil forbinde til en siemens plc og bruge if sætning
import snap7
from snap7.util import get_bool,get_int,set_int

PLC_IP = "192.168.154.120"
RACK = 0
SLOT = 1

client = snap7.client.Client()
client.connect(PLC_IP,RACK,SLOT)

# ====== db opsætning ============
DB_NUMBER = 1
BOOL_OFFSET = 0
BOOL_SIZE = 1

INT_OFFSET = 2
INT_SIZE = 2

# ====== reading inputs ==========
raw_bool = client.db_read(DB_NUMBER,BOOL_OFFSET,BOOL_SIZE)
raw_int = client.db_read(DB_NUMBER,INT_OFFSET,INT_SIZE)
my_bool = get_bool(raw_bool,0,0)
my_int = get_int(raw_int,0)

# ====== IF statement ============
if my_bool == False:
    set_int(raw_int,0,35)
    client.db_write(DB_NUMBER,0,raw_int)
    raw_int = client.db_read(DB_NUMBER,INT_OFFSET,INT_SIZE)
    my_int = get_int(raw_int,0)
    print("my_int = ",my_int)
else:
    set_int(raw_int,0,88)
    client.db_write(DB_NUMBER,0,raw_int)
    raw_int = client.db_read(DB_NUMBER,INT_OFFSET,INT_SIZE)
    my_int = get_int(raw_int,0)
    print("my_int = ",my_int)

# ====== disconnection ===========
client.disconnect()
client.destroy()