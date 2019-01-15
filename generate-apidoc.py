""" This script generates a pandadoc.rst file representing the Python
wrappers that can be parsed by doxygen to generate the Python documentation.
You need to run this before invoking Doxyfile.python.

It requires a valid makepanda installation with interrogatedb .in
files in the lib/pandac/input directory. """

from __future__ import print_function
from collections import defaultdict

__all__ = []

import os
from io import StringIO
import panda3d
import pandac
from panda3d.interrogatedb import *
from panda3d import core
import direct

LICENSE = """PANDA 3D SOFTWARE
Copyright (c) Carnegie Mellon University.  All rights reserved.
All use of this software is subject to the terms of the revised BSD
license.  You should have received a copy of this license along
with this source code in a file named \"LICENSE.\"""".split("\n")

CLASS_HEADER = """{type}
{type_underline}

{description}

.. currentmodule:: {module}

"""

CV_CLASSES = [
    "ConfigVariable",
    "ConfigVariableList",
    "ConfigVariableString",
    "ConfigVariableFilename",
    "ConfigVariableBool",
    "ConfigVariableInt",
    "ConfigVariableDouble",
    "ConfigVariableEnum",
    "ConfigVariableSearchPath",
    "ConfigVariableInt64",
    "ConfigVariableColor",
]

library_ordering = [
    "libp3dtoolbase",
    "libp3dtoolutil",
    "libp3prc",
    "libp3express",
    "libp3putil",
    "libp3linmath",
    "libp3mathutil",
    "libp3downloader",
    "libp3nativenet",
    "libp3net",
    "libp3event",
]

library_titles = {
    "libp3dtoolbase": "Type System",
    "libp3dtoolutil": "File System",
    "libp3prc": "Configuration",

    "libp3putil": "Utility",
    "libp3audio": "Audio",
    "libp3chan": "Animations",
    "libp3char": "Characters",
    "libp3collide": "Collision Detection",
    "libp3device": "Input Devices",
    "libp3dgraph": "Data Graph",
    "libp3display": "Display",
    "libp3downloader": "HTTP",
    "libp3dxml": "XML",
    "libp3event": "Tasks and Events",
    "libp3express": "Express",
    "libp3gobj": "Graphics Objects",
    "libp3grutil": "Graphical Utility",
    "libp3gsgbase": "Display Base",
    "libp3linmath": "Linear Math",
    "libp3mathutil": "Math Utility",
    "libp3movies": "Media",
    "libp3net": "Networking",
    "libp3nativenet": "Sockets",
    "libp3parametrics": "Parametrics",
    "libp3pgraph": "Scene Graph",
    "libp3pgraphnodes": "Scene Graph Nodes",
    "libp3pgui": "PGui",
    "libp3pipeline": "Multi-Threading",
    "libp3pnmimage": "Imaging",
    "libp3pnmtext": "Text Rasterization",
    "libp3pstatclient": "PStats Client",
    "libp3recorder": "Recorder",
    "libp3text": "Text",
    "libp3tform": "Transformers",

    "libp3physics": "Physics",
    "libp3particlesystem": "Particle System",

    "libp3dcparser": ".dc File Parser",
    "libp3deadrec": "Smooth Mover",
    "libp3interval": "Intervals",
    "libp3motiontrail": "Motion Trails",
    "libp3distributed": "Distributed Networking",
}


class ReSTWriter(object):
    def __init__(self):
        self._spaces = ""
        self._buffer = None

    def __del__(self):
        if self._buffer and self._buffer.getvalue():
            self.close()

    def _append(self, data):
        self._buffer += data

    def open(self, fn):
        self._fn = fn
        self._buffer = StringIO()
        self._write = self._buffer.write

    def close(self):
        if os.path.isfile(self._fn):
            current = open(self._fn, 'r').read()
        else:
            current = None

        buffer_value = self._buffer.getvalue()
        if current != buffer_value:
            print("Writing {}".format(self._fn))
            open(self._fn, 'w').write(buffer_value)
        self._buffer = None

    def discard(self):
        self._buffer = None

    def directive(self, block):
        self._write("\n" + self._spaces + ".. " + block + "\n")
        return self

    def __enter__(self):
        self._spaces += "   "
        return self

    def __exit__(self, type, value, traceback):
        self._spaces = " " * (len(self._spaces) - 3)

    def write(self, stuff):
        for line in stuff.splitlines():
            self._write(self._spaces + line + "\n")

    def writeln(self, line=""):
        if not line:
            self._write("\n")
        else:
            self._write(self._spaces + line + "\n")


def ref_class(typename, module=None):
    if module != "panda3d.core" and hasattr(core, typename):
        return ':py:class:`panda3d.core.{}`'.format(typename)
    elif module == "panda3d.core" and not hasattr(core, typename):
        return typename
    else:
        return ':py:class:`{}`'.format(typename)


def comment(code):
    if not code:
        return ""

    comment = ''

    empty_line = False
    for line in code.splitlines(False):
        line = line.strip('\t\n /')
        if line:
            if empty_line:
                # New paragraph.
                comment += '\n\n'
                empty_line = False
            elif comment:
                comment += '\n'
            comment += '/// ' + line
        else:
            empty_line = True

    if comment:
        return comment
    else:
        return ''


def block_comment(code, extra=None):
    if not code:
        return ""

    lines = code.split("\n")
    newlines = []
    indent = 0
    reading_desc = False

    while lines:
        line = lines.pop(0)
        if line.startswith("////"):
            continue

        line = line.rstrip()
        if line.startswith('///<'):
            strline = line[4:]
        else:
            strline = line

        strline = strline.lstrip('/ \t')

        if strline == "**" or strline == "*/":
            continue

        if strline.startswith("** "):
            strline = strline[3:]
        elif strline.startswith("* "):
            strline = strline[2:]
        elif strline == "*":
            strline = ""

        strline = strline.lstrip(' \t')

        if strline.startswith('@'):
            special = strline.split(' ', 1)[0][1:]
            if special == 'par' and strline.endswith(':') and lines and '@code' in lines[0]:
                newlines.append('   '*indent + strline[5:] + ':')
                newlines.append('')
                line = lines.pop(0)
                offset = line.index('@code')
                while lines:
                    line = lines.pop(0)
                    if '@endverbatim' in line or '@endcode' in line:
                        break
                    newlines.append('   ' + line[offset:])

                newlines.append('')
                continue
            elif special == "verbatim" or special == "code":
                if newlines and newlines[-1]:
                    newlines.append('')

                newlines.append('.. code-block:: guess')
                newlines.append('')
                offset = line.index('@' + special)
                while lines:
                    line = lines.pop(0)
                    if '@endverbatim' in line or '@endcode' in line:
                        break
                    newlines.append('   ' + line[offset:])

                newlines.append('')
                continue
            elif special == "f[":
                if newlines and newlines[-1]:
                    newlines.append('')

                newlines.append('.. math::')
                newlines.append('')
                offset = line.index('@' + special)
                while lines:
                    line = lines.pop(0)
                    if '@f]' in line:
                        break
                    newlines.append('   ' + line[offset:])

                newlines.append('')
                continue
            elif special == 'param':
                if extra is not None:
                    _, name, desc = strline.split(' ', 2)
                    extra['param:' + name] = desc
                continue
            elif special in ('brief', 'return', 'returns', 'deprecated'):
                if extra is not None:
                    _, value = strline.split(' ', 1)
                    extra[special] = value
                continue
            elif special == 'details':
                strline = strline[9:]
            elif special == 'sa' or special == 'see':
                if newlines and newlines[-1]:
                    newlines.append('')

                _, value = strline.split(' ', 1)
                values = value.split(',')

                for i, value in enumerate(values):
                    value = value.strip().replace('::', '.')
                    if '(' in value:
                        value = value.split('(', 1)[0]
                        value += '()'
                    values[i] = ':py:obj:`{}`'.format(value)

                if special == 'see':
                    newlines.append('See {}.'.format(', '.join(values)))
                else:
                    newlines.append('See also {}.'.format(', '.join(values)))
                newlines.append('')
                continue
            elif special == 'note':
                if newlines and newlines[-1]:
                    newlines.append('')

                newlines.append('.. note:: ')
                newlines.append('')
                newlines.append('   ' + strline[6:])
                while lines and lines[0].startswith('     '):
                    line = lines.pop(0)
                    newlines.append('   ' + line.lstrip(' *\t'))

                newlines.append('')
                continue
            else:
                print("Unhandled documentation tag: @" + special)
                print(code)

        if strline or len(newlines) > 0:
            strline = strline.replace('<b>', '**').replace('</b>', '**')
            newlines.append('   '*indent + strline)

        #if reading_desc:
        #    newlines.append('/// ' + line[min(indent, len(line) - len(strline)):])
        #else:
        #    # A "Description:" text starts the description.
        #    if strline.startswith("Description"):
        #        strline = strline[11:].lstrip(': \t')
        #        indent = len(line) - len(strline)
        #        reading_desc = True
        #        newlines.append('/// ' + strline)
        #    else:
        #        print line

    newcode = '\n'.join(newlines)
    if len(newcode) > 0:
        return newcode
    else:
        return ""


def translateFunctionName(name):
    return name
    if name.startswith("__"):
        return name

    new = ""
    for i in name.split("_"):
        if new == "":
            new += i
        elif i == "":
            pass
        elif len(i) == 1:
            new += i[0].upper()
        else:
            new += i[0].upper() + i[1:]
    return new


def translateTypeName(name, mangle=True):
    # Equivalent to C++ classNameFromCppName
    class_name = ""
    bad_chars = "!@#$%^&*()<>,.-=+~{}? "
    next_cap = False
    first_char = mangle

    for chr in name:
        if (chr == '_' or chr == ' ') and mangle:
            next_cap = True
        elif chr in bad_chars:
            if not mangle:
                class_name += '_'
        elif next_cap or first_char:
            class_name += chr.upper()
            next_cap = False
            first_char = False
        else:
            class_name += chr

    return class_name


def translated_type_name(type, scoped=True):
    while interrogate_type_is_wrapped(type):
        if interrogate_type_is_const(type):
            #return 'const ' + translated_type_name(interrogate_type_wrapped_type(type))
            return translated_type_name(interrogate_type_wrapped_type(type))
        else:
            type = interrogate_type_wrapped_type(type)

    typename = interrogate_type_name(type)
    if typename in ("PyObject", "_object"):
        return "object"
    elif typename == "PN_stdfloat" or typename == "double":
        return "float"

    if interrogate_type_is_atomic(type):
        token = interrogate_type_atomic_token(type)
        if token == 7:
            return 'str'
        else:
            return typename

    if not typename.endswith('_t'):
        # Hack: don't mangle size_t etc.
        typename = translateTypeName(typename)

    if scoped and interrogate_type_is_nested(type):
        return translated_type_name(interrogate_type_outer_class(type)) + '.' + typename
    else:
        return typename


def process_element(out, element):
    with out.directive('attribute:: %s' % interrogate_element_name(element)):
        if interrogate_element_has_comment(element):
            out.writeln()
            out.write(block_comment(interrogate_element_comment(element)))

        if interrogate_element_has_getter(element):
            getter = interrogate_element_getter(element)
            setter = None
            out.writeln()
            if interrogate_element_has_setter(element):
                setter = interrogate_element_setter(element)
                out.write("See :py:meth:`{}` and :py:meth:`{}`.".format(interrogate_function_name(getter), interrogate_function_name(setter)))
            else:
                out.write("Read-only.  See :py:meth:`{}`.".format(interrogate_function_name(getter)))


def process_function(out, function, isConstructor = False):
    for i_wrapper in range(interrogate_function_number_of_python_wrappers(function)):
        wrapper = interrogate_function_python_wrapper(function, i_wrapper)

        #if not isConstructor:
        #    print("   .. cpp:function::", end=' ')
        #    if interrogate_function_is_method(function):
        #        if not interrogate_wrapper_number_of_parameters(wrapper) > 0 or not interrogate_wrapper_parameter_is_this(wrapper, 0):
        #            print("static", end=' ')
        #    if interrogate_wrapper_has_return_value(wrapper):
        #        print(translated_type_name(interrogate_wrapper_return_type(wrapper)), end=' ')
        #    else:
        #        print("void", end=' ')
        #    print(translateFunctionName(interrogate_function_name(function)) + "(", end='')
        #else:
        #    print("   .. cpp:function:: void __init__(", end='')

        if isConstructor:
            fname = "__init__"
            ftype = "method"
        else:
            fname = translateFunctionName(interrogate_function_name(function))
            ftype = "method"
            if interrogate_function_is_method(function):
                if not interrogate_wrapper_number_of_parameters(wrapper) > 0 or not interrogate_wrapper_parameter_is_this(wrapper, 0):
                    ftype = "staticmethod"

        sig = ""
        for i_param in range(interrogate_wrapper_number_of_parameters(wrapper)):
            if not interrogate_wrapper_parameter_is_this(wrapper, i_param):
                if sig:
                    sig += ", "
                sig += translated_type_name(interrogate_wrapper_parameter_type(wrapper, i_param))
                sig += " "
                sig += interrogate_wrapper_parameter_name(wrapper, i_param)
                #print(" : ", end='')
                #print(translated_type_name(interrogate_wrapper_parameter_type(wrapper, i_param)), end='')

        with out.directive("py:{}:: {}({})".format(ftype, fname, sig)):
            extra = {}
            comment = block_comment(interrogate_wrapper_comment(wrapper), extra)

            if comment.strip():
                out.writeln()
                out.write(comment)

            out.writeln()

            if 'deprecated' in extra:
                out.writeln(':deprecated: ' + extra['deprecated'])

            for i_param in range(interrogate_wrapper_number_of_parameters(wrapper)):
                if not interrogate_wrapper_parameter_is_this(wrapper, i_param):
                    pname = interrogate_wrapper_parameter_name(wrapper, i_param)
                    tname = translated_type_name(interrogate_wrapper_parameter_type(wrapper, i_param))
                    if 'param:' + pname in extra:
                        out.writeln(":param %s %s: %s" % (tname, pname, extra['param:' + pname]))
                    else:
                        out.writeln(":param %s %s:" % (tname, pname))

            if 'return' in extra:
                out.writeln(':return: ' + extra['return'])

            if 'returns' in extra:
                out.writeln(':returns: ' + extra['returns'])

            if not isConstructor and interrogate_wrapper_has_return_value(wrapper):
                tname = translated_type_name(interrogate_wrapper_return_type(wrapper))
                out.writeln(":rtype: %s" % (tname))


def process_type(out, type, skip_comment=False):
    typename = translated_type_name(type, scoped=False)
    derivations = [ translated_type_name(interrogate_type_get_derivation(type, n)) for n in range(interrogate_type_number_of_derivations(type)) ]

    if interrogate_type_is_typedef(type):
        wrapped_type = translated_type_name(interrogate_type_wrapped_type(type))
        #print(".. cpp:type:: %s %s" % (wrapped_type, typename))
        with out.directive("py:class:: %s" % (typename)):
            out.writeln()
            out.writeln("Alias of :py:class:`%s`." % (wrapped_type))
        return

    #print(".. cpp:%s:: %s : public %s" % (classtype, typename, ", public ".join(derivations)))
    #else:
    if interrogate_type_is_enum(type):
        directive = "cpp:enum:: %s" % (typename or "anonymous")
    #elif len(derivations) > 0:
    #    directive = "py:class:: %s(%s)" % (typename, ', '.join(derivations))
    else:
        directive = "class:: %s" % (typename)

    with out.directive(directive):
        comment = None
        extra = {}
        if interrogate_type_has_comment(type):
            comment = block_comment(interrogate_type_comment(type), extra)

        if not skip_comment:
            if comment:
                out.writeln()
                out.write(comment)
        elif 'brief' in extra:
            out.writeln()
            out.write(extra['brief'])

        if len(derivations) > 0:
            inherits = []
            for deriv in derivations:
                inherits.append(ref_class(deriv, interrogate_type_module_name(type)))
            out.writeln()
            out.writeln("Inherits from " + ', '.join(inherits) + ".")

        if interrogate_type_is_enum(type):
            for i_value in range(interrogate_type_number_of_enum_values(type)):
                name = interrogate_type_enum_value_name(type, i_value)
                value = interrogate_type_enum_value(type, i_value)
                comment = interrogate_type_enum_value_comment(type, i_value)

                #handle.write(spaces + "   .. attribute:: {}\n\n".format(name))
                with out.directive("cpp:enumerator:: {} = {}".format(name, value)):
                    if comment:
                        out.writeln()
                        out.write(block_comment(comment))

        for i_method in range(interrogate_type_number_of_constructors(type)):
            process_function(out, interrogate_type_get_constructor(type, i_method), True)

        for i_method in range(interrogate_type_number_of_methods(type)):
            process_function(out, interrogate_type_get_method(type, i_method))

        #for i_method in range(interrogate_type_number_of_make_seqs(type)):
        #    print("list", translateFunctionName(interrogate_make_seq_seq_name(interrogate_type_get_make_seq(type, i_method))), "();", file=out)

        for i_method in range(interrogate_type_number_of_make_seqs(type)):
            seq = interrogate_type_get_make_seq(type, i_method)
            with out.directive("method:: " + translateFunctionName(interrogate_make_seq_seq_name(seq)) + "()"):
                #if interrogate_make_seq_has_comment(seq):
                #    out.writeln()
                #    out.write(block_comment(interrogate_make_seq_comment(seq)))

                num_name = interrogate_make_seq_num_name(seq)
                element_name = interrogate_make_seq_element_name(seq)
                out.writeln()
                out.writeln("See :py:meth:`{}` and :py:meth:`{}`.".format(element_name, num_name))

        for i_element in range(interrogate_type_number_of_elements(type)):
            process_element(out, interrogate_type_get_element(type, i_element))

        for i_ntype in range(interrogate_type_number_of_nested_types(type)):
            process_type(out, interrogate_type_get_nested_type(type, i_ntype))


def process_global_type(module_name, type):
    if interrogate_type_is_nested(type):
        return

    type_name = translated_type_name(type, scoped=False)

    if not interrogate_type_is_fully_defined(type):
        print(type_name, "is not fully defined")
        return

    if interrogate_type_is_unpublished(type):
        print(type_name, "is unpublished")
        return

    if interrogate_type_is_enum(type) and not type_name:
        return

    out = ReSTWriter()
    out.open("source/reference/{}/{}.rst".format(module_name, type_name))

    description = ""

    if interrogate_type_has_comment(type):
        comment = interrogate_type_comment(type)
        description = block_comment(comment)

    if interrogate_type_is_typedef(type):
        out.writeln(':orphan:')
        out.writeln()

    out.writeln(type_name)
    out.writeln("=" * len(type_name))

    if description:
        out.writeln()
        out.write(description)

    out.directive("currentmodule:: {}".format(module_name))

    process_type(out, type, skip_comment=True)

    # Now add aliases.
    if not interrogate_type_is_typedef(type):
        for i_type in range(interrogate_number_of_global_types()):
            typedef = interrogate_get_global_type(i_type)

            if interrogate_type_is_nested(typedef):
                continue

            if interrogate_type_is_typedef(typedef):
                wrapped_type = interrogate_type_wrapped_type(typedef)
                if type_name == translated_type_name(wrapped_type):
                    process_type(out, typedef)

    out.close()


def process_library(out, module_name, lib_name):
    classes = []
    for i_type in range(interrogate_number_of_global_types()):
        type = interrogate_get_global_type(i_type)

        if interrogate_type_is_nested(type):
            continue

        if not interrogate_type_is_fully_defined(type):
            continue

        if interrogate_type_is_unpublished(type):
            continue

        if interrogate_type_library_name(type) == lib_name and not interrogate_type_is_typedef(type):
            typename = translated_type_name(type, scoped=False)
            if typename:
                classes.append(typename)

    classes.sort()

    with out.directive("toctree::"):
        out.writeln(":titlesonly:")
        out.writeln()
        for typename in classes:
            out.writeln("/reference/" + module_name + "/" + typename)

    # Write global enums.
    for i_type in range(interrogate_number_of_global_types()):
        type = interrogate_get_global_type(i_type)

        if interrogate_type_is_nested(type):
            continue

        if not interrogate_type_is_fully_defined(type):
            continue

        if interrogate_type_is_unpublished(type):
            continue

        if interrogate_type_library_name(type) == lib_name and interrogate_type_is_enum(type):
            typename = translated_type_name(type, scoped=False)
            #if not typename:
            process_type(out, type)

    # Write global functions.
    has_header = False
    for i_func in range(interrogate_number_of_global_functions()):
        func = interrogate_get_global_function(i_func)

        if interrogate_function_has_library_name(func):
            if lib_name == interrogate_function_library_name(func):
                if not has_header:
                    out.writeln()
                    out.writeln("Global Functions")
                    out.writeln("----------------")
                    has_header = True
                process_function(out, func)
        else:
            print("Type %s has no module name" % typename)


def process_module(module_name):
    dirname = "source/reference/" + module_name
    if not os.path.isdir(dirname):
        os.mkdir(dirname)

    out = ReSTWriter()
    out.open(os.path.join(dirname, "index.rst"))

    out.writeln(module_name)
    out.writeln("=" * len(module_name))

    out.directive("module:: " + module_name)

    #with out.directive("toctree::"):
    #    out.writeln(":titlesonly:")
    #    out.writeln()

    libraries = defaultdict(list)

    for i_type in range(interrogate_number_of_global_types()):
        type = interrogate_get_global_type(i_type)

        if interrogate_type_is_nested(type):
            continue

        if interrogate_type_module_name(type) == module_name:
            process_global_type(module_name, type)
            if not interrogate_type_is_typedef(type):
                lib_name = interrogate_type_library_name(type)
                typename = translated_type_name(type, scoped=False)
                libraries[lib_name].append(typename)

    out.writeln()
    out.writeln("This module contains the following classes:")

    if len(libraries) > 1:
        with out.directive("toctree::"):
            #out.writeln(":titlesonly:")

            out.writeln()

            for lib_name, classes in sorted(libraries.items(), key=lambda k: library_ordering.index(k[0]) if k[0] in library_ordering else 100000):
                out.writeln("../{}".format(lib_name))

                out2 = ReSTWriter()
                out2.open(os.path.join("source", "reference", lib_name + ".rst"))
                lib_title = library_titles.get(lib_name, lib_name)
                out2.writeln(lib_title)
                out2.writeln("=" * len(lib_title))

                if module_name == "panda3d.direct":
                    dir_name = lib_name
                    if dir_name.startswith("lib"):
                        dir_name = dir_name[3:]
                    if dir_name.startswith("p3"):
                        dir_name = dir_name[2:]
                    if dir_name.startswith("panda"):
                        dir_name = dir_name[5:]
                    if os.path.isfile(os.path.join(os.path.dirname(direct.__file__), dir_name, "__init__.py")):
                        out2.writeln()
                        out2.writeln("Also see the :py:mod:`direct.{}` module.".format(dir_name))

                process_library(out2, module_name, lib_name)
                out2.close()
    else:
        for lib_name in libraries.keys():
            process_library(out, module_name, lib_name)

    out.writeln()
    #out.discard()


if __name__ == "__main__":
    if not os.path.isdir("source"):
        os.mkdir("source")
    if not os.path.isdir("source/reference"):
        os.mkdir("source/reference")

    # Determine the path to the interrogatedb files
    #interrogate_add_search_directory(os.path.join(os.path.dirname(pandac.__file__), "..", "..", "etc"))
    interrogate_add_search_directory(os.path.join(os.path.dirname(pandac.__file__), "input"))

    process_module("panda3d.core")

    import panda3d.direct
    process_module("panda3d.direct")

    import panda3d.egg
    process_module("panda3d.egg")

    import panda3d.fx
    process_module("panda3d.fx")

    import panda3d.physics
    process_module("panda3d.physics")

    import panda3d.vision
    process_module("panda3d.vision")

    import panda3d.ode
    process_module("panda3d.ode")

    import panda3d.bullet
    process_module("panda3d.bullet")

    import panda3d.ai
    process_module("panda3d.ai")

    #idb_dir = os.path.join(os.path.dirname(pandac.__file__), "input")
    #for in_file in os.listdir(idb_dir):
    #    if in_file.endswith(".in"):
    #        interrogate_request_database(os.path.join(idb_dir, in_file))

    #for lib in os.listdir(os.path.dirname(panda3d.__file__)):
    #    if lib.endswith(('.pyd', '.so')) and not lib.startswith('core.'):
    #        module_name = lib.split('.')[0]
    #        if module_name != 'physx':
    #            __import__("panda3d." + module_name)
    #            process_module(module_name)
