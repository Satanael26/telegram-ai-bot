"""
Servidor Flask para manejar webhooks de Stripe.
Este archivo se ejecuta en paralelo con el bot de Telegram.
"""

import os
import logging
from flask import Flask, request, jsonify
from utils.payments import process_webhook

logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"}), 200


@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    """Recibe webhooks de Stripe."""
    logger.info(f"Webhook recibido: {request.headers.get('Stripe-Signature')}")
    
    response, status = process_webhook(request)
    
    if status == 200:
        logger.info("Webhook procesado exitosamente")
    else:
        logger.error(f"Error en webhook: {response}")
    
    return jsonify(response), status


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(error):
    logger.error(f"Server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Obtener puerto de variable de entorno
    port = int(os.getenv("FLASK_PORT", 5000))
    
    print(f"🌐 Servidor Flask iniciado en puerto {port}")
    print(f"📍 Webhook URL: http://localhost:{port}/stripe-webhook")
    
    # En producción, usar Gunicorn o similar
    app.run(host="0.0.0.0", port=port, debug=False)
