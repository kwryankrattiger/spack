# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Opengles(BundlePackage):
    """Shim package for OpenGL ES"""

    # FIXME: Add a proper url for your package's homepage here.
    homepage = "https://registry.khronos.org/OpenGL/index_es.php"

    version("3.0")
    version("2.0", preferred=True)
    version("1.1", deprecated=True)

    provides("gles@1", when="@1.1")
    provides("gles@2", when="@2")
    provides("gles@3", when="@3.0")

    # GLES v3.1 and 3.2 support is available in spack
    conflicts("@3.1:")

    # GLES is only supported on Linux for now in spack
    conflicts("platform=darwin")
    conflicts("platform=windows")

    # Override the fetcher method to throw a useful error message
    @property
    def fetcher(self):
        msg = """This package is intended to be a placeholder for
        system-provided OpenGL ES libraries from hardware vendors.  Please
        download and install OpenGL drivers/libraries for your graphics
        hardware separately, and then set that up as an external package.
        An example of a working packages.yaml:

        packages:
          opengles:
            buildable: False
            externals:
            - spec: opengles@2
              prefix: /opt/opengl

        In that case, /opt/opengl/ should contain these two folders:

        include/GLES[2|3]/     (opengl headers, including "gl[2|3].h")
        lib                    (opengl libraries, including "libGLESv[2|3].so")
        """
        raise InstallError(msg)

    @fetcher.setter  # Since fetcher is read-write, must override both
    def fetcher(self):
        _ = self.fetcher

    @property
    def headers(self):
        return self.gles_libs

    @property
    def libs(self):
        return self.gles_libs

    @property
    def gles_headers(self):
        if self.spec.satisfies("@1.1"):
            header_name = [
                "GLES/gl.h",
                "GLES/glext.h",
                "GLES/glplatform.h",
                "GLES/egl.h",
            ]
        elif self.spec.satisfies("@2.0"):
            header_name = [
                "GLES2/gl2.h",
                "GLES2/gl2ext.h",
                "GLES2/gl2platform.h",
            ]
        elif self.spec.satisfies("@3.0"):
            header_name = [
                "GLES3/gl3.h",
                "GLES2/gl2ext.h",
                "GLES3/gl3platform.h",
            ]
        return find_headers(header_name, root=self.prefix, recursive=True)

    @property
    def gles_libs(self):
        if self.spec.satisfies("@1.1"):
            lib_name = "libGLESv1_CM"
        elif self.spec.satisfies("@2:3.0"):
            lib_name = "libGLESv2"

        return find_libraries(lib_name, root=self.prefix, recursive=True)
