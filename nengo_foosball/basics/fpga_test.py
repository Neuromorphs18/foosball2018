# Run gui with nengo -b nengo_board
import nengo
import numpy as np
from nengo_board.networks import RemotePESEnsembleNetwork

def input_func(t):
    return [np.sin(t * 10), np.cos(t * 10)]

with nengo.Network() as model:
    # Reference signal
    input_node = nengo.Node(input_func, label='input signal')

    # FPGA neural ensemble
    pes_ens = RemotePESEnsembleNetwork(
        'de1', input_dimensions=2, input_synapse=None,
        learn_rate=0, n_neurons=50, label='ensemble',
        ens_args={'neuron_type': nengo.neurons.SpikingRectifiedLinear()})
    nengo.Connection(input_node, pes_ens.input)
