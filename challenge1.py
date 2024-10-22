# -*- coding: utf-8 -*-
"""challenge1.ipynb

Automatically generated by Colaboratory.

#### *In order to run this notebook, you need to first cd into the MaskDataset folder(only if you are using the dataset outside the kaggle competition).* 

------------------------------

## This notebook contains two model. One is based on an architecture build by us; the other one is based on the transfer learning approach using the vgg16 architecture and the initial weights for the ImageNet dataset.
"""

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
#in order to hide a not dangerous warning
pd.options.mode.chained_assignment = None
import os
from keras.preprocessing.image import ImageDataGenerator
from keras.layers import GlobalAveragePooling2D, Dense, Dropout, Flatten, Conv2D, MaxPooling2D
from keras.models import Sequential, Model
from keras.applications import VGG16
from keras.applications.vgg16 import preprocess_input #used to preprocess our data for the transfer learning approach
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint, LearningRateScheduler, EarlyStopping, ReduceLROnPlateau
import json
import tensorflow as tf

"""## Pre-processing of the data."""

#set the seed for reproducible experiments
SEED = 1234
tf.random.set_seed(SEED)  

#set the model and the reative hyperparameter to use
use_transfer_learning = True 
#set to use or not data augmentation 
apply_data_augmentation = True

#Create training ImageDataGenerator object. It generate batches of tensor image data with real-time data augmentation.
#Preprocess_input function converts images from RGB to BGR, then each color channel is zero-centered with respect to the ImageNet dataset, without scaling.
#We choose this function because we apply transfer learning using the weights of ImageNet.
#If data augmentation is not selected we only rescale the image
if apply_data_augmentation:
    train_data_gen = ImageDataGenerator(horizontal_flip=True,
                                        height_shift_range= 0.2, 
                                        width_shift_range=0.2,
                                        zoom_range=0.3,
                                        rotation_range=20,
                                        shear_range=0.15,
                                        brightness_range= [0.8, 1],
                                        fill_mode='nearest',  
                                        preprocessing_function=preprocess_input,
                                        )
else:
    train_data_gen = ImageDataGenerator(rescale=1./255.0)
    
#take the path of MASKDATASET and store it in dataset_dir
cwd = os.getcwd()
dataset_dir = cwd

#IF YOU ARE ON kaggle competition, USE THIS LINE
#dataset_dir = os.path.join(cwd, '../input/artificial-neural-networks-and-deep-learning-2020/MaskDataset')

#load the json training file
with open(os.path.join(dataset_dir,'train_gt.json')) as f:
    dic = json.load(f)

#return a DataFrame with the renamed axis labels.
df = pd.DataFrame(dic.items())
df.rename(columns = {0:'filename', 1:'class'}, inplace = True)

#check if the dataset is correctly loaded priting the fist elements and the lenght
print(df.head())
print('--------')
print('total length: ', len(df))

#load the images of traing and test folders 
training_dir = os.path.join(dataset_dir, 'training')
test_dir = os.path.join(dataset_dir, 'test')

#split training and validation set (75% - 25%) in a stratified fashion, using this as the class labels.
from sklearn.model_selection import train_test_split
train_set, valid_set = train_test_split(df, test_size=0.25, random_state=SEED, stratify = df['class'])

#check if train and valid set have the same proportions of labels; these lines have debug purpose
print('% train set label 0: ', round((len(train_set[train_set['class'] == 0])/len(train_set)*100),2))
print('% valid set label 0: ', round((len(valid_set[valid_set['class'] == 0])/len(valid_set)*100),2))
print('% train set label 1: ', round((train_set[train_set['class'] == 1]['class'].sum()/len(train_set)*100),2))
print('% valid set label 1: ', round((valid_set[valid_set['class'] == 1]['class'].sum()/len(valid_set)*100),2))
print('% train set label 2: ', round((train_set[train_set['class'] == 2]['class'].sum()/(len(train_set)*2)*100),2))
print('% valid set label 2: ', round((valid_set[valid_set['class'] == 2]['class'].sum()/(len(valid_set)*2)*100),2))


#batch size, image heigth and width and the total number of classes
bs= 16 
if use_transfer_learning:
    img_h = 400
    img_w = 600
else:
    img_h = 204
    img_w = 306
    
num_classes=3


#create the training generator using augmented images. 
train_set["class"] = train_set["class"].astype(str)
train_gen = train_data_gen.flow_from_dataframe(train_set,
                                               directory=training_dir,
                                               batch_size=bs,
                                               x_col='filename',
                                               y_col='class',
                                               target_size=(img_h, img_w),
                                               class_mode='categorical',
                                               shuffle=True,
                                               seed = SEED)

"""## Display of same images in order to understand the applaied data augmentation."""

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
import matplotlib.pyplot as plt

t_x, t_y = next(train_gen)
fig, m_axs = plt.subplots(2, 2, figsize = (8, 8))
for (c_x, c_y, c_ax) in zip(t_x, t_y, m_axs.flatten()):
    c_ax.imshow(c_x[:,:,:])
    i = np.where(np.isclose(c_y, 1.0))[0][0]
    if i == 0:
        c_ax.set_title('noone wearing mask')
    elif i == 1:
        c_ax.set_title('everyone wearing mask')
    else:
        c_ax.set_title('someone wearing mask')
    c_ax.axis('off')
    c_ax.title.set_color('red')

# make basic intensity rescaling on validation set. 
# If data augmentation is selected then preprocess_input function is applied to the input 
if apply_data_augmentation:
    val_data_gen = ImageDataGenerator(preprocessing_function=preprocess_input)
else:
    val_data_gen = ImageDataGenerator(rescale= 1./255)

#VALIDATION
valid_set["class"] = valid_set["class"].astype(str)
valid_gen = val_data_gen.flow_from_dataframe(dataframe=valid_set, 
                                           directory=training_dir,
                                           batch_size=bs,
                                           x_col='filename',
                                           y_col='class',
                                           target_size=(img_h, img_w),
                                           class_mode='categorical',
                                           shuffle=True,
                                           seed = SEED)

# make basic intensity rescaling on test set. 
# If data augmentation is selected then preprocess_input function is applaied to the input 
if apply_data_augmentation:
    test_data_gen = ImageDataGenerator(preprocessing_function=preprocess_input)
else:
    test_data_gen = ImageDataGenerator(rescale= 1./255)

#TEST
test_gen = test_data_gen.flow_from_directory(directory=dataset_dir,
                                             batch_size=1,
                                             class_mode=None,
                                             classes=['test'],
                                             target_size=(img_h, img_w),
                                             shuffle=False,
                                            )

"""## Create Dataset objects.

"""

# Training
train_dataset = tf.data.Dataset.from_generator(lambda: train_gen,
                                               output_types=(tf.float32, tf.float32),
                                               output_shapes=([None, img_h, img_w, 3], [None, num_classes]))
# Repeat
train_dataset = train_dataset.repeat()


# Validation
valid_dataset = tf.data.Dataset.from_generator(lambda: valid_gen, 
                                               output_types=(tf.float32, tf.float32),
                                               output_shapes=([None, img_h, img_w, 3], [None, num_classes]))
# Repeat
valid_dataset = valid_dataset.repeat()


# Test
test_dataset = tf.data.Dataset.from_generator(lambda: test_gen,
                                              output_types=(tf.float32, tf.float32),
                                              output_shapes=([None, img_h, img_w, 3], [None, num_classes]))
# Repeat
test_dataset = test_dataset.repeat()

"""## Architecture. We build two different architectures: one is based on the transfer learning approach while the other is a custom architecture."""

input_shape = [img_h, img_w, 3] #shape of the model input data

if use_transfer_learning:
    #Features extraction: we take oly the feature extrator part of the Vgg16 architecture
    vgg16 = VGG16(include_top=False, weights='imagenet', input_shape=input_shape)
    transfer_layer = vgg16.get_layer('block5_pool')
    vgg_model = Model(inputs=vgg16.input, outputs=transfer_layer.output)
    
    #freeze weights up to the ten layer of the vgg16 architecture
    for layer in vgg_model.layers[0:10]:
        layer.trainable = False
    
    model = tf.keras.Sequential()
    model.add(vgg_model)
    
    #Classifier is made by two dense layer of 512 neurons for layer. We use also regularization and dropout techniques.
    model.add(Flatten())  # this converts our 3D feature maps to 1D feature vectors
    model.add(Dropout(0.2))
    model.add(tf.keras.layers.Dense(units=512, activation=tf.keras.activations.relu, kernel_regularizer=tf.keras.regularizers.l1(0.0005))) 
    model.add(tf.keras.layers.Dense(units=512, activation=tf.keras.activations.relu, kernel_regularizer=tf.keras.regularizers.l1(0.0005))) 
    model.add(Dense(num_classes, activation='softmax'))
    
else:
    #Features extraction composed by 6 repetition of the convolutional block (Conv2D -> Activation -> Pooling)
    model = Sequential()
    
    model.add(Conv2D(32, (3, 3), input_shape = input_shape, activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    
    model.add(Conv2D(32, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    
    model.add(Conv2D(32, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    
    model.add(Conv2D(32, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    
    model.add(Conv2D(32, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    
    model.add(Conv2D(64, (3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    
    # Classifier is made by one dense layer of 64 neurons
    model.add(Flatten())  # this converts our 3D feature maps to 1D feature vectors
    model.add(Dense(64, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(num_classes, activation='softmax'))

#print the model summary for debug purpose 
if use_transfer_learning:
    vgg_model.summary()

model.summary()

"""## Optimization parameters: loss, learning rate, validation metrics."""

# Loss
loss = tf.keras.losses.CategoricalCrossentropy()

# learning rate is set wrt the use of transfer learning
if use_transfer_learning:
    lr = 3e-5
else:
    lr = 3e-4
    
optimizer = tf.keras.optimizers.Adam(learning_rate=lr)

# Validation metrics
metrics = ['accuracy']

# Compile Model
model.compile(optimizer=optimizer, loss=loss, metrics=metrics)

"""## Define some *callbacks functions* that are going to be called at the end of each epoch. We used *Early Stopping* in order to stop the training before the model overfits. Moreover we used *ReduceLROnPlateau* that helps the validation loss to decrease and slow down the training part in order to avoid overfitting. We then added another callback called *LearningRateScheduler* in order to tweak the learning rate after each epoch given a function `scheduler` ."""

class CustomEarlyStopping(tf.keras.callbacks.Callback):
    def __init__(self, patience=0):
        super(CustomEarlyStopping, self).__init__()
        self.patience = patience
        # best_weights to store the weights at which the minimum loss occurs.
        self.best_weights = None

    def on_train_begin(self, logs=None):
        # The number of epoch it has waited when loss is no longer minimum.
        self.wait = 0
        # The epoch the training stops at.
        self.stopped_epoch = 0
        # Initialize the best as infinity.
        self.best = np.Inf

    def on_epoch_end(self, epoch, logs=None):
        accuracy = logs.get("accuracy")
        val_accuracy = logs.get("val_accuracy")
        if epoch > 10 and np.less(val_accuracy + 5, accuracy):
            self.wait += 1
            if self.wait >= self.patience:
                self.stopped_epoch = epoch
                self.model.stop_training = True
                print("Restoring model weights from the end of the best epoch.")
                self.model.set_weights(self.best_weights)
        else:
            self.best = current
            self.wait = 0
            # Record the best weights if current results is better (less).
            self.best_weights = self.model.get_weights()

    def on_train_end(self, logs=None):
        if self.stopped_epoch > 0:
            print("Epoch %05d: early stopping" % (self.stopped_epoch + 1))

callbacks = []
# --------------
early_stop = True
attenuate_lr = True
schedule_lr = False
use_custom = False #set the custom early stopping previously defined

#early stopping is set with a patience of four epoch on the reduction (delta of 0.005) of the validation accuracy
if early_stop:
    es = tf.keras.callbacks.EarlyStopping(monitor='val_loss',
                                          min_delta=0.005,
                                          patience = 4,
                                          verbose=1,
                                          mode='min',                                        
                                         )
    callbacks.append(es)

# Attenuate learning rate is set with a patience of three on the reduction of the validation accuracy.
#the new_lr is equal to the previous multiply by 0.3. this is repeated up to a minimum learninig rate of 10^(-7)
if attenuate_lr:
    reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', 
                                                     mode='min', 
                                                     factor=0.3, 
                                                     patience=3, 
                                                     min_lr=1e-7, 
                                                     verbose=1, 
                                                     cooldown=0)
    callbacks.append(reduce_lr)

# This function keeps the initial learning rate for the first ten epochs and decreases it exponentially after that.  
def scheduler(epoch, lr):
    k = 0.1
    if epoch < 10:
        return lr
    else:
        return lr * tf.math.exp(-k)

if schedule_lr:
    cb = tf.keras.callbacks.LearningRateScheduler(schedule=scheduler, verbose=1)
    callbacks.append(cb)
    
#save checkpoint of the best model wrt the validation loss
callbacks.append(tf.keras.callbacks.ModelCheckpoint(filepath='best_model.h5', monitor='val_loss', save_best_only=True))

#set to use the ustom early stopping
if use_custom:
    callbacks.append(CustomEarlyStopping())

"""## Now we are ready to train the model."""

#print start time of the model's training
from datetime import datetime
start = datetime.now()
print(start)

#fit of the model. It runs for a maximum of ten epochs. each epoch has a lenght of training set divided by batch size
history=model.fit(x=train_dataset,
          epochs=100,  
          steps_per_epoch=len(train_gen),
          validation_data=valid_dataset,
          validation_steps=len(valid_gen),
          callbacks=callbacks)

#print the total time of training for debug purpose
end = datetime.now()
delta = str(end-start)
print("============================================")
print("Time taken (h/m/s): %s" %delta[:7])
print("============================================")

"""## Import the best checkpoint of the model for all the epochs we went through. We decided that the best one is the one with the least validation  loss."""

from keras.models import load_model
model = load_model('best_model.h5')

"""## Create a function to export predictions to .csv format (required by kaggle to test our model)"""

def create_csv(results, results_dir='./'):

    csv_fname = 'results_'
    csv_fname += datetime.now().strftime('%b%d_%H-%M-%S') + '.csv'

    with open(os.path.join(results_dir, csv_fname), 'w') as f:

        f.write('Id,Category\n')

        for key, value in results.items():
            f.write(key + ',' + str(value) + '\n')

"""# Make Predictions with our new trained model."""

test_gen.reset()
predictions = model.predict_generator(test_gen, len(test_gen), verbose=1)

results = {}
import ntpath
images = test_gen.filenames

i = 0

for p in predictions:
  prediction = np.argmax(p)
  image_name = ntpath.basename(images[i])
  results[image_name] = str(prediction)
  i = i + 1
    
create_csv(results)

"""## Plot accuracy and loss for both training and validation sets."""

# plot of the training and validation loss
with plt.rc_context({'axes.edgecolor':'orange', 'xtick.color':'red', 'ytick.color':'green', 'figure.facecolor':'white'}):
    plt.plot(history.history['loss'],'r',label='training loss')
    plt.plot(history.history['val_loss'],label='validation loss')
    x=plt.xlabel('# epochs')
    y=plt.ylabel('loss')
    plt.legend()
    plt.show()

# plot of the training and validation accuracy
with plt.rc_context({'axes.edgecolor':'orange', 'xtick.color':'red', 'ytick.color':'green', 'figure.facecolor':'white'}):
    plt.plot(history.history['accuracy'],'r',label='training accuracy')
    plt.plot(history.history['val_accuracy'],label='validation accuracy')
    x=plt.xlabel('# epochs')
    y=plt.ylabel('loss')
    plt.legend()
    plt.show()
