from flask import *
from datetime import datetime
from dateutil.relativedelta import relativedelta
from google.cloud import firestore

app = Flask(__name__,
            static_url_path='/static',
            static_folder='static')

db = firestore.Client()


def interpolate(d1: dict, d2: dict, dx: datetime):
    v1 = d1['value']
    v2 = d2['value']
    delta = v2 - v1
    t1 = date_from_str(d1['date'])
    t2 = date_from_str(d2['date'])
    t_delta = (t2 - t1).total_seconds()
    
    return v2 + (delta / t_delta) * (dx - t2).total_seconds()

def date_from_str(d):
    try: return datetime.strptime(d, '%d-%m-%Y')
    except: return None

def date_to_str(d):
    return d.strftime("%d-%m-%Y")

def validate_body(json_body):
    if 'value' not in json_body:
        return False
    
    if type(json_body['value']) is not int:
        return False
    
    if json_body['value'] < 0:
        return False
    
    return True

@app.route('/api/v1/consumi/<string:data>', methods=['GET', 'POST'])
def HandleRequest(data):

    if (date := date_from_str(data)) == None:
        return "Date not valid", 400
    
    if request.method == 'GET':

        ref = db.collection('consumi').document(data)
        if ref.get().exists:
            value = ref.get().to_dict()['value']
            return {
                'value': value,
                'isInterpolated': False
            }, 200
            
        else:

            isInterpolated = True
            ref = db.collection('consumi')

            # prendi i due valori minori più vicini alla data
            res = ref.where(
                    field_path='date',
                    op_string='<',
                    value=data
                )\
                .order_by('date')\
                .limit(2)\
                .get()

            if len(res) == 0:
                value = 0
            elif len(res) == 1:
                value = res[0].to_dict()['value']
            else:
                value = interpolate(res[0].to_dict(), res[1].to_dict(), date)
                    
            return {
                'value': value,
                'isInterpolated': isInterpolated
            }, 200

                
    elif request.method == 'POST':

        if not validate_body(request.json):
            return "Body not valid", 400
        
        ref = db.collection('consumi').document(data)
        if ref.get().exists:
            return "Conflict", 409
        try:
            # inserisco nel database la data come stringa
            ref.set({
                'value': request.json['value'],
                'date': data
            })
            aggiungi_bolletta(data, request.json['value'])
        except:
            return "Generic Error", 400
        finally:
            return {
                'value': request.json['value'],
                'isInterpolated': False
            }, 201
    
    else:
        return "Method not allowed", 405
        
@app.route('/api/v1/clean', methods=['GET'])
def Clean():
    ref = db.collection('consumi')
    for doc in ref.stream():
        doc.reference.delete()
    ref = db.collection('bollette')
    for doc in ref.stream():
        doc.reference.delete()
    return 'Ok', 200

def aggiungi_bolletta(date, value):
    data = date_from_str(date) + relativedelta(months=+1)
    valore_lettura = int(value)
    try:
        ref = db.collection('bollette').document(f'{data.month}-{data.year}')
    except Exception as e:
        print(e)
    if ref.get().exists:
        # update
        ref.update({
            "consumi": firestore.Increment(valore_lettura),
            "costo_complessivo": firestore.Increment(valore_lettura * 0.5),
            "letture": firestore.ArrayUnion([valore_lettura])
        })
    else:
        ref.set({
            "consumi": valore_lettura,
            "costo_complessivo": valore_lettura * 0.5,
            "letture": [valore_lettura]
        })

@app.route('/bollette')
def list_bollette():
    ref = db.collection('bollette').limit(12).stream()
    lista_bollette = []
    for bolletta in ref:
        lista_bollette.append(
            {
                'id': bolletta.id,
                **bolletta.to_dict()
            }
        )
    return render_template('bollette.html', bollette=lista_bollette) 

mesi = [
    'Gennaio',
    'Febbraio',
    'Marzo',
    'Aprile',
    'Maggio',
    'Giugno',
    'Luglio',
    'Agosto',
    'Settembre',
    'Ottobre',
    'Novembre',
    'Dicembre'
]

@app.route('/bolletta/<string:id>')
def dettaglio_bolletta(id):
    ref = db.collection('bollette').document(id)
    if not ref.get().exists:
        return render_template('404.html', path=id)
    
    # periodo di riferimento
    rif = date_from_str(f'1-{id}') + relativedelta(months=-1)
    ultima_lettura = ref.get().to_dict()['letture'][-1:]
    bolletta = {
        'id': ref.id,
        **ref.get().to_dict()
    }
    return render_template('bolletta.html', bolletta=bolletta, ultima_lettura=ultima_lettura, rif=mesi[rif.month - 1])

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', path=request.path), 404

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
