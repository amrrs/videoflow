from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import numpy as np
import cv2

from ...core.node import ProcessorNode
from ...utils.parsers import parse_label_map
from ...utils.downloader import get_file

from .detectors import BASE_URL_DETECTION

class ImageAnnotator(ProcessorNode):
    '''
    Interface for all image annotators. 
    All image annotators receive as input an image and annotation
    metadata, and return as output a copy of the image with
    the drawings representing the metadata.
    '''
    def __init__(self, nb_tasks = 1):
        super(ImageAnnotator, self).__init__(nb_tasks = nb_tasks)
    
    def _annotate(self, im : np.array, annotations : any) -> np.array:
        raise NotImplementedError('Subclass must implement this method')

    def process(self, im : np.array, annotations : any) -> np.array:
        '''
        Returns a copy of ``im`` visually annotated with the annotations defined in `annotations`
        '''
        to_annotate = np.array(im)
        return self._annotate(to_annotate, annotations)
        
class BoundingBoxAnnotator(ImageAnnotator):
    '''
    Draws bounding boxes on images.
    - Arguments:
        - class_labels_path: path to pbtxt file that defines the labels indexes
        - class_labels_dataset: If class_labels_path is None, then we use this attribute to \
            download the file from the releases folder.
        - box_color: color to use to draw the boxes
        - box_thickness: thickness of boxes to draw
        - text_color: color of text to draw
    '''
    def __init__(self, class_labels_path = None, class_labels_dataset = 'coco', 
                box_color = (255, 225, 0), box_thickness = 2, text_color = (255, 255, 0), nb_tasks = 1):
        self._box_color = box_color
        self._text_color = text_color
        self._box_thickness = box_thickness

        if class_labels_path is None and class_labels_dataset is None:
            raise ValueError('If class_labels_path is None, then class_labels_dataset cannot be None')

        if class_labels_path is None:
            labels_file_name = f'labels_{class_labels_dataset}.pbtxt'
            remote_url = BASE_URL_DETECTION + labels_file_name
            class_labels_path = get_file(labels_file_name, remote_url)

        self._index_label_d = parse_label_map(class_labels_path)
        super(BoundingBoxAnnotator, self).__init__(nb_tasks = nb_tasks)

    def _annotate(self, im : np.array, boxes : np.array) -> np.array:
        '''
        - Arguments:
            - im: np.array
            - boxes: np.array of shape (nb_boxes, 6) \
                second dimension entries are [ymin, xmin, ymax, xmax, class_index, score]
        
        - Returns:
            - annotated_im: image with the visual annotations embedded in it.
        '''

        for i in range(len(boxes)):
            bbox = boxes[i]
            ymin, xmin, ymax, xmax = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            y_label = ymin - 15 if ymin - 15 > 15 else min(ymin + 15, ymax)
            klass_id = int(bbox[4])
            klass_text = self._index_label_d[klass_id]
            confidence = bbox[5]
            label = "{}: {:.2f}%".format(klass_text, confidence * 100)
            cv2.rectangle(im, (xmin, ymin), (xmax, ymax), self._box_color, self._box_thickness)
            cv2.putText(im, label, (xmin, y_label), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self._text_color, lineType = cv2.LINE_AA)
        return im

class TrackerAnnotator(ImageAnnotator):
    '''
    Draws bounding boxes on images with track id.
    '''
    def __init__(self, box_color = (255, 225, 0), box_thickness = 2, text_color = (255, 255, 255), nb_tasks = 1):
        self._box_color = box_color
        self._text_color = text_color
        self._box_thickness = box_thickness
        super(TrackerAnnotator, self).__init__(nb_tasks = nb_tasks)

    def _annotate(self, im : np.array, boxes : np.array) -> np.array:
        '''
        - Arguments:
            - im: np.array
            - boxes: np.array of shape (nb_boxes, 5) \
                second dimension entries are [ymin, xmin, ymax, xmax, track_id]
        
        - Returns:
            - annotated_im: image with the visual annotations embedded in it.
        '''
        for i in range(len(boxes)):
            bbox = boxes[i]
            ymin, xmin, ymax, xmax = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            y_label = ymin - 15 if ymin - 15 > 15 else min(ymin + 15, ymax)
            track_id = int(bbox[4])
            label = "{}".format(track_id)
            cv2.rectangle(im, (xmin, ymin), (xmax, ymax), self._box_color, self._box_thickness)
            cv2.putText(im, label, (xmin, y_label), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self._text_color, lineType = cv2.LINE_AA)
        return im


