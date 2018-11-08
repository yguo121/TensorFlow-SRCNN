import tensorflow as tf
import time
import os

from utils import (
    input_setup1,
    input_setup2,
    checkpoint_dir,
    checkpoint_dir1,
    read_data1,
    merge,
    #checkimage,
    imsave
)
class SRCNN(object):

    def __init__(self,sess, image_size, label_size,c_dim):
        self.sess = sess
        self.image_size = image_size
        self.label_size = label_size
        self.c_dim = c_dim
        self.build_model()
        
    def train(self, config):
            # NOTE : if train, the nx, ny are ingnored
            nx, ny = input_setup1(config)

            data_dir = checkpoint_dir1(config)
            print(data_dir)

            input_, label_ = read_data1(data_dir)
            print(input_)
            #print(input_)
            # Stochastic gradient descent with the standard backpropagation
            #self.train_op = tf.train.GradientDescentOptimizer(config.learning_rate).minimize(self.loss)
            self.train_op = tf.train.AdamOptimizer(learning_rate=config.learning_rate).minimize(self.loss)
            tf.global_variables_initializer().run()
            counter = 0
            time_ = time.time()

            # Train
            if config.is_train:
                print("Now Start Training...")
                for ep in range(config.epoch):
                    # Run by batch images
                    batch_idxs = len(input_) // config.batch_size
                    for idx in range(0, batch_idxs):
                        batch_images = input_[idx * config.batch_size : (idx + 1) * config.batch_size]
                        batch_labels = label_[idx * config.batch_size : (idx + 1) * config.batch_size]
                        counter += 1
                        _, err = self.sess.run([self.train_op, self.loss], feed_dict={self.images: batch_images, self.labels: batch_labels})

                        if counter % 10 == 0:
                            print("Epoch: [%2d], step: [%2d], time: [%4.4f], loss: [%.8f]" % ((ep+1), counter, time.time()-time_, err))
                            #print(label_[1] - self.pred.eval({self.images: input_})[1],'loss:]',err)
                        if counter % 10 == 0:
                            self.save(config.checkpoint_dir, counter)

                            
    def build_model(self):
        self.images = tf.placeholder(tf.float32, [None, self.image_size, self.image_size, self.c_dim], name='images')
        self.labels = tf.placeholder(tf.float32, [None, self.label_size, self.label_size, self.c_dim], name='labels')
        
        self.weights = {
            'w1': tf.Variable(tf.random_normal([9, 9, self.c_dim, 128], stddev=1e-3), name='w1'),
            'w2': tf.Variable(tf.random_normal([1, 1, 128, 64], stddev=1e-3), name='w2'),
            'w3': tf.Variable(tf.random_normal([5, 5, 64, self.c_dim], stddev=1e-3), name='w3')
        }

        self.biases = {
            'b1': tf.Variable(tf.zeros([128], name='b1')),
            'b2': tf.Variable(tf.zeros([64], name='b2')),
            'b3': tf.Variable(tf.zeros([self.c_dim], name='b3'))
        }
        
        self.pred = self.model()
        
        self.loss = tf.reduce_mean(tf.square(self.labels - self.pred))

        self.saver = tf.train.Saver() # To save checkpoint

    def model(self):
        conv1 = tf.nn.relu(tf.nn.conv2d(self.images, self.weights['w1'], strides=[1,1,1,1], padding='VALID') + self.biases['b1'])
        conv2 = tf.nn.relu(tf.nn.conv2d(conv1, self.weights['w2'], strides=[1,1,1,1], padding='SAME') + self.biases['b2'])
        conv3 = tf.nn.conv2d(conv2, self.weights['w3'], strides=[1,1,1,1], padding='VALID') + self.biases['b3'] # This layer don't need ReLU
        return conv3

    
    
    def save(self, checkpoint_dir, step):
        """
            To save the checkpoint use to test or pretrain
        """
        model_name = "SRCNN.model"
        model_dir = "%s_%s" % ("srcnn", self.label_size)
        checkpoint_dir = os.path.join(checkpoint_dir, model_dir)

        if not os.path.exists(checkpoint_dir):
             os.makedirs(checkpoint_dir)

        self.saver.save(self.sess,os.path.join(checkpoint_dir, model_name),global_step=step)
        
        
        
        
    def test(self, config):
        print('Testing...')
        nx, ny = input_setup2(config)
        data_dir = checkpoint_dir(config)
        input_, label_ = read_data(data_dir)
        self.load(config.checkpoint_dir)
        
        # Test
        result = self.pred.eval({self.images: input_})
        image = merge(result, [nx, ny], self.c_dim)
        #image_LR = merge(input_, [nx, ny], self.c_dim)
        #checkimage(image_LR)
        # Saving Image
        base, ext = os.path.basename(config.test_img).split('.')
        imsave(image, os.path.join(config.result_dir, base + '.png'), config)

    def load(self, checkpoint_dir):
        """
            To load the checkpoint use to test or pretrain
        """
        model_dir = '%s_%s' % ('srcnn', self.label_size)# give the model name by label_size
        checkpoint_dir = os.path.join(checkpoint_dir, model_dir)
        ckpt = tf.train.get_checkpoint_state(checkpoint_dir)
        
        # Check the checkpoint is exist 
        if ckpt and ckpt.model_checkpoint_path:
            ckpt_path = str(ckpt.model_checkpoint_path) # convert the unicode to string
            self.saver.restore(self.sess, os.path.join(os.getcwd(), ckpt_path))
#             print('Success! %s'% ckpt_path)
        else:
            print('Loading failed.')
            
    def save(self, checkpoint_dir, step):
        """
            To save the checkpoint use to test or pretrain
        """
        model_name = 'SRCNN.model'
        model_dir = '%s_%s' % ('srcnn', self.label_size)
        checkpoint_dir = os.path.join(checkpoint_dir, model_dir)

        if not os.path.exists(checkpoint_dir):
             os.makedirs(checkpoint_dir)

        self.saver.save(self.sess,
                        os.path.join(checkpoint_dir, model_name),
                        global_step=step)