from flask import Flask, request, render_template
import os
import sys

# Ensure we can import belief_graph and resolve data paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, project_root)
# Change working dir so belief_graph's relative paths resolve
os.chdir(project_root)

from belief_graph import similar_to

app = Flask(__name__, template_folder=current_dir)

# Inline HTML template
TEMPLATE = 'template.html'

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    query = ''
    if request.method == 'POST':
        query = request.form.get('query', '')
        result = similar_to(query)
    return render_template('template.html', result=result, query=query)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
