import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gradio_app import demo

if __name__ == "__main__":
    # Hugging Face Spaces dynamically assigns port and hosts on 0.0.0.0
    port = int(os.environ.get("PORT", 7860))
    exports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "exports")
    os.makedirs(exports_dir, exist_ok=True)
    demo.launch(server_name="0.0.0.0", server_port=port, allowed_paths=[exports_dir])

