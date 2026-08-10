# pyright: reportMissingImports=false
# pyright: reportMissingModuleSource=false
import os
import time

from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database=os.getenv("DB_NAME", "appdb"),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", "password"),
        connect_timeout=3
    )


@app.route("/")
def home():
    return jsonify({
        "application": "devops-challenge",
        "status": "running"
        
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/ready")
def ready():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({
            "status": "ready",
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "not-ready",
            "database": "unavailable",
            "error": str(e)
        }), 503


@app.route("/api")
def api():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute(
            "INSERT INTO requests DEFAULT VALUES RETURNING id"
        )

        request_id = cursor.fetchone()[0]

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": "Request processed successfully",
            "request_id": request_id
        })

    except Exception as e:
        return jsonify({
            "error": "Database operation failed",
            "details": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)