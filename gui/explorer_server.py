from flask import Flask, render_template, jsonify, request, current_app
import threading
import webbrowser

app = Flask(__name__)
logic_tree_data = None
tree_name = "LogicTree"

@app.route("/")
def index():
    return render_template("index.html", tree_name=tree_name)

@app.route("/api/tree")
def api_tree():
    view = request.args.get("view", "original") # Default to original view
    current_tree = app.config.get(f"logic_tree_{view}")
    if current_tree is None:
        return jsonify({"error": f"No tree found for view: {view}"}), 404
    print(f"DEBUG Tree for view '{view}: {current_tree}")
    current_app.logger.info(f"Serving logic tree view: {view}")
    from logictree.utils.serialize import logic_tree_to_json
    #return jsonify(current_tree.to_json_dict())
    return jsonify(logic_tree_to_json(current_tree))

#def launch_explorer(logic_tree_original, logic_tree_simplified, tree_name_input="LogicTree"):
#    from logictree.utils.serialize import logic_tree_to_json
#    global logic_tree_data, tree_name
#    tree_name = tree_name_input
#    print("[Explorer] Original tree root label:", logic_tree_original.label)
#    print(f"[Explorer] Original id: {id(logic_tree_original)}")
#    print(f"[Explorer] simplifed id: {id(logic_tree_simplified)}")
#    print("[Explorer] Original tree:", logic_tree_original)
#    print("[Explorer] Simplified tree:", logic_tree_simplified)
#    app.config["logic_tree_original"]   = logic_tree_original
#    app.config["logic_tree_simplified"] = logic_tree_simplified
#    app.config["tree_name_input"] = tree_name_input
#    logic_tree_data = logic_tree_to_json(logic_tree_original)
#    threading.Timer(1.0, lambda: webbrowser.open("http://localhost:5000")).start()
#    app.run(debug=False)
def launch_explorer(logic_tree_original, logic_tree_simplified, tree_name_input="LogicTree"):
    from logictree.utils.serialize import logic_tree_to_json
    global logic_tree_data_original, logic_tree_data_simplified, tree_name

    tree_name = tree_name_input

    print("[Explorer] Original tree root label:", logic_tree_original.label)
    print(f"[Explorer] Original id: {id(logic_tree_original)}")
    print(f"[Explorer] Simplified id: {id(logic_tree_simplified)}")
    print("[Explorer] Original tree:", logic_tree_original)
    print("[Explorer] Simplified tree:", logic_tree_simplified)
    print("[Explorer] Simplified tree type:", type(logic_tree_simplified).__name__)

    # Save raw trees for other endpoints
    app.config["logic_tree_original"] = logic_tree_original
    app.config["logic_tree_simplified"] = logic_tree_simplified
    app.config["tree_name_input"] = tree_name_input

    # Generate and store both trees as JSON
    logic_tree_data_original = logic_tree_to_json(logic_tree_original)
    logic_tree_data_simplified = logic_tree_to_json(logic_tree_simplified)

    app.config["logic_tree_data_original"] = logic_tree_data_original
    app.config["logic_tree_data_simplified"] = logic_tree_data_simplified

    threading.Timer(1.0, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=False)

