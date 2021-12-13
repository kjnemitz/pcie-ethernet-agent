#!/usr/bin/env python3

import cgitb
import xmltodict
import json
import nvidia_smi
import socket
from pynvml import *
from collections import OrderedDict

cgitb.enable()

response_dict = OrderedDict()
response_dict['pcie-ethernet-agent-version'] = '0.0.1'
response_dict['hostname'] = (socket.gethostname())
response_dict['device_count'] = 0
response_dict['process_count'] = 0
response_dict['devices'] = []
response_dict['processes'] = []
try:
    nvmlInit()
    deviceCount = nvmlDeviceGetCount()
    for i in range(0, deviceCount):
        handle = nvmlDeviceGetHandleByIndex(i)
        pciInfo = nvmlDeviceGetPciInfo(handle)
        deviceid = pciInfo.busId.decode()
        devicename = nvmlDeviceGetName(handle).decode()
        brandNames = {NVML_BRAND_UNKNOWN :  "Unknown",
                      NVML_BRAND_QUADRO  :  "Quadro",
                      NVML_BRAND_TESLA   :  "Tesla",
                      NVML_BRAND_NVS     :  "NVS",
                      NVML_BRAND_GRID    :  "Grid",
                      NVML_BRAND_GEFORCE :  "GeForce",
        }
        devicebrand = brandNames[nvmlDeviceGetBrand(handle)]
        response_dict['devices'].append({'device_id':deviceid,'device_name':devicename,'device_brand':devicebrand})
        response_dict['devices'][i]['processes'] = []

        procs = nvmlDeviceGetComputeRunningProcesses(handle)
        response_dict['process_count'] = response_dict['process_count'] + len(procs)
        for p in procs:
            try:
                name = nvmlSystemGetProcessName(p.pid).decode()
            except NVMLError as err:
                if (err.value == NVML_ERROR_NOT_FOUND):
                    # probably went away
                    continue
                else:
                    name = handleError(err)
                        
            if (p.usedGpuMemory == None):
                mem = 'N\A'
            else:
                # in MiB
                memmeasure = 'MiB'
                mem = (p.usedGpuMemory / 1024 / 1024)

            response_dict['processes'].append({'pid':p.pid,'name':name,'memory_measure':memmeasure,'memory_used':mem,'device_id':deviceid})
            response_dict['devices'][i]['processes'].append(response_dict['processes'][len(response_dict['processes'])-1])

        tempmeasure = 'Celsius'
        temp = str(nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU))
        maxtemp = str(nvmlDeviceGetTemperatureThreshold(handle, NVML_TEMPERATURE_THRESHOLD_SHUTDOWN))
        mintemp = str(nvmlDeviceGetTemperatureThreshold(handle, NVML_TEMPERATURE_THRESHOLD_SLOWDOWN))
        response_dict['devices'][i].update({'temp_measure':tempmeasure,'temp':temp,'max_temp':maxtemp,'min_temp':mintemp})

        powermeasure = 'Watts'
        powerdraw = '%.2f' % (nvmlDeviceGetPowerUsage(handle) / 1000.0)
        powerLimit = nvmlDeviceGetPowerManagementLimitConstraints(handle)
        maxpowerlimit = '%.2f' % (powerLimit[0] / 1000.0)
        minpowerlimit = '%.2f' % (powerLimit[1] / 1000.0)
        response_dict['devices'][i].update({'power_measure':powermeasure,'power_draw':powerdraw,'maximum_power_threshold':maxpowerlimit,'minimum_power_threshold':minpowerlimit})
except Exception as e:
    pass

response_json = json.dumps(response_dict, indent=2)


print("Content-type: text/json")
print("")
print(response_json)
#nvidia_dict = xmltodict.parse(nvidia_smi.XmlDeviceQuery())
#nvidia_json = json.dumps(nvidia_dict, indent=2)
#print(nvidia_json)
