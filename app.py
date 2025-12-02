import os
from flask import Flask, request, jsonify
import redis

app = Flask(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
PORT = int(os.getenv("PORT", "8000"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/notes", methods=["POST"])
def create_note():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON body"}), 400

    note_id = data.get("id")
    text = data.get("text")
    ttl = data.get("ttl")  # in seconds

    if not note_id or not text or ttl is None:
        return jsonify({"error": "id, text, ttl are required"}), 400

    try:
        ttl = int(ttl)
        if ttl <= 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "ttl must be a positive integer"}), 400

    key = f"note:{note_id}"
    # SETEX key ttl value
    r.setex(key, ttl, text)

    return jsonify({"message": "note stored", "id": note_id, "ttl": ttl}), 201


@app.route("/notes/<note_id>", methods=["GET"])
def get_note(note_id):
    key = f"note:{note_id}"
    value = r.get(key)
    if value is None:
        return jsonify({"error": "note not found or expired"}), 404
    return jsonify({"id": note_id, "text": value}), 200


if __name__ == "__main__":
    # Bind to 0.0.0.0 so Docker/K8s can reach it
    app.run(host="0.0.0.0", port=PORT)
