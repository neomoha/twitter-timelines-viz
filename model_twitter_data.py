import os, sys, codecs, json, argparse, string, urlparse

from gensim import corpora, models, similarities, matutils

def incr():
    i = 0
    while True:
        yield i
        i += 1

def is_url(url):
    return urlparse.urlparse(url).scheme != ""

def load_stopwords():
    stopwords = []
    with open('stopwords.txt') as f:
        stopwords = [line.rstrip() for line in f]
    return stopwords

def create_corpus(username, replace=False):
    user_filename = "%s__friends_timelines.json" % args.username
    if not os.path.exists(user_filename):
        return -1
    if os.path.exists('corpus/'+username+"/corpus.mm") and replace == False:
        return 0
    timelines = json.load(codecs.open(user_filename, "r", "utf-8"))
    stopwords = load_stopwords()
    if not os.path.exists('corpus'):
        os.mkdir('corpus')
    if not os.path.exists('corpus/'+username):
        os.mkdir('corpus/'+username)
    words = {}
    count, idx_tweets = 0, 0
    punctuations = "".join([p for p in string.punctuation if p not in ('@', '#')])
    for user, timeline in timelines.iteritems():
        for tweet in timeline:
            for token in tweet.split(): #iterate over the tokens (words) in the tweet
                token = token.rstrip(string.punctuation) #remove punctuation marks from the end of the word
                token = token.lstrip(punctuations) #remove punctuation marks from the beginning of the word
                #if token is not a stopword, has at least 2 characters and is not a URL
                if token.lower() not in stopwords and len(token)>=2 and not is_url(token):
                    words.setdefault(token, []).append(str(idx_tweets))
            idx_tweets += 1
        count += 1
        if count % 10 == 0:
            print count, 'friends processed'
    id2token = {}
    texts = []
    idx = incr()
    for word, occurrences in sorted(words.iteritems()):
        if len(occurrences) > 1: #only words that appear more than once
            id2token[idx.next()] = word 
            texts.append(occurrences)
    dictionary = corpora.Dictionary(texts)
    dictionary.save('corpus/'+username+'/dictionary.dict')
    json.dump(id2token, codecs.open('corpus/'+username+'/id2token.json', 'w', 'utf-8'))
    corpus = [dictionary.doc2bow(text) for text in texts]
    corpora.MmCorpus.serialize('corpus/'+username+'/corpus.mm', corpus) # store to disk, for later use
    return 0
    
def process_corpus(username):
    dictionary = corpora.Dictionary.load('corpus/'+username+'/dictionary.dict')
    corpus = corpora.MmCorpus('corpus/'+username+'/corpus.mm')
    id2token = json.load(codecs.open('corpus/'+username+'/id2token.json', 'r', 'utf-8'))
    tfidf = models.TfidfModel(corpus) # step 1 -- initialize a model
    corpus_tfidf = tfidf[corpus]
    for num_topics in [2,3]:
        lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=num_topics) # initialize an LSI transformation
        corpus_lsi = lsi[corpus_tfidf] # create a double wrapper over the original corpus: bow->tfidf->fold-in-lsi
        f = codecs.open('corpus/'+username+'/token_repr_%dd.tsv' % num_topics, 'w', 'utf-8')
        idx = incr()
        for vector in corpus_lsi:
            point = "\t".join([str(ax[1]) for ax in vector])
            f.write("%s\t%s\n" % (id2token[str(idx.next())], point))
        f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Model Twitter timelines of a certain user\'s friends.')
    parser.add_argument('username', help='Twitter user name')
    parser.add_argument("-r", "--replace-corpus", help="Replace the previous corpus if there was any", action="store_true")
    args = parser.parse_args()
    code = create_corpus(args.username, replace=args.replace_corpus)
    if code == -1:
        print "There is no timeline file for this user"
        sys.exit()
    process_corpus(args.username)
    
    

