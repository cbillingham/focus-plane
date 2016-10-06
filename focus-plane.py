import maya.cmds as cmds
import math, sys

def showPlaneWindow(camera, focusPlane):

   def frustumOn(*args):
      cmds.setAttr(camera[0]+".displayCameraFrustum", 1)
      cmds.setAttr(camera[0]+".displayCameraFarClip", 1)
      cmds.setAttr(camera[0]+".displayCameraNearClip", 1)

   def frustumOff(*args):
      cmds.setAttr(camera[0]+".displayCameraFrustum", 0)
      cmds.setAttr(camera[0]+".displayCameraFarClip", 0)
      cmds.setAttr(camera[0]+".displayCameraNearClip", 0)

   def planeOn(*args):
      cmds.showHidden(focusPlane)

   def planeOff(*args):
      cmds.hide(focusPlane)

   frustumOn()
   planeOn()

   window = cmds.window(title="Focus Plane Controls", width=300)
   cmds.columnLayout( adjustableColumn=True, columnOffset=["left", 30], rowSpacing=5 )
   frustum = cmds.checkBox( label='Display Camera Frustum', onCommand=frustumOn, offCommand=frustumOff, value=True)
   plane = cmds.checkBox( label='Display Focus Plane', onCommand=planeOn, offCommand=planeOff, value=True)

   cmds.showWindow(window)

def updateDistance(camera, focusPlane):
   distance = cmds.getAttr(camera[0]+".focusDistance")
   print distance
   cmds.move(distance, focusPlane, absolute=True, objectSpace=True, z=True)

def build_focal_plane(camera):
   #Gather relevant camera attributes
   focalLength = cmds.getAttr(camera[0]+".focalLength")
   horizontalAperture = cmds.getAttr(camera[0]+".cameraAperture")[0][0]
   verticalAperture = cmds.getAttr(camera[0]+".cameraAperture")[0][1]
   nearClipping = cmds.getAttr(camera[0]+".nearClipPlane")
   farClipping = cmds.getAttr(camera[0]+".farClipPlane")
   focusDistance = cmds.getAttr(camera[0]+".focusDistance")

   #Build geometry
   focusPlane = cmds.polyPlane(w=1, h=1, sy=3, sx=3, ax=[0,0,1], ch=1, name=camera[0].replace("Shape", "FocusPlane"))
   
   cmds.makeIdentity(apply=True, t=1, r=1, s=1, n=0, pn=1); 
   cmds.setAttr(focusPlane[0]+".rotatePivotZ", 0)
   cmds.setAttr(focusPlane[0]+".scalePivotZ", 0)
   cmds.setAttr(focusPlane[0]+".rotateY", 180)

   #Use expressions to update geo as FOV and apertures are changed 
   scaleX = "%s.scaleZ*((%s.focusDistance)/(%s.farClipPlane)*%s.farClipPlane)*%s.horizontalFilmAperture*25.4/%s.focalLength" % (focusPlane[0],camera[0],camera[0],camera[0],camera[0],camera[0])
   scaleY = "%s.scaleZ*((%s.focusDistance)/(%s.farClipPlane)*%s.farClipPlane)*%s.verticalFilmAperture*25.4/%s.focalLength" % (focusPlane[0],camera[0],camera[0],camera[0],camera[0],camera[0])


   cmds.expression(s="%s.scaleX = %s;%s.scaleY = %s;" % (focusPlane[0],scaleX,focusPlane[0],scaleY), n="%s_Expr" % focusPlane[0])
   cmds.parent(focusPlane, camera[0], relative=True)
   updateDistance(camera, focusPlane)

   cmds.scriptJob( attributeChange=[camera[0]+".focusDistance", (lambda: updateDistance(camera, focusPlane)) ] )

   cmds.toggle(focusPlane, te=True)

   showPlaneWindow(camera,focusPlane)

#get selected items
camera = cmds.ls(selection=True)
camera_children = cmds.listRelatives(camera)
camera = cmds.listRelatives(camera, s=True)

if not cmds.objectType(camera, isType="camera"):
   print "ERROR: You need to select a camera."
   sys.exit(0)
else:
   build = True
   for child in camera_children:
      if "FocusPlane" in child:
         build=False
         showPlaneWindow(camera,child)
         break
   if (build):
      build_focal_plane(camera)
