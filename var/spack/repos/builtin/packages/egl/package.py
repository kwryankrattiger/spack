# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import re
import sys

from spack.package import *


class Egl(BundlePackage):
    """Shim package for the EGL library."""

    homepage = "https://www.khronos.org/egl"
    maintainers("biddisco")

    version("1.5")

    depends_on("libegl")

    provides("gl@4.5")

    @property
    def home(self):
        return self.spec["libegl"].home

    @property
    def headers(self):
        return self.spec["libegl"].headers

    @property
    def libs(self):
        return self.spec["libegl"].libs

    @property
    def gl_headers(self):
        return self.spec["libegl"].gl_headers

    @property
    def gl_libs(self):
        return self.spec["libegl"].gl_libs

