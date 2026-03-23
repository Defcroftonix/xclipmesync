import threading
import queue
from Xlib import X, display as xdisplay
from Xlib.protocol import event
import uuid
import sys
import time
import hashlib



# Sink entity
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


    # waiter for SelectionClear
    def run(self):
        self._pending_request = None  # track if we're waiting for a SelectionNotify
        
        while True:
            while self.display.pending_events():
                ev = self.display.next_event()
                
                if ev.type == X.SelectionClear and ev.selection == self.primary:
                    self._broadcast_request()
                
                elif ev.type == X.SelectionRequest:
                    self._handle_selection_request(ev)
                
                elif ev.type == X.SelectionNotify:
                    self._handle_selection_notify(ev)
            
            try:
                request = self.inbox.get_nowait()
                self._start_request(request)  # renamed, no longer blocks
            except queue.Empty:
                pass
            
            time.sleep(0.01)
        
    def _start_request(self, request: dict):
        # Just fire the convert_selection and store the pending request
        self._pending_request = request
        self.window.convert_selection(
            self.primary,
            self.utf8,
            self.primary,
            X.CurrentTime
        )
        self.display.flush()




    def _handle_selection_notify(self, ev):
        if not self._pending_request:
            return
        if ev.property == X.NONE:
            self._pending_request = None
            return
        
        prop = self.window.get_full_property(ev.property, X.AnyPropertyType)
        if not prop:
            self._pending_request = None
            return
        
        content = prop.value.tobytes()
        self._pending_request["requester"].deliver({
            "tag": self._pending_request["tag"],
            "src": self._pending_request["src"],
            "content": content
        })
        self._pending_request = None
    
    
    
    # What happen when it detect SelectionClear
    def _broadcast_request(self):
        # Generate unique tag for this change event
        tag = str(uuid.uuid4())
        
        request = {
            "tag": tag,
            "src": self.display_name,
            "requester": self  # reference to self so src knows where to deliver
        }
        
        # Send to all other sinks
        for sink in self.sinks:
            if sink is not self:
                sink.inbox.put(request)
    
    
    # when sink receive request from another sink
    def _handle_request(self, request: dict):
        # Request the PRIMARY content from X11
        self.window.convert_selection(
            self.primary,
            self.utf8,
            self.primary,
            X.CurrentTime
        )
        self.display.flush()
        
        # Wait for SelectionNotify — content is ready
        while True:
            ev = self.display.next_event()
            if ev.type == X.SelectionNotify:
                if ev.property == X.NONE:
                    return  # conversion failed, bail out
                
                # Read the content
                prop = self.window.get_full_property(ev.property, X.AnyPropertyType)
                if not prop:
                    return
                
                content = prop.value.tobytes()
                
                # Deliver back to requester with tag
                request["requester"].deliver({
                    "tag": request["tag"],
                    "src": request["src"],
                    "content": content
                })
                return
    
    
    # When it finally arrive at the original sink that broadcast request
    def deliver(self, payload: dict):
        h = content_hash(payload["content"])
        
        # Loop prevention
        if h == self.last_written:
            return
        
        # Write to our display PRIMARY
        self._set_primary(payload["content"])
        self.last_written = h
    
    
    
    
    
    # This is for the PRIMARY ownetship handling
    def _set_primary(self, content: bytes):
        # Acquire PRIMARY ownership
        self.window.set_selection_owner(self.primary, X.CurrentTime)
        self.display.flush()
        
        # Store content so we can serve it when someone requests a paste
        self._held_content = content
        
        # Listen for SelectionRequest — someone wants to paste
        while True:
            ev = self.display.next_event()
            
            if ev.type == X.SelectionRequest:
                # Someone is requesting our PRIMARY content
                if ev.selection == self.primary:
                    # Send the content back
                    ev.requestor.change_property(
                        ev.property,
                        self.utf8,
                        8,
                        self._held_content
                    )
                    
                    # Notify requestor that content is ready
                    response = event.SelectionNotify(
                        time=ev.time,
                        requestor=ev.requestor,
                        selection=ev.selection,
                        target=ev.target,
                        property=ev.property
                    )
                    ev.requestor.send_event(response)
                    self.display.flush()
            
            elif ev.type == X.SelectionClear:
                # We lost PRIMARY ownership, someone else highlighted something
                # Break out so the main loop can handle it
                break

#hash function
def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

#main
def main():
    displays = sys.argv[1:] if len(sys.argv) > 1 else [":0", ":1"]
    
    if len(displays) < 2:
        print("Error: at least 2 displays required.")
        sys.exit(1)
    
    print(f"Starting PRIMARY sync across: {', '.join(displays)}")
    
    # Create all sinks first so they can reference each other
    sinks = []
    for d in displays:
        sink = Sink(d, sinks)
        sinks.append(sink)
    
    # Start all sink threads
    for sink in sinks:
        sink.start()
        print(f"Sink started for {sink.display_name}")
    
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("Stopped.")

if __name__ == "__main__":
    main()
