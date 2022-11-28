import asyncio
import datetime
from bleak import BleakScanner

# MiTermometerPVVX

async def main():
    print("Scanning BLE devices of type 'ATC_MiThermometer (PVVX)', please wait...")
    stop_event = asyncio.Event()
    atc_counters={}
    atc_date={}

    def callback(_device, advertising_data):
        name=advertising_data.local_name;
        if name and name[0:3]=="ATC" :
            adv_atc=advertising_data.service_data['0000181a-0000-1000-8000-00805f9b34fb']
            count=int.from_bytes(adv_atc[13:14], byteorder='little', signed=False) 
            if atc_counters.get(name) != count :
                atc_counters.update({name: count}) 
                datenow=datetime.datetime.now()
                dateprev=atc_date.get(name)
                if dateprev:
                    datediff=datenow-dateprev
                    datediff=datetime.timedelta(seconds=round(datediff.total_seconds()))
                else:
                    datediff=0
                atc_date.update({name: datenow}) 
                temp=int.from_bytes(adv_atc[6:8], byteorder='little', signed=True)/100.0
                humidity=int.from_bytes(adv_atc[8:10], byteorder='little', signed=True)/100.0
                batteryv=int.from_bytes(adv_atc[10:12], byteorder='little', signed=False)
                battery=int.from_bytes(adv_atc[12:13], byteorder='little', signed=False)    
                #flag=int.from_bytes(adv_atc[14:15], byteorder='little', signed=False) 
                print()
                print("device:\t ", name)
                namelen=len(str(name))+10
                print("-" * namelen)
                print(f"temp:\t  {temp}\xB0C")
                print(f'humidity: {humidity}%')
                print(f'batteryv: {batteryv} mV')
                print(f'battery:  {battery}%')
                print(f'count:\t  {count}')
                if datediff:
                    datedifftext=', duration: ' + str(datediff)
                else:
                    datedifftext=""
                print(f'time now: {datenow.strftime("%H:%M:%S")}{datedifftext}')

    try:
        async with BleakScanner(callback):
            await stop_event.wait()
    except asyncio.CancelledError:
        print('**** task scanner cancelled')
        stop_event.set()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(str(e))
