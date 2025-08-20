from flask import Flask, render_template, jsonify, request, current_app
import threading
import webbrowser
import logging

app = Flask(__name__)
logic_tree_data = None
tree_name = "LogicTree"
log = logging.getLogger(__name__)

@app.route("/")
def index():
    return render_template("index.html", tree_name=tree_name)

@app.route("/api/tree")
def api_tree():
    view = request.args.get("view", "original") # Default to original view
    current_tree = app.config.get(f"logic_tree_{view}")
    if current_tree is None:
        return jsonify({"error": f"No tree found for view: {view}"}), 404
    log.debug(f" Tree for view '{view}: {current_tree}")
    current_app.logger.info(f"Serving logic tree view: {view}")
    from logictree.utils.serialize import logic_tree_to_json
    #return jsonify(current_tree.to_json_dict())
    log.debug(f"[Explorer] Serializing node id={id(current_tree)} label={current_tree.label()}")
    return jsonify(logic_tree_to_json(current_tree))

import copy
from logictree.transforms import case_to_if_tree  # or wherever it lives

def launch_explorer(logic_tree_original, tree_name_input="LogicTree"):
    from logictree.utils.serialize import logic_tree_to_json
    global logic_tree_data_original, logic_tree_data_simplified, tree_name

    tree_name = tree_name_input

    log.debug("[Explorer] Original tree root label: %s", logic_tree_original.label())
    log.debug(f"[Explorer] Original id: {id(logic_tree_original)}")

    # Store original
    app.config["logic_tree_original"] = logic_tree_original
    logic_tree_data_original = logic_tree_to_json(logic_tree_original)
    app.config["logic_tree_data_original"] = logic_tree_data_original

    # Now deepcopy and transform after copy
    logic_tree_copy = copy.deepcopy(logic_tree_original)
    from logictree.transforms.simplify import simplify_logic_tree
    simplified_tree = simplify_logic_tree(logic_tree_copy)

    log.debug(f"[Explorer] Simplified id: {id(simplified_tree)}")
    log.debug(f"[Explorer] Simplified tree type: {type(simplified_tree).__name__}")

    app.config["logic_tree_simplified"] = simplified_tree
    logic_tree_data_simplified = logic_tree_to_json(simplified_tree)
    app.config["logic_tree_data_simplified"] = logic_tree_data_simplified

    threading.Timer(1.0, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False)

