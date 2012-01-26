import tempfile
import tarfile, zipfile
from simservice import service
from gensim import utils

def extract_from_archive(afile):
    tmp = tempfile.NamedTemporaryFile()
    tmp.file.write(afile.read())
    tmp.file.flush()
    if tarfile.is_tarfile(tmp.name):
        tmptf = tarfile.open(tmp.name)
        for ti in tmptf.getmembers():
            if ti.isfile() and ti.size > 0 :
                tf = tmptf.extractfile(ti)
                text = tf.read()
                id = ti.name
                tf.close()
                yield {'id': id, 'text': text}
    elif zipfile.is_zipfile(tmp.name):
        tmpzip = zipfile.ZipFile(tmp.file)
        for zi in tmpzip.infolist():
            tz = tmpzip.open(zi)
            text = tz.read()
            id = tz.name
            tz.close()
            yield {'id': id, 'text': text}
    tmp.close()

def find_similar(data, min_score, max_results):
    if isinstance(data, basestring):
        doc = data.strip()
        if ' ' in doc:
            doc = {'tokens': utils.simple_preprocess(data)}
        try:
            return {'status': 'OK', 'response':
                                service.find_similar(doc,
                                min_score=min_score,
                                max_results=max_results)}
        except ValueError:
            return {'status': 'NOTFOUND', 'response':[]}
    else:
        result = {}
        for doc in data:
            try:
                result[doc] = (service.find_similar(
                                doc,
                                min_score=min_score,
                                max_results=max_results))
            except ValueError:
                pass
        if result:
            return {'status': 'OK', 'response': result}
        else:
            return {'status': 'NOTFOUND', 'response':[]}

def _buffer(aservice, data):
    i = 0
    for d in data:
        if 'tokens' in d:
            aservice.buffer([{'id': d['id'], 'tokens': d['tokens']}])
        else:
            aservice.buffer([{'id': d['id'],
                'tokens': utils.simple_preprocess(d['text'])}])
        i+=1
    return i


def train(data):
    service.set_autosession(False)
    service.open_session()
    i = _buffer(service, data)
    service.train(method='lsi')
    #logger.info('training complete commit changes')
    service.commit()
    service.set_autosession(True)
    return {'status': 'OK', 'response':i}

def index(data):
    service.set_autosession(False)
    service.open_session()
    i =_buffer(service, data)
    service.index()
    #logger.info('training complete commit changes')
    service.commit()
    service.set_autosession(True)
    return {'status': 'OK', 'response':i}



def optimize():
    service.set_autosession(False)
    service.open_session()
    service.optimize()
    service.commit()
    service.set_autosession(True)
    return {'status': 'OK', 'response': 'index optimized'}

def delete(data):
    service.set_autosession(False)
    service.open_session()
    service.delete(data)
    service.commit()
    service.set_autosession(True)
    return {'status': 'OK', 'response': 'documents deleted'}

def status():
    return {'status': 'OK', 'response': service.status()}

def indexed_documents():
    return {'status': 'OK', 'response': service.keys()}

def is_indexed(doc):
    return {'status': 'OK', 'response': doc in service.keys()}

