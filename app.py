from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"message": "AutoCad_Buddy API is running"}), 200

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/equipment/categories')
def categories():
    return jsonify(["kitchen", "restaurant"]), 200

@app.route('/api/equipment/types')
def types():
    return jsonify(["refrigerator", "oven", "dishwasher", "sink", "counter", "cabinet", "island"]), 200

if __name__ == '__main__':
    app.run(debug=True)
