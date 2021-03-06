import os
import snowballstemmer
from pyramid.view import view_config
from pyramid.response import Response

try:
    import simplejson as json
except ImportError:
    import json
import utils
import simservice

service1 = simservice.SimService(os.path.join(simservice.path, 'unigram'),
    preprocess = utils.simple_preprocess, deaccent=True, lowercase=True,
    stemmer=snowballstemmer.stemmer('english'), stopwords=utils.STOPWORDS)

service2 = simservice.SimService(os.path.join(simservice.path, 'bigram'),
    preprocess = utils.bigram_preprocess, deaccent=True, lowercase=True,
    stemmer=snowballstemmer.stemmer('english'), stopwords=utils.STOPWORDS)

service = service2

class SimServerViews(object):

    def __init__(self, request):
        self.request = request

    def validate(self, params):
        appstruct = {
            'action': 'status',
            'format': 'html',
            'data': None,
            'text': None,
            'min_score': 0,
            'max_results': 100,
            'model_confirmation': False}
        if 'action' in params:
            assert(params['action'] in ['train', 'index', 'query',
                                    'optimize', 'delete', 'status',
                                    'documents', 'is_indexed'])
            appstruct['action'] = params['action']
        if 'format' in params:
            assert(params['format'] in ['json', 'html'])
            appstruct['format'] = params['format']
        if 'data' in params:
            if not isinstance(params['data'], basestring):
                appstruct['data'] = self.request.POST['data'].file
        if 'text' in params:
            appstruct['text'] = params['text']
        if 'min_score' in params:
            min_score = float(params['min_score'])
            assert(min_score > 0.0 and min_score < 1.0)
            appstruct['min_score'] = min_score
        if 'max_results' in params:
            max_results = int(params['max_results'])
            assert(max_results > 0)
            appstruct['max_results'] = max_results
        if 'model_confirmation' in params:
            model_confirmation = bool(int(params['model_confirmation']))
            appstruct['model_confirmation'] = model_confirmation
        return appstruct

    @view_config(route_name='home', renderer="templates/interaction_view.pt")
    def site_view(self):
        result = None
        error = None
        data = None
        if 'cancel' in self.request.params:
            # just render the form
            return {"error": error, "result": result}
        else:
            controls = self.request.params
            appstruct = self.validate(controls)
            if appstruct['action'] == 'query':
                if appstruct['text']:
                    try:
                        data = json.loads(appstruct['text'])
                    except ValueError:
                        data = appstruct['text']
                    min_score = appstruct['min_score']
                    max_results = appstruct['max_results']
                    result = service.find_similar(data, min_score, max_results)
                else:
                    error = "No data supplied"
            elif appstruct['action'] in ['train', 'index']:
                if appstruct['text']:
                    try:
                        data = json.loads(appstruct['text'])
                    except ValueError:
                        error = "Not valid json"
                elif appstruct['data']:
                    afile = appstruct['data']
                    data = utils.extract_from_archive(afile)
                else:
                    error = "No data supplied"
                if data:
                    if appstruct['action'] == 'train':
                        try:
                            # has the service a model?
                            has_model = bool(service.service.stable.model)
                        except:
                            has_model = False
                        if appstruct['model_confirmation'] or not has_model:
                            result = service.train(data)
                        else:
                            error = "confirmation required to train new model and thus loosing all previous training data"
                    elif appstruct['action'] == 'index':
                        result = service.index(data)
            elif appstruct['action'] == 'delete':
                try:
                    data = json.loads(appstruct['text'])
                    result = service.delete(data)
                except ValueError:
                    error = "Not valid json"
            elif appstruct['action'] == 'optimize':
                result = service.optimize()
            elif appstruct['action'] == 'status':
                result = service.status()
            elif appstruct['action'] == 'documents':
                result = service.indexed_documents()
            elif appstruct['action'] == 'is_indexed':
                result = service.is_indexed(appstruct['text'])
        if result != None:
            if appstruct['format'] == 'json':
                response =  Response(json.dumps(result))
                response.content_type='application/json'
                return response

        return {"error": error, "result": result}
