def add_cmdline_args(parser):
    # Runtime environment
    agent = parser.add_argument_group('Insults Arguments')
    agent.add_argument('--no_cuda', type='bool', default=False)
    agent.add_argument('--gpu', type=int, default=-1)
    agent.add_argument('--random_seed', type=int, default=1013)

    # Basics
    agent.add_argument('--embedding_file', type=str, default=None,
                       help='File of space separated embeddings: w e1 ... ed')
    agent.add_argument('--pretrained_model', type=str, default=None,
                       help='Load dict/features/weights/opts from this file')
    agent.add_argument('--log_file', type=str, default=None)
    agent.add_argument('--model_file', type=str, default=None)

    agent.add_argument('--max_sequence_length', type=int, default=100)
    agent.add_argument('--embedding_dim', type=int, default=128)
    agent.add_argument('--learning_rate', type=float, default=1e-1)
    agent.add_argument('--learning_decay', type=float, default=0.)
    agent.add_argument('--seed', type=int, default=243)
    agent.add_argument('--num_filters', type=int, default=128)
    agent.add_argument('--kernel_sizes',  default='3 4 5')
    agent.add_argument('--regul_coef_conv', type=float, default=1e-2)
    agent.add_argument('--regul_coef_dense', type=float, default=1e-2)
    agent.add_argument('--pool_sizes', default='2 2 2')
    agent.add_argument('--dropout_rate', type=float, default=0.)
    agent.add_argument('--dense_dim', type=int, default=100)

    agent.add_argument('-btd', '--balance_train_dataset',
                        type='bool', default=False,
                        help='balance train dataset for insult/non-insult ratio 1?')

    agent.add_argument('-mds', '--models',
                       type=str, default='cnn_word',
                       help='str of models to use. Example: cnn_word log_reg svc')



