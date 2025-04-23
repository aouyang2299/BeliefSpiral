from flask import Flask, request, render_template
from belief_graph import similar_to, all_queries
from conspiracy_generator import load_dataset, filter_docs, build_context, generate_conspiracy




app = Flask(
    __name__,
    static_url_path='/static'                               # <― mount them at /static
)
dataset = load_dataset("raw_data/final_data/all_spacy_concepts_final.json")


@app.route('/', methods=['GET', 'POST'])
def index():
    query = ''
    results = []
    dataset = 'all_spacy_concepts_final.json' 

    if request.method == 'POST':
        query = request.form.get('query', '')
        results = similar_to(query)
        
    return render_template('template2.html', results=results, query=query, all_queries = all_queries)

@app.route('/process_clicks', methods=['GET', 'POST'])
def process_clicks():
    payload = request.get_json() or {}
    clicked = payload.get('clicked', [])

    docs    = filter_docs(dataset, clicked)
    context = build_context(clicked, docs)
    story   = generate_conspiracy(context)

    # return plain JSON, not a template
    return jsonify({ "story": story })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
