import random

import varitae.utils as utils
import varitae.network as network

import tensorflow as tf


timeseries, validate_timeseries, validate_labels = utils.load()

lag = 1
assert lag > 0
x, y = utils.lag_data(timeseries, lag=lag)
x, y = utils.whiten(x), utils.whiten(y)
val_x, val_y = utils.lag_data(validate_timeseries, lag=1)  # maybe with lag
val_x, val_y = utils.whiten(val_x), utils.whiten(val_y)

# length_minib = val_x.shape[0]
# minibatches = []
# for i in range(x.shape[0] - length_minib + 1):
#     minibatches.append((x[i:i + length_minib], y[i:i + length_minib]))

timeseries_x = tf.placeholder(tf.float32, shape=[None, timeseries.shape[-1]])
timeseries_y = tf.placeholder(tf.float32, shape=[None, timeseries.shape[-1]])
count_timesteps = tf.placeholder(tf.int32, shape=[1])
training_status = tf.placeholder(tf.bool, shape=[])

batch_size = 999
net_out = network.time_lagged_variational_autoencoder(timeseries_x, timeseries_y, count_timesteps, training_status)
loss, encoded_mean, encoded_stdd, encoded, decoded = net_out
loss = tf.reduce_sum(loss)
train = tf.train.AdamOptimizer().minimize(loss)

epochs = 20000
with tf.Session() as sess:
    sess.run(tf.global_variables_initializer())
    for i in range(epochs):
        for j in range(int(x.shape[0]/batch_size)):
            if x.shape[0] - j*batch_size > batch_size:
                xx, yy = x[j*batch_size:(j+1)*batch_size], y[j*batch_size:(j+1)*batch_size]
            else:
                break
            _, l1 = sess.run([train, loss],
                            feed_dict={timeseries_x: xx,
                                       timeseries_y: yy,
                                       count_timesteps: [xx.shape[0]],
                                       training_status: True})

        if i % 500 == 0:
            validation_loss, validation_dim_reduction, enc_stdd = sess.run(
                [loss, encoded_mean, encoded_stdd],
                feed_dict={timeseries_x: val_x,
                           timeseries_y: val_y,
                           count_timesteps: [val_x.shape[0]],
                           training_status: False})
            print('Validation loss: {}'.format(validation_loss))
            score = utils.cluster_compare(validate_labels[:-1], validation_dim_reduction)
            print('Adjusted Rand Index: {}'.format(score))

    encoded_timeseries = sess.run(encoded,
                                  feed_dict={timeseries_x: timeseries,
                                             timeseries_y: timeseries,
                                             count_timesteps: [timeseries.shape[0]],
                                             training_status: False})

    pred_timeseries_y = utils.cluster(encoded_timeseries)
    print(pred_timeseries_y.labels_)
    utils.save(pred_timeseries_y.labels_)
