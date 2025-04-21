from flask import Flask, request, render_template
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
   # <― point at your static files
    static_url_path='/static'                               # <― mount them at /static
)


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    query = ''
    if request.method == 'POST':
        query = request.form.get('query', '')
        results   = similar_to(query)
        return render_template('template2.html', results=results, query=query)
        
    if not query or all(r == '' for r in results):
            return render_template('no_results.html', query=query)

    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
