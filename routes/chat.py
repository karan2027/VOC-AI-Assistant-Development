"""
Flask Chat Routes & API Blueprint
Project: VaultofCodes AI Assistant
Developer: Chhotelal Kushwaha
"""

from flask import Blueprint, render_template, request, jsonify, session
from services.gemini_service import GeminiService
from utils.prompt_templates import FUNCTION_TEMPLATES, STYLE_MODIFIERS
from config import Config

chat_bp = Blueprint("chat", __name__)
gemini_service = GeminiService()

@chat_bp.route("/")
def index():
    """Renders main AI Assistant Web Interface."""
    if "history" not in session:
        session["history"] = []
    
    return render_template(
        "index.html",
        project_name=Config.PROJECT_NAME,
        developer=Config.DEVELOPER,
        functions=FUNCTION_TEMPLATES,
        styles=STYLE_MODIFIERS
    )

@chat_bp.route("/api/chat", methods=["POST"])
def chat_api():
    """
    Main Chat API Endpoint.
    Accepts JSON: { "message": "...", "function_type": "qa", "style_type": "default" }
    Returns JSON: { "success": True, "response": "...", "source": "..." }
    """
    try:
        data = request.get_json() or {}
        message = data.get("message", "")
        function_type = data.get("function_type", "qa")
        style_type = data.get("style_type", "default")

        if not message or not message.strip():
            return jsonify({
                "success": False,
                "error": "Please enter a non-empty question or text prompt."
            }), 400

        result = gemini_service.generate_response(
            user_message=message,
            function_type=function_type,
            style_type=style_type
        )

        if result.get("success"):
            # Update session history
            history = session.get("history", [])
            history.append({
                "user": message,
                "assistant": result["response"],
                "function": function_type,
                "style": style_type
            })
            session["history"] = history
            return jsonify(result), 200
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"An unexpected server error occurred: {str(e)}"
        }), 500

@chat_bp.route("/api/clear", methods=["POST"])
def clear_api():
    """Clears user chat session history."""
    session["history"] = []
    return jsonify({"success": True, "message": "Chat history cleared successfully."}), 200
