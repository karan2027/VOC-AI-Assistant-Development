"""
VaultofCodes Web AI Assistant — Flask Application Entry Point
Developer: Chhotelal Kushwaha
"""

from flask import Flask
from config import Config
from routes.chat import chat_bp

def create_app():
    """App Factory Initializer"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register Chat Blueprint
    app.register_blueprint(chat_bp)

    return app

app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print(f"🚀 Launching {Config.PROJECT_NAME}")
    print(f"👨‍💻 Developer: {Config.DEVELOPER}")
    print(f"🌐 Server Running At: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
