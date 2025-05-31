from flask import Flask, request, render_template_string, send_from_directory
import uuid
import os
import json
import xml.etree.ElementTree as ET

app = Flask(__name__, static_folder='static', static_url_path='/static')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{{ title }}</title>
  <script src="https://cdn.jsdelivr.net/npm/mind-elixir/dist/mind-elixir.min.js"></script>
  <style>
    html, body { margin: 0; height: 100%; font-family: sans-serif; }
    #app { height: 100vh; width: 100vw; }
  </style>
</head>
<body>
  <div id="app"></div>
  <script>
    const mind = new MindElixir({
      el: '#app',
      direction: MindElixir.SIDE,
      draggable: true,
      contextMenu: true,
      toolBar: true,
      nodeMenu: true,
      keypress: true,
      data: {{ data | safe }}
    });
    mind.init();
  </script>
</body>
</html>
"""


def opml_to_mindelixir(opml_content):

    def parse_outline(node):
        text = node.attrib.get('text') or node.attrib.get(
            'title') or "(no title)"
        children = [parse_outline(child) for child in node.findall('outline')]
        result = {"topic": text}
        if children:
            result["children"] = children
        return result

    root = ET.fromstring(opml_content)
    body = root.find('body')
    top = body.find('outline')

    return {
        "nodeData": {
            "id": "root",
            "topic": top.attrib.get("text") or top.attrib.get("title")
            or "Mind Map",
            "root": True,
            "children":
            [parse_outline(child) for child in top.findall('outline')]
        }
    }


@app.route("/generate", methods=["POST"])
def generate():
    content = request.json
    mind_data = content.get("mindmap")
    title = content.get("title", "Mind Map")

    if not mind_data:
        return {"error": "Missing mindmap data"}, 400

    html = render_template_string(HTML_TEMPLATE,
                                  title=title,
                                  data=json.dumps(mind_data))
    filename = f"{uuid.uuid4().hex}.html"
    os.makedirs("static", exist_ok=True)
    filepath = os.path.join("static", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated viewer file: {filepath}")

    base_url = request.host_url.rstrip("/")
    return {"url": f"{base_url}/static/{filename}"}


@app.route("/")
def home():
    return "Mind Map Viewer Backend is running."


@app.route("/openapi.yaml")
def serve_openapi():
    return send_from_directory(directory=os.getcwd(), path="openapi.yaml", mimetype="text/yaml")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
