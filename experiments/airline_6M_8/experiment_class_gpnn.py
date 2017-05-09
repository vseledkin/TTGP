import tensorflow as tf
import os
import numpy as np
from tensorflow.contrib.layers import batch_norm

from gptt_embed.covariance import SE_multidim
from gptt_embed.projectors import FeatureTransformer, LinearProjector, Identity
from gptt_embed.gpc_runner import GPCRunner

data_basedir1 = "/Users/IzmailovPavel/Documents/Education/Programming/DataSets/"
data_basedir2 = "/Users/IzmailovPavel/Documents/Education/Projects/GPtf/experiments/"

class NN(FeatureTransformer):
    
    def __init__(self, H1=1000, H2=1000, H3=500, H4=50, d=4, D=8):

        with tf.name_scope('layer_1'):
            self.W1 = self.weight_var('W1', [D, H1])
            self.b1 = self.bias_var('b1', [H1])        
        with tf.name_scope('layer_2'):
            self.W2 = self.weight_var('W2', [H1, H2])
            self.b2 = self.bias_var('b2', [H2])
        with tf.name_scope('layer_3'):
            self.W3 = self.weight_var('W3', [H2, H3])
            self.b3 = self.bias_var('b3', [H3])
        with tf.name_scope('layer_4'):
            self.W4 = self.weight_var('W4', [H3, H4])
            self.b4 = self.bias_var('b4', [H4])
        with tf.name_scope('layer_5'):
            self.W5 = self.weight_var('W5', [H4, d])

        self.d = d
        self.reuse = False
        
    @staticmethod
    def weight_var(name, shape, trainable=True):
        init = tf.truncated_normal(shape, stddev=0.1, dtype=tf.float32)
        return tf.get_variable(name, initializer=init, 
                                dtype=tf.float32, trainable=trainable)
    @staticmethod
    def bias_var(name, shape, trainable=True):
        init = tf.constant(0.1, shape=shape, dtype=tf.float32) 
        return tf.get_variable(name, initializer=init, 
                                dtype=tf.float32, trainable=trainable)

    def transform(self, x, test=False):

        # layer 1
        x_input = tf.cast(x, tf.float32)
        h_preact1 = tf.matmul(x_input, self.W1) + self.b1
        norm1 = batch_norm(h_preact1, decay=0.99, is_training=(not test), 
                           reuse=self.reuse, scope="norm_1")
        h_1 = tf.nn.relu(norm1)

        # layer 2
        h_preact2 = tf.matmul(h_1, self.W2) + self.b2
        norm2 = batch_norm(h_preact2, decay=0.99, is_training=(not test), 
                           reuse=self.reuse, scope="norm_2")
        h_2 = tf.nn.relu(norm2)

        # layer 3
        h_preact3 = tf.matmul(h_2, self.W3) + self.b3
        norm3 = batch_norm(h_preact3, decay=0.99, is_training=(not test), 
                           reuse=self.reuse, scope="norm_3")
        h_3 = tf.nn.relu(norm3)

        # layer 4
        h_preact4 = tf.matmul(h_3, self.W4) + self.b4
        norm4 = batch_norm(h_preact4, decay=0.99, is_training=(not test), 
                           reuse=self.reuse, scope="norm_4")
        h_4 = tf.nn.relu(norm4)

        # layer 5
        h_preact5 = tf.matmul(h_4, self.W5) 
        projected = h_preact5

        projected = tf.cast(projected, tf.float32)
        projected = batch_norm(projected, decay=0.99, center=False, scale=False,
                                is_training=(not test), reuse=self.reuse, scope="norm_5")
        projected = tf.cast(projected, tf.float64)
        projected /= 3
        self.reuse = True

        projected = tf.minimum(projected, 1)
        projected = tf.maximum(projected, -1)
        return projected

    def initialize(self, sess):
        sess.run(tf.variables_initializer(self.get_params()))

    def get_params(self):
        bn_vars = []
        for scope in ["norm_1", "norm_2", "norm_3", "norm_4", "norm_5"]:
            bn_vars += tf.get_collection(tf.GraphKeys.GLOBAL_VARIABLES, scope=scope)
        return bn_vars + [self.W1, self.b1, self.W2, self.b2,
                self.W3, self.b3, self.W4, self.b4, self.W5] 

    def out_dim(self):
        return self.d

with tf.Graph().as_default():
    data_dir = "data/"
    n_inputs = 10
    mu_ranks = 10
    projector = NN(H1=1000, H2=1000, H3=500, H4=50, d=2)
    C = 2

    cov = SE_multidim(C, 0.7, 0.2, 0.1, projector)

    lr = 5e-3
    decay = (1, 0.2)
    n_epoch = 100
    batch_size = 50000
    data_type = 'numpy'
    log_dir = 'log'
    save_dir = 'models/gpnn_100_100_4.ckpt'
    model_dir = save_dir
    load_model = False#True
    
    runner=GPCRunner(data_dir, n_inputs, mu_ranks, cov,
                lr=lr, decay=decay, n_epoch=n_epoch, batch_size=batch_size,
                data_type=data_type, log_dir=log_dir, save_dir=save_dir,
                model_dir=model_dir, load_model=load_model, print_freq=10)
    runner.run_experiment()