# Script to freeze TF model and export it to jAER tools

import tensorflow as tf

from tensorflow.python.framework import graph_util
from tensorflow.python.framework import graph_io

# repository
nameNet = 'SEGNET_JAVA_MAX_POOL'
# last checkpoint
lastSave = 1000

with tf.Session() as sess:
    saver = tf.train.import_meta_graph(nameNet + '/model.ckpt-' + str(1000) + '.meta')
    saver.restore(sess, nameNet + '/model.ckpt-' + str(1000) )

    graph_def = sess.graph.as_graph_def()
    for node in graph_def.node:
        if node.op == 'RefSwitch':
            node.op = 'Switch'
            for index in range(len(node.input)):
                if 'moving_' in node.input[index]:
                    node.input[index] = node.input[index] + '/read'
        elif node.op == 'AssignSub':
            node.op = 'Sub'
            if 'use_locking' in node.attr: del node.attr['use_locking']
        elif node.op == 'AssignAdd':
            node.op = 'Add'
            if 'use_locking' in node.attr: del node.attr['use_locking']
    constant_graph = graph_util.convert_variables_to_constants(sess, graph_def,
                                                               ["output"])
    graph_io.write_graph(constant_graph, nameNet, nameNet + "_FoosballBallTrackerHeatmap.pb", as_text=False)


