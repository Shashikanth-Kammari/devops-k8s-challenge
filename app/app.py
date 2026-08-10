from flask import Flask, jsonify
import os
import socket

app = Flask(__name__)

@app.get("/")
def root():
    return jsonify({"message": "DevOps Kubernetes challenge", "pod": socket.gethostname()})

@app.get("/health")
def health():
    return jsonify({"status": "healthy"}), 200

@app.get("/ready")
def ready():
    return jsonify({"status": "ready"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
