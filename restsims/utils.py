import logging
import re
import tempfile
import tarfile, zipfile
from gensim.utils import tokenize

logger = logging.getLogger(__file__)


# improved list from Stone, Denis, Kwantes (2010)
STOPWORDS = """
a about above across after afterwards again against all almost alone along already also although always am among amongst amoungst amount an and another any anyhow anyone anything anyway anywhere are around as at back be
became because become becomes becoming been before beforehand behind being below beside besides between beyond bill both bottom but by call can
cannot cant co computer con could couldnt cry de describe
detail did do doc doesn done down due during
each eg eight either eleven else elsewhere empty enough etc even ever every everyone everything everywhere except few fifteen
fify fill find fire first five for former formerly forty found four from front full further get give go
had has hasnt have he hence her here hereafter hereby herein hereupon hers herself him himself his how however http hundred i ie
if in inc indeed interest into is it its itself keep last latter latterly least less ltd
just
kg km
ll
made many may me meanwhile might mill mine more moreover most mostly move much must my myself name namely
neither never nevertheless next nine no nobody none noone nor not nothing now nowhere nt of off
often on once one only onto or org other others otherwise our ours ourselves out over own part per
perhaps please pdf put rather re
quite
rather really regarding
same see seem seemed seeming seems serious several she should show side since sincere six sixty so some somehow someone something sometime sometimes somewhere still such system take ten
than that the their them themselves then thence there thereafter thereby therefore therein thereupon these they thick thin third this those though three through throughout thru thus to together too top toward towards twelve twenty two un under
until up unless upon us used using
various very very via
was we well were what whatever when whence whenever where whereafter whereas whereby wherein whereupon wherever whether which while whither who whoever whole whom whose why will with within without would www
xls
yet you
your yours yourself yourselves
i ii iii iv v vi vii viii ix x xi xii xiii xiv xv xvi xvii xviii xix xx xxi xxii xxiii xxiv xxv xxvi xxvii xxviii xxix xxx
"""
STOPWORDS = frozenset(w.encode('utf8') for w in STOPWORDS.split() if w)

SPLIT_SENTENCES = re.compile(u"[.!?:]\s+")  # split sentences on '.!?:' characters

def stem_tokenize(doc, deacc=True, lowercase=True, errors="strict", stemmer=None):
    """ Split into words and stem that word if a stemmer is given"""
    if stemmer is None:
        for token in tokenize(doc, lowercase=lowercase, deacc=deacc, errors=errors):
            yield token
    else:
         for token in tokenize(doc, lowercase=lowercase, deacc=deacc, errors=errors):
            yield stemmer.stemWord(token)


def simple_preprocess(doc, deacc=True, lowercase=True, errors='ignore',
    stemmer=None, stopwords=None):
    """
    Convert a document into a list of tokens.

    This lowercases, tokenizes, stems, normalizes etc. -- the output are final,
    utf8 encoded strings that won't be processed any further.
    """
    if not stopwords:
        stopwords = []
    #tokens = [token.encode('utf8') for token in
    #            tokenize(doc, lowercase=lowercase, deacc=deacc, errors=errors)
    #        if 2 <= len(token) <= 25 and
    #            not token.startswith('_') and
    #            token not in STOPWORDS]
    #return tokens
    for token in stem_tokenize(doc, lowercase=lowercase, deacc=deacc, errors=errors, stemmer=stemmer):
        if 2 <= len(token) <= 25 and not token.startswith(u'_') and token not in stopwords:
            yield token.encode('utf8')



def bigram_preprocess(doc, deacc=True, lowercase=True, errors='ignore',
    stemmer=None, stopwords=None):
    """
    Convert a document into a list of tokens.

    Split text into sentences and sentences into bigrams.
    the bigrams returned are the tokens
    """
    bigrams = []
    #split doc into sentences
    for sentence in SPLIT_SENTENCES.split(doc):
        #split sentence into tokens
        tokens = list(simple_preprocess(sentence, deacc, lowercase, errors=errors,
            stemmer=stemmer, stopwords=stopwords))
        #construct bigrams from tokens
        if len(tokens) >1:
            for i in range(0,len(tokens)-1):
                yield tokens[i] + '_' + tokens[i+1]



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

