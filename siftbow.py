"""
Batik image classification using SIFT Bag of Words feature extractor

Author: yohanes.gultom@gmail.com
"""

import sys
import os
import cv2
import numpy as np
import pickle
import argparse
from helper import get_dir_info, build_extractor, build_dataset
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

# config
classfiers = [
    LogisticRegression(),
    SVC(),    
    MLPClassifier(),
    DecisionTreeClassifier(),
    GradientBoostingClassifier(),
    RandomForestClassifier(),
]

# default params
CV = 7
dictionary_size = 2800
bow_sift_dictionary = 'bow_sift_dictionary.pkl'
bow_sift_features = 'bow_sift_features.pkl'
bow_sift_features_labels = 'bow_sift_features_labels.pkl'
bow_sift_features_test = 'bow_sift_features_test.pkl'
bow_sift_features_labels_test = 'bow_sift_features_labels_test.pkl'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Preprocess, vectorize, extract SIFT features and evaluate classifiers', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('train_dir_path', help="Path to raw train dataset directory")
    parser.add_argument('test_dir_path', help="Path to raw test dataset directory")
    parser.add_argument('--n_folds', '-n', type=int, default=CV, help="Number of folds (K) for K-fold cross validation")
    parser.add_argument('--dictionary_size', '-d', type=int, default=dictionary_size, help="BoW dictionary size (k-means clusters size)")

    args = parser.parse_args()
    train_dir_path = args.train_dir_path
    test_dir_path = args.test_dir_path
    n_folds = args.n_folds
    dictionary_size = args.dictionary_size

    sift = cv2.xfeatures2d.SIFT_create()

    # prepare train data
    print('Collecting train data..')
    if os.path.isfile(bow_sift_dictionary) and os.path.isfile(bow_sift_features) and os.path.isfile(bow_sift_features_labels):
        dictionary = pickle.load(open(bow_sift_dictionary, "rb"))
        extractor, _ = build_extractor(sift, dictionary=dictionary)
        train_desc = pickle.load(open(bow_sift_features, "rb"))
        train_labels = pickle.load(open(bow_sift_features_labels, "rb"))
        print('Loaded from {}'.format(bow_sift_dictionary))
        print('Loaded from {}'.format(bow_sift_features))
        print('Loaded from {}'.format(bow_sift_features_labels))
    else:        
        dir_names, file_paths, file_dir_indexes = get_dir_info(train_dir_path)
        extractor, dictionary = build_extractor(sift, dir_names=dir_names, file_paths=file_paths, dictionary_size=dictionary_size)
        train_desc, train_labels = build_dataset(
            dir_names, 
            file_paths,
            file_dir_indexes,
            extractor,
            sift
        )
        pickle.dump(dictionary, open(bow_sift_dictionary, "wb"))
        pickle.dump(train_desc, open(bow_sift_features, "wb"))
        pickle.dump(train_labels, open(bow_sift_features_labels, "wb"))

    # prepare test data
    print('Collecting test data..')
    if os.path.isfile(bow_sift_features_test) and os.path.isfile(bow_sift_features_labels_test):
        test_desc = pickle.load(open(bow_sift_features_test, "rb"))
        test_labels = pickle.load(open(bow_sift_features_labels_test, "rb"))
        print('Loaded from {}'.format(bow_sift_features_test))
        print('Loaded from {}'.format(bow_sift_features_labels_test))
    else:
        dir_names, file_paths, file_dir_indexes = get_dir_info(test_dir_path)
        test_desc, test_labels = build_dataset(
            dir_names, 
            file_paths,
            file_dir_indexes,
            extractor,
            sift
        )
        pickle.dump(test_desc, open(bow_sift_features_test, "wb"))
        pickle.dump(test_labels, open(bow_sift_features_labels_test, "wb"))

    print('Train & test classifiers. CV = {}..'.format(n_folds))
    X_train = np.array(train_desc)
    y_train = np.array(train_labels)
    X_test = np.array(test_desc)
    y_test = np.array(test_labels)

    # scale data
    # scaler = StandardScaler()
    # scaler.fit(X_train)
    # X_train = scaler.transform(X_train)
    # X_test = scaler.transform(X_test)

    # for CV
    X = np.concatenate((X_train, X_test), axis=0)
    y = np.concatenate((y_train, y_test), axis=0)
    print('Dataset: {}'.format(X.shape))
    
    for classifier in classfiers:
        # cross_validate
        scores = cross_val_score(classifier, X, y, cv=n_folds)
        print("{} CV accuracy: {:0.2f} (+/- {:0.2f})".format(type(classifier).__name__, scores.mean(), scores.std() * 2))

        # # no cv
        # classifier.fit(X_train, y_train)
        # y_predict = classifier.predict(X_test)
        # acc = accuracy_score(y_test, y_predict)
        # print('Accuracy: {}'.format(acc))
        # print('Confusion matrix: ')
        # cm = confusion_matrix(y_test, y_predict)
        # print(cm)
        # print('\n')