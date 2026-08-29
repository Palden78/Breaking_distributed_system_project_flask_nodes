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


