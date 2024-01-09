from flask import *
from flask_restful import Api
from wtforms import *
from google.cloud import firestore
from datetime import datetime
from api import *
import requests

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static')

db = firestore.Client()

base = '/api/v1'
api = Api(app)

api.add_resource(AddChirp, f'{base}/chirps')
api.add_resource(CleanChirps, f'{base}/clean')
api.add_resource(GetChirp, f'{base}/chirps/<string:id>')


class AddChirpForm(Form):
    id = StringField('id')
    message = StringField('message')
    submit1 = SubmitField('Chirp!')


class SearchHashtagsForm(Form):
    hashtag = StringField('hashtag')
    submit2 = SubmitField('Search')


@app.route('/hashtags/<string:hashtag>')
def hashtags(hashtag):
    try:
        ref = db.collection('hashtags').document(f'#{hashtag}')
    except Exception as e:
        print(e)
    
    chirps = []

    for message in ref.get().to_dict()['document_id']:
        chirp = db.collection('messages').document(message).get()
        chirps.append({
            'id': message,
            'message': chirp.get('message'),
            'timestamp': chirp.get('timestamp')
        })
    
    return render_template('hashtags.html', hashtag=hashtag, chirps=chirps)

@app.route('/', methods=['GET', 'POST'])
def chirps():
    
    if request.method == 'GET':
        
        addForm = AddChirpForm()
        searchForm = SearchHashtagsForm()

        return render_template('chirps.html', addForm=addForm, searchForm=searchForm)
    
    elif request.method == 'POST':

        addForm = AddChirpForm(request.form)
        searchForm = SearchHashtagsForm(request.form)

        # new chirp
        if addForm.submit1.data and addForm.validate():

            chirp = Chirp(
                id = addForm.id.data,
                message = addForm.message.data,
                timestamp = str(datetime.now())
            )

            res = requests.post(f'http://127.0.0.1:8080{base}/chirps', json=chirp.__dict__, headers={'Content-Type': 'application/json'})
            
            addForm = AddChirpForm()

            if res.status_code == 400:
                return render_template('chirps.html', addForm=addForm, searchForm=searchForm, error='Chirp already exists.')
            else:
                return render_template('chirps.html', addForm=addForm, searchForm=searchForm, success='Chirp added successfully.')
            
        # search hashtag
        elif searchForm.submit2.data and searchForm.validate():
            return redirect('/hashtags/' + searchForm.hashtag.data)
        
        else:
            return render_template('chirps.html', addForm=addForm, searchForm=searchForm)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', path=request.path), 404

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
