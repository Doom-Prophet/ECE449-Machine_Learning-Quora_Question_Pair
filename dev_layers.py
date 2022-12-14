import keras.backend as K
from keras.layers import Lambda, Activation, Dropout, Embedding, SpatialDropout1D, Dense, concatenate, Permute
from keras.layers import TimeDistributed  # This applies the model to every timestep in the input sequences
from keras.layers import Bidirectional, LSTM, GlobalMaxPooling1D, GlobalAveragePooling1D, Conv1D
# from keras.layers.advanced_activations import ELU
from keras.models import Sequential
from keras import regularizers
from keras.layers.normalization import BatchNormalization

class BiLSTM_Layer(object):
    """
    Encode the embedded words by using BiLSTM
    """

    def __init__(self, max_length, hidden_units, hidden_units_scale=1, dropout=0.5, ret_seq=True):
        self.model = Sequential()
        self.model.add(
            Bidirectional(
                LSTM(hidden_units, return_sequences=ret_seq, dropout=dropout, recurrent_dropout=0), input_shape=(max_length, hidden_units*hidden_units_scale)
            )
        )  
        # return_sequences: return the last output in the output sequence, or the full sequence.
        if ret_seq:
          self.model.add(TimeDistributed(Dense(hidden_units, activation='relu', kernel_initializer='he_normal')))
          self.model.add(TimeDistributed(Dropout(dropout)))

    def __call__(self, embedded_words):
        return self.model(embedded_words)

class Pooling_Layer(object):

    def __init__(self, hidden_units, output_units, hidden_units_scale=1, dropout=0.5, l2_weight_decay=0.0):
        self.model = Sequential()
        self.model.add(Dropout(dropout, input_shape=(hidden_units * hidden_units_scale,)))
        self.model.add(Dense(output_units, activation='relu', kernel_regularizer=regularizers.l2(l2_weight_decay)))
        self.model.add(BatchNormalization())

    def __call__(self, a, b):
        a_max = GlobalMaxPooling1D()(a)
        a_avg = GlobalAveragePooling1D()(a)

        b_max = GlobalMaxPooling1D()(b)
        b_avg = GlobalAveragePooling1D()(b)

        return self.model(concatenate([a_avg, a_max, b_avg, b_max]))   # shape=(batch_size, 4 * units)
    
def attention(encoded):
    """
    INPUTS:
        encoded_a    shape=(batch_size, time_steps, num_units)
        encoded_b    shape=(batch_size, time_steps, num_units)
    """

    weights = K.batch_dot(x=encoded[0], y=K.permute_dimensions(encoded[1], pattern=(0, 2, 1)))
    return weights


def attention_output(encoded):
    input_shape = encoded[0]
    embed_size = input_shape[1]
    return (input_shape[0], embed_size, embed_size)


def attention_softmax3d(x):
    attention = x[0]
    sentence = x[1]
    # 3D softmax: calculate the subphrase in the sentence through attention
    exp = K.exp(attention - K.max(attention, axis=-1, keepdims=True))
    summation = K.sum(exp, axis=-1, keepdims=True)
    weights = exp / summation

    return K.batch_dot(weights, sentence)

def attention_softmax3d_output(x):
    attention_shape = x[0]
    sentence_shape = x[1]

    return (attention_shape[0], attention_shape[1], sentence_shape[2])


def substract(x):
    encode = x[0]
    align = x[1]

    return encode - align


def substract_output(x):
    return x[0]


def multiply(x):
    encode = x[0]
    align = x[1]

    return encode * align


def multiply_output(x):
    return x[0]

class Attention_Layer(object):
    def __init__(self):
        pass

    def __call__(self,encoded_a, encoded_b):
        attention_ab = Lambda(attention, attention_output, name='attention')([encoded_a, encoded_b])
        attention_ab_T = Permute((1,2))(attention_ab)

        alpha = Lambda(attention_softmax3d, attention_softmax3d_output, name='soft_alignment_a')([attention_ab, encoded_b])
        beta = Lambda(attention_softmax3d, attention_softmax3d_output, name='soft_alignment_b')([attention_ab_T, encoded_a])
        
        sub_a = Lambda(substract, substract_output, name='substract_a')([encoded_a, alpha])
        mul_a = Lambda(multiply, multiply_output, name='multiply_a')([encoded_a, alpha])

        sub_b = Lambda(substract, substract_output, name='substract_b')([encoded_b, beta])
        mul_b = Lambda(multiply, multiply_output, name='multiply_b')([encoded_b, beta])

        m_a = concatenate([encoded_a, alpha, sub_a, mul_a])  # shape=(batch_size, time-steps, 4 * units) 
        m_b = concatenate([encoded_b, beta, sub_b, mul_b])  # shape=(batch_size, time-steps, 4 * units)        

        return m_a,m_b

def Convolution_layer(emb):
    conv1 = Conv1D(filters=128, kernel_size=1, padding='same', activation='relu')
    conv2 = Conv1D(filters=128, kernel_size=2, padding='same', activation='relu')
    conv3 = Conv1D(filters=128, kernel_size=3, padding='same', activation='relu')
    conv4 = Conv1D(filters=128, kernel_size=4, padding='same', activation='relu')
    conv5 = Conv1D(filters=32, kernel_size=5, padding='same', activation='relu')
    conv6 = Conv1D(filters=32, kernel_size=6, padding='same', activation='relu')
    conv7 = Conv1D(filters=32, kernel_size=7, padding='same', activation='relu')
    conv8 = Conv1D(filters=32, kernel_size=8, padding='same', activation='relu')

  
    convl1=conv1(emb)
    glob1=GlobalAveragePooling1D()(convl1)

    convl2=conv2(emb)
    glob2=GlobalAveragePooling1D()(convl2)

    convl3=conv3(emb)
    glob3=GlobalAveragePooling1D()(convl3)

    convl4=conv4(emb)
    glob4=GlobalAveragePooling1D()(convl4)

    convl5=conv5(emb)
    glob5=GlobalAveragePooling1D()(convl5)

    convl6=conv6(emb)
    glob6=GlobalAveragePooling1D()(convl6)

    convl7=conv7(emb)
    glob7=GlobalAveragePooling1D()(convl7)

    convl8=conv8(emb)
    glob8=GlobalAveragePooling1D()(convl8)
  
    merge=concatenate([glob1,glob2,glob3,glob4,glob5,glob6,glob7,glob8])
    
    return merge