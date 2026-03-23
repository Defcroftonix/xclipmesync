import threading
import queue
from Xlib import X, display as xdisplay
from Xlib.protocol import event

class Sink(threading.Thread):
    def __init__(self, display_name: str, sinks: list):
        super().__init__(daemon=True)
        self.display_name = display_name
        self.sinks = sinks  # reference to all sinks including self
        self.inbox = queue.Queue()
        self.last_written = None
        
        # X11 connection
        self.display = xdisplay.Display(display_name)
        self.screen = self.display.screen()
        self.root = self.screen.root
        
        # Dummy window to receive events
        self.window = self.root.create_window(
            0, 0, 1, 1, 0,
            self.screen.root_depth,
            X.InputOutput,
            X.CopyFromParent,
            event_mask=X.PropertyChangeMask
        )
        
        # PRIMARY atom
        self.primary = self.display.intern_atom("PRIMARY")
        self.utf8 = self.display.intern_atom("UTF8_STRING")




def run(self):
    while True:
        # Check X11 events
        while self.display.pending_events():
            ev = self.display.next_event()
            
            if ev.type == X.SelectionClear and ev.selection == self.primary:
                # Someone on our display just highlighted something
                # Broadcast a request to all other sinks
                self._broadcast_request()
        
        # Check our inbox for incoming requests from other sinks
        try:
            request = self.inbox.get_nowait()
            self._handle_request(request)
        except queue.Empty:
            pass
        
        time.sleep(0.01)  # tiny sleep to avoid busy loop
