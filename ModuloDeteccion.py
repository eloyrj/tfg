import torch
import numpy as np
import cv2
from time import time
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pika, sys, os


class ObjectDetection:
    def __init__(self, capture_index, id,actionModuleId):
        """Initializes an ObjectDetection instance with a given camera index."""
        # module data
        self.id = id
        self.actionModuleId=actionModuleId


        self.capture_index = capture_index
        self.drondect = False
        # model information
        self.model = YOLO("runs/detect/train4/weights/last.pt")
        self.names = self.model.names
        # visual information
        self.annotator = None
        self.start_time = 0
        self.end_time = 0
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        

        self.channel.basic_publish(exchange='',
                        routing_key='detectConnect',
                        body=str(self.id+"%k%"+self.actionModuleId))

        # device information
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

    def predict(self, im0):
        """Run prediction using a YOLO model for the input image `im0`."""
        results = self.model(im0)
        return results

    def display_fps(self, im0):
        """Displays the FPS on an image `im0` by calculating and overlaying as white text on a black rectangle."""
        self.end_time = time()
        fps = 1 / np.round(self.end_time - self.start_time, 2)
        text = f'FPS: {int(fps)}'
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
        gap = 10
        cv2.rectangle(im0, (20 - gap, 70 - text_size[1] - gap), (20 + text_size[0] + gap, 70 + gap), (255, 255, 255), -1)
        cv2.putText(im0, text, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)

    def plot_bboxes(self, results, im0):
        """Plots bounding boxes on an image given detection results; returns annotated image and class IDs."""
        class_ids = []
        self.annotator = Annotator(im0, 3, results[0].names)
        boxes = results[0].boxes.xyxy.cpu()
        clss = results[0].boxes.cls.cpu().tolist()
        names = results[0].names
        for box, cls in zip(boxes, clss):
            class_ids.append(cls)
            self.annotator.box_label(box, label=names[int(cls)], color=colors(int(cls), True))
        return im0, class_ids

    def main(self):
        
        """Executes object detection on video frames from a specified camera index, plotting bounding boxes and returning modified frames."""
        cap = cv2.VideoCapture(self.capture_index)
        assert cap.isOpened()
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        frame_count = 0
        while True:
            self.start_time = time()
            ret, im0 = cap.read()
            assert ret
            results = self.predict(im0)
            im0, class_ids = self.plot_bboxes(results, im0)

            if len(class_ids) > 0:  # Only send email If not sent before
                for i in class_ids:
                    if int(i) == 0 and not self.drondect: 
                        self.dronDetectado()
                        self.drondect= True
            else:
                self.drondect = False

            self.display_fps(im0)
            cv2.imshow('Drones ', im0)
            frame_count += 1
            if cv2.waitKey(5) & 0xFF == 27:
                self.desconexion()
                break
        cap.release()
        cv2.destroyAllWindows()

    def dronDetectado(self):
        print('ALERTA - Se ha detectado un dron en las inmediaciones.')
        self.channel.queue_declare(queue='camera')
        self.channel.basic_publish(exchange='',
                        routing_key='camera',
                        body=str(self.id))
        
    def desconexion(self):
        print("dis")
        self.channel.basic_publish(exchange='',
                        routing_key='detectDisconnect',
                        body=str(self.id))
        


detector = ObjectDetection(capture_index=0, id="CamaraNorte", actionModuleId="1")


if __name__ == '__main__':
    try:
        detector.main()
    except KeyboardInterrupt:
        print('Modulo parado')
        detector.desconexion()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)