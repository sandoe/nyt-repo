import snap7
from snap7.util import get_bool, set_bool, get_int, get_real
from snap7.type import Area
import time
import sys
from datetime import datetime

# =================== PLC Konfiguration =================
PLC_IP = '192.168.154.1'  # Erstat med din PLC's IP-adresse
RACK = 0
SLOT = 1

AREA_IN = snap7.Area.PE
AREA_OUT = snap7.Area.PA

first_scan = True
# =================== Opret forbindelse =================

try:
    client = snap7.client.Client()
    client.connect(PLC_IP, RACK, SLOT) # husk tcp_port hvis i bruger server.py
    print("Forbindelse oprettet.")
except Exception as e:
    print("Fejl ved oprettelse af forbindelse:", e)
    sys.exit(1) # Afslut programmet hvis forbindelsen ikke kunne oprettes
filename = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(filename+".csv","a") as f:
    f.write("Time,Tank Level\n")
    try:
        while True:
            # 1. Læs 4 bytes fra AREA_IN (ID0). Brug index 0.
            # Parametre: (Area, Index/DB, Start_byte, Antal_bytes)
            INPUT_RAW = client.read_area(AREA_IN, 0, 0, 4)
            DB_RAW = client.db_read(1,0,4)
            
            # 2. Læs 1 byte fra AREA_OUT (QB0). 
            # HER VAR FEJLEN: Det skal være 0, ikke 1.
            OUTPUT_RAW = client.read_area(AREA_OUT, 0, 0, 1) 

            # 3. Konverter ID0 til et REAL (float)
            id0_val = get_real(INPUT_RAW, 0)
            db0_val = get_real(DB_RAW, 0)

            # =========== Logik ============================
            print(f"Tank Level (ID0): {id0_val:.4f}")
            content = datetime.now().strftime("%H:%M") + "," + f"{float(id0_val*200)},{db0_val}\n"
            f.write(content)
            f.flush()
            time.sleep(0.5)

            # =========== Skriv Output =====================
            #set_bool(OUTPUT_RAW, 0, 0, q00) # Sæt bit 0 i output til True
            #client.write_area(AREA_OUT, 1, 0, OUTPUT_RAW) # Skriv det muterede bytearray tilbage til output (PA)
            time.sleep(0.035) # Vent i 35 ms før næste cyklus
    except KeyboardInterrupt:
        print("Program stoppet af bruger.")
    except Exception as e:
        print("Der opstod en fejl:", e)
    finally:
        client.disconnect()
        print("Forbindelse lukket.")
        client.destroy()