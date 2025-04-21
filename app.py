from flask import Flask, request, render_template
from belief_graph import similar_to, _seen_queries # added by andy
import os
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

    if request.method == 'POST':
        query = request.form.get('query', '')
        results = similar_to(query)
        return render_template('template2.html', results=results, query=query)

    _seen_queries.clear()  # 👈 Clear past seen nodes when the page is reloaded
    return render_template('welcome.html', query=query)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
