"""Utility for visualizing focus-plane on maya cameras."""

import functools

from maya import cmds


def show_plane_window(camera, focusPlane):
    def frustum_visible(value, *args):
        cmds.setAttr(camera + ".displayCameraFrustum", value)
        cmds.setAttr(camera + ".displayCameraFarClip", value)
        cmds.setAttr(camera + ".displayCameraNearClip", value)

    def plane_visible(value, *args):
        if value:
            cmds.showHidden(focusPlane)
        else:
            cmds.hide(focusPlane)

    frustum_visible(True)
    plane_visible(True)

    window = cmds.window(title="Focus Plane Controls", width=300)
    cmds.columnLayout(adjustableColumn=True, columnOffset=["left", 30], rowSpacing=5)
    frustum = cmds.checkBox(
        label="Display Camera Frustum",
        onCommand=functools.partial(frustum_visible, True),
        offCommand=functools.partial(frustum_visible, False),
        value=True,
    )
    plane = cmds.checkBox(
        label="Display Focus Plane",
        onCommand=functools.partial(plane_visible, True),
        offCommand=functools.partial(plane_visible, False),
        value=True,
    )

    cmds.showWindow(window)


def update_plane(camera, focusPlane):
    distance = cmds.getAttr(camera + ".focusDistance")
    if distance != abs(cmds.getAttr(focusPlane + ".translateZ")):
        cmds.move(distance, focusPlane, absolute=True, objectSpace=True, z=True)


def update_focus(camera, focusPlane):
    focusDistanceAttr = camera + ".focusDistance"
    distance = abs(cmds.getAttr(focusPlane + ".translateZ"))
    if distance != cmds.getAttr(focusDistanceAttr):
        cmds.setAttr(focusDistanceAttr, distance)


def build_focal_plane(camera):
    current_selection = cmds.ls(selection=True)
    # Build geometry
    cameraXform = cmds.listRelatives(camera, parent=True)[0]
    cameraName = cameraXform.split("|")[-1]
    focusPlane = cmds.polyPlane(
        w=1, h=1, sy=3, sx=3, ax=[0, 0, 1], ch=1, name=(cameraName + "FocusPlane")
    )[0]

    cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0, pn=1)
    cmds.setAttr(focusPlane + ".rotatePivotZ", 0)
    cmds.setAttr(focusPlane + ".scalePivotZ", 0)
    cmds.setAttr(focusPlane + ".rotateY", 180)

    # Use expressions to update geo as FOV and apertures are changed
    expr = "{0}.scaleZ * (({1}.focusDistance / {1}.farClipPlane) * {1}.farClipPlane) * {1}.{2} * 25.4 / {1}.focalLength"
    scaleX = expr.format(focusPlane, camera, "horizontalFilmAperture")
    scaleY = expr.format(focusPlane, camera, "verticalFilmAperture")

    cmds.expression(
        s="{0}.scaleX = {1};{0}.scaleY = {2};".format(focusPlane, scaleX, scaleY),
        n="{}_Expr".format(focusPlane),
    )
    cmds.parent(focusPlane, cameraXform, relative=True)
    update_plane(camera, focusPlane)

    transformAttrs = (
        "scale",
        "rotate",
        "rotateOrder",
        "translateX",
        "translateY",
        "shear",
        "inheritsTransform",
    )
    for attr in transformAttrs:
        cmds.setAttr("{}.{}".format(focusPlane, attr), lock=True)

    cmds.scriptJob(
        attributeChange=[
            camera + ".focusDistance",
            functools.partial(update_plane, camera, focusPlane),
        ]
    )
    cmds.scriptJob(
        attributeChange=[
            focusPlane + ".translateZ",
            functools.partial(update_focus, camera, focusPlane),
        ]
    )

    cmds.toggle(focusPlane, template=True)
    show_plane_window(camera, focusPlane)
    cmds.select(current_selection, replace=True)


def main():
    # get selected items
    selected_cameras = cmds.ls(selection=True, type="camera", dag=True)

    if not selected_cameras:
        cmds.error("You need to select a camera.", noContext=True)
    else:
        camera = selected_cameras[0]
        cameraXform = cmds.listRelatives(camera, parent=True)[0]
        camera_children = cmds.listRelatives(cameraXform, allDescendents=True) or []
        for child in camera_children:
            if "FocusPlane" in child:
                show_plane_window(camera, child)
                break
        else:
            build_focal_plane(camera)


main()
