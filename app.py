import os 
import time 

from flask import Flask, request, jsonify 
import requests

from kv_store import store

app = Flask(__name__)

NODE_NAME = os.environ.get("NODE_NAME") 
PEERS = [p for p in os.environ.get("PEERS","").split(',') if p]
MODE = os.environ.get("MODE", "CP")


"""
GET METHODS TO GET DATA OF EACH NODE
"""
@app.route("/data", methods=["GET"])
def getAllData():
    return jsonify({
        "node": NODE_NAME,
        "mode": MODE,
        "store": store
    })

@app.route("/data/<key>", methods = ["GET"])
def getDataByKey(key):
    if key in store:
        return jsonify({
            "node": NODE_NAME,
            "key": key ,
            "value": store[key]
        })

    return jsonify({
        "error": "key not found"
    }), 404


"""
PUT METHODS TO HANDLE WRITES IN NODES DURING 
AP AND CP MODE
AP = AVAILABILITY
CP = CONSISTENCY
"""
@app.route("/data/<key>", methods=["PUT"])
def put_data(key):
    global MODE
    value = request.json.get("value")

    if MODE == "AP":
        # Write locally first, replicate with best effort
        store[key] = value 
        replication_results = []
        #try writing to peers
        for peer in PEERS:
            try:
                requests.post(
                    f"http://{peer}/replicate",
                    json= {"key": key, "value": value},
                    timeout=1,
                )
                replication_results.append(
                    {"peer": peer, 
                     "status": "replicated"
                })
            except requests.exceptions.RequestException:
                replication_results.append(
                    {"peer":peer, 
                     "status": "unreachable"
                })

            return jsonify({
                "status": "ok",
                "node": NODE_NAME,
                "key": key,
                "value": value ,
                "mode": "AP",
                "replication": replication_results
            })
    else:
        # MODE == CP 
        # REPLICATE TO ALL PEERS FIRST BEFORE CONFIRMING
        for peer in PEERS:
            try:
                resp = requests.post(
                    f"http://{peer}/replicate",
                    json = {"key": key, "value": value},
                    timeout=2
                )

                if resp.status_code != 200:
                    return jsonify({
                        "err": f"Replication to {peer} failed",
                        "reason": "write rejected to maintain consistency CP mode"
                    }), 503
            except requests.exceptions.RequestException:
                return jsonify({
                    "error":f"cant reach {peer}",
                    "reason": "Write rejected to maintain consistency mode CP"
                }),503

            # write locally
            store[key] = value
            return jsonify({
                "status": "ok",
                "node": NODE_NAME,
                "key": key,
                "value": value,
                "mode": "CP",
                "message": "All nodes consistent",
            })


#endpoint to replicate
@app.route("/replicate", methods=["POST"])
def replicate():
    key = request.json.get("key")
    value = request.json.get("value")
    store[key] = value 
    return jsonify({
        "status": "ok",
        "node": NODE_NAME
    })

#endpoint to get current mode
@app.route("/mode", methods=["GET"])
def get_mode():
    return jsonify({
        "node": NODE_NAME,
        "mode": MODE
    })

#endpoint to switch modes
@app.route("/mode", methods=["POST"])
def set_mode():
    global MODE 
    new_mode = request.json.get(
        "mode",
        ""
    ).upper()

    if new_mode in ("AP","CP"):
        MODE = new_mode
        return jsonify({"status": "ok", "node": NODE_NAME, "mode": MODE})
    return jsonify({"error": "Mode must be CP or AP"}), 400


#main namespace
if __name__ == "__main__" :
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host='0.0.0.0',
        port=port
    )



