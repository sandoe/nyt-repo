# Velkommen til denne video
# I denne video vil vi oprette forbindelse mellem siemens plc og snap7
# opsætning af plc vil blive gennemgået i klassen samt forklaringer dette er mere for at se hvordan man gør

import snap7
from snap7.util import get_bool, get_int, get_real

plc_ip = "192.168.154.1"#"192.168.154.120"
rack = 0
slot = 1
port = 1102
client = snap7.client.Client()
client.connect(plc_ip,rack,slot,port)
print("Connected to PLC",client.get_cpu_info())

#db_number = 1
#bool_offset = 0
#bool_size = 1
#int_offset = 2
#int_size = 2
#real_offset = 4
#real_size = 4
#
#my_bool = client.db_read(db_number,bool_offset,bool_size)
#dbx00 = get_bool(my_bool,0,0) # svare til dbx 0.0 i jeres [DB1] see i TIA Portal
#print(dbx00)
#
#my_int = client.db_read(db_number,int_offset,int_size)
#dbx20 = get_int(my_int,0)
#print(dbx20)
#
#my_real = client.db_read(db_number,real_offset,real_size)
#dbx40 = get_real(my_real,0)
#print(round(dbx40,2)) # her kan vi bruge round(variabel,2)
#
client.disconnect() # skal i ALTID huske
client.destroy() # tak fordi i så med
