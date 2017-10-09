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

import numpy as np
import time
import os
from os.path import join, basename
import json
from sklearn import cross_validation
from tqdm import tqdm
import parlai.core.build_data as build_data
import tensorflow as tf

def RuCoref2CoNLL(path, out_path, language='russian'):
    data = {"doc_id": [],
            "part_id": [],
            "word_number": [],
            "word": [],
            "part_of_speech": [],
            "parse_bit": [],
            "lemma": [],
            "sense": [],
            "speaker": [],
            "entiti": [],
            "predict": [],
            "coref": []}

    part_id = '0'
    speaker = 'spk1'
    sense = '-'
    entiti = '-'
    predict = '-'

    tokens_ext = "txt"
    groups_ext = "txt"
    tokens_fname = "Tokens"
    groups_fname = "Groups"

    tokens_path = os.path.join(path, ".".join([tokens_fname, tokens_ext]))
    groups_path = os.path.join(path, ".".join([groups_fname, groups_ext]))
    print('Convert rucoref corpus into conll format ...')
    start = time.time()
    coref_dict = {}
    with open(groups_path, "r") as groups_file:
        for line in groups_file:
            doc_id, variant, group_id, chain_id, link, shift, lens, content, tk_shifts, attributes, head, hd_shifts = line[
                                                                                                                      :-1].split('\t')

            if doc_id not in coref_dict:
                coref_dict[doc_id] = {'unos': {}, 'starts': {}, 'ends': {}}
                if len(tk_shifts.split(',')) == 1:
                    if tk_shifts not in coref_dict[doc_id]['unos']:
                        coref_dict[doc_id]['unos'][shift] = [chain_id]
                    else:
                        coref_dict[doc_id]['unos'][shift].append(chain_id)
                else:
                    tk = tk_shifts.split(',')
                    if tk[0] not in coref_dict[doc_id]['starts']:
                        coref_dict[doc_id]['starts'][tk[0]] = [chain_id]
                    else:
                        coref_dict[doc_id]['starts'][tk[0]].append(chain_id)
                    if tk[-1] not in coref_dict[doc_id]['ends']:
                        coref_dict[doc_id]['ends'][tk[-1]] = [chain_id]
                    else:
                        coref_dict[doc_id]['ends'][tk[-1]].append(chain_id)
            else:
                if len(tk_shifts.split(',')) == 1:
                    if tk_shifts not in coref_dict[doc_id]['unos']:
                        coref_dict[doc_id]['unos'][shift] = [chain_id]
                    else:
                        coref_dict[doc_id]['unos'][shift].append(chain_id)
                else:
                    tk = tk_shifts.split(',')
                    if tk[0] not in coref_dict[doc_id]['starts']:
                        coref_dict[doc_id]['starts'][tk[0]] = [chain_id]
                    else:
                        coref_dict[doc_id]['starts'][tk[0]].append(chain_id)
                    if tk[-1] not in coref_dict[doc_id]['ends']:
                        coref_dict[doc_id]['ends'][tk[-1]] = [chain_id]
                    else:
                        coref_dict[doc_id]['ends'][tk[-1]].append(chain_id)
        groups_file.close()

    # Write conll structure
    with open(tokens_path, "r") as tokens_file:
        k = 0
        for line in tokens_file:
            doc_id, shift, length, token, lemma, gram = line[:-1].split('\t')
            if doc_id == 'doc_id':
                continue
            data['word_number'].append(k)
            data['word'].append(token)
            if token == '.':
                k = 0
            else:
                k += 1
            data['doc_id'].append('bc' + doc_id)
            data['part_id'].append(part_id)
            data['lemma'].append(lemma)
            data['part_of_speech'].append(gram[0:-1])
            data['sense'].append(sense)
            data['speaker'].append(speaker)
            data['entiti'].append(entiti)
            data['predict'].append(predict)
            data['parse_bit'].append('-')

            opens = coref_dict[doc_id]['starts'][shift] if shift in coref_dict[doc_id]['starts'] else []
            ends = coref_dict[doc_id]['ends'][shift] if shift in coref_dict[doc_id]['ends'] else []
            unos = coref_dict[doc_id]['unos'][shift] if shift in coref_dict[doc_id]['unos'] else []
            s = []
            s += ['({})'.format(el) for el in unos]
            s += ['({}'.format(el) for el in opens]
            s += ['{})'.format(el) for el in ends]
            s = '|'.join(s)
            if len(s) == 0:
                s = '-'
                data['coref'].append(s)
            else:
                data['coref'].append(s)

        tokens_file.close()
        # Write conll structure in file
    conll = os.path.join(out_path, ".".join([language, 'v4_conll']))
    with open(conll, 'w') as CoNLL:
        for i in tqdm(range(len(data['doc_id']))):
            if i == 0:
                CoNLL.write('#begin document ({}); part {}\n'.format(data['doc_id'][i], data["part_id"][i]))
                CoNLL.write(u'{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(data['doc_id'][i],
                                                                                       data["part_id"][i],
                                                                                       data["word_number"][i],
                                                                                       data["word"][i],
                                                                                       data["part_of_speech"][i],
                                                                                       data["parse_bit"][i],
                                                                                       data["lemma"][i],
                                                                                       data["sense"][i],
                                                                                       data["speaker"][i],
                                                                                       data["entiti"][i],
                                                                                       data["predict"][i],
                                                                                       data["coref"][i]))
            elif i == len(data['doc_id']) - 1:
                CoNLL.write(u'{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(data['doc_id'][i],
                                                                                       data["part_id"][i],
                                                                                       data["word_number"][i],
                                                                                       data["word"][i],
                                                                                       data["part_of_speech"][i],
                                                                                       data["parse_bit"][i],
                                                                                       data["lemma"][i],
                                                                                       data["sense"][i],
                                                                                       data["speaker"][i],
                                                                                       data["entiti"][i],
                                                                                       data["predict"][i],
                                                                                       data["coref"][i]))
                CoNLL.write('\n')
                CoNLL.write('#end document\n')
            else:
                if data['doc_id'][i] == data['doc_id'][i + 1]:
                    CoNLL.write(u'{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(data['doc_id'][i],
                                                                                           data["part_id"][i],
                                                                                           data["word_number"][i],
                                                                                           data["word"][i],
                                                                                           data["part_of_speech"][i],
                                                                                           data["parse_bit"][i],
                                                                                           data["lemma"][i],
                                                                                           data["sense"][i],
                                                                                           data["speaker"][i],
                                                                                           data["entiti"][i],
                                                                                           data["predict"][i],
                                                                                           data["coref"][i]))
                    if data["word_number"][i + 1] == 0:
                        CoNLL.write('\n')
                else:
                    CoNLL.write(u'{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(data['doc_id'][i],
                                                                                           data["part_id"][i],
                                                                                           data["word_number"][i],
                                                                                           data["word"][i],
                                                                                           data["part_of_speech"][i],
                                                                                           data["parse_bit"][i],
                                                                                           data["lemma"][i],
                                                                                           data["sense"][i],
                                                                                           data["speaker"][i],
                                                                                           data["entiti"][i],
                                                                                           data["predict"][i],
                                                                                           data["coref"][i]))
                    CoNLL.write('\n')
                    CoNLL.write('#end document\n')
                    CoNLL.write('#begin document ({}); part {}\n'.format(data['doc_id'][i + 1], data["part_id"][i + 1]))

    print('End of convertion. Time - {}'.format(time.time() - start))
    return None


def split_doc(inpath, outpath, language):
    # split massive conll file to many little
    print('Start of splitting ...')
    with open(inpath, 'r+') as f:
        lines = f.readlines()
        f.close()
    set_ends = []
    k = 0
    print('Splitting conll document ...')
    for i in range(len(lines)):
        if lines[i] == '#end document\n':
            set_ends.append([k, i])
            k = i + 1
    for i in range(len(set_ends)):
        cpath = os.path.join(outpath, ".".join([str(i), language, 'v4_conll']))
        with open(cpath, 'w') as c:
            for j in range(set_ends[i][0], set_ends[i][1] + 1):
                c.write(lines[j])
            c.close()

    del lines
    print('Splitts {} docs in {}.'.format(len(set_ends), outpath))
    del set_ends
    del k

    return None


def train_test_split(inpath, output, split, random_seed):
    z = os.listdir(inpath)
    doc_split = cross_validation.ShuffleSplit(len(z),
                                              n_iter=1,
                                              test_size=split,
                                              random_state=random_seed)
    train_set = [z[i] for i in sorted(list(doc_split)[0][0])]
    # test_set = [z[i] for i in sorted(list(doc_split)[0][1])]

    # train_path = os.path.join(output, 'train')
    # test_path = os.path.join(output, 'test')

    for x in train_set:
        build_data.move(os.path.join(inpath, x), os.path.join(output, x))
    # for x in os.listdir(inpath):
    #     build_data.move(os.path.join(inpath, x), os.path.join(test_path, x))

    return None


def get_all_texts_from_tokens_file(tokens_path, out_path):
    lengths = {}
    # determine number of texts and their lengths
    with open(tokens_path, "r") as tokens_file:
        for line in tokens_file:
            doc_id, shift, length, token, lemma, gram = line[:-1].split('\t')
            try:
                doc_id, shift, length = map(int, (doc_id, shift, length))
                lengths[doc_id] = shift + length
            except ValueError:
                pass

    texts = {doc_id: [' '] * length for (doc_id, length) in lengths.items()}
    # read texts
    with open(tokens_path, "r") as tokens_file:
        for line in tokens_file:
            doc_id, shift, length, token, lemma, gram = line[:-1].split('\t')
            try:
                doc_id, shift, length = map(int, (doc_id, shift, length))
                texts[doc_id][shift:shift + length] = token
            except ValueError:
                pass
    for doc_id in texts:
        texts[doc_id] = "".join(texts[doc_id])

    with open(out_path, "w") as out_file:
        for doc_id in texts:
            out_file.write(texts[doc_id])
            out_file.write("\n")
    return None

def get_char_vocab(input_filename, output_filename):
    data = open(input_filename, "r").read()
    vocab = sorted(list(set(data)))

    with open(output_filename, 'w') as f:
        for c in vocab:
            f.write(u"{}\n".format(c))
    print("[Wrote {} characters to {}] ...".format(len(vocab), output_filename))

def conll2dict(iter_id, conll, agent, mode, doc, epoch_done=False):
    data = {'doc_id': [],
            'part_id': [],
            'word_number': [],
            'word': [],
            'part_of_speech': [],
            'parse_bit': [],
            'lemma': [],
            'sense': [],
            'speaker': [],
            'entiti': [],
            'predict': [],
            'coreference': [],
            'iter_id': iter_id,
            'id': agent,
            'epoch_done': epoch_done,
            'mode': mode,
            'doc_name': doc}

    with open(conll, 'r') as f:
        for line in f:
            row = line.split('\t')
            if row[0].startswith('#'):
                continue
            elif row[0] == '\n':
                data['doc_id'].append('bc')
                data['part_id'].append('0')
                data['word_number'].append('0')
                data['word'].append('.')
                data['part_of_speech'].append('End_of_sentence')
                data['parse_bit'].append('-')
                data['lemma'].append('-')
                data['sense'].append('-')
                data['speaker'].append('spk1')
                data['entiti'].append('-')
                data['predict'].append('-')
                data['coreference'].append('-')
            else:
                assert len(row) >= 12
                data['doc_id'].append(row[0])
                data['part_id'].append(row[1])
                data['word_number'].append(row[2])
                data['word'].append(row[3])
                data['part_of_speech'].append(row[4])
                data['parse_bit'].append(row[5])
                data['lemma'].append(row[6])
                data['sense'].append(row[7])
                data['speaker'].append(row[8])
                data['entiti'].append(row[9])
                data['predict'].append(row[10])
                data['coreference'].append(row[11][0:-1])
        f.close()
    return data

def dict2conll(data, predict):
    #
    with open(predict, 'w') as CoNLL:
        for i in range(len(data['doc_id'])):
            if i == 0:
                CoNLL.write('#begin document ({}); part {}\n'.format(data['doc_id'][i], data["part_id"][i]))
                CoNLL.write(u'{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(data['doc_id'][i],
                                                    data["part_id"][i],
                                                    data["word_number"][i],
                                                    data["word"][i],
                                                    data["part_of_speech"][i],
                                                    data["parse_bit"][i],
                                                    data["lemma"][i],
                                                    data["sense"][i],
                                                    data["speaker"][i],
                                                    data["entiti"][i],
                                                    data["predict"][i],
                                                    data["coreference"][i]))
            elif i == len(data['doc_id'])-1 and data['part_of_speech'][i] == 'End_of_sentence':
                CoNLL.write('#end document\n')
            elif data['part_of_speech'][i] == 'End_of_sentence':
                continue
            else:
                if data['doc_id'][i] == data['doc_id'][i+1]:
                    CoNLL.write(u'{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(data['doc_id'][i],
                                                        data["part_id"][i],
                                                        data["word_number"][i],
                                                        data["word"][i],
                                                        data["part_of_speech"][i],
                                                        data["parse_bit"][i],
                                                        data["lemma"][i],
                                                        data["sense"][i],
                                                        data["speaker"][i],
                                                        data["entiti"][i],
                                                        data["predict"][i],
                                                        data["coreference"][i]))
                elif data['part_of_speech'][i] == 'End_of_sentence':
                    continue
                else:
                    CoNLL.write(u'{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n'.format(data['doc_id'][i],
                                                    data["part_id"][i],
                                                    data["word_number"][i],
                                                    data["word"][i],
                                                    data["part_of_speech"][i],
                                                    data["parse_bit"][i],
                                                    data["lemma"][i],
                                                    data["sense"][i],
                                                    data["speaker"][i],
                                                    data["entiti"][i],
                                                    data["predict"][i],
                                                    data["coreference"][i]))
                    CoNLL.write('\n')
        CoNLL.close()
    return None

def score(scorer, keys_path, predicts_path):
    key_files = []
    pred_files = []
    
    for dirpath, dirnames, filenames in os.walk(keys_path):
        # f.endswith("auto_conll") or f.endswith("gold_conll") or f.endswith('gold_parse_conll')
        for filename in [f for f in filenames if (f.endswith('v4_conll'))]:
            key_files.append(os.path.join(dirpath, filename))
    key_files = list(sorted(key_files))
    
    for dirpath, dirnames, filenames in os.walk(predicts_path):
        # f.endswith("auto_conll") or f.endswith("gold_conll") or f.endswith('gold_parse_conll')
        for filename in [f for f in filenames if (f.endswith('v4_conll'))]:
            pred_files.append(os.path.join(dirpath, filename))
    pred_files = list(sorted(pred_files))    

    print('score: Files to process: {}'.format(len(pred_files)))
    for key_file in tqdm(pred_files):
        predict_files = join(predicts_path, basename(key_file))
        gold_files = join(keys_path, basename(key_file))
        for metric in ['muc', 'bcub', 'ceafm', 'ceafe']:
            out_pred_score = '{0}.{1}'.format(join(predicts_path, basename(key_file)), metric)
            cmd = '{0} {1} {2} {3} none > {4}'.format(scorer, metric, gold_files, predict_files, out_pred_score)
            #print(cmd)
            os.system(cmd)

    # make sure that all files processed
    time.sleep(1)

    print('score: aggregating results...')
    k = 0
    results = dict()

    f1=[]
    for metric in ['muc', 'bcub', 'ceafm', 'ceafe']:
        recall = []
        precision = []
        for key_file in pred_files:
            out_pred_score = '{0}.{1}'.format(join(predicts_path, basename(key_file)), metric)
            with open(out_pred_score, 'r', encoding='utf8') as score_file:
                lines = score_file.readlines()
                if lines[-1].strip() != '--------------------------------------------------------------------------':
                    continue

                coreference_scores_line = lines[-2]
                tokens = coreference_scores_line.replace('\t', ' ').split()
                r1 = float(tokens[2].strip('()'))
                r2 = float(tokens[4].strip('()'))
                p1 = float(tokens[7].strip('()'))
                p2 = float(tokens[9].strip('()'))
                if r2 == 0 or p2 == 0:
                    continue
                recall.append((r1, r2))
                precision.append((p1, p2))
                k += 1

        r1 = sum(map(lambda x: x[0], recall))
        r2 = sum(map(lambda x: x[1], recall))
        p1 = sum(map(lambda x: x[0], precision))
        p2 = sum(map(lambda x: x[1], precision))
        
        
        r = 0 if r2 == 0 else r1 / float(r2)
        p = 0 if p2 ==0 else p1 / float(p2)
        f = 0 if (p+r) == 0 else (2 * p * r) / (p + r)
        
        
        f1.append(f)
        print('{0} precision: ({1:.3f}/{2}) {3:.3f}\t recall: ({4:.3f}/{5}) {6:.3f}\t F-1: {7:.5f}'.format(metric, p1, p2, p, r1, r2, r, f))
        results[metric] = {'p': p, 'r': r, 'f-1': f}

    print('avg: {0:.5f}'.format(np.mean(f1)))
    # muc bcub ceafe
    conllf1 = np.mean(f1[:2] + f1[-1:])
    print('conll F-1: {0:.5f}'.format(conllf1))
    print('using {}/{}'.format(k, 4 * len(key_files)))
    results['avg F-1'] = np.mean(f1)
    results['conll-F-1'] = conllf1
    json.dump(results, open(join(predicts_path, 'results.json'), 'w'))
    return results

def make_summary(value_dict):
    return tf.Summary(value=[tf.Summary.Value(tag=k, simple_value=v) for k, v in value_dict.items()])

def summary(value_dict, global_step, writer):
    summary = tf.Summary(value=[tf.Summary.Value(tag=k, simple_value=v) for k, v in value_dict.items()])
    writer.add_summary(summary, global_step)
    return None
