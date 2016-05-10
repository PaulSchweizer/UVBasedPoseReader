"""@brief Pose Reader based on color values on a Nurbs sphere
@date 2015/11/13
@version 1.0
@author Paul Schweizer
@email paulSchweizer@gmx.net
"""
import pymel.core as pm
from maya import cmds
__all__ = ['UVBasedPoseReader']


class UVBasedPoseReader(object):

    """Pose Reader based on color values on a Nurbs sphere.

    The top node of the setup, referred to as info_node in the code
    will hold attributes for the outValue and the coneAngle of the
    PoseReader that work just like a classic PoseReader setup.
    """

    def __init__(self,
                 name='UVBasedPoseReader',
                 cone_angle=180,
                 with_visualizer=True):
        """Initialize the PoseReader.

        @param name Name A name for the nodes
        @param cone_angle The initial cone angle of the PoseReader
        @param with_visualizer Whether to create a visualizer or not
        """
        self.name = name
        self.cone_angle = cone_angle
        self.with_visualizer = with_visualizer

        self.info_node = None
        self.nurbs_sphere = None
        self.point_on_surface = None
        self.ramp = None
        self.driver = None
        self.pose = None
        self.setup()
    # end def __init__

    def setup(self):
        """Run the setup."""
        self._basic_setup()
        self._target_setup()
        if self.with_visualizer:
            self._visualizer_setup()
        # end if
    # end def setup

    def _basic_setup(self):
        """Create the nurbs sphere and the necessary utility nodes.

        Connect the nodes to sample the color value on the closest
        point on the surface of the nurbs sphere.
        """
        self.info_node = pm.createNode('transform', n='C_%s_GRP' % (self.name))
        self.info_node.addAttr('outValue', min=-1, max=1, k=True)
        self.info_node.addAttr('coneAngle', min=0, max=180,
                               dv=self.cone_angle, k=True)
        self.info_node.addAttr('visualize', at='bool', k=True, dv=1)

        self.sphere = pm.sphere(ch=False, n='C_%s_NRB' % (self.name))[0]
        pm.parent(self.sphere, self.info_node)
        self.point_on_surface = pm.createNode('closestPointOnSurface')
        mdl = pm.createNode('multDoubleLinear')
        self.ramp = pm.createNode('ramp')

        self.sphere.ws >> self.point_on_surface.inputSurface
        mdl.setAttr('input2', 0.25)
        self.point_on_surface.parameterU >> mdl.input1
        mdl.output >> self.ramp.uCoord
        self.ramp.setAttr('type', 1)
        self.ramp.setAttr('colorEntryList[0].color', 0, 0, 0)
        self.ramp.setAttr('colorEntryList[1].position', 1)
        self.ramp.setAttr('colorEntryList[1].color', 1, 1, 1)
        self.ramp.setAttr('colorEntryList[2].position', 0)
        # Need to use maya.cmds here, because pymel does not allow to
        # set negative values on a color attribute
        cmds.setAttr('%s.colorEntryList[2].color' % self.ramp,
                     -1, -1, -1, type='double3')
        self.ramp.setAttr('colorEntryList[3].color', 0, 0, 0)
        self.ramp.outColorR >> self.info_node.outValue

        # cone angle
        rmv = pm.createNode('remapValue', n='coneAngle')
        rmv.setAttr('inputMin', 0)
        rmv.setAttr('inputMax', 180)
        rmv.setAttr('outputMin', 1)
        rmv.setAttr('outputMax', 0.5)
        self.info_node.coneAngle >> rmv.inputValue
        rmv.outValue >> self.ramp.colorEntryList[0].position
        rvs = pm.createNode('reverse', n='coneAngle')
        rmv.outValue >> rvs.inputX
        rvs.outputX >> self.ramp.colorEntryList[3].position
    # end def _basic_setup

    def _target_setup(self):
        """Setup the driver and the pose locator.

        They are used to achieve the classic pose reader setup.
        The driver rotates the pose locator which is used to get the
        closest point on surface for the color sample which determines
        the output value of the pose reader.
        """
        self.driver = pm.createNode('transform',
                                    n='C_%sDriver_LOC' % self.name,
                                    p=self.info_node)
        pm.createNode('locator',
                      n='C_%sDriver_LOCShape' % self.name,
                      p=self.driver)
        self.pose = pm.createNode('transform',
                                  n='C_%sPose_LOC' % self.name,
                                  p=self.driver)
        pm.createNode('locator',
                      n='C_%sPose_LOCShape' % self.name,
                      p=self.pose)
        self.pose.setAttr('tx', 1)
        dcm = pm.createNode('decomposeMatrix')
        self.pose.wm >> dcm.inputMatrix
        dcm.outputTranslate >> self.point_on_surface.inPosition
    # end def _target_setup

    def _visualizer_setup(self):
        """Add a shader to visualize the outValue and the coneAngle."""
        visualize_sdr = pm.shadingNode('surfaceShader', asShader=True,
                                       n='visualize')
        sets = pm.sets(renderable=True, noSurfaceShader=True, empty=True,
                       n='visualize')
        visualize_sdr.outColor >> sets.surfaceShader
        vis_ramp = pm.createNode('ramp', n='visualize')
        vis_ramp.setAttr('type', 1)
        vis_ramp.setAttr('colorEntryList[0].color', 0, 0, 0)
        vis_ramp.setAttr('colorEntryList[1].position', 1)
        vis_ramp.setAttr('colorEntryList[1].color', 0, 0, 0)
        vis_ramp.setAttr('colorEntryList[2].position', 0)
        cmds.setAttr('%s.colorEntryList[2].color' % vis_ramp, 0, 0, 0,
                     type='double3')
        vis_ramp.setAttr('colorEntryList[3].color', 0, 0, 0)
        self.ramp.outColorR >> vis_ramp.colorEntryList[1].color.colorG
        rmv = pm.createNode('remapValue', n='visualize')
        rmv.setAttr('inputMin', -1)
        rmv.setAttr('inputMax', 0)
        rmv.setAttr('outputMin', 1)
        rmv.setAttr('outputMax', 0)
        self.ramp.outColorR >> rmv.inputValue
        rmv.outValue >> vis_ramp.colorEntryList[2].color.colorR

        (self.ramp.colorEntryList[0].position >>
         vis_ramp.colorEntryList[0].position)
        (self.ramp.colorEntryList[3].position >>
         vis_ramp.colorEntryList[3].position)

        vis_ramp.outColor >> visualize_sdr.outColor
        pm.defaultNavigation(source=visualize_sdr,
                             destination=self.sphere.getShape().instObjGroups[0],
                             connectToExisting=True)
    # end def _visualizer_setup
# end class UVBasedPoseReader


UVBasedPoseReader()
