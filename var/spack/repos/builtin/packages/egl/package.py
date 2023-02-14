# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Egl(BundlePackage):
    """Shim package for the EGL library."""

    homepage = "https://registry.khronos.org/EGL/"

    version("1.4")

    # If not external, depends on a libegl provider
    depends_on("libegl")

    @property
    def home(self):
        return self.spec["libegl"].home

    @property
    def headers(self):
        if "libegl" in self.spec:
            return self.spec["libegl"].headers
        else:
            return find_headers("EGL/egl.h", root=self.prefix, recursive=True)

    @property
    def libs(self):
        if "libegl" in self.spec:
            return self.spec["libegl"].headers
        else:
            return find_libraries("libEGL", root=self.prefix, recursive=True)
