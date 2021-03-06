"""
Copyright 2017 Neural Networks and Deep Learning lab, MIPT

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import copy
import numpy as np
import urllib.request
import fasttext


class EmbeddingsDict(object):
    def __init__(self, opt, embedding_dim):
        self.tok2emb = {}
        self.embedding_dim = embedding_dim
        self.opt = copy.deepcopy(opt)
        self.load_items()

        if not self.opt.get('fasttext_model'):
            raise RuntimeError('No pretrained fasttext model provided')
        self.fasttext_model_file = self.opt.get('fasttext_model')
        if not os.path.isfile(self.fasttext_model_file):
            emb_path = os.environ.get('EMBEDDINGS_URL')
            if not emb_path:
                raise RuntimeError('No pretrained fasttext model provided')
            fname = os.path.basename(self.fasttext_model_file)
            try:
                print('Trying to download a pretrained fasttext model from repository')
                url = urllib.parse.urljoin(emb_path, fname)
                urllib.request.urlretrieve(url, self.fasttext_model_file)
                print('Downloaded a fasttext model')
            except Exception as e:
                raise RuntimeError('Looks like the `EMBEDDINGS_URL` variable is set incorrectly', e)
        self.fasttext_model = fasttext.load_model(self.fasttext_model_file)

    def add_items(self, sentence_li):
        for sen in sentence_li:
            tokens = sen.split(' ')
            tokens = [el for el in tokens if el != '']
            for tok in tokens:
                if self.tok2emb.get(tok) is None:
                    self.tok2emb[tok] = self.fasttext_model[tok]

    def save_items(self, fname):
        if self.opt.get('fasttext_embeddings_dict') is not None:
            fname = self.opt['fasttext_embeddings_dict']
        else:
            fname += '.emb'
        f = open(fname, 'w')
        string = '\n'.join([el[0] + ' ' + self.emb2str(el[1]) for el in self.tok2emb.items()])
        f.write(string)
        f.close()

    def emb2str(self, vec):
        string = ' '.join([str(el) for el in vec])
        return string

    def load_items(self):
        """Initialize embeddings from file."""
        fname = None
        if self.opt.get('fasttext_embeddings_dict') is not None:
            fname = self.opt['fasttext_embeddings_dict']
        elif self.opt.get('pretrained_model') is not None:
            fname = self.opt['pretrained_model']+'.emb'
        elif self.opt.get('model_file') is not None:
            fname = self.opt['model_file']+'.emb'

        if fname is None or not os.path.isfile(fname):
            print('There is no %s file provided. Initializing new dictionary.' % fname)
        else:
            print('Loading existing dictionary from %s.' % fname)
            with open(fname, 'r') as f:
                for line in f:
                    values = line.rsplit(sep=' ', maxsplit=self.embedding_dim)
                    assert(len(values) == self.embedding_dim + 1)
                    word = values[0]
                    coefs = np.asarray(values[1:], dtype='float32')
                    self.tok2emb[word] = coefs