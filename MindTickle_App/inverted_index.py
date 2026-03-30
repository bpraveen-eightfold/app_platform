"""
Inverted index for small indices (for larger ones use solr).
1. add_doc_to_index(): Add a document (token or list) to the index. Specify doc_id to associate with this doc.
2. query(): given a key (token or list), find all matching docs. Optionally specify full_query_match, full_doc_match and min_match.
eg:
index = InvertedIndex("name")
index.add_doc_to_index("foo bar", doc_id=1)
index.add_doc_to_index("bar baz", doc_id=2)
index.query("foo")
"""
from __future__ import absolute_import

import re
import traceback
from collections import defaultdict

import glog as log
import six
import heapq

INDEX_REGISTERY = {}

def generate_ngrams(lst, ngram=3, delim=' ', ngram_min=1):
    ngrams = []
    for i in range(ngram_min, ngram + 1):
        ngrams.extend([delim.join(gram) for gram in zip(*[lst[j:] for j in range(i)])])
    return ngrams

class InvertedIndex:
    def __init__(self, index_name, tokenize_lowercase=True, tokenize_ngram=True, tokenize_stopwords=None, add_to_registry=True):
        self.index_name = index_name
        if self.index_name in INDEX_REGISTERY:
            log.warn('Duplicate index being registered %s %s', self.index_name, traceback.format_stack())
        if add_to_registry:
            INDEX_REGISTERY[self.index_name] = self
        self.index = defaultdict(list)
        self.doc = {}
        self.doc_tokens = {}
        self.doc_metadata = {}
        self.tokenize_lowercase = tokenize_lowercase
        self.tokenize_ngram = tokenize_ngram
        self.tokenize_stopwords = set(tokenize_stopwords or [])

    def get_doc_metadata(self, doc_id):
        return self.doc_metadata[doc_id]

    def add_doc_to_index(self, token_or_list, doc_id=None, tokenize=True, doc_metadata=None):
        if doc_id is None:
            doc_id = 1 + len(self.doc)
        if not self.doc.get(doc_id):
            self.doc[doc_id] = token_or_list
        if doc_metadata:
            self.doc_metadata[doc_id] = doc_metadata
        if tokenize or isinstance(token_or_list, (list, set)):
            tokens = self._tokenize(token_or_list)
        else:
            tokens = [token_or_list.lower().strip()] if self.tokenize_lowercase else [token_or_list]
        self.doc_tokens[doc_id] = tokens
        for t in tokens:
            if doc_id not in self.index[t]:
                self.index[t].append(doc_id)
        return doc_id

    def query(self,
              token_or_list,
              default=None,
              tokenize=True,
              full_query_match=False,
              full_doc_match=False,
              # match score is computed as sum of len of words
              min_match=0,
              limit=10,
              include_metadata=False,
              return_match_score=False,
              partial_query_match=False,
              score_fn=lambda x: len(x)):
        match_score = {}
        if tokenize or isinstance(token_or_list, (list, set)):
            words = self._tokenize(token_or_list)
            if min_match < 1:  # it's a percent
                min_match = int(min_match * sum([score_fn(w) for w in words] or [0]))
        else:
            words = [token_or_list.lower().strip()] if self.tokenize_lowercase else [token_or_list]
        #adding the token string itself to the tokenized words if it's not already present
        if partial_query_match:
            tokens = token_or_list.lower() if isinstance(token_or_list, six.string_types) else ' '.join(token_or_list).lower()
            if tokens not in words:
                words.append(tokens)
        if full_query_match:
            min_match = sum(score_fn(w) for w in words) - 1
        for word in set(words):
            doc_ids = self.index.get(word, [])
            # for full_query_match all tokens in query should be present in document
            if not doc_ids and full_query_match:
                return (default, default) if limit == 1 else [(default, default)]
            for doc_id in doc_ids:
                if partial_query_match:
                    #the scoring function for partial query match takes into account that the docs that match are close to the query term
                    #in the number of words that they contain. For example, for the query term `analyst`, the matches will be ordered as follows
                    #[`analyst`, `data analyst`, `data analyst programmer`] 
                    match_score[doc_id] = match_score.get(doc_id, 0) + score_fn(word) * 1/(1 + abs(len(words[-1].split()) - len(self.doc[doc_id].split())))
                else:
                    match_score[doc_id] = match_score.get(doc_id, 0) + score_fn(word)

        match_score_heap = MaxHeap()
        for x, y in match_score.items():
            if y > min_match and (not full_doc_match or all(dword in words for dword in self.doc_tokens.get(x))):
                match_score_heap.push((y, x))
        if not match_score_heap.data:
            return (default, default) if limit == 1 else [(default, default)]
        if limit == 1:
            candidate_matches = match_score_heap.pop()
            if include_metadata:
                if return_match_score:
                    return candidate_matches[1], self.doc.get(candidate_matches[1]), self.doc_metadata.get(candidate_matches[1]), candidate_matches[0]
                else:
                    return candidate_matches[1], self.doc.get(candidate_matches[1]), self.doc_metadata.get(candidate_matches[1])
            else:
                if return_match_score:
                    return candidate_matches[1], self.doc.get(candidate_matches[1]), candidate_matches[0]
                else:
                    return candidate_matches[1], self.doc.get(candidate_matches[1])
        candidate_matches = [match_score_heap.pop() for i in range(min(limit, len(match_score_heap.data)))]
        if include_metadata:
            if return_match_score:
                return [(tup[1], self.doc.get(tup[1]), self.doc_metadata.get(tup[1]), tup[0]) for tup in candidate_matches]
            else:
                return [(tup[1], self.doc.get(tup[1]), self.doc_metadata.get(tup[1])) for tup in candidate_matches]
        else:
            if return_match_score:
                return [(tup[1], self.doc.get(tup[1]), tup[0]) for tup in candidate_matches]
            else:
                return [(tup[1], self.doc.get(tup[1])) for tup in candidate_matches]

    def _tokenize(self, token_or_list):
        if not isinstance(token_or_list, (list, set)):
            token_or_list = re.split(r"\W+", token_or_list, flags=re.UNICODE)
            if self.tokenize_ngram:
                token_or_list = generate_ngrams(token_or_list)
        ret = []
        for t in token_or_list:
            t = t.strip()
            if not t:
                continue
            if self.tokenize_lowercase:
                t = t.lower()
            if self.tokenize_stopwords and t in self.tokenize_stopwords:
                continue
            ret.append(t)
        return ret

class MaxHeap:

    #initialize the max heap
    def __init__(self, data=None):
        if data is None:
            self.data = []
        else:
            self.data = [self._negate(i) for i in data]
            heapq.heapify(self.data)

    def _negate(self, ele):
        if isinstance(ele, tuple):
            return tuple([-i for i in ele])
        elif isinstance(ele, list):
            return [-i for i in ele]
        else:
            return -ele

    def push(self, item):
        heapq.heappush(self.data, self._negate(item))

    def pop(self):
        return self._negate(heapq.heappop(self.data))

    def replace(self, item):
        return heapq.heapreplace(self.data, self._negate(item))

    def top(self):
        return self._negate(self.data[0])
