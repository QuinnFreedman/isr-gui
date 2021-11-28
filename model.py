import ISR
import ISR.models
import numpy as np
from PIL import Image

from PySide6.QtCore import QThread, Signal

class Model:
    class WorkerThread(QThread):
        done = Signal()

        def __init__(self, model, params, parent=None):
            super().__init__(parent)
            self.model = model
            self.params = params

        def run(self):
            print(self.params)
            network_id = self.params["model"]
            print("Loading model...")
            if network_id == 0:
                self.model._network = ISR.models.RDN(weights="psnr-small", arch_params=self.params)
            elif network_id == 1:
                self.model._network = ISR.models.RDN(weights="psnr-large", arch_params=self.params)
            elif network_id == 2:
                self.model._network = ISR.models.RDN(weights="noise-cancel", arch_params=self.params)
            elif network_id == 3:
                self.model._network = ISR.models.RRDN(weights="gans", arch_params=self.params)
            print("Processing image...")

            original = np.array(self.model._source.convert("RGB"))
            upscaled = self.model._network.predict(original)
            self.model._result = Image.fromarray(upscaled).convert("RGBA")
            print("worker thread done")
            self.done.emit()
            
    def __init__(self):
        self._source = None
        self._result = None
        self._network = None
        self.source_changed_listeners = []
        self.result_changed_listeners = []
        self.loading_listeners = []
        self.networks = [
            "PSNR small",
            "PSNR large",
            "PSNR denoise",
            "RRDN GANs",
            ]

    def _did_load_network(self):
        self._set_busy(False)

    def set_source(self, image):
        self._source = image
        self._result = None
        for fn in self.source_changed_listeners:
            fn(self._source)
        for fn in self.result_changed_listeners:
            fn(self._result)

    def process_image(self, **kwargs):
        print("process image")
        self._set_busy(True)
        self.thread = Model.WorkerThread(self, kwargs)
        self.thread.done.connect(self._did_process_image)
        self.thread.start()
        
    def _did_process_image(self):
        print("Done processing image")
        for fn in self.result_changed_listeners:
            fn(self._result)
        self._set_busy(False)
            

    def _set_busy(self, busy):
        for fn in self.loading_listeners:
            fn(busy)

    def save(self, filename):
        if self._result:
            self._result.save(filename)
            print("Image saved to", filename)
        

    def add_source_listener(self, fn):
        self.source_changed_listeners.append(fn)
        
    def remove_source_listener(self, fn):
        self.source_changed_listeners.remove(fn)
        
    def add_result_listener(self, fn):
        self.result_changed_listeners.append(fn)
        
    def remove_result_listener(self, fn):
        self.result_changed_listeners.remove(fn)
        
    def add_loading_listener(self, fn):
        self.loading_listeners.append(fn)
        
    def remove_loading_listener(self, fn):
        self.loading_listeners.remove(fn)


