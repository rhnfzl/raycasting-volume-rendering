try:
    import wx
    from wx import glcanvas
except ImportError:
    raise ImportError("Required dependency wx.glcanvas not present")
from os.path import basename
import os
import sys
import traceback
from genevis.visualization import Visualization
from volume.volume import Volume
from volume.volumeIO import VolumeIO
from genevis.render import RenderMode
from genevis.transfer_function import TransferFunction, ControlPoint, TFColor
from util import Ellipse2D
import numpy as np
import pickle

RADIO_LABELS = {RenderMode.SLICER: "Slicer", RenderMode.MIP: "MIP", RenderMode.COMPOSITING: "Compositing", RenderMode.MULTI_VOLUME: "Challenge data", RenderMode.BRAIN_PHONG: "Challenge Data + Phong Shadowing", RenderMode.COLOR_MULTI: "Challenge Data Colour"}

DOT_SIZE = 8

TFUNC = TransferFunction()

ENERGY_TYPE = "ENERGY"
ANNOTATION_TYPE = "ANNOTATION"

try:
    with open("mapping.pkl", "rb") as file:
        ANNOTATION_2_ENERGY = pickle.load(file)
except Exception:
    print(f"File 'mapping.pkl' was not loaded. Check it is in the same base directory ({os.getcwd()}) as your python execution")
    raise Exception()


class TransferFunctionView(wx.Panel):
    mouse_down = False
    selected = 0
    drag_start = None

    def __init__(self, parent, tfunc: TransferFunction, histogram: np.ndarray, visualization: Visualization):
        wx.Panel.__init__(self, parent)
        self.tfunc = tfunc
        self.editor = parent
        self.histogram = histogram
        self.visualization = visualization

        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_mouse_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_mouse_up)

    def on_size(self, event):
        event.Skip()
        self.Refresh()

    def on_paint(self, event=None):
        dc = wx.PaintDC(self)
        w, h = self.GetSize()
        h = h - 30
        value_range = self.tfunc.sMax - self.tfunc.sMin
        minimum = self.tfunc.sMin

        dc.SetBackground(wx.Brush(wx.WHITE))
        dc.Clear()

        nrBins = len(self.histogram)
        maxBinHeight = self.histogram.max()
        binWidth = w / nrBins
        scalingFactor = h / maxBinHeight

        xs = np.arange(nrBins) * binWidth
        ys = h - scalingFactor * self.histogram
        widths = np.full(nrBins, binWidth)
        heights = scalingFactor * self.histogram

        dc.SetPen(wx.Pen(wx.Colour(125, 125, 125, 255), 4))
        dc.DrawRectangleList(np.dstack((xs, ys, widths, heights)).squeeze())

        control_points = self.tfunc.control_points
        dc.SetPen(wx.Pen(wx.BLACK))
        dc.SetBrush(wx.Brush(wx.BLACK))
        xprev = -1
        yprev = -1
        currentcolor = wx.Colour()
        prevcolor = wx.Colour()
        rect = wx.Rect(0, h + 5, 0, 0)
        for cp in control_points:
            s = cp.value
            color = cp.color
            t = (s - minimum) / value_range
            xpos = int(t * w)
            ypos = h - int(color.a * h)
            dc.DrawEllipse(xpos - DOT_SIZE / 2, ypos - DOT_SIZE / 2, DOT_SIZE, DOT_SIZE)
            if xprev > -1:
                currentcolor.Set(color.r * 255, color.g * 255, color.b * 255, 255)
                dc.DrawLine(xpos, ypos, xprev, yprev)
                rect.SetX(xprev)
                rect.SetWidth(xpos - xprev)
                rect.SetHeight(25)
                dc.GradientFillLinear(rect, prevcolor, currentcolor)

            xprev = xpos
            yprev = ypos
            prevcolor.Set(color.r * 255, color.g * 255, color.b * 255, 255)

    def get_control_point_area(self, control_point: ControlPoint) -> Ellipse2D:
        w, h = self.GetSize()
        value_range = self.tfunc.sMax - self.tfunc.sMin
        minimum = self.tfunc.sMin

        s = control_point.value
        color = control_point.color
        t = (s - minimum) / value_range
        xpos = int(t * w)
        ypos = h - int(color.a * h)
        bounds = Ellipse2D(xpos - DOT_SIZE / 2, ypos - DOT_SIZE / 2, DOT_SIZE, DOT_SIZE)
        return bounds

    def on_mouse_down(self, evt: wx.MouseEvent):
        self.drag_start = None
        control_points = self.tfunc.control_points
        inside = False
        idx = 0
        x, y = evt.GetPosition()
        while not inside and idx < len(control_points):
            inside = inside | self.get_control_point_area(control_points[idx]).contains(x, y)
            if inside:
                break
            else:
                idx = idx + 1

        if inside:
            if evt.GetButton() == wx.MOUSE_BTN_LEFT:
                self.selected = idx
                control_point = control_points[self.selected]
                self.editor.set_selected_info(self.selected, control_point.value, control_point.color.a,
                                              control_point.color)
                self.drag_start = (x, y)
            elif evt.GetButton() == wx.MOUSE_BTN_RIGHT:
                if 0 < idx < len(control_points) - 1:
                    self.tfunc.remove_control_point(idx)
                    self.selected = idx - 1
                    control_point = control_points[self.selected]
                    self.editor.set_selected_info(self.selected, control_point.value, control_point.color.a,
                                                  control_point.color)
                    self.drag_start = (x, y)
        else:
            w, h = self.GetSize()
            if 0 <= x < w and 0 <= y < h - 30:
                h = h - 30
                value_range = self.tfunc.sMax - self.tfunc.sMin
                minimum = self.tfunc.sMin
                t = x / w
                s = int((t * value_range) + minimum)
                a = (h - y) / h
                self.selected = self.tfunc.add_control_point(s, .0, .0, .0, a)
                control_point = control_points[self.selected]
                self.editor.set_selected_info(self.selected, control_point.value, control_point.color.a,
                                              control_point.color)
                self.drag_start = (x, y)
                self.Refresh()

    def on_mouse_up(self, evt: wx.MouseEvent):
        self.Refresh()
        self.visualization.Refresh()

    def on_mouse_motion(self, evt: wx.MouseEvent):
        # Dragging
        if evt.Dragging() and evt.LeftIsDown():
            if self.selected < 0:
                return
            drag_end_x, drag_end_y = evt.GetPosition()
            control_points = self.tfunc.control_points
            w, h = self.GetSize()
            h = h - 30

            if self.selected == 0 or self.selected == len(control_points) - 1:
                cp = self.get_control_point_area(control_points[self.selected])
                drag_end_x = cp.get_center_x()
                if drag_end_y < 0:
                    drag_end_y = 0
                if drag_end_y > h:
                    drag_end_y = h
            else:
                left_point = self.get_control_point_area(control_points[self.selected - 1])
                right_point = self.get_control_point_area(control_points[self.selected + 1])

                if drag_end_x <= left_point.get_center_x() + 1:
                    drag_end_x = left_point.get_center_x() + 2
                if drag_end_x >= right_point.get_center_x() - 1:
                    drag_end_x = right_point.get_center_x() - 2
                if drag_end_y < 0:
                    drag_end_y = 0
                if drag_end_y > h:
                    drag_end_y = h

            value_range = self.tfunc.sMax - self.tfunc.sMin
            minimum = self.tfunc.sMin
            t = drag_end_x / w
            s = int((t * value_range) + minimum)
            a = (h - drag_end_y) / h

            self.tfunc.update_control_point_scalar(self.selected, s)
            self.tfunc.update_control_point_alpha(self.selected, a)
            self.editor.set_selected_info(self.selected, s, a, control_points[self.selected].color)
            self.Refresh()
        # Moving around
        else:
            x, y = evt.GetPosition()
            control_points = self.tfunc.control_points
            if any(self.get_control_point_area(cp).contains(x, y) for cp in control_points):
                self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
            else:
                self.SetCursor(wx.Cursor(wx.CURSOR_DEFAULT))


class TransferFunctionTab(wx.Panel):
    selected = 0

    def __init__(self, parent, tfunc: TransferFunction, histogram: np.ndarray, visualization: Visualization):
        wx.Panel.__init__(self, parent)

        self.tfunc = tfunc
        self.tfView = TransferFunctionView(self, tfunc, histogram, visualization)
        self.visualization = visualization

        sizer = wx.BoxSizer(wx.VERTICAL)
        hbox0 = wx.BoxSizer(wx.HORIZONTAL)
        hbox0.Add(self.tfView, 2, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
        sizer.Add(hbox0, 2, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        scalar_value_label = wx.StaticText(self, -1, label="Scalar value")
        hbox1.Add(scalar_value_label, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
        self.scalar_value_field = wx.TextCtrl(self)
        hbox1.Add(self.scalar_value_field, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
        sizer.Add(hbox1)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        opacity_label = wx.StaticText(self, -1, label="Opacity")
        hbox2.Add(opacity_label, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
        self.opacity_value_field = wx.TextCtrl(self)
        hbox2.Add(self.opacity_value_field, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
        sizer.Add(hbox2)

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        color_label = wx.StaticText(self, -1, label="Color")
        hbox3.Add(color_label, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
        self.color_picker = wx.ColourPickerCtrl(self)
        hbox3.Add(self.color_picker, 1, wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, 5)
        sizer.Add(hbox3)

        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.on_color_changed)

        self.SetSizer(sizer)

    def set_selected_info(self, idx: int, s: int, a: float, color: TFColor) -> None:
        self.selected = idx
        self.scalar_value_field.SetValue(str(s))
        self.opacity_value_field.SetValue(str(a)[:4])
        self.color_picker.SetColour(wx.Colour(color.r * 255, color.g * 255, color.b * 255, 255))

    def on_color_changed(self, evt: wx.ColourPickerEvent):
        color = evt.GetColour()
        self.tfunc.update_control_point_color(self.selected, color)
        self.tfView.Refresh(False)
        self.visualization.Refresh(False)


class LoadDataTab(wx.Panel):
    def __init__(self, parent, visualization, on_data_loaded, on_challenge_data_changed):
        wx.Panel.__init__(self, parent)
        #
        # Create the load data dialog
        self.load_dialog = wx.FileDialog(self, "Open", style=wx.FD_OPEN)
        self.dir_dialog = wx.DirDialog(self, "Open folder", style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        sizer = wx.BoxSizer(wx.VERTICAL)
        font = wx.Font(15, wx.DECORATIVE, wx.NORMAL, wx.BOLD)

        volume_data_label = wx.StaticText(self, -1, style=wx.ALIGN_CENTER, label="Test volume data")
        volume_data_label.SetFont(font)
        load_button = wx.Button(self, -1, "Load volume")
        self.file_name_label = wx.StaticText(self, -1, style=wx.ALIGN_LEFT, label="File name: -")
        self.dimensions_label = wx.StaticText(self, -1, style=wx.ALIGN_LEFT, label="Dimensions: -")
        self.value_range_label = wx.StaticText(self, -1, style=wx.ALIGN_LEFT, label="Voxel value range: -")

        challenge_data_label = wx.StaticText(self, -1, style=wx.ALIGN_CENTER, label="Challenge data")
        challenge_data_label.SetFont(font)
        load_annotations_button = wx.Button(self, -1, "Open annotations folder")
        load_energies_button = wx.Button(self, -1, "Open energies folder")
        sizer_challenge = wx.BoxSizer(wx.HORIZONTAL)
        self.annotation_list = wx.ListBox(self, style=wx.LB_SINGLE)
        self.energy_list = wx.ListBox(self, style=wx.LB_MULTIPLE)
        self.energy_selected = set()
        sizer_lists = wx.BoxSizer(wx.HORIZONTAL)

        sizer.AddSpacer(5)
        sizer.Add(volume_data_label, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer.Add(load_button, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer.AddSpacer(10)
        sizer.Add(self.file_name_label)
        sizer.Add(self.dimensions_label)
        sizer.Add(self.value_range_label)
        sizer.AddSpacer(50)
        sizer.Add(challenge_data_label, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)
        sizer.AddSpacer(4)
        sizer_challenge.Add(load_annotations_button, proportion=1)
        sizer_challenge.Add(load_energies_button, proportion=1)
        sizer.Add(sizer_challenge)
        sizer_lists.Add(self.annotation_list, proportion=1, flag=wx.EXPAND)
        sizer_lists.Add(self.energy_list, proportion=1, flag=wx.EXPAND)
        sizer.Add(sizer_lists, proportion=2, flag=wx.EXPAND)

        self.SetSizer(sizer)

        load_button.Bind(wx.EVT_BUTTON, self.handle_click)
        load_annotations_button.Bind(wx.EVT_BUTTON, self.handle_annotations_click)
        load_energies_button.Bind(wx.EVT_BUTTON, self.handle_energies_click)
        self.annotation_list.Bind(wx.EVT_LISTBOX, self.handle_annotation_selected)
        self.energy_list.Bind(wx.EVT_LISTBOX, self.handle_energy_selected)

        self.visualization = visualization
        self.on_data_loaded = on_data_loaded
        self.on_challenge_data_changed = on_challenge_data_changed
        self.annotations_path = ""
        self.energies_path = ""
        self.available_energy_items = []
        self.selection = -1

    def handle_energy_selected(self, evt: wx.CommandEvent):
        selection = evt.GetSelection()
        file_name = self.available_energy_items[selection]
        energy_number = int(file_name[:-11])
        if energy_number in self.energy_selected:
            self.energy_selected.remove(energy_number)
            self.visualization.remove_energy_volume(energy_number)
        else:
            self.energy_selected.add(energy_number)
            volumeio = VolumeIO(os.path.join(self.energies_path, file_name))
            volume = Volume(volumeio.data, compute_histogram=False)
            self.visualization.add_energy_volume(energy_number, volume)

        self.on_challenge_data_changed(len(self.energy_selected) > 0)

    def handle_annotation_selected(self, evt: wx.CommandEvent):
        selection = evt.GetSelection()  # type: int
        if self.selection != selection:
            self.selection = selection
            item = self.annotations_items[selection]
            mhd_energies = ANNOTATION_2_ENERGY[item][:10]
            intersection = set(self.energy_items) & set(mhd_energies)
            self.available_energy_items = [file for file in mhd_energies if file in intersection]
            self.energy_list.Clear()
            self.energy_list.AppendItems(self.available_energy_items)
            self.energy_selected.clear()
            self.visualization.clear_energy_volumes()
            volumeio = VolumeIO(os.path.join(self.annotations_path, self.annotations_items[selection]))
            self.visualization.set_annotation_volume(Volume(volumeio.data, compute_histogram=False))

            self.on_challenge_data_changed(False)

    def handle_challenge_click(self, evt):
        if self.dir_dialog.ShowModal() == wx.ID_CANCEL:
            return "", None

        path = self.dir_dialog.GetPath()
        try:
            challenge_files = [file for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)) and file[-3:].lower() == "mhd"]
            return path, challenge_files
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
            dialog = wx.MessageDialog(None, message="An error occurred while opening the folder",
                                      style=wx.ICON_ERROR | wx.OK)
            dialog.ShowModal()
            dialog.Destroy()
            return "", None

    def handle_annotations_click(self, evt):
        path, items = self.handle_challenge_click(evt)
        self.annotations_path = path
        self.annotations_items = items
        if items is None:
            self.annotation_list.Clear()
        else:
            self.annotation_list.AppendItems(items)

    def handle_energies_click(self, evt):
        path, items = self.handle_challenge_click(evt)
        self.energies_path = path
        self.energy_items = items

    def handle_click(self, event):
        """Show the load file dialog"""
        if self.load_dialog.ShowModal() == wx.ID_CANCEL:
            return

        pathname = self.load_dialog.GetPath()
        try:
            volume_io = VolumeIO(pathname)
            volume_data = volume_io.data
            volume = Volume(volume_data)

            TFUNC.init(volume.get_minimum(), volume.get_maximum())
            self.file_name_label.SetLabel(f"File name: {basename(pathname)}")
            self.dimensions_label.SetLabel(f"Dimensions: {volume_io.dim_x}x{volume_io.dim_y}x{volume_io.dim_z}")
            self.value_range_label.SetLabel(f"Voxel value range: {volume.get_minimum():.3g}-{volume.get_maximum():.3g}")

            self.visualization.set_volume(volume)
            self.on_data_loaded(volume)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stdout)
            dialog = wx.MessageDialog(None, message="An error occurred while reading the file",
                                      style=wx.ICON_ERROR | wx.OK)
            dialog.ShowModal()
            dialog.Destroy()


class RaycastTab(wx.Panel):
    def __init__(self, parent, handle_event_radio_button):
        wx.Panel.__init__(self, parent)

        self.slicer_button = wx.RadioButton(self, label=RADIO_LABELS[RenderMode.SLICER])
        self.mip_button = wx.RadioButton(self, label=RADIO_LABELS[RenderMode.MIP])
        self.compositing_button = wx.RadioButton(self, label=RADIO_LABELS[RenderMode.COMPOSITING])
        self.multivolume_button = wx.RadioButton(self, label=RADIO_LABELS[RenderMode.MULTI_VOLUME])
        self.multivolume_button.Disable()
        self.colourmulti2_button = wx.RadioButton(self, label=RADIO_LABELS[RenderMode.BRAIN_PHONG])
        self.colourmulti2_button.Disable()
        self.colourmulti_button = wx.RadioButton(self, label=RADIO_LABELS[RenderMode.COLOR_MULTI])
        self.colourmulti_button.Disable()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.slicer_button)
        sizer.Add(self.mip_button)
        sizer.Add(self.compositing_button)
        sizer.Add(self.multivolume_button)
        sizer.Add(self.colourmulti2_button)
        sizer.Add(self.colourmulti_button)

        self.SetSizer(sizer)

        self.Bind(wx.EVT_RADIOBUTTON, self.on_radio_button)
        self.handle_event_radio_button = handle_event_radio_button

    def on_radio_button(self, event):
        if self.slicer_button.GetValue():
            mode = RenderMode.SLICER
        elif self.mip_button.GetValue():
            mode = RenderMode.MIP
        elif self.compositing_button.GetValue():
            mode = RenderMode.COMPOSITING
        elif self.multivolume_button.GetValue():
            mode = RenderMode.MULTI_VOLUME
        elif self.colourmulti2_button.GetValue():
            mode = RenderMode.BRAIN_PHONG
        elif self.colourmulti_button.GetValue():
            mode = RenderMode.COLOR_MULTI
        else:
            raise Exception("Mode not specified")

        self.handle_event_radio_button(mode)

    def enable_multivolume_mode(self, enable):
        if enable:
            self.multivolume_button.Enable()
            self.colourmulti2_button.Enable()
            self.colourmulti_button.Enable()
        else:
            self.multivolume_button.Disable()
            self.colourmulti2_button.Disable()
            self.colourmulti_button.Disable()

class GLFrame(wx.Frame):
    """A simple class for using OpenGL with wxPython."""

    def __init__(self, parent, title):
        super(GLFrame, self).__init__(parent, title=title, size=(800, 600))

        #
        # Create the load data dialog
        self.load_dialog = wx.FileDialog(self, "Open", style=wx.FD_OPEN)

        #
        # Create the canvas
        self.visualization = Visualization(self, TFUNC)
        self.volume = None

        panel = wx.Panel(self)
        note_book = wx.Notebook(panel)

        load_data_tab = LoadDataTab(note_book, self.visualization, self.on_data_loaded, self.on_challenge_data_changed)
        self.raycast_tab = RaycastTab(note_book, self.handle_event_radio_button)

        note_book.AddPage(load_data_tab, "Load Data")
        note_book.AddPage(self.raycast_tab, "Raycaster")

        note_book_sizer = wx.BoxSizer()
        note_book_sizer.Add(note_book, 1, wx.EXPAND)
        panel.SetSizer(note_book_sizer)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.visualization, proportion=3, flag=wx.EXPAND)
        sizer.Add(panel, proportion=2, flag=wx.EXPAND)
        self.SetSizer(sizer)
        sizer.Layout()
        self.note_book = note_book

    def on_data_loaded(self, volume):
        transfer_function_tab = TransferFunctionTab(self.note_book, TFUNC, volume.histogram, self.visualization)
        self.note_book.AddPage(transfer_function_tab, "Transfer function")

    def handle_event_radio_button(self, mode):
        self.visualization.set_mode(mode)

    def on_challenge_data_changed(self, enable):
        self.raycast_tab.enable_multivolume_mode(enable)
