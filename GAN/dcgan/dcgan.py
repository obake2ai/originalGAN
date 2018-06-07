### -*-coding:utf-8-*-
from __future__ import print_function, division

from keras.datasets import mnist
from keras.layers import Input, Dense, Reshape, Flatten, Dropout
from keras.layers import BatchNormalization, Activation, ZeroPadding2D
from keras.layers.advanced_activations import LeakyReLU
from keras.layers.convolutional import UpSampling2D, Convolution2D
from keras.models import Sequential, Model, load_model

from keras.optimizers import Adam

import matplotlib.pyplot as plt

import sys

import numpy as np

import os

import shutil

class DCGAN():

    def __init__(self):
        self.path = "dcgan_generated_images"
        if os.path.exists(self.path):
            if os.path.exists('bu_' + self.path):
                shutil.rmtree('bu_' + self.path)
                shutil.copytree(self.path, 'bu_' + self.path)
            else:
                shutil.copytree(self.path, 'bu_' + self.path)
            shutil.rmtree(self.path)
            os.mkdir(self.path)
            print ('remove past, made bu')
        else:
            os.mkdir(self.path)
            print ('made')
        #mnistデータ用の入力データサイズ
        self.img_rows = 28
        self.img_cols = 28
        self.channels = 1
        self.img_shape = (self.img_rows, self.img_cols, self.channels)

        # 潜在変数の次元数
        self.z_dim = 5

        # 画像保存の際の列、行数
        self.row = 5
        self.col = 5
        self.row2 = 1 # 連続潜在変数用
        self.col2 = 10# 連続潜在変数用

        # 画像生成用の固定された入力潜在変数
        self.noise_fix1 = np.random.normal(0, 1, (self.row * self.col, self.z_dim))
        # 連続的に潜在変数を変化させる際の開始、終了変数
        self.noise_fix2 = np.random.normal(0, 1, (1, self.z_dim))
        self.noise_fix3 = np.random.normal(0, 1, (1, self.z_dim))

        # 横軸がiteration数のプロット保存用np.ndarray
        self.g_loss_array = np.array([])
        self.d_loss_array = np.array([])
        self.d_accuracy_array = np.array([])
        self.d_predict_true_num_array = np.array([])
        self.c_predict_class_list = []

        discriminator_optimizer = Adam(lr=1e-5, beta_1=0.1)
        combined_optimizer = Adam(lr=2e-4, beta_1=0.5)

        # discriminatorモデル
        self.discriminator = self.build_discriminator()
        self.discriminator.compile(loss='binary_crossentropy',
            optimizer=discriminator_optimizer,
            metrics=['accuracy'])

        # Generatorモデル
        self.generator = self.build_generator()
        # generatorは単体で学習しないのでコンパイルは必要ない
        #self.generator.compile(loss='binary_crossentropy', optimizer=optimizer)

        self.combined = self.build_combined1()
        #self.combined = self.build_combined2()
        self.combined.compile(loss='binary_crossentropy', optimizer=combined_optimizer)

        # Classifierモデル
        self.classifier = self.build_classifier()

    def build_generator(self):

        noise_shape = (self.z_dim,)
        model = Sequential()
        model.add(Dense(1024, input_shape=noise_shape))
        model.add(BatchNormalization())
        model.add(Activation('relu'))
        model.add(Dense(128*7*7))
        model.add(BatchNormalization())
        model.add(Activation('relu'))
        model.add(Reshape((7,7,128), input_shape=(128*7*7,)))
        model.add(UpSampling2D((2,2)))
        model.add(Convolution2D(64,5,5,border_mode='same'))
        model.add(BatchNormalization())
        model.add(Activation('relu'))
        model.add(UpSampling2D((2,2)))
        model.add(Convolution2D(1,5,5,border_mode='same'))
        model.add(Activation('tanh'))
        model.summary()
        return model

    def build_discriminator(self):

        img_shape = (self.img_rows, self.img_cols, self.channels)

        model = Sequential()
        model.add(Convolution2D(64,5,5, subsample=(2,2),\
                  border_mode='same', input_shape=img_shape))
        model.add(LeakyReLU(0.2))
        model.add(Convolution2D(128,5,5,subsample=(2,2)))
        model.add(LeakyReLU(0.2))
        model.add(Flatten())
        model.add(Dense(256))
        model.add(LeakyReLU(0.2))
        model.add(Dropout(0.5))
        model.add(Dense(1))
        model.add(Activation('sigmoid'))
        return model

    def build_combined1(self):
        self.discriminator.trainable = False
        model = Sequential([self.generator, self.discriminator])
        return model

    def build_combined2(self):
        z = Input(shape=(self.z_dim,))
        img = self.generator(z)
        self.discriminator.trainable = False
        valid = self.discriminator(img)
        model = Model(z, valid)
        model.summary()
        return model

    def build_classifier(self):
        model = load_model("cnn_model.h5")
        model.load_weights('cnn_weight.h5')
        return model

    def save_grad(self, model):
        """Return the gradient of every trainable weight in model

        Parameters
        -----------
        model : a keras model instance

        First, find all tensors which are trainable in the model. Surprisingly,
        `model.trainable_weights` will return tensors for which
        trainable=False has been set on their layer (last time I checked), hence the extra check.
        Next, get the gradients of the loss with respect to the weights.

        """
        #weights = [tensor for tensor in model.trainable_weights if model.get_layer(tensor.name[:-2]).trainable]
        weights = [tensor for tensor in model.trainable_weights]
        optimizer = model.optimizer

        grads = optimizer.get_gradients(model.total_loss, weights)

        print (weights)

    def save_param(self, epoch):
        g_para = self.generator.get_weights()
        d_para = self.discriminator.get_weights()
        g_abs_max = 0
        g_abs_min = 1
        d_abs_max = 0
        d_abs_min = 1
        for data in g_para:
            if g_abs_max < max(abs(data.reshape(-1))):
                g_abs_max = max(abs(data.reshape(-1)))
            if g_abs_min > min(abs(data[data!=0].reshape(-1))):
                g_abs_min = min(abs(data[data!=0].reshape(-1)))
        epoch_g_data = [epoch,g_abs_min, g_abs_max, np.log2(g_abs_max/g_abs_min)]
        for data in d_para:
            if d_abs_max < max(abs(data.reshape(-1))):
                d_abs_max = max(abs(data.reshape(-1)))
            if d_abs_min > min(abs(data[data!=0].reshape(-1))):
                d_abs_min = min(abs(data[data!=0].reshape(-1)))
        epoch_d_data = [epoch,d_abs_min, d_abs_max, np.log2(d_abs_max/d_abs_min)]
        with open(self.path + 'g_epoch_data.txt', 'a') as f:
            f.write(str(epoch)+','+str(g_abs_min)+','+str(g_abs_max)+','+str(np.log2(g_abs_max/g_abs_min)) + '\n')
        with open(self.path + 'd_epoch_data.txt', 'a') as g:
            g.write(str(epoch)+','+str(d_abs_min)+','+str(d_abs_max)+','+str(np.log2(d_abs_max/d_abs_min)) + '\n')
        #self.generator.save_weights(self.path + "generator_%s.h5" % epoch)

    def train(self, epochs, batch_size=128, save_interval=50):

        # mnistデータの読み込み
        (X_train, _), (_, _) = mnist.load_data()

        # 値を-1 to 1に規格化
        X_train = (X_train.astype(np.float32) - 127.5) / 127.5
        X_train = np.expand_dims(X_train, axis=3)

        half_batch = int(batch_size / 2)

        self.g_loss_array = np.zeros(epochs)
        self.d_loss_array = np.zeros(epochs)
        self.d_accuracy_array = np.zeros(epochs)
        self.d_predict_true_num_array = np.zeros(epochs)

        for epoch in range(epochs):

            # ---------------------
            #  Discriminatorの学習
            # ---------------------

            # バッチサイズの半数をGeneratorから生成
            noise = np.random.normal(0, 1, (half_batch, self.z_dim))
            gen_imgs = self.generator.predict(noise)


            # バッチサイズの半数を教師データからピックアップ
            idx = np.random.randint(0, X_train.shape[0], half_batch)
            imgs = X_train[idx]

            # discriminatorを学習
            # 本物データと偽物データは別々に学習させる
            d_loss_real = self.discriminator.train_on_batch(imgs, np.ones((half_batch, 1)))
            d_loss_fake = self.discriminator.train_on_batch(gen_imgs, np.zeros((half_batch, 1)))
            # それぞれの損失関数を平均
            d_loss = 0.5 * np.add(d_loss_real, d_loss_fake)

            # discriminatorの予測（本物と偽物が半々のミニバッチ）
            d_predict = self.discriminator.predict_classes(np.concatenate([gen_imgs,imgs]), verbose=0)
            d_predict = np.sum(d_predict)

            # classifierの予測
            c_predict = self.classifier.predict_classes(np.concatenate([gen_imgs,imgs]), verbose=0)

            weights = [tensor for tensor in self.discriminator.trainable_weights if self.discriminator.get_layer(tensor.name[:-2]).trainable]
            print (weights)
            d_grads =self.discriminator.optimizer.get_gradients(d_loss, weights)
            print (d_grads)


            # ---------------------
            #  Generatorの学習
            # ---------------------

            noise = np.random.normal(0, 1, (batch_size, self.z_dim))


            # 生成データの正解ラベルは本物（1）
            valid_y = np.array([1] * batch_size)

            # Train the generator
            g_loss = self.combined.train_on_batch(noise, valid_y)


            # 進捗の表示
            print ("%d [D loss: %f, acc.: %.2f%%] [G loss: %f]" % (epoch, d_loss[0], 100*d_loss[1], g_loss))

            if epoch % 100 == 0:
                self.save_param(epoch)
                #self.save_grad(self.generator)


            # np.ndarrayにloss関数を格納
            self.g_loss_array[epoch] = g_loss
            self.d_loss_array[epoch] = d_loss[0]
            self.d_accuracy_array[epoch] = 100*d_loss[1]
            self.d_predict_true_num_array[epoch] = d_predict
            self.c_predict_class_list.append(c_predict)

            if epoch % save_interval == 0:

                # 毎回異なる乱数から画像を生成
                self.save_imgs(self.row, self.col, epoch, '', noise)
                # 毎回同じ値から画像を生成
                self.save_imgs(self.row, self.col, epoch, 'fromFixedValue', self.noise_fix1)
                # 二つの潜在変数の間の遷移画像を生成
                total_images = self.row*self.col
                noise_trans = np.zeros((total_images, self.z_dim))
                for i in range(total_images):
                    t = (i*1.)/((total_images-1)*1.)
                    noise_trans[i,:] = t * self.noise_fix2 + (1-t) * self.noise_fix3
                self.save_imgs(self.row2, self.col2, epoch, 'trans', noise_trans)

                # classifierに生成画像のクラス識別をさせる（10000サンプル）
                noise = np.random.normal(0, 1, (10000, self.z_dim))
                class_res = self.classifier.predict_classes(self.generator.predict(noise), verbose=0)
                # plot histgram
                plt.hist(class_res)
                plt.savefig(self.path + "mnist_hist_%d.png" % epoch)
                plt.ylim(0,2000)
                plt.close()



                # 学習結果をプロット
                fig, ax = plt.subplots(4,1, figsize=(8.27,11.69))
                ax[0].plot(self.g_loss_array[:epoch])
                ax[0].set_title("g_loss")
                ax[1].plot(self.d_loss_array[:epoch])
                ax[1].set_title("d_loss")
                ax[2].plot(self.d_accuracy_array[:epoch])
                ax[2].set_title("d_accuracy")
                ax[3].plot(self.d_predict_true_num_array[:epoch])
                ax[3].set_title("d_predict_true_num_array")
                fig.suptitle("epoch: %5d" % epoch)
                fig.savefig(self.path + "training_%d.png" % epoch)
                plt.close()

        # 重みを保存
        self.generator.save_weights(self.path + "generator_%s.h5" % epoch)
        self.discriminator.save_weights(self.path + "discriminator_%s.h5" % epoch)




    def save_imgs(self, row, col, epoch, filename, noise):
        # row, col
        # 生成画像を敷き詰めるときの行数、列数

        gen_imgs = self.generator.predict(noise)

        # 生成画像を0-1に再スケール
        gen_imgs = 0.5 * gen_imgs + 0.5


        fig, axs = plt.subplots(row, col)
        cnt = 0
        if row == 1:
            for j in range(col):
                axs[j].imshow(gen_imgs[cnt, :,:,0], cmap='gray')
                axs[j].axis('off')
                cnt += 1
        else:
            for i in range(row):
                for j in range(col):
                    axs[i,j].imshow(gen_imgs[cnt, :,:,0], cmap='gray')
                    axs[i,j].axis('off')
                    cnt += 1

        #fig.savefig("images/mnist_%s_%d.png" % (filename, epoch))
        fig.suptitle("epoch: %5d" % epoch)
        fig.savefig(self.path + "mnist_%s_%d.png" % (filename, epoch))
        plt.close()


if __name__ == '__main__':
    gan = DCGAN()
    gan.train(epochs=100000, batch_size=32, save_interval=1000)
