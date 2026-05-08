"""
app/routes/web.py
-----------------
HTML web interface route.
"""

from __future__ import annotations

import logging

from flask import Blueprint, render_template, request

from app import extensions
from app.core.controller import Controller
from app.core.model import Model
from app.widgets.ui import (
    MyDisplayBox, MyEditBox, MyRadioGroup,
    MyReturnButton, MyWindow, Point,
)

logger = logging.getLogger(__name__)

web_bp = Blueprint("web", __name__, template_folder="../templates")


@web_bp.route("/", methods=["GET", "POST"])
def index():
    extensions.auth_manager._load_auth_state()
    
    # ---- Build widget tree ------------------------------------------------
    mainwindow = MyWindow(Point(100, 200), 950, 400, "Main Window")

    firstdb  = MyDisplayBox(Point(100, 50),  200, 50, "My display box")
    seconddb = MyDisplayBox(Point(375, 50),  200, 50, "Second display")
    thirddb  = MyDisplayBox(Point(200, 275), 250, 50, "Third display")

    firstdb.setText("My first output text.")
    seconddb.setText("My second output text.")
    thirddb.setText("My third output text.")

    mainwindow.addDisplayBox(firstdb)
    mainwindow.addDisplayBox(seconddb)
    mainwindow.addDisplayBox(thirddb)

    # ---- MVC wiring -------------------------------------------------------
    model = Model(extensions.db_manager, cache=extensions.global_cache)
    model.setCalculatorView(firstdb)
    model.setFibonacciView(seconddb)
    model.setFactorialView(thirddb)

    controller = Controller(db_manager=extensions.db_manager, auth_manager=extensions.auth_manager)
    controller.setModel(model)

    # ---- Radio group ------------------------------------------------------
    rg = MyRadioGroup(Point(160, 150), 150, 90, "MyChoice", 3)
    rg.setController(controller)
    mainwindow.addRadioGroup(rg)

    # ---- Return button ----------------------------------------------------
    mainwindow.addReturnButton(MyReturnButton(Point(400, 350), 100, 25))

    # ---- Edit box ---------------------------------------------------------
    eb = MyEditBox(Point(400, 130), 150, 100, "&My Input")
    eb.setText("Initial edit text\nSecond line")
    
    #------------------------------------------------------------------------

    # ---- Handle POST ------------------------------------------------------
    if request.method == "POST":
        input_text      = request.form.get("edit_box", "")
        selected_choice = request.form.get("radio_option", "")

        if selected_choice:
            controller.chControl(selected_choice)

        # Determine operation for permission check
        op_map = {"1": "calculator", "2": "fibonacci", "3": "factorial"}
        operation_type = op_map.get(selected_choice)

        error_message = None
        if operation_type:
            permitted, msg = controller.check_permission(operation_type, input_text)
            if not permitted:
                error_message = msg
                view_map = {
                    "calculator": firstdb,
                    "fibonacci":  seconddb,
                    "factorial":  thirddb,
                }
                view_map[operation_type].setText(msg)

        if not error_message:
            controller.inpControl(input_text)

        eb.setText(input_text)
        current_input   = input_text
        selected_choice = int(selected_choice) if selected_choice else 0
    else:
        current_input   = eb.getText()
        selected_choice = 0

    # ---- Render -----------------------------------------------------------
    params = mainwindow.getRenderParams()
    params.update({
        "selected_choice": selected_choice,
        "current_input":   current_input,
        "first_text":      firstdb.getText(),
        "second_text":     seconddb.getText(),
        "third_text":      thirddb.getText(),
    })

    return render_template("index.html", **params)