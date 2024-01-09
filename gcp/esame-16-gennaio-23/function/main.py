#!/usr/bin/env python3
from google.cloud import firestore
from datetime import datetime
from dateutil.relativedelta import relativedelta


def aggiungi_bolletta(data, context):
    db = firestore.Client()
    doc = data['value']['fields']
    data = date_from_str(doc['date']['stringValue']) + relativedelta(months=+1)
    valore_lettura = int(doc['value']['integerValue'])

    ref = db.collection('bollette').document(f'{data.month}-{data.year}')
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

def date_from_str(d):
    try: return datetime.strptime(d, '%d-%m-%Y')
    except: return None