from flask import *
from flask_restful import Api
from google.cloud import firestore
from api import *
from wtforms import *
import requests

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static')

db = firestore.Client()

base = '/api/v1'
api = Api(app)

api.add_resource(HandleRules, f'{base}/routing/<string:id>')
api.add_resource(ListRules, f'{base}/routing/')
api.add_resource(CleanGeneric, f'{base}/clean')


class SearchForm(Form):
    ip = StringField('Search')
    submit = SubmitField('Submit')

@app.route('/', methods=['GET', 'POST'])
def handler():

    ref = db.collection('rules').stream()
    routing_table = []
    for doc in ref:

        routing_table.append({
            'id': doc.id,
            **doc.to_dict()
        })

    if request.method == 'POST':
            
            form = SearchForm(request.form)
            if form.submit.data and form.validate():            
                res = requests.post(f'http://127.0.0.1:8080{base}/routing/', 
                                    json=json.dumps(form.ip.data), 
                                    headers={'Content-Type': 'application/json'})
                if res.status_code != 200:
                    return render_template('404.html', path=request.path), 404                
                foundRule = res.json().strip('"')
                return render_template('table.html', form=form, routing_table=routing_table, selected=foundRule)

    if request.method == 'GET':

        form = SearchForm()
        
        return render_template('table.html', form=form, routing_table=routing_table)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', path=request.path), 404

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
