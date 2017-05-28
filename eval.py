# -*- coding: utf-8 -*-
from __future__ import print_function
from hyperparams import Hyperparams as hp
import codecs
import tensorflow as tf
import numpy as np
from prepro import *
from train import Graph
from nltk.translate.bleu_score import corpus_bleu

def eval(): 
    # Load graph
    g = Graph(is_training=False)
    with tf.Session(graph=g.graph) as sess:
        saver = tf.train.Saver()
        saver.restore(sess, tf.train.latest_checkpoint(hp.logdir))
        print("Restored!")
        mname = open(hp.logdir + '/checkpoint', 'r').read().split('"')[1] # model name
        print(mname)
        
        # Load data
        X, Sources, Targets = load_test_data()
        char2idx, idx2char = load_vocab()
         
        with codecs.open(hp.savedir + "/" + mname, "w", "utf-8") as fout:
            list_of_refs, hypotheses = [], []
            for i in range(len(X) // hp.batch_size):
                
                # Get mini-batches
                x = X[i*hp.batch_size: (i+1)*hp.batch_size] # mini-batch
                sources = Sources[i*hp.batch_size: (i+1)*hp.batch_size]
                targets = Targets[i*hp.batch_size: (i+1)*hp.batch_size]
                 
                preds_prev = np.zeros((hp.batch_size, hp.maxlen), np.int32)
                preds_prev[:, 0] = 2
                preds = np.zeros((hp.batch_size, hp.maxlen), np.int32)        
                for j in range(hp.maxlen):
                    # predict next character
                    outs = sess.run(g.preds, {g.x: x, g.decoder_inputs: preds_prev})
                    # update character sequence
                    if j < hp.maxlen - 1:
                        preds_prev[:, j + 1] = outs[:, j]
                    preds[:, j] = outs[:, j]
                 
                # Write to file
                for source, target, pred in zip(sources, targets, preds): # sentence-wise
                    got = "".join(idx2char[idx] for idx in pred).split(u"␃")[0]
                    fout.write("- source: " + source +"\n")
                    fout.write("- expected: " + target + "\n")
                    fout.write("- got: " + got + "\n\n")
                    fout.flush()
                     
                    # For bleu score
                    ref = target.split()
                    hypothesis = got.split()
                    if len(ref) > 3 and len(hypothesis) > 3:
                        list_of_refs.append([ref])
                        hypotheses.append(hypothesis)
             
            # Get bleu score
            score = corpus_bleu(list_of_refs, hypotheses)
            fout.write("Bleu Score = " + str(100*score))
                                                
if __name__ == '__main__':
    eval()
    print("Done")
    
    
