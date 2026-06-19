import json
import numpy as np
from sklearn.neighbors import KNeighborsClassifier


class ImgKNN:
    def __init__(self, dataset):
        self.x = []  # features
        self.y = []  # labels start from number 0
        self.labels = []  # names of label, match y
        self.number_samples = []  # number of samples of each label
        self.features_len = 0
        self.dataset_total = 0  # number of total data samples
        self.k_value = 3  # set default k_value
        self.neigh = None  # classifier object
        
        # initial classifier
        self.format_dataset_aicode101(dataset)
        self.set_classifier()

    def format_dataset_aicode101(self, dataset):
        """
        dataset: downloaded dataset (dtype: dic) format from aicode101
        """
        # get basic information
        for idx, d in enumerate(dataset):
            for key, value in d.items():
                if key == 'classId':
                    self.labels += [value]
                if key == 'shape':
                    self.number_samples += [value[0]]
                    self.dataset_total += value[0]
                    self.features_len = value[1]
        
        # create labels in number
        for idx, num_samples in enumerate(self.number_samples):
            self.y += [idx]*num_samples

        # get features
        for idx, d in enumerate(dataset):
            for key, value in d.items():
                if key == 'data':
                    value = np.array(value)
                    self.x += np.split(value, self.number_samples[idx])

        # pick k value
        self.k_value = self.pick_k(self.dataset_total)

    def pick_k(self, num_samples):
        k_value = np.round(np.sqrt(num_samples))
        k_value = np.int(k_value)
        return k_value
                    
    def set_classifier(self): 
        self.neigh = KNeighborsClassifier(n_neighbors=self.k_value)
        self.neigh.fit(self.x, self.y)
    
    def predict(self, sample_features):
        sample_features = [sample_features]
        predict_label_num = int(self.neigh.predict(sample_features))
        predict_label = self.labels[predict_label_num]
        predict_proba = self.neigh.predict_proba(sample_features)
        return predict_label, predict_proba



if __name__ == '__main__':
    from aicode101_img_utils import read_json

    dataset = read_json('dataset.json')
    classifier = ImgKNN(dataset)
    features_len = classifier.features_len
    # fake sample
    sample = np.random.randint(2, size=features_len)
    predict, predict_proba = classifier.predict(sample)
    print(predict, predict_proba)
    

