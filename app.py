import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from hubspot_service import update_hubspot_contact_and_deal

app = Flask(__name__)
CORS(app)

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "Invalid JSON received."}), 400

    print("Received data:", data)
    time.sleep(3)
    print("Delay complete.")

    email = data.get("email")
    interest = data.get("interest")

    if not email or not interest:
        return jsonify({"success": False, "message": "Missing required fields: 'email' or 'interest'."}), 400

    success, message = update_hubspot_contact_and_deal(email, interest)
    status_code = 200 if success else 500

    return jsonify({"success": success, "message": message, "received": data}), status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
