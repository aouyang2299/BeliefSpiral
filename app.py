from flask import Flask, request, render_template, jsonify
from belief_graph import model, similar_to, _seen_queries # added by andy
import os
import random

import sys

# Ensure we can import belief_graph and resolve data paths
# current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.abspath(os.path.join(current_dir, '..'))
# sys.path.insert(0, project_root)
# # Change working dir so belief_graph's relative paths resolve
# os.chdir(project_root)

from belief_graph import similar_to

app = Flask(
    __name__,
    static_url_path='/static'                               # <― mount them at /static
)




@app.route('/', methods=['GET', 'POST'])
def index():
    query = ''
    results = None
    all_queries = ["trump", "e"]

    if request.method == 'POST':
        query = request.form.get('query', '')
        results = similar_to(query)
        print("🧪 all_queries before render:", all_queries)  # should print ['trump', 'e']

        return render_template('template2.html', query=query, results=results, all_queries=all_queries)
    

    return render_template(
        'template2.html',
        query=query,
        results=results,          # ✅ MUST be here
        all_queries=all_queries
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
