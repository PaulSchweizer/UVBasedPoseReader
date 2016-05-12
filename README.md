# UVBasedPoseReader
## PoseReader setup for Maya

This setup uses a nurbsSphere with a color ramp and a locator to sample the color at the closest point on surface to determine the outValue for the poseReader. To achieve a variable coneAngle, the ramp color value positions are made controllable through a simple node setup and an attribute driving it.

![PoseReader](/posereader.gif)

1. Instantiating the class will run the setup.

3. The top node of the setup, referred to as info_node in the code will hold attributes for the __outValue__ and the __coneAngle__ of the PoseReader that work just like a classic PoseReader setup.
