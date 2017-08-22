# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.
"""Train a model.

After training, computes validation and test error.

Run with, e.g.:

python examples/train_model.py -m ir_baseline -t dialog_babi:Task:1 -mf /tmp/model

..or..

python examples/train_model.py -m seq2seq -t babi:Task10k:1 -mf '/tmp/model' -bs 32 -lr 0.5 -hs 128

..or..

python examples/train_model.py -m drqa -t babi:Task10k:1 -mf /tmp/model -bs 10

TODO List:
- More logging (e.g. to files), make things prettier.
"""
from parlai.core.agents import create_agent
from parlai.core.worlds import create_task
from parlai.core.params import ParlaiParser
from parlai.core.utils import Timer
import build_dict
import math

def run_eval(agent, opt, datatype, max_exs=-1, write_log=False, valid_world=None):
    """Eval on validation/test data.
    - Agent is the agent to use for the evaluation.
    - opt is the options that specific the task, eval_task, etc
    - datatype is the datatype to use, such as "valid" or "test"
    - write_log specifies to write metrics to file if the model_file is set
    - max_exs limits the number of examples if max_exs > 0
    - valid_world can be an existing world which will be reset instead of reinitialized
    """
    print('[ running eval: ' + datatype + ' ]')
    opt['datatype'] = datatype
    if opt.get('evaltask'):

        opt['task'] = opt['evaltask']

    if valid_world is None:
        valid_world = create_task(opt, agent)
    else:
        valid_world.reset()
    cnt = 0
    for _ in valid_world:
        valid_world.parley()
        if cnt == 0 and opt['display_examples']:
            print(valid_world.display() + '\n~~')
            print(valid_world.report())
        cnt += opt['batchsize']
        if valid_world.epoch_done() or (max_exs > 0 and cnt > max_exs):
            # note this max_exs is approximate--some batches won't always be
            # full depending on the structure of the data
            break
    valid_report = valid_world.report()

    metrics = datatype + ':' + str(valid_report)
    print(metrics)
    if write_log and opt['model_file']:
        # Write out metrics
        f = open(opt['model_file'] + '.' + datatype, 'a+')
        f.write(metrics + '\n')
        f.close()

    return valid_report, valid_world


def main():
    # Get command line arguments
    parser = ParlaiParser(True, True)
    train = parser.add_argument_group('Training Loop Arguments')
    train.add_argument('-et', '--evaltask',
                        help=('task to use for valid/test (defaults to the ' +
                              'one used for training if not set)'))
    train.add_argument('-d', '--display-examples',
                        type='bool', default=False)
    train.add_argument('-e', '--num-epochs', type=float, default=-1)
    train.add_argument('-ttim', '--max-train-time',
                        type=float, default=-1)
    train.add_argument('-ltim', '--log-every-n-secs',
                        type=float, default=2)
    train.add_argument('-le', '--log-every-n-epochs',
                        type=int, default=0)
    train.add_argument('-vtim', '--validation-every-n-secs',
                        type=float, default=-1)
    train.add_argument('-ve', '--validation-every-n-epochs',
                        type=int, default=0)
    train.add_argument('-vme', '--validation-max-exs',
                        type=int, default=-1,
                        help='max examples to use during validation (default ' +
                             '-1 uses all)')
    train.add_argument('-vp', '--validation-patience',
                        type=int, default=5,
                        help=('number of iterations of validation where result '
                              + 'does not improve before we stop training'))
    train.add_argument('-dbf', '--dict-build-first',
                        type='bool', default=True,
                        help='build dictionary first before training agent')
    opt = parser.parse_args()
    # Possibly build a dictionary (not all models do this).
    if opt['dict_build_first'] and 'dict_file' in opt:
        if opt['dict_file'] is None and opt.get('pretrained_model'):
            opt['dict_file'] = opt['pretrained_model'] + '.dict'
        if opt['dict_file'] is None and opt.get('model_file'):
            opt['dict_file'] = opt['model_file'] + '.dict'
        print("[ building dictionary first... ]")
        build_dict.build_dict(opt)
    # Create model and assign it to the specified task
    agent = create_agent(opt)
    if opt['datatype'].split(':')[0] == 'train':
        world = create_task(opt, agent)

        train_time = Timer()
        validate_time = Timer()
        log_time = Timer()
        print('[ training... ]')
        parleys = 0
        total_exs = 0
        max_exs = opt['num_epochs'] * len(world)
        epochs_done = 0
        max_parleys = math.ceil(max_exs / opt['batchsize'])
        best_accuracy = 0
        impatience = 0
        saved = False
        valid_world = None
        try:
            while True:
                world.parley()
                parleys += 1
                new_epoch = world.epoch_done()
                if new_epoch:
                    world.reset()
                    epochs_done += 1

                if opt['num_epochs'] > 0 and parleys >= max_parleys:
                    print('[ num_epochs completed: {} ]'.format(opt['num_epochs']))
                    break
                if 0 < opt['max_train_time'] < train_time.time():
                    print('[ max_train_time elapsed: {} ]'.format(train_time.time()))
                    break
                if (0 < opt['log_every_n_secs'] < log_time.time()) or \
                        (opt['log_every_n_epochs'] > 0 and new_epoch and
                                 (epochs_done % opt['log_every_n_epochs']) == 0):
                    if opt['display_examples']:
                        print(world.display() + '\n~~')

                    logs = list()
                    # time elapsed
                    logs.append('time:{}s'.format(math.floor(train_time.time())))
                    logs.append('parleys:{}'.format(parleys))
                    if epochs_done > 0:
                        logs.append('epochs done:{}'.format(epochs_done))

                    # get report and update total examples seen so far
                    if hasattr(agent, 'report'):
                        train_report = agent.report()
                        agent.reset_metrics()
                    else:
                        train_report = world.report()
                        world.reset_metrics()

                    if hasattr(train_report, 'get') and train_report.get('total'):
                        total_exs += train_report['total']
                        logs.append('total_exs:{}'.format(total_exs))

                    # check if we should log amount of time remaining
                    time_left = None
                    if opt['num_epochs'] > 0 and total_exs > 0:
                        exs_per_sec = train_time.time() / total_exs
                        time_left = (max_exs - total_exs) * exs_per_sec
                    if opt['max_train_time'] > 0:
                        other_time_left = opt['max_train_time'] - train_time.time()
                        if time_left is not None:
                            time_left = min(time_left, other_time_left)
                        else:
                            time_left = other_time_left
                    if time_left is not None:
                        logs.append('time_left:{}s'.format(math.floor(time_left)))

                    # join log string and add full metrics report to end of log
                    log = '[ {} ] {}'.format(' '.join(logs), train_report)

                    print(log)
                    log_time.reset()

                if 0 < opt['validation_every_n_secs'] < validate_time.time() or \
                        (opt['validation_every_n_epochs'] > 0 and new_epoch and (
                                    epochs_done % opt['validation_every_n_epochs']) == 0):

                    valid_report, valid_world = run_eval(agent, opt, 'valid',
                                                         opt['validation_max_exs'],
                                                         valid_world=valid_world)
                    if valid_report['accuracy'] > best_accuracy:
                        best_accuracy = valid_report['accuracy']
                        impatience = 0
                        print('[ new best accuracy: ' + str(best_accuracy) + ' ]')
                        world.save_agents()
                        saved = True
                        if best_accuracy == 1:
                            print('[ task solved! stopping. ]')
                            break
                    else:
                        impatience += 1
                        print('[ did not beat best accuracy: {} impatience: {} ]'.format(
                                round(best_accuracy, 4), impatience))
                    validate_time.reset()
                    if 0 < opt['validation_patience'] <= impatience:
                        print('[ ran out of patience! stopping training. ]')
                        break
        except KeyboardInterrupt:
            print('Stopped training, starting testing')

        world.shutdown()
        if not saved:
            world.save_agents()
        else:
            # reload best validation model
            opt['pretrained_model'] = opt['model_file']
            agent = create_agent(opt)

        run_eval(agent, opt, 'valid', write_log=True)
        run_eval(agent, opt, 'test', write_log=True)
    else:
        run_eval(agent, opt, opt['datatype'], write_log=True)


if __name__ == '__main__':
    main()
