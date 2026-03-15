import snap7
from snap7.util import set_bool, get_bool
from snap7.type import Area
import time
import sys

# ====================== PLC konfiguration ====================
PLC_IP = "192.168.154.120"
RACK = 0
SLOT = 1

AREA_IN = Area.PE
AREA_OUT = Area.PA

S1 = False
S2 = False
S3 = False
Q1 = False

first_scan = True

# ====================== Forbindelse ==========================
try:
    client = snap7.client.Client()
    client.connect(PLC_IP,RACK,SLOT)
    print("Forbundet til PLC på IP: ",PLC_IP)
except Exception as e:
    print("Fejl ved forbindelse: ",e)
    print("Lukker script pænt ned")
    sys.exit(1)

# ===================== Main ==================================
try:    
    while True:
        if first_scan:
            Q1 = False
        
        # ================= Læser Input ===========================
        INPUT_RAW = client.read_area(AREA_IN,1,0,1) #  INPUT_RAW -> [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7]
        OUTPUT_RAW = client.read_area(AREA_OUT,1,0,1) #  OUTPUT_RAW -> [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7]
        S1 = get_bool(INPUT_RAW,0,0)
        S2 = get_bool(INPUT_RAW,0,1)
        S3 = get_bool(INPUT_RAW,0,2)
        Q1 = get_bool(OUTPUT_RAW,0,0)

        # ================= Program ===============================
        Q1 = S1 and S2 and not S3

        # ================= Skriver Output ========================
        set_bool(OUTPUT_RAW,0,0,Q1)
        client.write_area(AREA_OUT,1,0,OUTPUT_RAW)
        time.sleep(0.035)

except Exception as e:
    print("Programmet fejlet: ",e)

except KeyboardInterrupt:
    print("Bruger lukker program")

finally:
    client.disconnect()
    client.destroy()
