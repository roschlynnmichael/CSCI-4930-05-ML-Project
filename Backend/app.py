from flask import Flask, request, jsonify
import joblib  # or import pickle
import numpy as np
from werkzeug.exceptions import BadRequest
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variable for the model
model = None

def load_model():
    """Load the trained model from disk."""
    global model
    try:
        # Replace 'model.joblib' with your model file
        model = joblib.load('model.joblib')
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise

@app.before_first_request
def initialize():
    """Initialize the model before first request."""
    load_model()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint to check if the server is running."""
    return jsonify({"status": "healthy"}), 200

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint to make predictions."""
    try:
        # Get input data from request
        data = request.get_json(force=True)
        
        if not data or 'features' not in data:
            raise BadRequest("Missing 'features' in request body")

        # Convert input data to numpy array
        features = np.array(data['features'])
        
        # Make prediction
        prediction = model.predict(features.reshape(1, -1))
        
        # Return prediction
        return jsonify({
            'status': 'success',
            'prediction': prediction.tolist()
        }), 200

    except BadRequest as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)