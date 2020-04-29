from conans import ConanFile, CMake, tools, __version__ as conan_version
from conans.model.version import Version
from conans.tools import download, unzip
import os, re
import shutil

class ArpackNG(ConanFile):
    name = "arpack-ng"
    version = "3.7.0"
    license = "BSD"
    url = "https://github.com/opencollab/arpack-ng"
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake"
    build_policy    = 'missing'
    options         = {
        "shared"            : [True, False],
        "fPIC"              : [True, False],
        "blas"              : ['OpenBLAS','MKL','Intel','Intel10_64lp','Intel10_64lp_seq','Intel10_64ilp',
                               'Intel10_64lp_seq', 'FLAME', 'Goto', 'ATLAS PhiPACK','Generic','All'],
        "interface64"       : [True,False],
        "mpi"               : [True,False],
        "prefer_pkgconfig"  : [True,False],
        "blas_libraries"    : "ANY",
        "lapack_libraries"  : "ANY",
    }
    default_options = {
        "shared"            : False,
        "fPIC"              : True,
        "blas"              : "OpenBLAS",
        "interface64"       : False,
        "mpi"               : False,
        "prefer_pkgconfig"  : False,
        "blas_libraries"    : None,
        "lapack_libraries"  : None,
    }

    _source_subfolder = "arpack-ng-" + version
    _build_subfolder  = "arpack-ng-" + version

    def requirements(self):
        if self.options.blas == "OpenBLAS":
            self.requires("openblas/0.3.7")

    def configure(self):
        if self.options.blas == "MKL":
            self.options.blas = "Intel10_64lp"
        if self.options.blas == "OpenBLAS":
            self.options["openblas"].build_lapack = True
            self.options["openblas"].dynamic_arch = False
            self.options["openblas"].fPIC = self.options.fPIC
            self.options["openblas"].shared = self.options.shared

    def source(self):

        ext = "tar.gz" if tools.os_info.is_linux else "zip"
        md5 = "6fc6c6bf78dbd4f144595ef0675c8430" if tools.os_info.is_linux else "aa3f1ff2645fdec744ecd30461e21291"
        url = "https://github.com/opencollab/arpack-ng/archive/{0}.{1}".format(self.version,ext)
        tools.get(url=url, md5=md5)

    def build(self):
        cmake = CMake(self)
        cmake.definitions["BUILD_SHARED_LIBS"] = self.options.shared
        cmake.definitions["BLA_VENDOR"] = self.options.blas
        cmake.definitions["BLA_STATIC"] = not self.options.shared
        cmake.definitions["BLA_PREFER_PKGCONFIG"] = self.options.prefer_pkgconfig
        cmake.definitions["EXAMPLES"] = False
        cmake.definitions["MPI"] = self.options.mpi
        cmake.definitions["CMAKE_POSITION_INDEPENDENT_CODE"] = self.options.fPIC
        cmake.definitions["INTERFACE64"] = self.options.interface64
        if self.options.blas == "OpenBLAS":
            valid_ext = []
            if self.options.shared:
                valid_ext = ['.so', '.dll','.dylib']
            else:
                valid_ext = ['.a', '.lib']
            openblas_libs = []
            for path in self.deps_cpp_info["openblas"].lib_paths:
                for file in os.listdir(path):
                    if "openblas" in file and any(file.endswith(ext) for ext in valid_ext):
                        openblas_libs.append(path + '/' + file)
            for lib in self.deps_cpp_info["openblas"].system_libs:
                openblas_libs.append(lib)

            openblas_libs=';'.join(str(x) for x in openblas_libs)
            cmake.definitions["BLAS_LIBRARIES"]     = openblas_libs
            cmake.definitions["LAPACK_LIBRARIES"]   = openblas_libs
        # Override
        if self.options.blas_libraries:
            cmake.definitions["BLAS_LIBRARIES"]     = self.options.blas_libraries
        if self.options.lapack_libraries:
            cmake.definitions["LAPACK_LIBRARIES"]   = self.options.lapack_libraries

        cmake.configure(source_folder=self._build_subfolder)
        cmake.build()
        cmake.install()

    def package(self):
        self.copy(pattern="COPYING", src=self._source_subfolder, dst=".")
        self.copy(pattern="COPYING", src=self._source_subfolder, dst="LICENSE")

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.cpp_info.names["cmake_find_package"] = "arpack-ng"
        self.cpp_info.names["cmake_find_package_multi"] = "arpack-ng"
        self.cpp_info.names['pkg_config'] = "arpack-ng"
        if not self.cpp_info.libs:
            raise Exception("No libs collected")
