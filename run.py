#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
A script to test model automatically or generate result file of the model.

Usage
-----
    $ python run.py test model-sgm model-lr model-lfm
    $ python run.py gen model-sgm

Arguments
---------

1:  command, 'test' or 'gen'.
    'test' - test the model
    'gen'  - generate result file of the model

2~: model name, i.e., the folder where corresponding pred.py lies
    *NOTE*: command `gen` accepts one model only

Note
----

There should be a function named `get_model` in pred.py, which returns
a properly initialized model object.

A model object should have at least two methods: `fit` and `predict`.
`fit` accepts a ndarray as parameter, of which column = [user_id, brand_id,
type, visit_datetime], and it returns nothing.
`predict` accepts a time unit as parameter, which stands for now, and it
should return a tuple of two
ndarray:
    the first one: shape = [n_results, 2], column=[user_id, item_id]
    the second one: shape = [n_results], rating score of each corresponding prediction
"""

import numpy as np
import pylab as pl

import sys
import os
import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, 'data')
sys.path.append(data_path)
import prep

all_data = np.load(os.path.join(data_path, 'raw_data.npy'))

def ndarray2dict(ndarray):
    result = {}
    for u, i in ndarray:
        result.setdefault(u, set())
        result[u].add(i)
    return result

def f1(pred_result, test_result, all_userids):
    """
    pred_result has the same format as test_result:
        key: user_id
        value: set of brand_id
    """
    pBrands = sum([len(pred_result[ui]) for ui in pred_result])
    hitBrands = 0
    for ui in np.unique(all_userids):
        if ui in pred_result and ui in test_result:
            hitBrands += len(pred_result[ui].intersection(test_result[ui]))
    bBrands = sum([len(test_result[ui]) for ui in test_result])
    p = hitBrands * 1. / pBrands
    assert 0 < p <= 1
    r = hitBrands * 1. / bBrands
    assert 0 < r <= 1
    return (p, r, 2.*p*r/(p+r))

def test():
    if len(sys.argv) < 3:
        raise LookupError('Please specify model to test.')
    test_cases = [
        (prep.date(5, 16), prep.date(6, 16), 'predicts 5/16 to 6/16', '5/16'),
        (prep.date(6, 16), prep.date(7, 16), 'predicts 6/16 to 7/16', '6/16'),
        (prep.date(7, 16), prep.date(8, 16), 'predicts 7/16 to 8/16', '7/16'),
    ]
    for model in sys.argv[2:]:
        sys_path = sys.path[:]
        model_path = os.path.join(current_dir, model)
        sys.path.append(model_path)
        import pred
        print('======')
        print('Model:\t%s' % model)
        Ps = []
        Rs = []
        Fs = []
        for TRAIN_DATE, TEST_DATE, DESC, _ in test_cases:
            model = pred.get_model()
            train_data = all_data[all_data[:, 3] < TRAIN_DATE]
            model.fit(train_data)
            pred_result = ndarray2dict(model.predict(TRAIN_DATE-1))
            test_data = all_data[np.logical_and(
                all_data[:, 3] >= TRAIN_DATE,
                all_data[:, 3] < TEST_DATE,
                )]
            test_result = test_data[:, :2]
            all_userids = train_data[:, 0]
            p, r, f = f1(pred_result, test_result, all_userids)
            Ps.append(p)
            Rs.append(r)
            F1s.append(f)
            print('******')
            print(DESC)
            print('Precision:\t%f' % p)
            print('Recall:\t%f' % r)
            print('F1 Score:\t%f' % f)
        pl.figure(model)
        pl.plot(range(len(test_cases)), Ps)
        pl.plot(range(len(test_cases)), Rs)
        pl.plot(range(len(test_cases)), Fs)
        pl.legend(('Precision', 'Recall', 'F1 Score'))
        pl.xticks(range(len(test_cases)), [i[3] for i in test_cases])
        pl.show()
        sys.path = sys_path

def gen():
    sys_path = sys.path[:]
    if len(sys.argv) < 3:
        raise LookupError('Please specify model result to transfer.')
    elif len(sys.argv) > 3:
        raise UserWarning('Only one model result can be transfered.')
    model_path = os.path.join(current_dir, sys.argv[2])
    sys.path.append(model_path)
    import pred
    model = pred.get_model()
    model.fit(all_data)
    pred_result = ndarray2dict(model.predict(prep.date(8, 15)))
    lines = []
    for u, items in pred_result.items():
        line = '{0}\t{1}\n'.format(u, ','.join([str(i) for i in items]))
        lines.append(line)
    target_path = os.path.join(current_dir, 'result{0}.txt'.format(date.today().day))
    f = open(target_path, 'w')
    f.writelines(lines)
    f.close()
    sys.path = sys_path

if __name__ == '__main__':
    if sys.argv[1] not in ['test', 'gen']:
        raise LookupError('Unknown command: %d' % sys.argv[1])
    eval('%s()' % sys.argv[1])
