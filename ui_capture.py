import time
import tkinter as tk
from PIL import ImageGrab


class RegionCapture:
    def __init__(self):
        self._owns_parent = False
        self.parent = tk._default_root
        if self.parent is None:
            self.parent = tk.Tk()
            self.parent.withdraw()
            self._owns_parent = True

        self.root = tk.Toplevel(self.parent)
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.25)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        self.start_x = 0
        self.start_y = 0
        self.rect = None
        self.bbox = None

        self.canvas = tk.Canvas(
            self.root,
            cursor="crosshair",
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<ButtonPress-3>", self.on_cancel)
        self.canvas.bind("<Escape>", self.on_cancel)
        self.root.bind("<Escape>", self.on_cancel)

    def on_press(self, event):
        if self.rect is not None:
            self.canvas.delete(self.rect)
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(
            self.start_x,
            self.start_y,
            self.start_x,
            self.start_y,
            outline='white',
            width=2,
            dash=(4, 2)
        )

    def on_drag(self, event):
        if self.rect is None:
            return
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        if self.rect is None:
            self.on_cancel()
            return

        end_x, end_y = event.x, event.y
        if abs(end_x - self.start_x) < 3 or abs(end_y - self.start_y) < 3:
            self.on_cancel()
            return

        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        offset_x = self.root.winfo_rootx()
        offset_y = self.root.winfo_rooty()
        self.bbox = (
            int(x1 + offset_x),
            int(y1 + offset_y),
            int(x2 + offset_x),
            int(y2 + offset_y)
        )
        self.cleanup()

    def on_cancel(self, event=None):
        self.bbox = None
        self.cleanup()

    def cleanup(self):
        if self.rect is not None:
            try:
                self.canvas.delete(self.rect)
            except tk.TclError:
                pass
            self.rect = None
        try:
            self.root.grab_release()
        except tk.TclError:
            pass
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def capture(self):
        self.root.deiconify()
        self.root.lift()
        self.root.grab_set()
        self.root.focus_force()
        self.canvas.focus_set()
        self.root.update_idletasks()
        self.root.wait_window()

        if self._owns_parent and self.parent is not None:
            try:
                self.parent.destroy()
            except tk.TclError:
                pass

        if not self.bbox:
            return None

        time.sleep(0.05)
        try:
            return ImageGrab.grab(bbox=self.bbox, all_screens=True)
        except TypeError:
            return ImageGrab.grab(bbox=self.bbox)


def capture_region_to_image():
    cap = RegionCapture()
    img = cap.capture()
    return img