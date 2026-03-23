from flask import Flask, render_template
from config import Config
from routes.api import api_bp

#principal

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(api_bp)
    return app


app = create_app()


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
