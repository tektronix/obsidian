import sys
import time
import os

from requests import get
from http import HTTPStatus

if len(sys.argv) > 1:
    job_name = str(sys.argv[1])

    server = os.getenv("SERVER")
    job_url = server + "/job/" + job_name + "/lastBuild/api/json"

    while(True):
        response = get(job_url, verify=False)
        if response.status_code == HTTPStatus.OK:
            if response.json()["result"]: 
                # Put light function here
                print("DONE")
            else:
                response = get(job_url + "/job/" + job_name + "/lastBuild/api/json?tree=executor[progress]")
                progress =  str(response.json()["executor"]["progress"])
                # Put light function here
                
                print("IN PROGRESS \nprogress: " + progress)
        time.sleep(10)

else:
    print("No job passed in. Use: 'obsidian.py <job_name>'")
