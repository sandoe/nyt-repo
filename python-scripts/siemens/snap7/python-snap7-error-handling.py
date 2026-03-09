# Velkommen til denne video
# I denne video vil vi lave simpel error  handling ved brug af try, except og finally

import snap7
from snap7.util import get_bool, get_int, get_real, set_bool, set_int, set_real

plc_ip = "192.168.154.12"
rack = 0
slot = 1

try:
    client = snap7.client.Client()
    client.connect(plc_ip,rack,slot)

    db_number = 1
    bool_offset = 0
    bool_size = 1
    int_offset = 2
    int_size = 2
    real_offset = 4
    real_size = 4

    my_bool = client.db_read(db_number,bool_offset,bool_size)
    set_bool(my_bool,bool_offset,0,False)
    client.db_write(db_number,bool_offset,my_bool)
    my_bool = client.db_read(db_number,bool_offset,bool_size)
    dbx00 = get_bool(my_bool,0,0) # svare til dbx 0.0 i jeres [DB1] see i TIA Portal
    print(dbx00)

    my_int = client.db_read(db_number,int_offset,int_size)
    set_int(my_int,0,20)
    client.db_write(db_number,int_offset,my_int)
    my_int = client.db_read(db_number,int_offset,int_size)
    dbx20 = get_int(my_int,0)
    print(dbx20)

    my_real = client.db_read(db_number,real_offset,real_size)
    set_real(my_real,0,111.2)
    client.db_write(db_number,real_offset,my_real)
    my_real = client.db_read(db_number,real_offset,real_size)
    dbx40 = get_real(my_real,0)
    print(round(dbx40,2)) # her kan vi bruge round(variabel,2)
    print("Everything went fine")
except:
    print("Couldn't connect to plc")
finally:
    client.disconnect() # skal i ALTID huske
    client.destroy() 
    print("We have disconnected from plc and destroyed the object client") # Tak fordi i så med
