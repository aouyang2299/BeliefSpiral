from flask import Flask, request, render_template
from belief_graph import similar_to, all_queries, _seen_queries


app = Flask(
    __name__,
    static_url_path='/static'                               # <― mount them at /static
)


@app.route('/', methods=['GET', 'POST'])
def index():
    query = ''
    results = []

    if request.method == 'POST':
        query = request.form.get('query', '')
        results = similar_to(query)

    return render_template('template2.html', results=results, query=query, all_queries = all_queries)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
