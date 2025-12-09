from flask import Flask, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

vectorizer = TfidfVectorizer(stop_words='english')

@app.route('/similarity', methods=['POST'])
def calculate_similarity():
    data = request.get_json()
    input_text = data.get('text', '')
    corpus = data.get('corpus', [])
    ids = data.get('ids', [])

    tfidf_matrix = vectorizer.fit_transform(corpus)
    input_vector = vectorizer.transform([input_text])

    similarity_scores = cosine_similarity(input_vector, tfidf_matrix)

    results = [
        {"id": ids[i], "similarity": score}
        for i, score in enumerate(similarity_scores[0])
    ]

    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
