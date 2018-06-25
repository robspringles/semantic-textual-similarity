#!/Users/sunnymarkliu/softwares/miniconda3/bin/python
# _*_ coding: utf-8 _*_

"""
@author: SunnyMarkLiu
@time  : 2018/6/25 下午5:36
"""
import warnings

from keras import backend as K
from keras import layers
from keras.layers import Input, TimeDistributed, Dense, Lambda, LSTM
from keras.layers import concatenate, Dropout, BatchNormalization
from keras.layers.embeddings import Embedding
from keras.models import Model

warnings.filterwarnings('ignore')
from base_model import BaseModel


class DSSM(BaseModel):

    def build_model(self, data):
        """
        built model architecture
        """
        embedding_layer = Embedding(data['nb_words'],
                                    self.cfg.embedding_dim,
                                    weights=[data['embedding_matrix']],
                                    input_length=self.cfg.max_sequence_length,
                                    trainable=self.cfg.embed_trainable)
        sequence_1_input = Input(shape=(self.cfg.max_sequence_length,), dtype='int32')
        sequence_2_input = Input(shape=(self.cfg.max_sequence_length,), dtype='int32')
        embedded_sequences_1 = embedding_layer(sequence_1_input)
        embedded_sequences_2 = embedding_layer(sequence_2_input)

        q1 = TimeDistributed(Dense(self.cfg.embedding_dim, activation='relu'))(embedded_sequences_1)
        q1 = Lambda(lambda x: K.max(x, axis=1), output_shape=(self.cfg.embedding_dim,))(q1)

        q2 = TimeDistributed(Dense(self.cfg.embedding_dim, activation='relu'))(embedded_sequences_2)
        q2 = Lambda(lambda x: K.max(x, axis=1), output_shape=(self.cfg.embedding_dim,))(q2)

        # 计算 q1 和 q2 的 rmse
        minus_q2 = Lambda(lambda x: -x)(q2)
        subtracted_out = layers.add([q1, minus_q2])
        rmse_out = Lambda(lambda x: x ** 2)(subtracted_out)
        multiply_out = layers.multiply([q1, q2])

        merged = concatenate([subtracted_out, rmse_out, multiply_out])
        merged = BatchNormalization()(merged)

        for dense_unit in self.cfg.dssm_cfg['dense_units']:
            merged = Dense(dense_unit, activation=self.cfg.dssm_cfg['activation'])(merged)
            merged = Dropout(self.cfg.dssm_cfg['dense_dropout'])(merged)
            merged = BatchNormalization()(merged)

        preds = Dense(1, activation='sigmoid')(merged)
        model = Model(inputs=[sequence_1_input, sequence_2_input],
                      outputs=preds)
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['binary_accuracy'])
        # model.summary()

        return model

class CDSSM(BaseModel):

    def build_model(self, data):
        pass


class LSTM_DSSM(BaseModel):

    def build_model(self, data):
        embedding_layer = Embedding(data['nb_words'],
                                    self.cfg.embedding_dim,
                                    weights=[data['embedding_matrix']],
                                    input_length=self.cfg.max_sequence_length,
                                    trainable=self.cfg.embed_trainable)
        sequence_1_input = Input(shape=(self.cfg.max_sequence_length,), dtype='int32')
        sequence_2_input = Input(shape=(self.cfg.max_sequence_length,), dtype='int32')
        embedded_sequences_1 = embedding_layer(sequence_1_input)
        embedded_sequences_2 = embedding_layer(sequence_2_input)

        # LSTM encode question input
        lstm_layer = LSTM(
            units=self.cfg.lstm_dssm_cfg['lstm_units'],
            dropout=self.cfg.lstm_dssm_cfg['rnn_dropout'],
            recurrent_dropout=self.cfg.lstm_dssm_cfg['rnn_dropout']
        )
        q1_encode = lstm_layer(embedded_sequences_1)
        q2_encode = lstm_layer(embedded_sequences_2)

        merged = concatenate([q1_encode, q2_encode])
        merged = BatchNormalization()(merged)

        for dense_unit in self.cfg.lstm_dssm_cfg['dense_units']:
            merged = Dense(dense_unit, activation=self.cfg.lstm_dssm_cfg['activation'])(merged)
            merged = Dropout(self.cfg.lstm_dssm_cfg['dense_dropout'])(merged)
            merged = BatchNormalization()(merged)

        preds = Dense(1, activation='sigmoid')(merged)
        model = Model(inputs=[sequence_1_input, sequence_2_input],
                      outputs=preds)
        model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['binary_accuracy'])
        # model.summary()

        return model


class Merge_DSSM(BaseModel):

    def build_model(self, data):
        pass
