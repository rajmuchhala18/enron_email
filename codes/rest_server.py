from datetime import datetime
from multiprocessing import Process, Manager, Queue
import sys
import time
import traceback
from sanic import Sanic
from sanic.response import json

import config
from ai_process import ProcessClass

app = Sanic('enron_emails')
sys.path.append("../")

@app.route('/api/v1/enron_analysis', methods=['POST'])
async def api(request):
    start = time.time()
    request_data = request.json
    request_id = request_data.get("req_id", None)
    print(f"{request_id} request received at {str(datetime.now())}", flush=True)


    ai_result = {}
    ai_result["result"] = ""

    try:
        uid = request_data["req_id"]
        process_queue.put([request_data])

        while True:
            if uid in resultproc:
                ai_result = resultproc.pop(uid)
                FLAG = True
                error_message = ""
                break

    except Exception as e:
        traceback.print_exc()
        ai_result["success"] =False
        ai_result["error_message"] = "Exception occured while processing request: "+ str(e)

    print(f"{request_id} response sent at {str(datetime.now())}", flush=True)
    return json(ai_result)

def main(n_workers):
    app.run(host="0.0.0.0", port=config.port, debug=False, workers=config.no_of_workers)

if __name__ == '__main__':
    manager = Manager()
    num_of_workers = config.no_of_workers
    process_queue = Queue()
    result_queue = Queue()
    process_stat = manager.dict()
    workers = []

    process_stat["run_flag"] = True
    resultproc = manager.dict()

    for i in range(num_of_workers):
        workers.append(ProcessClass(process_queue, resultproc, process_stat))

    for i in range(len(workers)):
        workers[i].start()

    try:
        main(num_of_workers)

    except Exception as e:
        quit()

    process_stat["run_flag"] = False

    for i in range(len(workers)):
        workers[i].join()
