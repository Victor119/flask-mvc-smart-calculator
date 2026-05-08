"""
app/widgets/ui.py
-----------------
Lightweight Python representations of FLTK-style UI widgets used by the
web layer to build render parameters.
"""

from __future__ import annotations


class Point:
    def __init__(self, x: int, y: int) -> None:
        self._x = x
        self._y = y

    def getX(self) -> int:
        return self._x

    def getY(self) -> int:
        return self._y

    def setY(self, y: int) -> None:
        self._y = y


class Fl_Output:
    def __init__(self, x: int, y: int, w: int, h: int, label: str = None) -> None:
        self.x = x
        self.y = y
        self.width = w
        self.height = h
        self.label = label
        self._value: str = ""

    def value(self, txt: str) -> None:
        self._value = txt

    def redraw(self) -> None:
        pass  # no-op in web context

    def getText(self) -> str:
        return self._value


class MyDisplayBox(Fl_Output):
    def __init__(self, pos: Point, w: int, h: int, label: str = None) -> None:
        super().__init__(pos.getX(), pos.getY(), w, h, label)

    def setText(self, txt: str) -> None:
        self.value(txt)
        self.redraw()


class MyReturnButton:
    def __init__(self, pos: Point, w: int, h: int, label: str = "&Return") -> None:
        self.x = pos.getX()
        self.y = pos.getY()
        self.w = w
        self.h = h
        self.label = label
        self.tooltip = "Push Return button to exit"
        self.labelsize = 12

    def getRenderParams(self) -> dict:
        return {"ret_x": self.x, "ret_y": self.y, "ret_w": self.w, "ret_h": self.h, "label": self.label}


class MyEditBox:
    def __init__(self, pos: Point, w: int, h: int, label: str) -> None:
        self.x = pos.getX()
        self.y = pos.getY()
        self.w = w
        self.h = h
        self.label = label
        self.tooltip = "Input field for short text with newlines."
        self.wrap = True
        self.value: str = ""

    def setText(self, txt: str) -> None:
        self.value = txt

    def getText(self) -> str:
        return self.value

    def getRenderParams(self) -> dict:
        return {
            "edit_x": self.x, "edit_y": self.y,
            "edit_w": self.w, "edit_h": self.h,
            "edit_label": self.label, "edit_value": self.value,
        }


class MyRadioButton:
    _id_counter: int = 0

    def __init__(self, pos: Point, w: int, h: int, slabel: str) -> None:
        self.x = pos.getX()
        self.y = pos.getY()
        self.w = w
        self.h = h
        self.label = slabel
        self.tooltip = "Radio button, only one button is set at a time."
        self.down_box = "FL_ROUND_DOWN_BOX"
        self.id = f"radio{MyRadioButton._id_counter}"
        MyRadioButton._id_counter += 1
        self.controller = None

    def getRenderParams(self) -> dict:
        return {"id": self.id, "label": self.label}

    def setController(self, controller) -> None:
        self.controller = controller

    def radio_button_cb(self) -> None:
        if self.controller:
            self.controller.chControl(self.label)


class MyRadioGroup:
    def __init__(self, pos: Point, w: int, h: int, label: str, no: int) -> None:
        self.elts: list[MyRadioButton] = []
        bpos = Point(pos.getX(), pos.getY())
        for i in range(no):
            bpos.setY(pos.getY() + i * 30)
            self.elts.append(MyRadioButton(bpos, w, h // no, f"My Choice {i + 1}"))

    def getButtons(self) -> list[MyRadioButton]:
        return self.elts

    def setController(self, controller) -> None:
        for rb in self.elts:
            rb.setController(controller)


class MyWindow:
    def __init__(self, pos: Point, w: int, h: int, title: str) -> None:
        if pos is None:
            self.x, self.y = 100, 200
        else:
            self.x, self.y = pos.getX(), pos.getY()
        self.w = w
        self.h = h
        self.title = title
        self.display_box = None
        self.return_button = None
        self.radio_buttons: list[MyRadioButton] = []
        self.firstdb: MyDisplayBox = None
        self.seconddb: MyDisplayBox = None
        self.thirddb: MyDisplayBox = None

    def addDisplayBox(self, box: MyDisplayBox) -> None:
        if self.firstdb is None:
            self.firstdb = box
        elif self.seconddb is None:
            self.seconddb = box
        elif self.thirddb is None:
            self.thirddb = box

    def addReturnButton(self, btn: MyReturnButton) -> None:
        self.return_button = btn

    def addRadioButton(self, rb: MyRadioButton) -> None:
        self.radio_buttons.append(rb)

    def addRadioGroup(self, group: MyRadioGroup) -> None:
        self.radio_buttons.extend(group.getButtons())

    def getRenderParams(self) -> dict:
        params = {
            "x": self.x, "y": self.y, "w": self.w, "h": self.h,
            "title": self.title,
            "first_display_box_text":  self.firstdb.getText()  if self.firstdb  else "",
            "second_display_box_text": self.seconddb.getText() if self.seconddb else "",
            "third_display_box_text":  self.thirddb.getText()  if self.thirddb  else "",
            "label": self.display_box.label if self.display_box else "",
        }
        if self.return_button:
            params.update(self.return_button.getRenderParams())
        if self.radio_buttons:
            params["radio_buttons"] = [rb.getRenderParams() for rb in self.radio_buttons]
        return params