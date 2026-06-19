import os
import io
import time
import tflite_runtime.interpreter as tflite
import picamera
from PIL import Image
import numpy as np


class MobilenetFeatures:
    def __init__(self, model_path="./imagenet_mobilenet_v2_050_224_feature_vector_1.tflite"):
        model_path = model_path 
        print(model_path)
        # Load the TFLite model and allocate tensors.
        self.interpreter = tflite.Interpreter(model_path)
        self.interpreter.allocate_tensors()

        # Get input and output tensors.
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        #print(self.input_details)
        #print(self.output_details)
        #print(self.interpreter.get_tensor_details())
    
    def processing_frame(self, frame):
        '''
        do frame processing
        input frame: PIL image or np array
        scaling options: PIL.Image.NEAREST, PIL.Image.BILINEAR, PIL.Image.BICUBIC,         or PIL.Image.ANTIALIAS (best quality).
        '''
        if isinstance(frame, np.ndarray):
            frame = Image.fromarray(np.uint8(frame))
            
        image = frame.convert('RGB')
        image = image.resize((224, 224), Image.BICUBIC)

        image = np.float32(image)
        nor_factor = 1./255.0
        image = image * nor_factor

        # add a batch dimension
        image = image[np.newaxis, ...]
        return image

    def extract_features(self, img):
        """
        img: shape of (1, 224, 224, 3) np array
        """
        handled_img = self.processing_frame(img)

        self.interpreter.set_tensor(self.input_details[0]['index'], handled_img)
        self.interpreter.invoke()

        # The function `get_tensor()` returns a copy of the tensor data.
        # Use `tensor()` in order to get a pointer to the tensor.
        
        #output_data = self.interpreter.get_tensor(self.output_details[0]['index']
        
        # index 172 is the AvgPool
        output_data = self.interpreter.get_tensor(172)
        #print(output_data)

        return np.squeeze(output_data)


def main_stream():
    # read data features 
    dataset = read_json('dataset.json')

    # prepare knn classifier
    classifier = ImgKNN(dataset)
    
    # use mobilenet
    mob_obj = MobilenetFeatures()

    with picamera.PiCamera(resolution=(640, 480), framerate=30) as camera:
        camera.start_preview()

        try:
            stream = io.BytesIO()
            for _ in camera.capture_continuous(
                    stream, format='jpeg', use_video_port=True):
                stream.seek(0)
                start_time = time.time()
                
                # get features and predict
                frame = Image.open(stream)
                sample_features = mob_obj.extract_features(frame)
                predict, predict_proba = classifier.predict(sample_features)
                print(predict, predict_proba)

                elapsed_ms = (time.time() - start_time) * 1000
                stream.seek(0)
                stream.truncate()
                camera.annotate_text = '%s \n%.1fms' % (predict, elapsed_ms)
        finally:
            camera.stop_preview()

def main_img(img_path):
    
    img = Image.open(img_path)
    
    # use mobilenet
    mob_obj = MobilenetFeatures()
    sample_features = mob_obj.extract_features(img)
    #np.savetxt('features_debug_pi.txt', sample_features) 
    # read data features
    dataset = read_json('dataset.json')

    # prepare KNN classifier
    classifier = ImgKNN(dataset)

    # predict
    predict, predict_proba = classifier.predict(sample_features)
    print(predict, predict_proba)
    

if __name__ == '__main__':
    from aicode101_img_utils import read_json
    from img_classify_utils import ImgKNN

    os.environ["DISPLAY"] = ":0"
    
    #main_img('paper.jpg')
    main_stream()
