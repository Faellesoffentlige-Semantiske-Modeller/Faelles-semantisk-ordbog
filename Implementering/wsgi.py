"""WSGI entrypoint.

Production servers import ``app`` from here (e.g. ``gunicorn wsgi:app``).
Running this file directly starts Flask's development server.
"""

from ordbogen import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
