import re
import json
from collections import defaultdict

# Some page name substitutions.  Ones that are None or not in the dict
# will be automatically converted by transform_title().
page_map = {
    "Main Page": "",
    "Introduction to Panda3D": "intro",
    "Installing Panda3D in Windows": "installation-windows",
    "Installing Panda3D in Linux": "installation-linux",
    "General Preparation": "preparation",
    "Running your Program": None,
    "A Panda3D Hello World Tutorial": "tutorial",
    "Starting Panda3D": None,
    "Loading the Grassy Scenery": None,
    "Controlling the Camera": None,
    "Loading and Animating the Panda Model": None,
    "Using Intervals to move the Panda": None,
    "Tutorial End": None,
    "User Contributed Tutorials and Examples": None,
    "Video Tutorials": None,
    "Programming with Panda3D": None,
    "ShowBase": None,
    "The Scene Graph": None,
    "Scene Graph Manipulations": None,
    "Common State Changes": None,
    "Manipulating a Piece of a Model": None,
    "Searching the Scene Graph": None,
    "Instancing": None,
    "The Configuration File": None,
    "Configuring Panda3D": None,
    "List of All Config Variables": None,
    "Accessing Config Vars in a Program": None,
    "Models and Actors": None,
    "Loading Models": None,
    "Loading Actors and Animations": None,
    "Actor Animations": None,
    "Multi-Part Actors": None,
    "Attaching an Object to a Joint": None,
    "Controlling a Joint Procedurally": None,
    "Level of Detail": None,
    "Render Attributes": None,
    "List of All Attributes": None,
    "Lighting": None,
    "Materials": None,
    "Depth Test and Depth Write": None,
    "Fog": None,
    "Alpha Testing": None,
    "Color Write Masks": None,
    "Antialiasing": None,
    "Clip Planes": None,
    "Tinting and Recoloring": None,
    "Backface Culling and Frontface Culling": None,
    "Occlusion Culling": None,
    "Polygon Occluder Culling": None,
    "Portal Culling": None,
    "Light Ramps": None,
    "Auxiliary Bitplane Control": None,
    "Stencil Test/Write Attribute": "stencil-attribute",
    "Texturing": None,
    "Simple Texturing": None,
    "Choosing a Texture Size": None,
    "Texture Wrap Modes": None,
    "Texture Filter Types": None,
    "Simple Texture Replacement": None,
    "Multitexture Introduction": None,
    "Texture Modes": None,
    "Texture Order": None,
    "Texture Combine Modes": None,
    "Texture Transforms": None,
    "Multiple Texture Coordinate Sets": None,
    "Automatic Texture Coordinates": None,
    "Projected Textures": None,
    "Simple Environment Mapping": None,
    "3-D Textures": "3d-textures",
    "Cube Maps": None,
    "Environment Mapping with Cube Maps": None,
    "Automatic Texture Animation": None,
    "Playing MPG and AVI files": None,
    "Stereo/Multiview Textures": None,
    "Transparency and Blending": None,
    "Texture Management": None,
    "Texture Compression": None,
    "Shaders": None,
    "Shader Basics": None,
    "List of Possible Cg Shader Inputs": None,
    "List of GLSL Shader Inputs": None,
    "Shaders and Coordinate Spaces": None,
    "Known Shader Bugs and Limitations": "known-shader-issues",
    "The Shader Generator": None,
    "Cg Shader Tutorial": None,
    "Cg Tutorial Part 1": None,
    "Cg Tutorial Part 2": None,
    "Compute Shaders": None,
    "Camera Control": None,
    "The Default Camera Driver": None,
    "Lenses and Field of View": None,
    "Orthographic Lenses": None,
    "Sound": None,
    "Loading and Playing Sounds and Music": None,
    "Manipulating Sounds": None,
    "Audio Managers": None,
    "DSP Effects": None,
    "3D Audio": None,
    "Multi-Channel": None,
    "Intervals": None,
    "Lerp Intervals": None,
    "Function Intervals": None,
    "Actor Intervals": None,
    "Sound Intervals": None,
    "Motion Path and Particle Intervals": None,
    "Sequences and Parallels": None,
    "Position, Rotation and Scale Intervals": None,
    "Projectile Intervals": None,
    "Tasks and Event Handling": None,
    "Tasks": None,
    "Task Chains": None,
    "Event Handlers": None,
    "Main Loop": None,
    "Text and Image Rendering": None,
    "Text Fonts": None,
    "Text Node": None,
    "OnscreenText": None,
    "OnscreenImage": None,
    "Embedded Text Properties": None,
    "DirectGUI": None,
    "DirectButton": None,
    "DirectCheckButton": None,
    "DirectRadioButton": None,
    "DirectDialog": None,
    "DirectEntry": None,
    "DirectFrame": None,
    "DirectLabel": None,
    "DirectOptionMenu": None,
    "DirectScrolledList": None,
    "DirectWaitBar": None,
    "DirectSlider": None,
    "DirectScrollBar": None,
    "DirectScrolledFrame": None,
    "Render Effects": None,
    "Compass Effects": None,
    "Billboard Effects": None,
    "Finite State Machines": None,
    "FSM Introduction": None,
    "Simple FSM Usage": None,
    "FSM with input": None,
    "Advanced FSM Tidbits": None,
    "Terrain": None,
    "The Heightfield Tesselator": None,
    "Geometrical MipMapping": None,
    "Advanced operations with Panda3D's internal structures": "internal-structures",
    "How Panda3D Stores Vertices and Geometry": None,
    "GeomVertexData": None,
    "GeomVertexFormat": None,
    "GeomPrimitive": None,
    "Geom": None,
    "GeomNode": None,
    "BoundingVolume": None,
    "Procedurally Generating 3D Models": "procedural-generation",
    "Defining your own GeomVertexFormat": None,
    "Pre-defined vertex formats": None,
    "Creating and filling a GeomVertexData": None,
    "Creating the GeomPrimitive objects": None,
    "Putting your new geometry in the scene graph": None,
    "Other Vertex and Model Manipulation": None,
    "Reading existing geometry data": None,
    "Modifying existing geometry data": None,
    "MeshDrawer": None,
    "More about GeomVertexReader, GeomVertexWriter, and GeomVertexRewriter": None,
    "Creating New Textures from Scratch": None,
    "Writing 3D Models out to Disk": None,
    "Render-to-Texture and Image Postprocessing": None,
    "Common Image Filters": None,
    "Generalized Image Filters": None,
    "Dynamic Cube Maps": None,
    "Low-Level Render to Texture": None,
    "Panda3D Rendering Process": None,
    "Multithreaded Render Pipeline": None,
    "Introducing Graphics Classes": None,
    "The Graphics Pipe": None,
    "Creating Windows and Buffers": None,
    "Display Regions": None,
    "Creating New MouseWatchers for Display Regions": None,
    "Clearing Display Regions": None,
    "The 2D Display Region": None,
    "Stereo Display Regions": None,
    "Multi-Pass Rendering": None,
    "How to Control Render Order": None,
    "Panda3D Utility Functions": None,
    "Particle Effects": None,
    "Using the Particle Panel": None,
    "Loading Particle Systems": None,
    "Particle Effect Basic Parameters": None,
    "Particle Factories": None,
    "Particle Emitters": None,
    "Particle Renderers": None,
    "Collision Detection": None,
    "Collision Solids": None,
    "Collision Handlers": None,
    "Collision Entries": None,
    "Collision Traversers": None,
    "Collision Bitmasks": None,
    "Rapidly-Moving Objects": None,
    "Pusher Example": None,
    "Event Example": None,
    "Bitmask Example": None,
    "Clicking on 3D Objects": None,
    "Garbage Collection": None,
    "Removing Custom Class Instances": None,
    "Hardware support": None,
    "Keyboard Support": None,
    "Mouse Support": None,
    "Joystick Support": None,
    "VR Helmets and Trackers": None,
    "Math Engine": None,
    "Matrix Representation": None,
    "Physics": None,
    "Panda3D Physics Engine": None,
    "Enabling physics on a node": None,
    "Applying physics to a node": None,
    "Types of forces": None,
    "Notes and caveats": None,
    "Using ODE with Panda3D": "ode",
    "Worlds, Bodies and Masses": None,
    "Simulating the Physics World": None,
    "Attaching Bodies using Joints": None,
    "Collision Detection with ODE": None,
    "Using Bullet with Panda3D": "bullet",
    "Bullet Hello World": "hello-world",
    "Bullet Debug Renderer": "debug-renderer",
    "Bullet Collision Shapes": "collision-shapes",
    "Bullet Collision Filtering": "collision-filtering",
    "Bullet Continuous Collision Detection": "ccd",
    "Bullet Queries": "queries",
    "Bullet Ghosts": "ghosts",
    "Bullet Character Controller": "character-controller",
    "Bullet Constraints": "constraints",
    "Bullet Vehicles": "vehicles",
    "Bullet Softbodies": "softbodies",
    "Bullet Softbody Rope": "softbody-rope",
    "Bullet Softbody Patch": "softbody-patch",
    "Bullet Softbody Triangles": "softbody-triangles",
    "Bullet Softbody Tetrahedron": "softbody-tetrahedron",
    "Bullet Softbody Config": "softbody-config",
    "Bullet Config Options": "config-options",
    "Bullet FAQ": "faq",
    "Bullet Samples": "samples",
    "Motion Paths": None,
    "Timing": None,
    "The Global Clock": None,
    "Networking": None,
    "Datagram Protocol": None,
    "Client-Server Connection": None,
    "Transmitting Data": None,
    "Downloading a File": None,
    "Distributed Networking": None,
    "Multifiles": None,
    "Creating Multifiles": None,
    "Patching": None,
    "Loading resources from nonstandard sources": None,
    "File Reading": None,
    "Threading": None,
    "Subclassing": None,
    "Table of features supported per graphic renderer": None,
    "Artificial Intelligence (PANDAI)": "pandai",
    "Getting Started": None,
    "Steering Behaviors": None,
    "Seek": None,
    "Flee": None,
    "Pursue": None,
    "Evade": None,
    "Wander": None,
    "Flock": None,
    "Obstacle Avoidance": None,
    "Path Follow": None,
    "Pathfinding": None,
    "Mesh Generation": None,
    "Static Obstacles": None,
    "Dynamic Obstacles": None,
    "Uneven Terrain": None,
    "Source Codes": None,
    "Distributing Panda3D Applications": "distribution",
    "Introduction to p3d files": None,
    "Using packp3d": None,
    "Referencing packages": None,
    "Running p3d files": None,
    "Distributing via the web": None,
    "Embedding with an object element": None,
    "Embedding with RunPanda3D": None,
    "About certificates": None,
    "Public key, private key": None,
    "Self-signed certificates": None,
    "HTTPS (Apache) certificates": None,
    "Email certificates": None,
    "Signing your p3d files": None,
    "P3D file config settings": None,
    "Distributing as a self-contained installer": None,
    "The runtime Panda3D directory": None,
    "The package system": None,
    "Standard packages": None,
    "Installing packages": None,
    "More about referencing packages": None,
    "Building and hosting your own packages": None,
    "Using ppackage": None,
    "The pdef syntax": None,
    "Creating multiple packages": None,
    "Hosting packages": None,
    "SSL hosting": None,
    "Building multiplatform packages": None,
    "Building patches": None,
    "Advanced scripting techniques": None,
    "DetectPanda3D.js": None,
    "Advanced object tags": None,
    "Splash window tags": None,
    "Plugin notify callbacks": None,
    "AppRunner": None,
    "The appRunner.main object": None,
    "The appRunner.dom object": None,
    "Reading the HTML tokens": None,
    "Other appRunner members": None,
    "P3D origin security": None,
    "PackageInstaller": None,
    "Sample Programs in the Distribution": "samples",
    "Sample Programs: Asteroids": "asteroids",
    "Sample Programs: Ball in Maze": "ball-in-maze",
    "Sample Programs: Boxing Robots": "boxing-robots",
    "Sample Programs: Carousel": "carousel",
    "Sample Programs: Cartoon Shader": "cartoon-shader",
    "Sample Programs: Chessboard": "chessboard",
    "Sample Programs: Disco Lights": "disco-lights",
    "Sample Programs: Distortion": "distortion",
    "Sample Programs: Fireflies": "fireflies",
    "Sample Programs: Fractal Plants": "fractal-plants",
    "Sample Programs: Glow Filter": "glow-filter",
    "Sample Programs: Infinite Tunnel": "infinite-tunnel",
    "Sample Programs: Looking and Gripping": "looking-and-gripping",
    "Sample Programs: Media Player": "media-player",
    "Sample Programs: Motion Trails": "motion-trails",
    "Sample Programs: Mouse Modes": "mouse-modes",
    "Sample Programs: Music Box": "music-box",
    "Sample Programs: Normal Mapping": "bump-mapping",
    "Sample Programs: Particles": "particles",
    "Sample Programs: Procedural Cube": "procedural-cube",
    "Sample Programs: Roaming Ralph": "roaming-ralph",
    "Sample Programs: Shadows": "shadows",
    "Sample Programs: Solar System": "solar-system",
    "Sample Programs: Teapot on TV": "render-to-texture",
    "Sample Programs: Texture Swapping": "texture-swapping",
    "Debugging": None,
    "Log Messages": None,
    "The Python Debugger": None,
    "Running Panda3D under the CXX Debugger": None,
    "Performance Tuning": None,
    "Basic Performance Diagnostics": None,
    "Measuring Performance with PStats": None,
    "The Rigid Body Combiner": None,
    "Performance Issue: Too Many Meshes": "too-many-meshes",
    "Performance Issue: Too Many State Changes": "too-many-state-changes",
    "Performance Issue: Too Many Text Updates": "too-many-text-updates",
    "Performance Issue: Too Many Shader Instructions": "too-many-shader-instructions",
    "Performance Issue: Excessive Fill": "excessive-fill",
    "Performance Issue: Memory Full": "memory-full",
    "Performance Issue: Python Calculation": "python-calculation",
    "Performance Issue: Failure to Garbage Collect": "failure-to-garbage-collect",
    "Performance Issue: Collision System Misuse": "collision-system-misuse",
    "Performance Issue: Motherboard Integrated Video": "motherboard-integrated-video",
    "Performance Issue: Too Many Polygons": "too-many-polygons",
    "Performance Issue: Miscellaneous": "miscellaneous",
    "Using CXX": None,
    "How to compile a CXX Panda3D program": None,
    "How to build a CXX Panda3D game using Microsoft Visual Studio 2008": None,
    "How to compile a CXX Panda3D program on Linux": None,
    "How to compile a CXX Panda3D program on Mac OS X": None,
    "The Window Framework": None,
    "Texturing in CXX": None,
    "Reference Counting": None,
    "Panda3D Tools": "tools",
    "The Scene Graph Browser": None,
    "Enhanced Mouse Navigation": None,
    "Interrogate": None,
    "Python Editors": None,
    "SPE": None,
    "Pipeline Tips": None,
    "Model Export": None,
    "Converting from 3D Studio Max": None,
    "Converting from Maya": None,
    "Converting from Blender": None,
    "Converting from SoftImage": None,
    "Converting from Milkshape 3D": None,
    "Converting from GMax": None,
    "Converting from other Formats": None,
    "Converting Egg to Bam": None,
    "Parsing and Generating Egg Files": None,
    "Egg Syntax": None,
    "Previewing 3D Models in Pview": "pview",
    "Building an installer using packpanda": "packpanda",
    "The Scene Editor": None,
    "Scene Editor Lectures": None,
    "Building Panda3D from Source": "building-from-source",
    "Tutorial: Compiling the Panda3D Source on Windows": "compiling-panda3d-source-on-windows",

    "Third-party dependencies and license info": "thirdparty-licenses",
}

page_parents = {"Main Page": None}
page_children = defaultdict(list)

def parse_toc_tree(text):
    """ Parses the MediaWiki main page body and stores the TOC info. """

    stack = ["Main Page"]

    for line in text.splitlines():
        if not line.startswith('#') and not line.startswith('*'):
            continue

        prefix, title = line.split(None, 1)
        title = title.strip(' \t[]')

        while len(prefix) < len(stack):
            stack.pop()

        parent = stack[-1]

        page_parents[title] = parent
        page_children[parent].append(title)
        stack.append(title)


def write_toc_tree(fn):
    """ Writes out a JSON document containing the TOC tree. """

    json.dump(page_parents, open(fn, 'w'))


def read_toc_tree(fn):
    """ Reads the JSON file that has previously been generated by
    write_toc_tree(). """

    page_parents.clear()
    page_parents.update(json.load(open(fn, 'r')))
    page_children.clear()

    for title, parent in page_parents.items():
        page_children[parent].append(title)


def transform_title(title):
    """ Transforms a MediaWiki title into an appropriate filename. """

    if page_map.get(title) is not None:
        return page_map[title]

    title = title.replace('CXX', 'C++')
    title = re.sub(r'[_ /]', '-', title)
    title = re.sub(r'[^a-zA-Z0-9-+.]', '', title)
    title = re.sub(r'-+', '-', title)
    return title.lower()


def get_page_path(title, noindex=False):
    """ Returns the path of the given page.  Requires read_toc_tree or
    parse_toc_tree to be called first. """

    if title in page_parents:
        parent = get_page_path(page_parents[title], noindex=True)
        transformed = transform_title(title)

        if not noindex and page_children[title]:
            transformed += '/index'

        if not parent:
            return transformed
        else:
            return parent + '/' + transformed
    else:
        # Not in table of contents.
        return None


def get_page_children(title, noindex=False):
    """ Returns the subpages under a particular page, useful for building
    up the TOC tree.  Requires a TOC tree to have been read in first. """

    child_paths = []
    for child in page_children[title]:
        transformed = transform_title(child)

        if not noindex and page_children[child]:
            transformed += '/index'

        child_paths.append(transformed)

    return child_paths
